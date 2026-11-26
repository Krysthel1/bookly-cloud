import logging
from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.database.session import get_db
from app.exceptions.handlers import register_exception_handlers
from app.middlewares.security import ObservabilityMiddleware, limiter

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(message)s",
)

app = FastAPI(
    title="BOOKLY API",
    description=(
        "API REST modular para la librería digital BOOKLY. "
        "Gestiona catálogo, carrito persistente, checkout transaccional, inventario, "
        "cupones, reseñas y analítica administrativa."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

register_exception_handlers(app)


@app.get("/health", tags=["Infraestructura"])
def health_check():
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.get("/ready", tags=["Infraestructura"])
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "unavailable", "detail": str(exc)},
        )


app.include_router(api_router, prefix=settings.api_v1_prefix)
