import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
            'app.main:app',
            host=settings.host, # 127.0.0.1
            port=settings.port, # 8000
            reload=settings.debug, # True
            log_level='debug',
            )
