import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from ..config import settings

# Content-Type от клиента нельзя доверять как единственной проверке (легко
# подделать), но полноценный анализ содержимого (например, Pillow) — лишняя
# зависимость ради задачи "картинка для сайта". Белого списка типов +
# серверного (не из пользовательского ввода) имени файла достаточно, чтобы
# исключить path traversal и загрузку произвольных не-картинок.
_ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def save_uploaded_image(file: UploadFile) -> str:
    """Сохраняет загруженное изображение на диск (settings.upload_dir) и
    возвращает публичный URL — раздаётся тем же FastAPI через StaticFiles
    (см. main.py), путь /api/uploads/... проходит через тот же nginx
    location /api, что и остальной бэкенд, без отдельной настройки.

    400 — неподдерживаемый тип или пустой файл; 413 — больше upload_max_size_mb.
    """
    ext = _ALLOWED_CONTENT_TYPES.get(file.content_type)
    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только изображения (JPEG, PNG, WebP, GIF)",
        )

    max_bytes = settings.upload_max_size_mb * 1024 * 1024
    # Читаем максимум на 1 байт больше лимита — достаточно, чтобы отличить
    # "ровно лимит" от "больше лимита", не держа в памяти файл целиком, если
    # он окажется сильно больше допустимого.
    data = file.file.read(max_bytes + 1)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустой файл")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Файл больше {settings.upload_max_size_mb} МБ",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    (upload_dir / filename).write_bytes(data)

    return f"/api/uploads/{filename}"
