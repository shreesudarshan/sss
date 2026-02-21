"""FastAPI application entrypoint.

Startup behavior:
- read settings
- initialize database tables
- register auth and patient routers
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import logger
from app.auth_routes import router as auth_router
from app.database import get_database_status, init_db
from app.routes import router as patient_router
from app.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize persistent storage before serving traffic."""
    await init_db()
    logger.info("Application startup complete")
    yield


app = FastAPI(title="Secure Bloom SSE", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> dict[str, str]:
    """Simple liveness endpoint."""
    return {"message": "Secure Bloom SSE API is running"}


@app.get("/health")
async def health() -> dict[str, bool | str | None]:
    """Health endpoint for checks and monitoring."""
    db_ready, db_error = get_database_status()
    return {"status": db_ready, "database_ready": db_ready, "database_error": db_error}


app.include_router(auth_router)
app.include_router(patient_router)
