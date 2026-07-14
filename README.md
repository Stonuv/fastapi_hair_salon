# CMS для Парикмахерских/Барбершопов/Груминг-салонов «Сайтама»

**Стек:** FastAPI · SQLAlchemy · Pydantic · PostgreSQL · Alembic · JWT · Vue 3 · Pinia · Tailwind CSS · Vite

---

## Роли

### Клиент
- Каталог мастеров с фильтрацией по имени/специализации
- Просмотр расписания мастера → выбор свободного слота → бронирование
- Просмотр и отмена своих записей, отслеживание статуса
- Отзыв на завершённую запись (один отзыв на одну запись)
- Восстановление пароля по ссылке, отправляется письмом (SMTP — см. «Email и VK ID» ниже)
- Вход через VK ID (OAuth 2.1 + PKCE) — при первом входе создаёт аккаунт или
  привязывается к существующему по email, если он совпадает

### Мастер (личный кабинет)
- Список своих входящих записей, смена статуса (`pending → confirmed → done`, отмена)
- Редактирование рабочего расписания по дням недели
- Своя лента отзывов

### Администратор (панель)
| Раздел | Что можно делать |
|---|---|
| Статистика | Счётчики (пользователи, записи, выручка за месяц) + график регистраций за 30 дней |
| Отчёты | Аналитика за произвольный период: KPI-карточки, линейный график выручки, разбивка по услугам и мастерам, экспорт в Excel |
| Пользователи | Поиск, смена роли, создание/редактирование, блокировка, мягкое удаление, создание профиля мастера |
| Услуги | CRUD (создание через /api/docs), редактирование, мягкое удаление |
| Мастера | Просмотр, обновление фото |
| Отзывы | Модерация: публикация / скрытие |
| Настройки | CMS-редактор контента главной страницы (шапка, главный экран, блоки «Почему мы»/услуги/мастера/CTA, футер) с живым предпросмотром рядом с формой |
| Настройки (тест) | Экспериментальный WYSIWYG-редактор той же модели контента: правки делаются кликом прямо по реальной главной странице (шапка/hero/блоки/футер в натуральную величину), тема/шрифты/дизайн hero — в плавающей панели снизу. Не заменяет обычные «Настройки», сохраняет через тот же `PATCH /api/settings` |

---

## Ключевые технические решения

**Защита от двойного бронирования** работает на двух уровнях: проверка в репозитории перед вставкой (читаемое сообщение об ошибке) + ограничение `EXCLUDE USING gist` с предикатом `WHERE (status <> 'cancelled')` прямо в БД (защита от гонок). Первая миграция (`alembic/versions/0001_initial.py`) создаёт расширение `btree_gist` и пишет ограничение сырым SQL — SQLAlchemy declarative API такое не поддерживает.

**Мягкое удаление** (`deleted_at`) для пользователей, мастеров и услуг. Уникальность email/телефона при этом обеспечивается частичными уникальными индексами (`WHERE deleted_at IS NULL`), а не `unique=True` на колонке.

**Машина состояний записи** (`ALLOWED_TRANSITIONS` в `appointment_service.py`): `pending → {confirmed, cancelled}`, `confirmed → {done, cancelled}`, `done`/`cancelled` — терминальные.

**Строгий SQLAlchemy 2.0** (`Mapped`/`mapped_column`, `select()`/`session.execute()`) и **строгий Pydantic v2** (`Annotated`, `ConfigDict`) везде в кодовой базе.

**Слоёная архитектура** `routes → services → repositories → models`; репозитории — единственное место с SQL-запросами.

**Живой предпросмотр главной страницы** в «Админ → Настройки»: рендеринг главной вынесен в `components/HomePreview.vue`, который принимает контент пропом — сама главная (`HomePage.vue`) передаёт туда данные из стора, а страница настроек передаёт туда же ещё не сохранённую форму, так что правки видно мгновенно без лишней синхронизации состояния.

