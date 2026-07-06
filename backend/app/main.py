import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import (auth_router, services_router,
                     masters_router, appointments_router, admin_router,
                     reviews_router, site_settings_router, setup_router)

# uvicorn настраивает только свои собственные логгеры (uvicorn.*) —
# без этого вызова логгеры приложения (например, auth_service при
# восстановлении пароля) молча проглатываются root-логгером.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
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


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/api/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
