from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import auth_router, services_router, masters_router, appointments_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Роуты ────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(services_router)
app.include_router(masters_router)
app.include_router(appointments_router)


# ── Служебные эндпоинты ──────────────────────────────────────────
@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "docs": "/api/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
