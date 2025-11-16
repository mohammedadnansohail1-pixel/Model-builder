"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.redis import close_redis, get_redis
from app.api.v1 import auth, users, organizations, projects, models, datasets, training, deployments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await get_redis()
    yield
    # Shutdown
    await close_redis()


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware in production
if settings.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return JSONResponse(
        content={
            "status": "healthy",
            "redis": redis_status,
        }
    )


# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["authentication"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"]
)

app.include_router(
    organizations.router,
    prefix=f"{settings.API_V1_PREFIX}/organizations",
    tags=["organizations"]
)

app.include_router(
    projects.router,
    prefix=f"{settings.API_V1_PREFIX}/projects",
    tags=["projects"]
)

app.include_router(
    models.router,
    prefix=f"{settings.API_V1_PREFIX}/models",
    tags=["models"]
)

app.include_router(
    datasets.router,
    prefix=f"{settings.API_V1_PREFIX}/datasets",
    tags=["datasets"]
)

app.include_router(
    training.router,
    prefix=f"{settings.API_V1_PREFIX}/training",
    tags=["training"]
)

app.include_router(
    deployments.router,
    prefix=f"{settings.API_V1_PREFIX}/deployments",
    tags=["deployments"]
)
