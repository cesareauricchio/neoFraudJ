from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health(request: Request) -> dict:
    driver = request.app.state.neo4j_driver
    try:
        await driver.verify_connectivity()
        neo4j_ok = True
    except Exception:
        neo4j_ok = False

    return {
        "service": "neofraudj-detection",
        "neo4j": "ok" if neo4j_ok else "error",
        "status": "ok" if neo4j_ok else "degraded",
    }