**Инлайн-WYSIWYG (эксперимент)** в «Админ → Настройки (тест)» (`views/admin/AdminSettingsLive.vue`): `AppHeader.vue`, `HomePreview.vue` и `AppFooter.vue` получили необязательные пропы `editable`/`content` (по умолчанию `false`/из стора — публичный сайт и старая страница настроек не затронуты). При `editable` текстовые узлы рендерятся через `components/ui/EditableText.vue` (input/автоширящийся textarea вместо текста), а ссылки/кнопки-переходы — через `components/ui/EditableLink.vue` (не-навигирующий `<span>` вместо `router-link`/`<a>`, иначе клик по редактируемому бренду/hero-кнопке уводил бы со страницы). Оба компонента мутируют тот же реактивный объект формы и сохраняются тем же `PATCH /api/settings`.

---

## Структура репозитория

```
backend/
  app/
    models/       ORM-модели (UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin)
    repositories/ SQL-запросы (paginated() — общий хелпер пагинации)
    services/     Бизнес-логика (auth, appointments, admin, reports, ...)
    routes/       FastAPI-роутеры
    schemas/      Pydantic-схемы (PageParams/PageResponse[T] для пагинации)
  alembic/        Миграции (0001_initial.py содержит raw SQL для EXCLUDE + btree_gist)
  run.py          Точка запуска (uvicorn, reload=settings.debug)

frontend/
  src/
    views/        Страницы (публичные, /dashboard, /admin)
    components/   UI-примитивы (BaseButton, BaseCard, Skeleton, StatusPill, ...)
    stores/       Pinia (auth, toast, masterProfile)
    api/          Axios-клиент + модули по ресурсам
    router/       Vue Router с beforeEach-гардом по ролям
  design-system/  Дизайн-система проекта (палитра, типографика, паттерны по типу страницы)
```

---

## Быстрый старт

### Вариант 1: Docker (весь стек одной командой)

```bash
cp .env.example .env   # заполните SECRET_KEY/SETUP_TOKEN, см. комментарии в файле
docker compose up --build -d
```

Приложение — http://localhost, Swagger — http://localhost/api/docs (Caddy
слушает 80/443 и проксирует на nginx/бэкенд — см. «Деплой на VPS» ниже).
Миграции накатываются автоматически при старте бэкенда.

Сразу после первого старта зайдите на http://localhost/setup — см.
«Первичная настройка» ниже.

### Вариант 2: локально

#### Требования
- Python 3.14
- Node.js 18+
- PostgreSQL 13+ (нужны права на `CREATE EXTENSION` для `btree_gist`)

#### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # и заполните под своё окружение
```

Все переменные и дефолты — в `backend/.env.example` и `backend/app/config.py`.

```bash
alembic upgrade head   # создаёт схему, расширение btree_gist и EXCLUDE-ограничение
python run.py          # http://localhost:8000 · Swagger: /api/docs
```

#### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, /api проксируется на :8000
```

---

## Email и VK ID (локальная разработка)

