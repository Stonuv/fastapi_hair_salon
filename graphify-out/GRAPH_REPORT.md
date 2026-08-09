# Graph Report - .  (2026-08-05)

## Corpus Check
- 251 files · ~85,364 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2197 nodes · 5360 edges · 153 communities (128 shown, 25 thin omitted)
- Extraction: 93% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 346 edges (avg confidence: 0.54)
- Token cost: 125,827 input · 0 output

## Community Hubs (Navigation)
- Site Settings & Setup Service
- Master Photo & Schema Fields
- Frontend Base UI Components
- Alembic Env & Core Models
- App Bootstrap & Auth Store
- VK OAuth PKCE Login
- Auth Service Email/Password Flows
- Auth Service Unit Tests
- Master Schedule Repository
- User Model & VK Linking
- Appointment Model
- Admin Routes
- Admin Users View
- Appointment Status & Reschedule Tests
- Login & Setup Wizard Routes
- Content Filter Utility
- Booking Slots Tests
- Master Service & Soft Delete
- Master Routes Handlers
- Image Upload Component
- Services Routes
- Admin Reports Repository
- Auth Routes & Schemas
- Booking Page Flow
- Appointment Service
- DB Session & Login Attempts
- Appointment Routes
- Toast & VK Login UI
- Salon Scope Resolution
- Admin Role Assignment Tests
- Frontend API Clients
- Home Preview & Hero Editing
- Master Service Pricing Logic
- Date Input Component
- Salon Routes & Repository
- Salon Repository Slug Logic
- Auth Schemas & Password Reset
- Appointment Schemas
- Admin Services View
- Appointment Status Utilities
- Profile Page
- Form Error Handling
- Admin Reports View
- Setup Wizard Frontend
- Master Profile Admin Tests
- Review Routes
- Upload Utilities
- Master Repository
- Admin Salons View
- Review Model & Repository
- Slug Generation Utility
- Business Hours Fakes
- Admin Session Revocation Tests
- Master Dashboard Schedule View
- Frontend Dev Dependencies
- Repository Query Utilities
- Salon Service & Setup
- Appointment Create Guard Tests
- Hero 3D Room Component
- Password Reset Token
- Review Creation Schema
- Pagination Schemas
- Salon Scoping Integration Tests
- Appointment State Machine Tests
- Admin Stats Cards
- Frontend Runtime Dependencies
- Master Schedule Model
- Admin Reports Routes
- Client IP & Rate Limit Utils
- Admin Site Theme Settings
- Reschedule Modal
- Email Verification Token Repository
- Admin Stats Repository
- Docker Compose Services Overview
- Password Reset Page
- Rate Limit Handler Tests
- Double Booking Constraint Tests
- Health Check Endpoint Tests
- Reminder Service Tests
- Site Content Store & SEO
- CI & Dependency Config
- Concurrent Booking Test Helpers
- Admin Role Assignment Flow Tests
- Salon-Scoped Appointment Get Tests
- Master Management Authorization Tests
- Frontend NPM Scripts
- Time Input Component
- App Config & Settings
- Main App & Reminder Scheduler
- Rate Limit Wiring Tests
- App Footer Component
- App Header Component
- Registrations Chart Component
- Admin Stats Schema
- Reminder Service
- Editable Text Component
- Theme Presets
- E2E Core Flows Test
- Salon List Route
- Pagination Query Params
- Prettier Config
- Salon Landing Hero Screenshot
- Salon Scoping Migration
- Frontend Package Metadata
- Status Pill Component
- Design System Anti-Patterns & Layout
- Auth Security Measures
- Autoprefixer Dependency
- Backend Test Fixtures
- Mailpit Dev SMTP
- ESLint Dependency
- ESLint JS Config Dependency
- Typography Discrepancy (Design vs HTML)
- SEO & Analytics Tags
- Globals Dependency
- Jsdom Dependency
- Playwright Dependency
- Tailwind Dependency
- Vitest Dependency
- Frontend Build CI & npm audit
- Appointment State Machine & Architecture
- Deploy Script
- Design System Color Palette
- Favicon Monogram Icon
- Compose Validate CI Job
- Frontend Lint CI Job
- Frontend Unit Tests CI Job
- Inline WYSIWYG Editor
- UTC Timezone Policy

## God Nodes (most connected - your core abstractions)
1. `User` - 111 edges
2. `Session` - 107 edges
3. `UserRole` - 85 edges
4. `extractErrorMessage()` - 76 edges
5. `AppointmentService` - 70 edges
6. `UserRepository` - 47 edges
7. `AuthService` - 44 edges
8. `Appointment` - 43 edges
9. `AppointmentStatus` - 39 edges
10. `Master` - 38 edges

## Surprising Connections (you probably didn't know these)
- `Dependabot Configuration (pip/npm/docker/github-actions weekly updates)` --conceptually_related_to--> `docker-compose.yml (production stack: Postgres + FastAPI + nginx SPA + Caddy)`  [AMBIGUOUS]
  .github/dependabot.yml → docker-compose.yml
- `Double-booking protection (repo check + EXCLUDE USING gist)` --references--> `docker-compose.yml (production stack: Postgres + FastAPI + nginx SPA + Caddy)`  [AMBIGUOUS]
  README.md → docker-compose.yml
- `First-run /setup admin creation wizard` --references--> `docker-compose.yml service: backend (FastAPI)`  [INFERRED]
  README.md → docker-compose.yml
