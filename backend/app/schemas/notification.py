from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..models.enums import NotificationType, NotificationChannel, NotificationStatus


class NotificationResponse(BaseModel):
    id:             UUID
    appointment_id: UUID
    type:           NotificationType
    channel:        NotificationChannel
    scheduled_at:   datetime
    sent_at:        Optional[datetime] = Field(None, description="None если ещё не отправлено")
    status:         NotificationStatus
    error_message:  Optional[str]      = Field(None, description="Заполняется при статусе failed")

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total:         int
