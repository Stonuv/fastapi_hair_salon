from typing import Annotated

from pydantic import BaseModel, Field

from .salon import SalonCreate
from .site_settings import SiteContent
from .user import UserCreate


class SetupStatusResponse(BaseModel):
    completed: bool
    requires_token: Annotated[bool, Field(
        description="Настроен ли SETUP_TOKEN на сервере — если да, POST /api/setup "
                    "требует его в поле setup_token",
    )]


class SetupRequest(BaseModel):
    # owner, не admin: первый аккаунт управляет всей сетью (ROADMAP.md §4.8).
    # Роль admin с этого момента salon-scoped и требует salon_id
    # (ck_users_admin_requires_salon), которого на первом запуске взять неоткуда.
    owner: UserCreate
    # Первая точка сети — обязательна: мастера и записи ссылаются на salon_id
    # (NOT NULL), без точки инсталляция нерабочая.
    salon: SalonCreate
    site_content: SiteContent | None = None
    setup_token: Annotated[str | None, Field(
        default=None,
        description="Bootstrap-код из переменной окружения SETUP_TOKEN на сервере. "
                    "Нужен, только если сервер запущен вне debug-режима.",
    )]
