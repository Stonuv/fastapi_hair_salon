# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

"Барбершоп «Сайтама»" — a barbershop booking CMS. FastAPI + SQLAlchemy + PostgreSQL backend, Vue 3 + Pinia + Vite frontend. This is a coursework/portfolio project built against an explicit graded requirements spec (see "Project requirements spec" below) — features like RBAC, overlap-checked booking, an admin panel, and API docs exist because the spec scores them, not just for their own sake.

## Commands

### Backend (run from `backend/`)
```bash
source venv/bin/activate                 # venv already created, Python 3.14
pip install -r requirements.txt
python run.py                            # uvicorn on :8000, reload=settings.debug, docs at /api/docs
alembic revision --autogenerate -m "..." # new migration (models/__init__.py imports must stay exhaustive or autogen misses tables)
alembic upgrade head
python -m pytest tests/                  # unit tests (no DB needed: fakes for repositories, pure schema/function tests)
```
There is no configured lint/format command (no black, ruff, or eslint config present in either package) — don't assume one exists. Tests live in `backend/tests/` and deliberately avoid PostgreSQL: services are constructed via `__new__` with fake repositories; the DB-level EXCLUDE constraint is not covered by them.

### Frontend (run from `frontend/`)
```bash
npm install
npm run dev       # vite dev server, expects backend on :8000 (proxy baseURL is "/api")
npm run build
```

### Type checking
`pyrightconfig.json` points at `backend/venv` (the real virtualenv), `typeCheckingMode: basic`.

### Deploy
`docker-compose.yml` at the repo root builds the full stack (PostgreSQL 16 + backend with auto-migrations + nginx serving the SPA and proxying `/api`); requires `SECRET_KEY` in the environment because the compose file sets `DEBUG=false` and `Settings` fail-fasts on the default secret outside debug.

## Architecture

