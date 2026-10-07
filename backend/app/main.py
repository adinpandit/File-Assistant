from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.documents import router as document_router
from app.api.routes.query import router as query_router
from app.api.routes.history import router as history_router
from app.core.logging import setup_logging
from app.core.db import initialize_database

setup_logging()

@asynccontextmanager
async def lifespan(app:FastAPI):
    initialize_database()
    yield

app = FastAPI(
    title = settings.app_name,
    version = settings.app_version,
    debug = settings.debug,
    lifespan = lifespan,
)

app.include_router(health_router)
app.include_router(auth_router , prefix=settings.api_prefix,)
app.include_router(upload_router , prefix=settings.api_prefix)
app.include_router(document_router , prefix=settings.api_prefix)
app.include_router(query_router , prefix=settings.api_prefix)
app.include_router(history_router , prefix=settings.api_prefix)

@app.get("/")
def root():
    return{
        "name":settings.app_name,
        "version":settings.app_version,
        "status":"running",
    }