- `Dependabot Configuration (pip/npm/docker/github-actions weekly updates)` --references--> `Backend production dependencies (requirements.txt)`  [INFERRED]
  .github/dependabot.yml → backend/requirements.txt
- `CI job: backend-integration-tests (real Postgres)` --references--> `Double-booking protection (repo check + EXCLUDE USING gist)`  [INFERRED]
  .github/workflows/ci.yml → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **All GitHub Actions CI jobs in ci.yml** — github_workflows_ci_backend_tests, github_workflows_ci_backend_lint, github_workflows_ci_backend_integration_tests, github_workflows_ci_frontend_build, github_workflows_ci_frontend_unit_tests, github_workflows_ci_frontend_e2e, github_workflows_ci_frontend_lint, github_workflows_ci_compose_validate [EXTRACTED 1.00]
- **Authentication security section of README (token revocation, cookie storage, VK ID, rate limiting)** — readme_jwt_token_revocation, readme_httponly_cookie_auth, readme_vk_id_oauth, readme_rate_limiting [INFERRED 0.85]
- **Full docker-compose.yml production stack (Postgres, backend, frontend, Caddy, backups)** — docker_compose_db, docker_compose_backend, docker_compose_frontend, docker_compose_caddy, docker_compose_backup_local, docker_compose_backup_s3 [EXTRACTED 1.00]

## Communities (153 total, 25 thin omitted)

### Community 0 - "Site Settings & Setup Service"
Cohesion: 0.05
Nodes (46): Глобальные настройки/контент сайта — singleton, всегда ровно одна строка…, SiteSettings, SiteSettingsRepository, get_setup_status(), get, Публичный эндпоинт: нужен ли фронтенду показать визард первого запуска и…, get_settings(), get (+38 more)

### Community 1 - "Master Photo & Schema Fields"
Cohesion: 0.10
Nodes (32): Обновить (или очистить — photo_url=null) фото мастера., update_master_photo(), Переиспользуемые Annotated-типы для полей схем (см. claude_hints.md)., MasterPhotoUpdate, MasterPublicResponse, MasterResponse, MasterServiceCreate, MasterServiceResponse (+24 more)

### Community 2 - "Frontend Base UI Components"
Cohesion: 0.05
Nodes (32): sizes, variants, useDebouncedWatch(), isPublished, load(), loading, minRating, moderating (+24 more)

### Community 3 - "Alembic Env & Core Models"
Cohesion: 0.17
Nodes (14): Base, EmailVerificationToken, Токен подтверждения email. В БД хранится только SHA-256 хеш токена — сам токен…, LoginAttempt, Аудит-лог попыток входа (требование 5.1 — логирование попыток авторизации)., Master, PK-столбец, общий для всех сущностей домена., Момент создания записи — выставляется на стороне БД. (+6 more)

### Community 4 - "App Bootstrap & Auth Store"
Cohesion: 0.07
Nodes (30): authApi, setUnauthorizedHandler(), route, auth, { content }, mobileOpen, router, auth (+22 more)

### Community 5 - "VK OAuth PKCE Login"
Cohesion: 0.11
Nodes (19): vk_login(), _b64url(), build_authorize_url(), generate_pkce(), is_enabled(), (code_verifier, code_challenge) для OAuth 2.1 PKCE, метод S256., Ошибка на любом шаге обмена кода VK ID. Роут ловит её и делает redirect на…, VkOAuthError (+11 more)

