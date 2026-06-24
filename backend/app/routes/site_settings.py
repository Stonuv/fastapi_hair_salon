from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.site_settings import SiteContent
from ..services.auth_service import get_current_admin
from ..services.site_settings_service import SiteSettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SiteContent)
def get_settings(db: Session = Depends(get_db)):
    """Редактируемый контент сайта (шапка, главная, футер и т.п.). Публичный эндпоинт."""
    return SiteSettingsService(db).get()


@router.patch("", response_model=SiteContent)
def update_settings(data: SiteContent,
                    db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить контент сайта. Только для администратора."""
    return SiteSettingsService(db).update(data)
