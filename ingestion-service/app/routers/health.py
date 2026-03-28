from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health(request: Request) -> dict:
    publisher = request.app.state.publisher
    try:
        await publisher._client.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "service": "neofraudj-ingestion",
        "redis": "ok" if redis_ok else "error",
        "status": "ok" if redis_ok else "degraded",
    }
