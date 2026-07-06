from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import TokenResponse
from ..schemas.setup import SetupRequest, SetupStatusResponse
from ..services.setup_service import SetupService

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatusResponse)
def get_setup_status(db: Session = Depends(get_db)):
    """Публичный эндпоинт: нужен ли фронтенду показать визард первого запуска
    и запрашивать ли у оператора код настройки (SETUP_TOKEN)."""
    service = SetupService(db)
    return SetupStatusResponse(completed=service.is_completed(),
                               requires_token=service.requires_token())


@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def complete_setup(data: SetupRequest, db: Session = Depends(get_db)):
    """
    Создаёт первого администратора (и опционально базовые настройки сайта).
    Публичный по необходимости — до первого вызова в системе нет ни одного
    admin, которым можно было бы его защитить; если задан SETUP_TOKEN, вместо
    этого запрос обязан предъявить его в теле (см. SetupService.complete).
    Самоблокируется: как только admin появился, дальнейшие вызовы возвращают 409.
    """
    return SetupService(db).complete(data)