**Письма (сброс пароля)** отправляются по SMTP; дефолты в `config.py` уже
нацелены на [Mailpit](https://github.com/axllent/mailpit) — фейковый
SMTP-сервер, который ловит письма вместо реальной отправки:

```bash
docker compose -f docker-compose.dev.yml up -d   # поднимает mailpit
```

Запросите сброс пароля на `/password-reset` — письмо появится на
http://localhost:8025. Для прод-провайдера переопределите `SMTP_*` в `.env`
(см. `backend/.env.example`).

**Вход через VK ID** (OAuth 2.1 + PKCE) требует зарегистрированное приложение
на [id.vk.com/business](https://id.vk.com/business): создайте приложение,
укажите redirect URI `http://localhost:8000/api/auth/vk/callback` (VK ID
разрешает `localhost` на этапе разработки) и скопируйте `client_id` в
`VK_CLIENT_ID` (`backend/.env`). Без `VK_CLIENT_ID` кнопка «Войти через VK»
на фронтенде автоматически скрывается (`GET /api/auth/vk/enabled`). В проде
VK ID требует настоящий HTTPS-домен (не IP, не `localhost`) — см. «Деплой на
VPS» ниже про Caddy, `VK_REDIRECT_URI` придётся обновить на `https://<домен>/api/auth/vk/callback`.

---

## Деплой на VPS

Стек — `docker-compose.yml` (Postgres + backend + nginx со статикой SPA +
[Caddy](https://caddyserver.com/) как единственная точка входа на 80/443).
Caddy сам получает и продлевает сертификат Let's Encrypt — руками ничего не
трогать не нужно, ни nginx, ни backend TLS не касаются.

#### 1. Docker на VPS (если ещё не установлен)

```bash
curl -fsSL https://get.docker.com | sh   # официальный скрипт Docker
sudo usermod -aG docker $USER && newgrp docker
```

#### 2. Код на сервер

```bash
git clone <URL вашего репозитория>
cd fastapi_hair_salon
cp .env.example .env
```

Заполните в `.env`: `SECRET_KEY` и `SETUP_TOKEN` (команды генерации — прямо в
комментариях файла). Остальное (`SITE_ADDRESS`, `COOKIE_SECURE`, `SMTP_*`,
`VK_*`) можно оставить закомментированным — заработает по IP на голом HTTP.

#### 3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw enable
```

#### 4. Запуск

```bash
docker compose up --build -d
```

Приложение — `http://<IP вашего VPS>/`. Зайдите на `/setup` и введите
`SETUP_TOKEN` — создаст первого админа (см. «Первичная настройка» ниже).

#### 5. Когда появится домен

Пропишите A-запись домена на IP VPS, затем в `.env`:

```bash
SITE_ADDRESS=your-domain.ru
COOKIE_SECURE=true
FRONTEND_BASE_URL=https://your-domain.ru
```

```bash
docker compose up -d   # пересоздаст caddy и backend с новыми переменными
```

Caddy сам выпустит сертификат и включит редирект `http -> https` — никаких
дополнительных действий. После этого можно вернуться к VK ID (redirect URI
и `VK_REDIRECT_URI` на `https://your-domain.ru/api/auth/vk/callback`) и/или
подключить реальный SMTP — оба блока переменных уже готовы в `.env.example`.

---

## Бэкапы БД

`docker compose up -d` сразу поднимает `backup-local` — ежедневный сжатый
`pg_dump` в `./backups` рядом с `docker-compose.yml`, с ротацией (7
ежедневных / 4 еженедельных / 6 ежемесячных копий, см. `BACKUP_KEEP_*` в
`docker-compose.yml`). Донастройки не требует, но сам по себе не защищает от
потери всего VPS/диска — заберите `./backups` на другую машину (`rsync`/`scp`
по расписанию) или включите второй, S3-бэкап:

```bash
# заполнить S3_BACKUP_* в .env (см. .env.example), затем:
docker compose --profile s3-backup up -d
```

#### Восстановление

```bash
# самый свежий дамп клиентской БД:
ls -t backups/barbershop/daily/*.sql.gz | head -1

# восстановить (стек должен быть остановлен/backend не пишет в это время):
docker compose stop backend
gunzip -c backups/barbershop/daily/barbershop-<дата>.sql.gz | \
  docker compose exec -T db psql -U barbershop -d barbershop
docker compose start backend
```

---

## Мониторинг ошибок (Sentry)

> **TODO:** аккаунт на sentry.io ещё не создан — регистрация была недоступна
> (403) на момент настройки этой интеграции. Код готов и ждёт DSN.

Код (backend `sentry_sdk.init(...)`, frontend `Sentry.init({ app, ... })` в
`main.js`) уже подключён, но выключен: без `SENTRY_DSN`/`VITE_SENTRY_DSN` в
`.env` инициализация просто не вызывается. Когда появится доступ к sentry.io
(или self-hosted/GlitchTip — DSN того же формата):

1. Завести проект на sentry.io, скопировать DSN.
2. Вписать в `.env`: `SENTRY_DSN=...` (backend) и `VITE_SENTRY_DSN=...`
   (frontend — см. комментарий в `.env.example`, значения обычно совпадают).
3. **Frontend требует пересборки**, не просто рестарта — `VITE_SENTRY_DSN`
   запекается в бандл на этапе `npm run build` (Vite build ARG, см.
   `frontend/Dockerfile`), а не читается в рантайме:
   ```bash
   docker compose up --build -d
   ```

## Первичная настройка

После деплоя в системе нет ни одного пользователя с ролью `admin` — создать
его можно только через визард `/setup` (открывается автоматически при первом
заходе на сайт, пока admin не создан). Визард одним запросом (`POST
/api/setup`) заводит первого администратора и опционально сохраняет базовые
поля контента сайта (название бренда, адрес, часы работы); остальной контент
донастраивается позже в «Админ → Настройки».

`/api/setup` неизбежно публичен — защитить его существующей RBAC-схемой
нечем, потому что до этого момента в системе нет ни одного admin. Поэтому
вне `DEBUG` обязателен `SETUP_TOKEN` (см. `backend/.env.example`): без верного
кода в визарде запрос отклоняется с 403, а само приложение отказывается
стартовать при `DEBUG=false`, если `SETUP_TOKEN` не задан. В `DEBUG=true`
(локальная разработка) код не требуется. Как только первый admin создан,
`/api/setup` навсегда возвращает 409 — второй раз им воспользоваться нельзя.

## Таймзоны

Салон «живёт» в UTC: рабочее расписание мастеров хранится и трактуется как
UTC-время, `start_time` записи обязан приходить с таймзоной и нормализуется в
UTC, отчёты режут сутки по UTC, а фронтенд показывает время записей и слотов
как «настенные часы» салона (`timeZone: 'UTC'`), а не в таймзоне браузера.

## Безопасность аутентификации

- **Отзыв JWT через `token_version`**: у каждого пользователя в БД есть
  счётчик `token_version`, зашитый в payload токена при выдаче (`ver`).
  `get_current_user` сверяет его с текущим значением на каждый запрос —
  logout, смена/сброс пароля и блокировка инкрементируют счётчик, и все
  ранее выданные токены (включая скомпрометированные) мгновенно становятся
  недействительны без хранения denylist'а или сессий.
- **Access-токен — в httpOnly-cookie**, не в localStorage: JS не может его
  прочитать, что закрывает классический вектор кражи токена через XSS.
  Cookie ставится с `SameSite=Lax` — этого достаточно для защиты не-GET
  запросов от CSRF без отдельного CSRF-токена, т.к. простой JSON API без
  form-encoded эндпоинтов не эксплуатируется стандартной CSRF-формой.
  `Secure`-флаг включается переменной `COOKIE_SECURE` (не `DEBUG`!) — только
  когда перед приложением реально стоит TLS-терминатор. Токен также
  возвращается в теле ответа `/auth/login`, `/auth/register`, `/api/setup` —
  это нужно для Swagger "Authorize" и внешних API-клиентов, у которых нет
  доступа к cookie; `get_current_user` принимает оба источника.
- Перебор паролей ограничен: временная блокировка входа после 5 неудач за
  15 минут (журнал `login_attempts`), запросы сброса пароля — 3/час.

## Известные ограничения

- CI/CD не настроен — деплой на VPS ручной (`git pull && docker compose up --build -d`)
- HTTPS настроен через Caddy (`docker-compose.yml`, см. «Деплой на VPS»), но
  требует домена — по голому IP Let's Encrypt сертификат не выдать, Caddy
  просто отдаёт HTTP
- Дефолтные тексты сайта продублированы в `stores/siteContent.js` и
  `schemas/site_settings.py` — при изменении синхронизировать вручную
