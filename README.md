# Барбершоп «Сайтама»

Учебный CMS-проект: онлайн-запись в барбершоп с полноценным бэкендом, тремя ролями и фронтендом в едином репозитории.

**Стек:** FastAPI · SQLAlchemy 2.0 · Pydantic v2 · PostgreSQL · Alembic · JWT · Vue 3 · Pinia · Tailwind CSS · Vite

---

## Что умеет

### Клиент
- Каталог мастеров с фильтрацией по имени/специализации
- Просмотр расписания мастера → выбор свободного слота → бронирование
- Просмотр и отмена своих записей, отслеживание статуса
- Отзыв на завершённую запись (один отзыв на одну запись)
- Восстановление пароля по ссылке (в dev-режиме ссылка в логе сервера, SMTP не подключён)

### Мастер (личный кабинет)
- Список своих входящих записей, смена статуса (`pending → confirmed → done`, отмена)
- Редактирование рабочего расписания по дням недели
- Своя лента отзывов

### Администратор (панель)
| Раздел | Что можно делать |
|---|---|
| Статистика | Счётчики (пользователи, записи, выручка за месяц) + график регистраций за 30 дней |
| Отчёты | Аналитика за произвольный период: KPI-карточки, линейный график выручки, разбивка по услугам и мастерам, экспорт в Excel |
| Пользователи | Поиск, смена роли, создание/редактирование, мягкое удаление, создание профиля мастера |
| Услуги | CRUD (создание через /api/docs), редактирование, мягкое удаление |
| Мастера | Просмотр, обновление фото |
| Отзывы | Модерация: публикация / скрытие |
| Настройки | CMS-редактор главной страницы (заголовок, подзаголовок, фото героя, адрес, телефон) |

---

## Ключевые технические решения

**Защита от двойного бронирования** работает на двух уровнях: проверка в репозитории перед вставкой (читаемое сообщение об ошибке) + ограничение `EXCLUDE USING gist` с предикатом `WHERE (status <> 'cancelled')` прямо в БД (защита от гонок). Первая миграция (`alembic/versions/0001_initial.py`) создаёт расширение `btree_gist` и пишет ограничение сырым SQL — SQLAlchemy declarative API такое не поддерживает.

**Мягкое удаление** (`deleted_at`) для пользователей, мастеров и услуг. Уникальность email/телефона при этом обеспечивается частичными уникальными индексами (`WHERE deleted_at IS NULL`), а не `unique=True` на колонке.

**Машина состояний записи** (`ALLOWED_TRANSITIONS` в `appointment_service.py`): `pending → {confirmed, cancelled}`, `confirmed → {done, cancelled}`, `done`/`cancelled` — терминальные.

**Строгий SQLAlchemy 2.0** (`Mapped`/`mapped_column`, `select()`/`session.execute()`) и **строгий Pydantic v2** (`Annotated`, `ConfigDict`) везде в кодовой базе.

**Слоёная архитектура** `routes → services → repositories → models`; репозитории — единственное место с SQL-запросами.

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

### Требования
- Python 3.14
- Node.js 18+
- PostgreSQL 13+ (нужны права на `CREATE EXTENSION` для `btree_gist`)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Создайте `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/hair_salon
SECRET_KEY=<случайная строка>
```

Все переменные и дефолты — в `backend/app/config.py`.

```bash
alembic upgrade head   # создаёт схему, расширение btree_gist и EXCLUDE-ограничение
python run.py          # http://localhost:8000 · Swagger: /api/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, /api проксируется на :8000
```

---

## Известные ограничения

- OAuth и реальная отправка email не реализованы (в задаче не требовались)
- Деплой и CI/CD не настроены
- Тестовое покрытие отсутствует
