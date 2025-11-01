# veritas_app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints import router
from app.core.clients import api_clients


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    app.state.api_clients = api_clients
    yield
    # On shutdown
    await app.state.api_clients.close()


app = FastAPI(
    title="Veritas - Data Verification System",
    description="A best-practice MVP for location data verification.",
    version="1.0.0",
    lifespan=lifespan
)

# Include the API router
app.include_router(router, prefix="/verify")
