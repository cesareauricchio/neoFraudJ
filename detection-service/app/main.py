import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase

from app.config import get_settings
from app.routers import alerts, graph, health, risk
from app.routers import graph_rest, ws as ws_router
from app.routers.ws import redis_broadcast_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Neo4j driver
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        max_connection_pool_size=50,
        connection_acquisition_timeout=30.0,
    )
    await driver.verify_connectivity()
    app.state.neo4j_driver = driver
    app.state.neo4j_database = settings.neo4j_database

    # Redis broadcaster background task
    broadcaster = asyncio.create_task(
        redis_broadcast_loop(
            settings.redis_url,
            settings.redis_stream_name,
            driver,
            settings.neo4j_database,
        )
    )

    yield

    broadcaster.cancel()
    await asyncio.gather(broadcaster, return_exceptions=True)
    await driver.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="NeoFraudJ — Detection Service",
        description="Real-time fraud pattern detection via Neo4j graph queries.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(alerts.router)
    app.include_router(risk.router)
    app.include_router(graph.router)
    app.include_router(graph_rest.router)
    app.include_router(ws_router.router)
    app.include_router(health.router)
    return app


app = create_app()
