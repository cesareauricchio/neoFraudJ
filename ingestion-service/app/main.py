from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.routers import health, transactions
from app.services.publisher import RedisPublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    publisher = RedisPublisher()
    await publisher.connect(settings.redis_url)
    app.state.publisher = publisher
    yield
    await publisher.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="NeoFraudJ — Ingestion Service",
        description="Validates incoming financial transactions and publishes them to Redis Streams.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(transactions.router)
    app.include_router(health.router)
    return app


app = create_app()
