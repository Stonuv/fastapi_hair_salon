from typing import Annotated

from pydantic import BaseModel, Field

from .site_settings import SiteContent
from .user import UserCreate


class SetupStatusResponse(BaseModel):
    completed: bool
    requires_token: Annotated[bool, Field(
        description="Настроен ли SETUP_TOKEN на сервере — если да, POST /api/setup "
                    "требует его в поле setup_token",
    )]


class SetupRequest(BaseModel):
    admin: UserCreate
    site_content: SiteContent | None = None
    setup_token: Annotated[str | None, Field(
        default=None,
        description="Bootstrap-код из переменной окружения SETUP_TOKEN на сервере. "
                    "Нужен, только если сервер запущен вне debug-режима.",
    )]