### Community 6 - "Auth Service Email/Password Flows"
Cohesion: 0.10
Nodes (17): AuthService, _hash_token(), Если email зарегистрирован — создаёт токен сброса и отправляет ссылку письмом…, Отправляет письмо со ссылкой подтверждения email — после регистрации и при…, Повторная отправка по явному запросу пользователя (кнопка «отправить письмо ещё…, Удаляет ровно текущую сессию (устройство) — не трогает остальные. Access-токен…, В БД хранится только хеш — сам токен живёт лишь в ссылке пользователю., make_service() (+9 more)

### Community 7 - "Auth Service Unit Tests"
Cohesion: 0.08
Nodes (16): require_role(), _verify_password(), _FakeDb, make_auth_service(), Пароли и RBAC-зависимости — без БД., logout() отзывает ровно текущую сессию по refresh-токену устройства, а не все…, Успешный refresh удаляет старую сессию и создаёт новую — старый refresh-токен…, Пользователь удалён между выдачей refresh-токена и его использованием — сессия… (+8 more)

### Community 8 - "Master Schedule Repository"
Cohesion: 0.12
Nodes (16): Задать расписание на день (upsert: существующий день перезаписывается, поэтому…, set_schedule(), BaseModel, model_validator, ScheduleCreate, ScheduleResponse, ScheduleUpdate, make_master_service() (+8 more)

### Community 9 - "User Model & VK Linking"
Cohesion: 0.09
Nodes (12): User, datetime, UUID, Первый вход через VK ID. email может быть None — VK ID не всегда его отдаёт;…, Привязывает VK-аккаунт к уже существующему пользователю (найденному по email из…, Обновляет только те поля, которые переданы (не None). Паттерн…, Отзывает все ранее выданные JWT пользователя (logout, смена/сброс пароля,…, Список пользователей для админ-панели: фильтр по роли + поиск по имени/email.… (+4 more)

### Community 10 - "Appointment Model"
Cohesion: 0.10
Nodes (16): Appointment, UUID, Запись (приём) клиента к мастеру на конкретную услугу. Защита от двойного…, AppointmentRepository, datetime, Decimal, UUID, Ищет пересекающиеся записи у мастера в заданном диапазоне времени. Нужно для… (+8 more)

### Community 11 - "Admin Routes"
Cohesion: 0.10
Nodes (32): assign_user_salon(), AssignSalonRequest, BlockRequest, change_user_role(), ChangeRoleRequest, create_master_profile(), create_user(), CreateMasterProfileRequest (+24 more)

### Community 12 - "Admin Users View"
Cohesion: 0.07
Nodes (29): askForSalon(), auth, changeRole(), confirmSalonPrompt(), createMasterProfile(), deleteUser(), deleting, editingId (+21 more)

### Community 13 - "Appointment Status & Reschedule Tests"
Cohesion: 0.14
Nodes (17): AppointmentStatus, UserRole, FakeAppointmentRepo, FakeMasterRepo, FakeSalonRepo, FakeScheduleRepo, make_admin_user(), make_appointment() (+9 more)

### Community 14 - "Login & Setup Wizard Routes"
Cohesion: 0.13
Nodes (25): login(), complete_setup(), post, Response, Создаёт владельца сети и первую точку (и опционально базовые настройки сайта)…, TokenResponse, build_token_response(), _create_access_token() (+17 more)

### Community 15 - "Content Filter Utility"
Cohesion: 0.11
Nodes (8): _clean_word(), contains_link(), contains_profanity(), Схлопывает типичный обход фильтра внутри одного "слова": разделители (х.у.й,…, contains_profanity()/contains_link() — regression coverage focused on the…, Regression: "плохую" + начало следующего слова на "й" не должны склеиваться в…, TestContainsLink, TestContainsProfanity

### Community 16 - "Booking Slots Tests"
Cohesion: 0.11
Nodes (12): _dt(), FakeAppointmentRepo, FakeMasterRepo, FakeScheduleRepo, FakeServiceRepo, make_service(), datetime, Генерация свободных слотов — сервис с фейковыми репозиториями, без БД. (+4 more)

### Community 17 - "Master Service & Soft Delete"
Cohesion: 0.09
Nodes (21): MasterService, Связь N:M — какой мастер оказывает какую услугу., Мягкое удаление: запись скрывается из выдачи, но не пропадает из БД — на неё…, SoftDeleteMixin, Service, UUID, ServiceRepository, BookableSetup (+13 more)

### Community 18 - "Master Routes Handlers"
Cohesion: 0.09
Nodes (31): add_master_service(), _ensure_can_manage_master(), get_master(), get_master_services(), get_masters(), get_schedule(), get_slots(), date (+23 more)

### Community 19 - "Image Upload Component"
Cohesion: 0.08
Nodes (28): emit, fileInput, onFileChange(), toast, uploading, extractErrorMessage(), addService(), allServices (+20 more)

### Community 20 - "Services Routes"
Cohesion: 0.11
Nodes (22): create_service(), get_service(), get_services(), Depends, description, ge, get, patch (+14 more)

### Community 21 - "Admin Reports Repository"
Cohesion: 0.15
Nodes (17): date, Decimal, UUID, salon_id (ROADMAP.md §4.8, Фаза C) — None означает всю сеть (owner);…, (total_appointments, total_revenue, avg_check) for done appointments., % of clients who visited in the period AND had a prior visit before it., ReportRepository, DailyRevenue (+9 more)

### Community 22 - "Auth Routes & Schemas"
Cohesion: 0.11
Nodes (27): confirm_email_verification(), get_me(), logout(), description, get, limit, patch, post (+19 more)

### Community 23 - "Booking Page Flow"
Cohesion: 0.07
Nodes (22): auth, availableDates, avgRating, book(), booked, bookingLoading, emailInput, fullName (+14 more)

### Community 24 - "Appointment Service"
Cohesion: 0.16
Nodes (14): AppointmentResponse, AppointmentService, date, datetime, UUID, Мои записи (личный кабинет клиента)., Записи конкретного мастера. Мастер может смотреть только свои — админ может…, Все записи системы — для администратора (1.4: фильтр + пагинация). salon_id… (+6 more)

### Community 25 - "DB Session & Login Attempts"
Cohesion: 0.11
Nodes (13): get_db(), Dependency для FastAPI-роутов: сессия на запрос (unit-of-work). Транзакцией…, Сессия входа (refresh-токен). В БД хранится только SHA-256 хеш токена — сам…, Session, LoginAttemptRepository, datetime, Неудачные попытки входа по email за окно — для временной блокировки. Покрыто…, datetime (+5 more)

### Community 26 - "Appointment Routes"
Cohesion: 0.13
Nodes (24): cancel_appointment(), create_appointment(), get_all_appointments(), get_appointment(), get_master_appointments(), get_my_appointments(), datetime, Depends (+16 more)

### Community 27 - "Toast & VK Login UI"
Cohesion: 0.10
Nodes (18): store, { toasts }, variantClasses, enabled, props, toast, useToastStore, auth (+10 more)

### Community 28 - "Salon Scope Resolution"
Cohesion: 0.17
Nodes (10): UUID, None = вся сеть (доступно только owner). Для admin — всегда его salon_id; чужой…, resolve_salon_scope(), make_admin(), make_owner(), make_review_service(), Salon-scoping (ROADMAP.md §4.8, Фаза C) — owner видит всю сеть или выбранную…, _ensure_can_moderate — тестируется напрямую, а не через moderate(): та в конце… (+2 more)

### Community 29 - "Admin Role Assignment Tests"
Cohesion: 0.20
Nodes (11): make_create_data(), make_fake_user(), make_requesting_admin(), make_requesting_owner(), make_service(), AdminService.create_user/change_role/assign_salon — сетевая иерархия ролей…, role=admin требует salon_id (ck_users_admin_requires_salon), а AdminUserCreate…, Технически разрешено на бэкенде — фронтенд сознательно не предлагает эту опцию… (+3 more)

### Community 30 - "Frontend API Clients"
Cohesion: 0.19
Nodes (10): adminApi, appointmentsApi, client, NO_RETRY_PATHS, reviewsApi, salonsApi, servicesApi, settingsApi (+2 more)

### Community 31 - "Home Preview & Hero Editing"
Cohesion: 0.09
Nodes (19): avgDurationLabel, Hero3DRoom, heroVariant, loadMasters(), loadServices(), marqueeText, masters, mastersLoading (+11 more)

### Community 32 - "Master Service Pricing Logic"
Cohesion: 0.19
Nodes (10): _final_price(), MasterService, Decimal, UUID, Возвращает услуги мастера с итоговыми ценами., Расписание мастера не может выходить за общее время работы его точки (ISSUES…, Итоговая цена услуги мастера: override, если задан, иначе базовая ×…, Публичный профиль: деактивированный мастер наружу не отдаётся, контакты… (+2 more)

### Community 33 - "Date Input Component"
Cohesion: 0.11
Nodes (18): cellClass(), cells, clear(), emit, goToday(), isSameDate(), label, MONTHS (+10 more)

### Community 34 - "Salon Routes & Repository"
Cohesion: 0.17
Nodes (16): create_salon(), _ensure_can_manage_salon(), get_salon(), patch, post, UUID, Владелец сети может редактировать любую точку целиком. Admin — только свою…, Детали одной точки. Публичный эндпоинт. (+8 more)

### Community 35 - "Salon Repository Slug Logic"
Cohesion: 0.10
Nodes (12): UUID, Старейшая точка сети — временный дефолт там, где salon_id ещё не выбирается…, Без пагинации — намеренно, у сети физически десятки точек максимум (ROADMAP.md…, Полная замена данных точки — в отличие от update() перезаписывает и slug (он…, SalonRepository, bookable_setup(), Салон + мастер + услуга + расписание на весь понедельник (09:00–20:00 UTC) —…, anyio (+4 more)

### Community 36 - "Auth Schemas & Password Reset"
Cohesion: 0.16
Nodes (11): confirm_password_reset(), LoginRequest, PasswordResetConfirm, PasswordResetRequest, BaseModel, Email не case sensitive нигде в проекте (ISSUES #31) — .lower() применяется на…, TestAppointmentCreateTimezone, TestEmailNormalization (+3 more)

### Community 37 - "Appointment Schemas"
Cohesion: 0.25
Nodes (17): AppointmentBriefResponse, AppointmentCreate, AppointmentReschedule, AppointmentStatusUpdate, BaseModel, datetime, Клиент передаёт только эти три поля. end_time и final_price вычисляются на…, Услуга и мастер не меняются — только время; end_time пересчитывается на сервере… (+9 more)

### Community 38 - "Admin Services View"
Cohesion: 0.10
Nodes (18): props, auth, deleteService(), deleting, editingId, form, formOpen, isActive (+10 more)

### Community 39 - "Appointment Status Utilities"
Cohesion: 0.10
Nodes (18): props, ALLOWED_TRANSITIONS, RESCHEDULABLE_STATUSES, STATUS_ACTION_LABELS, appointments, dateFrom, dateTo, load() (+10 more)

### Community 40 - "Profile Page"
Cohesion: 0.09
Nodes (19): appointments, auth, cancel(), cancelling, editData, editLoading, editOpen, initials (+11 more)

### Community 41 - "Form Error Handling"
Cohesion: 0.14
Nodes (17): useFormErrors(), FIELD_MESSAGES, friendlyValidationError(), MESSAGE_BY_TYPE, auth, consent, { errors, setError, clearError, setFromResponse }, form (+9 more)

### Community 42 - "Admin Reports View"
Cohesion: 0.10
Nodes (17): auth, dateFrom, dateTo, exporting, exportToExcel(), loading, loadReport(), report (+9 more)

### Community 43 - "Setup Wizard Frontend"
Cohesion: 0.13
Nodes (21): auth, { errors, setError, clearError, clearAll, setFromResponse }, finish(), loading, onSubmitStep(), owner, router, salon (+13 more)

### Community 44 - "Master Profile Admin Tests"
Cohesion: 0.23
Nodes (10): Обратное к deactivate() — при повторном назначении роли master тому же…, make_fake_master(), make_fake_user(), make_requesting_admin(), make_requesting_owner(), make_service(), AdminService.create_master_profile() — реактивация вместо блокировки при…, Regression: change_role() only deactivates (is_active=False), never deletes — a… (+2 more)

### Community 45 - "Review Routes"
Cohesion: 0.16
Nodes (19): delete_review(), get_all_reviews(), get_master_reviews(), moderate_review(), delete, Depends, description, get (+11 more)

### Community 46 - "Upload Utilities"
Cohesion: 0.17
Nodes (11): UploadFile, Сохраняет загруженное изображение на диск (settings.upload_dir) и возвращает…, save_uploaded_image(), make_upload(), fixture, UploadFile, save_uploaded_image() — тип/размер и что файл реально попадает на диск под…, Имя файла не должно зависеть от filename пользователя (path traversal /… (+3 more)

### Community 47 - "Master Repository"
Cohesion: 0.14
Nodes (10): MasterRepository, Decimal, UUID, Создаёт профиль мастера для существующего пользователя., Скрывает мастера из каталога без мягкого удаления (например, при смене роли)., Загружает мастера вместе с профилем пользователя и точкой сети…, Загружает мастера вместе с его услугами и базовыми ценами., get_my_master_profile() (+2 more)

### Community 48 - "Admin Salons View"
Cohesion: 0.12
Nodes (16): close(), emit, editing, { errors, setError, clearAll, setFromResponse }, form, formOpen, load(), loading (+8 more)

### Community 49 - "Review Model & Repository"
Cohesion: 0.16
Nodes (6): Отзыв клиента о завершённой записи. Один отзыв на одну запись., Review, UUID, Отзывы — фильтр по мастеру/услуге/минимальной оценке, с пагинацией.…, (средний рейтинг, всего опубликованных отзывов) мастера — среднее считается по…, ReviewRepository

### Community 50 - "Slug Generation Utility"
Cohesion: 0.18
Nodes (7): generate_unique_slug(), Сайтама на Тверской" → "sajtama-na-tverskoj". Транслитерация + lowercase +…, slug из name + числовой суффикс при коллизии (-2, -3, …). `exists` — предикат…, slugify(), slugify()/generate_unique_slug() — генерация URL-слага точки сети из названия…, TestGenerateUniqueSlug, TestSlugify

### Community 51 - "Business Hours Fakes"
Cohesion: 0.12
Nodes (10): FakeSalonRepo, FakeScheduleRepoForAppointment, FakeScheduleRepoForMaster, make_appointment_service(), make_fake_appointment(), _next_weekday_at(), Расписание мастера шире часов работы салона — как будто заведено до появления…, Ближайшая будущая дата с заданным днём недели (0=пн) и временем UTC. (+2 more)

### Community 52 - "Admin Session Revocation Tests"
Cohesion: 0.21
Nodes (9): AdminService, Блокировка/разблокировка (ТЗ 4.2): аккаунт и история сохраняются, вход и…, Мягкое удаление — пользователь скрывается, но история записей сохраняется., make_fake_user(), make_service(), AdminService: события безопасности (принудительная смена пароля, блокировка,…, TestDeleteUser, TestSetBlocked (+1 more)

### Community 53 - "Master Dashboard Schedule View"
Cohesion: 0.14
Nodes (14): mastersApi, useMasterProfileStore, days, labels, loading, profileStore, saveDay(), saving (+6 more)

### Community 54 - "Frontend Dev Dependencies"
Cohesion: 0.12
Nodes (17): @axe-core/playwright, eslint-config-prettier, eslint-plugin-vue, devDependencies, @axe-core/playwright, eslint-config-prettier, eslint-plugin-vue, postcss (+9 more)

### Community 55 - "Repository Query Utilities"
Cohesion: 0.24
Nodes (7): Каталог мастеров — фильтр по специализации/оказываемой услуге/точке.…, escape_like(), paginated(), Экранирует спецсимволы LIKE/ILIKE (%, _) в пользовательском вводе. Использовать…, Выполняет уже отфильтрованный/отсортированный select с пагинацией. Возвращает…, Каталог услуг — поиск по названию + фильтр по цене/активности (1.4)., T

### Community 56 - "Salon Service & Setup"
Cohesion: 0.22
Nodes (9): SalonResponse, UUID, Первая точка сети при первичной настройке (/api/setup). Миграция 0013 всегда…, exclude_id — чтобы точка не считала коллизией собственный slug при…, SalonService, _make_salon_data(), Уникальность salons.slug — SalonService.create() генерирует slug и разруливает…, test_second_salon_with_same_name_gets_suffixed_slug() (+1 more)

### Community 57 - "Appointment Create Guard Tests"
Cohesion: 0.18
Nodes (8): FakeAppointmentRepo, FakeMasterRepo, FakeServiceRepo, make_data(), make_service(), AppointmentService.create() — лимит активных записей и запрет самозаписи…, TestActiveAppointmentLimit, TestMasterCannotBookSelf

### Community 58 - "Hero 3D Room Component"
Cohesion: 0.15
Nodes (13): animate(), canvasEl, containerEl, currentRotation, initScene(), loadModel(), ready, removeOutlierMeshes() (+5 more)

### Community 59 - "Password Reset Token"
Cohesion: 0.19
Nodes (8): PasswordResetToken, Токен сброса пароля. В БД хранится только SHA-256 хеш токена — сам токен живёт…, PasswordResetTokenRepository, datetime, UUID, Токен валиден если не использован и не просрочен., Сколько токенов сброса выдано пользователю за окно — для rate limit., Гасит все неиспользованные токены пользователя при новом запросе сброса.

### Community 60 - "Review Creation Schema"
Cohesion: 0.17
Nodes (10): create_review(), limit, post, Request, Оставить отзыв на свою завершённую запись., ReviewCreate, _validate_comment_content(), make_review() (+2 more)

### Community 61 - "Pagination Schemas"
Cohesion: 0.16
Nodes (10): PageResponse, BaseModel, Универсальная обёртка для постраничных списков., BaseModel, ReviewResponse, UUID, Опубликованные отзывы мастера — публичный эндпоинт., Все отзывы (включая скрытые) — для модерации. salon_id (ROADMAP.md §4.8, Фаза… (+2 more)

### Community 62 - "Salon Scoping Integration Tests"
Cohesion: 0.28
Nodes (15): _login(), _make_master(), _make_salon(), _make_user(), anyio, fixture, Salon-scoping сквозь реальный HTTP-стек и Postgres (ROADMAP.md §4.8, Фаза C).…, Regression (ROADMAP.md §4.8 Фаза C): раньше admin видел любую запись сети. (+7 more)

### Community 63 - "Appointment State Machine Tests"
Cohesion: 0.20
Nodes (6): make_appointment(), make_service(), Машина состояний записи (ALLOWED_TRANSITIONS) и права на переходы., TestCancel, TestTransitionTable, TestUpdateStatus

### Community 64 - "Admin Stats Cards"
Cohesion: 0.13
Nodes (8): auth, load(), loading, salonStore, scopeName, stats, toast, { viewingSalonId, viewingSalon }

### Community 65 - "Frontend Runtime Dependencies"
Cohesion: 0.13
Nodes (15): axios, dependencies, axios, @heroicons/vue, pinia, @sentry/vue, three, vue (+7 more)

### Community 66 - "Master Schedule Model"
Cohesion: 0.20
Nodes (6): Рабочее расписание мастера по дням недели. day_of_week: 0 = пн … 6 = вс., Schedule, UUID, Всё расписание мастера, отсортированное по дням недели., Расписание мастера на конкретный день недели., ScheduleRepository

### Community 67 - "Admin Reports Routes"
Cohesion: 0.22
Nodes (15): export_report(), get_all_users(), get_report(), get_stats(), date_, Depends, description, get (+7 more)

### Community 68 - "Client IP & Rate Limit Utils"
Cohesion: 0.27
Nodes (6): client_ip(), Request, Реальный IP клиента из X-Forwarded-For, а не request.client.host — за…, make_request(), client_ip() — реальный IP клиента из-за прокси-цепочки Caddy -> nginx (см.…, TestClientIp

### Community 69 - "Admin Site Theme Settings"
Cohesion: 0.15
Nodes (11): applyFont(), FONT_PRESETS, form, heroVariants, loading, save(), saving, showColors (+3 more)

### Community 70 - "Reschedule Modal"
Cohesion: 0.18
Nodes (12): availableDates, close(), confirm(), emit, loading, props, selectDate(), selectedDate (+4 more)

### Community 71 - "Email Verification Token Repository"
Cohesion: 0.22
Nodes (6): EmailVerificationTokenRepository, datetime, UUID, Токен валиден если не использован и не просрочен., Сколько писем подтверждения выдано пользователю за окно — для rate limit…, Гасит все неиспользованные токены пользователя при новой отправке письма.

### Community 72 - "Admin Stats Repository"
Cohesion: 0.18
Nodes (6): datetime, Decimal, UUID, Агрегирующие запросы для счётчиков/графиков админ-панели (4.4). salon_id…, Количество и суммарная выручка завершённых визитов с указанной даты. Фильтр по…, StatsRepository

### Community 73 - "Docker Compose Services Overview"
Cohesion: 0.18
Nodes (13): docker-compose.yml service: backend (FastAPI), Backend healthcheck uses 127.0.0.1, not localhost, docker-compose.yml service: backup-local (daily pg_dump, bind-mounted), docker-compose.yml service: backup-s3 (optional S3 backup, profile-gated), docker-compose.yml service: caddy (TLS terminator, ports 80/443), docker-compose.yml service: db (Postgres 16-alpine), docker-compose.yml service: frontend (nginx static SPA), CI job: frontend-e2e (Playwright against real backend+Postgres) (+5 more)

### Community 74 - "Password Reset Page"
Cohesion: 0.18
Nodes (11): props, email, error, loading, newPassword, requested, route, router (+3 more)

### Community 75 - "Rate Limit Handler Tests"
Cohesion: 0.17
Nodes (11): Request, rate_limit_handler(), client(), _limited_endpoint(), fixture, limit, Request, Rate-limit wiring (utils/rate_limit.py + main.py exception handler) —… (+3 more)

### Community 76 - "Double Booking Constraint Tests"
Cohesion: 0.29
Nodes (10): UserCreate, hash_password(), _make_client(), EXCLUDE USING gist (no_double_booking) — единственная гарантия от двойного…, Прямая проверка на уровне репозитория, в обход сервисного pre-flight-чека…, test_exclusion_constraint_rejects_overlapping_appointment(), Partial unique indexes (WHERE deleted_at IS NULL) — email/телефон/vk_user_id…, Тот же сценарий, но без soft-delete между созданиями — вызов идёт напрямую… (+2 more)

### Community 77 - "Health Check Endpoint Tests"
Cohesion: 0.23
Nodes (7): _BrokenSession, _clear_override(), _fake_get_db(), fixture, GET /health — SELECT 1 против БД, не только "процесс жив" (см. main.py).…, TestHealth, _WorkingSession

### Community 78 - "Reminder Service Tests"
Cohesion: 0.35
Nodes (5): make_appointment(), make_service(), ReminderService.send_due_reminders() — фейковый репозиторий, без БД., Ошибка при сборке/отправке письма не должна помечать напоминание отправленным —…, TestSendDueReminders

### Community 79 - "Site Content Store & SEO"
Cohesion: 0.24
Nodes (6): useSiteContentStore, applySeo(), { content }, brandName, { content }, footerAddress

### Community 80 - "CI & Dependency Config"
Cohesion: 0.22
Nodes (10): Backend production dependencies (requirements.txt), Backend dev/CI dependencies (requirements-dev.txt: pytest, ruff), docker-compose.yml (production stack: Postgres + FastAPI + nginx SPA + Caddy), Dependabot Configuration (pip/npm/docker/github-actions weekly updates), CI job: backend-integration-tests (real Postgres), CI job: backend-lint (ruff check), CI job: backend-tests (pytest unit tests, no DB), pip-audit exception: PYSEC-2026-1325 (ecdsa) (+2 more)

### Community 81 - "Concurrent Booking Test Helpers"
Cohesion: 0.22
Nodes (9): next_weekday_at(), datetime, Следующая дата с указанным днём недели (0=пн … 6=вс) на фиксированный час UTC —…, anyio, Две одновременные HTTP-заявки на один и тот же слот. Второй ответ не должен…, test_concurrent_booking_requests_only_one_succeeds(), anyio, Happy path целиком через реальный HTTP-стек поверх реальной БД: клиент… (+1 more)

### Community 82 - "Admin Role Assignment Flow Tests"
Cohesion: 0.47
Nodes (8): _login(), _make_owner(), _make_salon(), anyio, Полный HTTP-флоу назначения salon-scoped admin (ROADMAP.md §4.10 Фаза B):…, _register(), test_non_owner_admin_cannot_assign_salon_or_promote(), test_two_step_flow_promotes_user_to_scoped_admin()

### Community 83 - "Salon-Scoped Appointment Get Tests"
Cohesion: 0.31
Nodes (5): make_appointment_service_for_get_by_id(), make_fake_appointment_full(), Полностью сформированный фейк — get_by_id() в конце сериализует…, Regression (ROADMAP.md §4.8 Фаза C): раньше любой admin видел любую запись…, TestAppointmentGetByIdScoping

### Community 84 - "Master Management Authorization Tests"
Cohesion: 0.36
Nodes (3): patch_master_repo(), Не раскрываем существование мастера чужой точки — 403, как и mismatch., TestEnsureCanManageMaster

### Community 85 - "Frontend NPM Scripts"
Cohesion: 0.22
Nodes (9): scripts, build, dev, format, format:check, lint, preview, test:e2e (+1 more)

### Community 86 - "Time Input Component"
Cohesion: 0.28
Nodes (7): emit, hour, minute, onHourChange(), onMinuteChange(), parts, props

### Community 87 - "App Config & Settings"
Cohesion: 0.29
Nodes (4): model_validator, # TODO: SENTRY_DSN пока не задан нигде — sentry.io недоступен для, Settings, BaseSettings

### Community 88 - "Main App & Reminder Scheduler"
Cohesion: 0.39
Nodes (6): health(), get, root(), lifespan(), _reminder_loop(), _run_reminder_pass()

### Community 90 - "App Footer Component"
Cohesion: 0.29
Nodes (6): content, { content: storeContent }, props, salons, salonStore, year

### Community 91 - "App Header Component"
Cohesion: 0.29
Nodes (5): auth, { content: storeContent }, localContent, props, router

### Community 92 - "Registrations Chart Component"
Cohesion: 0.29
Nodes (5): ariaLabel, coords, maxCount, points, props

### Community 93 - "Admin Stats Schema"
Cohesion: 0.47
Nodes (4): AdminStatsResponse, DailyCount, BaseModel, salon_id (ROADMAP.md §4.8, Фаза C) — None означает всю сеть (owner).…

### Community 95 - "Editable Text Component"
Cohesion: 0.33
Nodes (4): el, emit, local, props

### Community 96 - "Theme Presets"
Cohesion: 0.47
Nodes (5): applyTheme(), hexToRgbTriplet(), matchPreset(), THEME_PRESETS, THEME_TOKENS

### Community 97 - "E2E Core Flows Test"
Cohesion: 0.33
Nodes (4): CLIENT, OWNER, RUN_ID, SALON

### Community 98 - "Salon List Route"
Cohesion: 0.40
Nodes (5): get_salons(), description, get, Query, Список точек сети — без пагинации, у сети физически десятки точек максимум.…

### Community 99 - "Pagination Query Params"
Cohesion: 0.40
Nodes (4): description, ge, le, Query

### Community 100 - "Prettier Config"
Cohesion: 0.40
Nodes (4): printWidth, semi, singleQuote, trailingComma

### Community 101 - "Salon Landing Hero Screenshot"
Cohesion: 0.50
Nodes (4): Salon Landing Page Hero (3D Interior Render), Nav Header (Masters / Admin Panel / User Menu), Isometric 3D Render of Barbershop Interior, Hero Stats Row (45 min avg cut / 4 services / 1 master on shift)

### Community 103 - "Frontend Package Metadata"
Cohesion: 0.50
Nodes (3): name, type, version

### Community 104 - "Status Pill Component"
Cohesion: 0.50
Nodes (3): entry, map, props

### Community 119 - "Design System Anti-Patterns & Layout"
Cohesion: 0.67
Nodes (3): Design system: anti-patterns list, Design system: component specs (buttons, cards, inputs, status pills, toasts, skeletons, z-index scale), Design system: 3 layout patterns (public/marketing, client app, dashboard)

### Community 120 - "Auth Security Measures"
Cohesion: 0.67
Nodes (3): Access token in httpOnly cookie (SameSite=Lax, COOKIE_SECURE), JWT revocation via token_version counter, Brute-force protection: login lockout + password-reset rate limit

## Ambiguous Edges - Review These
- `Dependabot Configuration (pip/npm/docker/github-actions weekly updates)` → `docker-compose.yml (production stack: Postgres + FastAPI + nginx SPA + Caddy)`  [AMBIGUOUS]
  .github/dependabot.yml · relation: conceptually_related_to
- `Double-booking protection (repo check + EXCLUDE USING gist)` → `docker-compose.yml (production stack: Postgres + FastAPI + nginx SPA + Caddy)`  [AMBIGUOUS]
  README.md · relation: references
- `Design system: typography (Playfair Display headings + Inter body)` → `index.html preloaded fonts: Golos Text + JetBrains Mono`  [AMBIGUOUS]
  frontend/index.html · relation: conceptually_related_to
- `Yandex.Metrika analytics counter (metrika.js + noscript pixel)` → `Static default <title>/description/favicon overridden by applySeo() at runtime`  [AMBIGUOUS]
  frontend/index.html · relation: conceptually_related_to

## Knowledge Gaps
- **383 isolated node(s):** `semi`, `singleQuote`, `trailingComma`, `printWidth`, `name` (+378 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Dependabot Configuration (pip/npm/docker/github-actions weekly updates)` and `docker-compose.yml (production stack: Postgres + FastAPI + nginx SPA + Caddy)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Double-booking protection (repo check + EXCLUDE USING gist)` and `docker-compose.yml (production stack: Postgres + FastAPI + nginx SPA + Caddy)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Design system: typography (Playfair Display headings + Inter body)` and `index.html preloaded fonts: Golos Text + JetBrains Mono`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Yandex.Metrika analytics counter (metrika.js + noscript pixel)` and `Static default <title>/description/favicon overridden by applySeo() at runtime`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `UserRole` connect `Appointment Status & Reschedule Tests` to `Site Settings & Setup Service`, `Master Photo & Schema Fields`, `Alembic Env & Core Models`, `Auth Service Email/Password Flows`, `Auth Service Unit Tests`, `Master Schedule Repository`, `User Model & VK Linking`, `Admin Routes`, `Login & Setup Wizard Routes`, `Master Service & Soft Delete`, `Services Routes`, `Appointment Service`, `Salon Scope Resolution`, `Admin Role Assignment Tests`, `Salon Routes & Repository`, `Salon Repository Slug Logic`, `Master Profile Admin Tests`, `Admin Session Revocation Tests`, `Repository Query Utilities`, `Salon Scoping Integration Tests`, `Appointment State Machine Tests`, `Admin Reports Routes`, `Admin Stats Repository`, `Double Booking Constraint Tests`, `Admin Role Assignment Flow Tests`, `Salon-Scoped Appointment Get Tests`, `Master Management Authorization Tests`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `User` connect `User Model & VK Linking` to `Master Photo & Schema Fields`, `Alembic Env & Core Models`, `Auth Service Email/Password Flows`, `Master Schedule Repository`, `Appointment Model`, `Admin Routes`, `Appointment Status & Reschedule Tests`, `Login & Setup Wizard Routes`, `Master Service & Soft Delete`, `Master Routes Handlers`, `Services Routes`, `Appointment Service`, `DB Session & Login Attempts`, `Appointment Routes`, `Salon Scope Resolution`, `Salon Routes & Repository`, `Review Routes`, `Master Repository`, `Review Model & Repository`, `Admin Session Revocation Tests`, `Repository Query Utilities`, `Password Reset Token`, `Review Creation Schema`, `Pagination Schemas`, `Admin Reports Routes`, `Salon List Route`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `Session` connect `DB Session & Login Attempts` to `Site Settings & Setup Service`, `Master Photo & Schema Fields`, `Alembic Env & Core Models`, `VK OAuth PKCE Login`, `Master Schedule Repository`, `User Model & VK Linking`, `Admin Routes`, `Login & Setup Wizard Routes`, `Master Service & Soft Delete`, `Master Routes Handlers`, `Services Routes`, `Admin Reports Repository`, `Auth Routes & Schemas`, `Appointment Routes`, `Salon Routes & Repository`, `Salon Repository Slug Logic`, `Auth Schemas & Password Reset`, `Review Routes`, `Master Repository`, `Review Model & Repository`, `Repository Query Utilities`, `Salon Service & Setup`, `Password Reset Token`, `Review Creation Schema`, `Master Schedule Model`, `Admin Reports Routes`, `Email Verification Token Repository`, `Admin Stats Repository`, `Main App & Reminder Scheduler`, `Reminder Service`, `Salon List Route`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._