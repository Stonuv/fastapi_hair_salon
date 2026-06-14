from .auth         import router as auth_router
from .services     import router as services_router
from .masters      import router as masters_router
from .appointments import router as appointments_router
from .admin        import router as admin_router

__all__ = [
    "auth_router",
    "services_router",
    "masters_router",
    "appointments_router",
    "admin_router",
]
