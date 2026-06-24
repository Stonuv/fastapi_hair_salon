from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import NotificationChannel, NotificationStatus, NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             UUID
    appointment_id: UUID
    type:           NotificationType
    channel:        NotificationChannel
    scheduled_at:   datetime
    sent_at:        Annotated[datetime | None, Field(default=None, description="None если ещё не отправлено")]
    status:         NotificationStatus
    error_message:  Annotated[str | None, Field(default=None, description="Заполняется при статусе failed")]


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total:         int
