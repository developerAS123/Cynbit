from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from implementation.core.config import settings
from implementation.core.database import engine, Base
from implementation.middleware.security_headers import SecurityHeadersMiddleware
from implementation.middleware.audit_log import AuditLoggingMiddleware
from implementation.api.v1.health import router as health_router
from implementation.api.v1.auth import router as auth_router
from implementation.api.v1.inquiries import router as inquiries_router
from implementation.api.v1.applications import router as applications_router
from implementation.api.v1.payments import router as payments_router
from implementation.api.v1.intern import router as intern_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing database table creation and cleanup."""
    # Ensure database schema exists on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Graceful shutdown
    await engine.dispose()

def create_application() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="High-performance, defense-in-depth async backend service for Cynbit Technologies.",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan
    )

    # 1. Audit Logging Middleware (Outermost)
    app.add_middleware(AuditLoggingMiddleware)

    # 2. Defense-in-Depth Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Strict CORS (Replaces the observed wildcard '*')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=86400
    )

    # Mount v1 API Routers
    api_v1_prefix = "/api/v1"
    app.include_router(health_router, prefix=api_v1_prefix)
    app.include_router(auth_router, prefix=api_v1_prefix)
    app.include_router(inquiries_router, prefix=api_v1_prefix)
    app.include_router(applications_router, prefix=api_v1_prefix)
    app.include_router(payments_router, prefix=api_v1_prefix)
    app.include_router(intern_router, prefix=api_v1_prefix)

    return app

app = create_application()