### Backend layering
Strict `routes -> services -> repositories -> models` layering, one file per entity across all four layers:
- **routes/** — FastAPI routers, only request/response wiring + `Depends`-based auth. No business logic.
- **services/** — business rules, orchestrate one or more repositories, raise `HTTPException` directly (no separate exception-translation layer).
- **repositories/** — all `Session`/query code lives here. Routes and services never touch `db.query` directly.
- **models/** — SQLAlchemy ORM classes, one file per table. **`models/__init__.py` must import every model** — Alembic's autogenerate only sees models reachable from that file.

`database.py` exposes `get_db()` as the FastAPI dependency; every route takes `db: Session = Depends(get_db)`.

`models/mixins.py` provides `UUIDPrimaryKeyMixin`, `TimestampMixin` (DB-side `created_at`), and `SoftDeleteMixin` (`deleted_at` + `is_deleted` property) — mixed into models rather than repeating the same three columns everywhere. `repositories/_query_utils.py::paginated()` is the shared offset/limit + count helper used by every `list_paginated()` repository method; pair it with `schemas/pagination.py`'s `PageParams` (FastAPI class-dependency for `?page=&page_size=`, max 20/page) and generic `PageResponse[T]` for the response side.

### Auth & RBAC
JWT bearer auth via `python-jose`, password hashing via `bcrypt`, all in `services/auth_service.py`. Three roles in `models/enums.py::UserRole`: `client`, `master`, `admin`. Role gates are built with `require_role(*roles)`, which produces a FastAPI dependency; the three pre-built ones are `get_current_client`, `get_current_master`, `get_current_admin` (all of which also implicitly allow `admin`). A `Master` is a 1:1 profile attached to a `User` with `role == master` — `master_repo.get_by_user_id()` is how services map "the logged-in user" to "their master row" for ownership checks. `User.is_blocked` (admin-toggled via `PATCH /api/admin/users/{id}/block`) is distinct from soft delete: the account and history stay, but login returns 403 and `get_current_user` rejects previously issued tokens. Login is rate-limited (5 failures per 15 min per email, via the `login_attempts` audit table); `AuthService.login` commits the attempt row explicitly because `get_db` rolls back on `HTTPException`.

The access token is delivered two ways from the same response: as `TokenResponse.access_token` in the JSON body (for Swagger's "Authorize" and non-browser API clients) and as an httpOnly `access_token` cookie (`set_auth_cookie()`/`clear_auth_cookie()`, path `/api`) that the Vue SPA relies on exclusively — `get_current_user`/`get_current_user_optional` accept either source (`_token_from_request()`: cookie first, then `Authorization: Bearer`). `User.token_version` is embedded in the JWT payload (`ver`) at issuance and compared against the DB value on every request; `UserRepository.bump_token_version()` increments it on logout (`AuthService.logout`), password change/reset (`AuthService.confirm_password_reset`, `AdminService.update_user` when `new_password` is set), and admin block (`AdminService.set_blocked(True)`) — this is what actually revokes a JWT, since the token itself is never denylisted. `settings.cookie_secure` gates the cookie's `Secure` flag and is deliberately **not** tied to `settings.debug`: the project's own docker-compose runs `DEBUG=false` over plain HTTP (TLS is left to an external terminator per README), so tying `Secure` to `debug` would silently break login there.

### Booking / overlap logic
This is the core business rule and is intentionally enforced at two layers:
1. **Application layer** — `AppointmentRepository.get_overlapping()` checks `start_time < end_time AND end_time > start_time` against non-cancelled appointments for a master, called from `AppointmentService.create()` before insert.
2. **Database layer** — the initial Alembic migration (`alembic/versions/0001_initial.py`) adds the `btree_gist` extension and an `EXCLUDE USING gist` constraint on `appointments`, which cannot be expressed via SQLAlchemy's declarative API and is written as raw SQL in the migration. This is the actual race-condition-proof guarantee; the repository check is a pre-flight for a clean error message. The constraint carries `WHERE (status <> 'cancelled')` — without that predicate a cancelled appointment would permanently block re-booking the same slot at the DB level even though the app-level check allows it (this was a real bug, fixed when the schema was rewritten).

Appointment status follows an explicit state machine, `ALLOWED_TRANSITIONS` in `services/appointment_service.py`: `pending → {confirmed, cancelled}`, `confirmed → {done, cancelled}`, `done`/`cancelled` are terminal. `AppointmentService.update_status()` (master/admin, via `PATCH /api/appointments/{id}/status`) and `.cancel()` (client-only, via `POST /api/appointments/{id}/cancel`) both check against this table — don't mutate `appointment.status` directly anywhere else.

`AppointmentService.create()` also computes `end_time` (`start_time + service.duration_min`) and `final_price` (`MasterService.price_override` if set, else `service.price * master.coefficient`) before handing off to the repository — repositories never compute, only persist. `final_price` is snapshotted onto the appointment row at creation time and is not recalculated if the service price changes later.

Available slots (`AppointmentService.get_available_slots`) are generated by walking the master's `Schedule` for that weekday in `service.duration_min` steps; on hitting a booked interval the walk jumps to that booking's end (not a fixed grid — otherwise a booking misaligned with the step would eat two slots and real gaps between bookings would never be offered). Booked intervals come from `get_by_master_in_range`, which matches by interval overlap (not `start_time` containment) and excludes cancelled in SQL. Past slots for today are filtered out. This is still separate code from the overlap check above and can drift from it if one is changed without the other.

**Timezone convention: the salon "lives" in UTC.** `Schedule.start_time/end_time` are salon wall-clock times interpreted as UTC; `AppointmentCreate.start_time` requires an offset (`AwareDatetime`) and is normalized to UTC by a schema validator, so weekday selection and the working-hours window are computed identically in `_validate_within_schedule` and `get_available_slots`. Reports/stats cut days by UTC (`func.timezone("UTC", …)` before `func.date`). The frontend renders all appointment/slot times with `timeZone: 'UTC'` (salon wall-clock, not browser-local) and builds date strings from the UTC calendar — keep any new date formatting consistent with this.

### Data model
Tables: `users`, `masters` (1:1 to a `user`), `master_services` (M:N join between `masters`/`services`, carries optional `price_override`), `services`, `schedules` (per-master, per-weekday working hours), `appointments`, `reviews` (1:1 off a `done` appointment — denormalizes `master_id`/`service_id` from the appointment so master/service review queries don't need a join), `password_reset_tokens` (only a SHA-256 hash of the token is stored, never the raw token), `login_attempts` (audit log, `user_id` nullable since a failed login may not match any account). All PKs are UUIDs generated client-side (`uuid.uuid4` default).

FK `ondelete` is deliberate: `CASCADE` for owned child rows (master's services/schedules, appointment's review, password reset tokens, review's denormalized FKs), `RESTRICT` on `appointments.{client_id,master_id,service_id}` so a user/master/service can't be deleted out from under historical bookings, `SET NULL` on `login_attempts.user_id`.

`User`, `Master`, and `Service` use `SoftDeleteMixin` (`deleted_at`) instead of hard delete — `AdminService.delete_user()`/`delete_service()` set the timestamp rather than calling `db.delete()`, and every repository read path filters `deleted_at IS NULL` by default. Because soft-deleted rows still occupy their `email`/`phone`/`user_id` values, uniqueness on those columns is enforced via **partial unique indexes** (`WHERE deleted_at IS NULL`, see `0001_initial.py`) rather than plain `unique=True` — otherwise a soft-deleted user would permanently block that email from re-registering. `Service.is_active` is a separate, unrelated boolean — it's the catalog publish/unpublish toggle, not a deletion marker.

`Master` exposes `first_name`/`last_name` as Python `@property` passthroughs to `self.user` — needed because `AppointmentResponse.master: MasterBriefResponse` validates straight off the ORM `Master` object via `from_attributes=True`, and `MasterBriefResponse` expects those fields at the top level.

### Frontend
Vue 3 `<script setup>` + Pinia + Vue Router + Tailwind, no TypeScript. Design tokens (colors, fonts) live in `tailwind.config.js`; the full design rationale (palette, typography, layout patterns per page type, component specs) is in `design-system/saitama-barbershop/MASTER.md` — read that before changing visual style, it documents *why* choices were made (e.g. why the auto-generated tool suggestion was overridden).

`src/api/client.js` is the single axios instance (bearer token interceptor + 401 → redirect to `/login`); each resource gets its own module (`auth.js`, `masters.js`, `services.js`, `appointments.js`, `reviews.js`, `admin.js`) re-exported from `src/api/index.js`. `src/stores/auth.js` is the session source of truth (token in `localStorage` + reactive `user`, `ready` flag so router guards know when `fetchMe()` has resolved); `stores/toast.js` is the global toast queue (auto-dismiss 4s, rendered by `components/ui/ToastContainer.vue` in `App.vue`); `stores/masterProfile.js` caches the logged-in master's own profile (needed because there's no way to derive your own `master_id` other than `GET /api/masters/me`).

Routing (`src/router/index.js`) is nested for the two dashboard areas: `/dashboard` (master, `meta.roles: ['master']`) and `/admin` (admin only) each have a layout component (`views/MasterDashboard.vue`, `views/AdminPanel.vue`) that renders `DashboardLayout.vue` (sidebar shell) + `<router-view>` for child pages (`views/dashboard/*`, `views/admin/*`). Public/client pages use the flat top-nav `AppHeader.vue` instead — `App.vue` picks between the two via `route.meta.hideHeader`. The `router.beforeEach` guard awaits `auth.fetchMe()` once (`auth.ready`) before evaluating `meta.requiresAuth`/`meta.roles`/`meta.guestOnly`.

Shared primitives live in `components/ui/` (BaseButton, BaseInput, BaseSelect, BaseCard, StatusPill, Pagination, ConfirmDialog, Skeleton, EmptyState, StarRatingInput, StepTitle) — build new UI from these rather than one-off markup. `composables/useFormErrors.js` gives inline field errors (+ best-effort mapping of FastAPI 422 responses); `composables/useDebouncedWatch.js` debounces filter/search inputs before refetching.

`views/admin/AdminSettingsLive.vue` (sidebar "Настройки (тест)", route `admin-settings-live`) is an experimental parallel to `AdminSettings.vue` — a true WYSIWYG editor that renders the real `AppHeader` + `HomePreview` + `AppFooter` at full scale and lets you click any text in place instead of filling a side form, with a sticky bottom toolbar for hero variant / theme presets / fonts / manual colors / save. It's built on two additive props threaded through those three components: `content` (object, falls back to the `siteContent` store when omitted) and `editable` (boolean, default `false` — so the public site and `AdminSettings.vue`'s own shrunk preview render exactly as before). When `editable` is true, text nodes render through `components/ui/EditableText.vue` (swaps plain text for an `<input>`/auto-growing `<textarea>` styled to match) and navigational buttons/links render through `components/ui/EditableLink.vue` (swaps `router-link`/`<a>` for a non-navigating `<span>` — needed because a real `router-link` still navigates on click even if you `preventDefault()` in a parent handler, which would otherwise yank you off the settings page while trying to edit the brand name or hero CTA text). Both new pages read/write the same `GET`/`PATCH /api/settings` as `AdminSettings.vue` — there is exactly one CMS content model, just two editors for it.

Several backend response shapes were extended specifically to support the frontend (don't re-derive these as bugs if you see them): `AppointmentBriefResponse`/`ReviewResponse` carry denormalized `*_name` fields and `AppointmentBriefResponse.review_id` (nullable) so list views don't need N+1 lookups just to render a name or know whether a review already exists.

## Project requirements spec

The original task brief (in Russian, `claude_hints.md`) encodes the grading rubric this project is built against. Key mandates for any backend code you write or modify:
- **Pydantic v2 strict**: `Annotated[...]`-style field declarations, `model_config = ConfigDict(from_attributes=True)` — no v1 `class Config`, no bare `Field(...)` without `Annotated`. Followed throughout `schemas/`; shared `Annotated` aliases live in `schemas/fields.py` (e.g. `NameStr`, `PositiveMoney`) specifically for the reuse-across-schemas reason the spec calls out.
- **SQLAlchemy 2.0 strict**: `Mapped[...]` + `mapped_column()`, typed `Mapped[list["X"]]` relationships, no legacy `Column(...)` and no `db.query(Model)`. Followed throughout `models/` and `repositories/` (the latter use `select()` + `session.execute()`).
- Every FK needs an explicit `ondelete` (`CASCADE`, `RESTRICT`, or `SET NULL`) — see the Data model section above for which is used where.
- Booking overlap checks must stay atomic / race-safe — this is the rubric's top business-logic priority, hence the DB-level `EXCLUDE` constraint described above.
- Rubric also expects: search/filter/pagination (`PageParams`/`PageResponse[T]`, used on services/masters/appointments/reviews/admin-users lists), a state machine for appointment status transitions (`ALLOWED_TRANSITIONS`), an admin dashboard with stats (`GET /api/admin/stats`), Swagger docs (already at `/api/docs`). Still outstanding / explicitly out of scope: OAuth login and real email delivery (no SMTP provider — password reset logs the link via `logging` instead, see `AuthService.request_password_reset()`), responsive frontend work, deployment/HTTPS/CI — treat these as the backlog when asked "what's left."
