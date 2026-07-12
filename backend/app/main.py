import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routes import (auth_router, services_router,
                     masters_router, appointments_router, admin_router,
                     reviews_router, site_settings_router, setup_router)
from .scheduler import lifespan

# uvicorn настраивает только свои собственные логгеры (uvicorn.*) —
# без этого вызова логгеры приложения (например, auth_service при
# восстановлении пароля) молча проглатываются root-логгером.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(setup_router)
app.include_router(auth_router)
app.include_router(services_router)
app.include_router(masters_router)
app.include_router(appointments_router)
app.include_router(admin_router)
app.include_router(reviews_router)
app.include_router(site_settings_router)

# Загруженные изображения (фото мастеров, hero-картинка — см. utils/uploads).
# Путь /api/uploads проходит через тот же nginx location /api, что и весь
# остальной бэкенд (frontend/nginx.conf) — отдельная настройка не нужна.
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/api/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
