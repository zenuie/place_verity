# veritas_app/core/clients.py
import httpx
from openai import AsyncOpenAI

from .config import settings


class APIClientManager:
    """A manager for handling the lifecycle of API clients."""

    def __init__(self):
        self.httpx_client = httpx.AsyncClient()
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        print("API Clients initialized.")

    async def close(self):
        await self.httpx_client.aclose()
        # The openai client closes its httpx client automatically, no explicit close needed.
        print("API Clients closed gracefully.")


# A global instance that will be managed by the FastAPI lifespan
api_clients = APIClientManager()
