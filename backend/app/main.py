from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from .config import settings
from .routes import (auth_router, services_router,
                     masters_router, appointments_router, admin_router)

security = HTTPBearer()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    # Явно регистрируем HTTPBearer — появится отдельное поле в Authorize
    swagger_ui_init_oauth={},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(services_router)
app.include_router(masters_router)
app.include_router(appointments_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/api/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
