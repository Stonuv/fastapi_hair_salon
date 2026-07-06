from .admin         import router as admin_router
from .appointments  import router as appointments_router
from .auth          import router as auth_router
from .masters       import router as masters_router
from .reviews       import router as reviews_router
from .services      import router as services_router
from .setup         import router as setup_router
from .site_settings import router as site_settings_router

__all__ = [
    "auth_router",
    "services_router",
    "masters_router",
    "appointments_router",
    "admin_router",
    "reviews_router",
    "site_settings_router",
    "setup_router",
]
