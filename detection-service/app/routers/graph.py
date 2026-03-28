from fastapi import APIRouter, Query, Request

from app.services.detection import DetectionService

router = APIRouter(prefix="/v1/entities", tags=["graph"])


@router.get(
    "/{entity_id}/graph",
    summary="Get neighbourhood subgraph for an entity (for visualization)",
)
async def get_entity_graph(
    entity_id: str,
    request: Request,
    depth: int = Query(default=2, ge=1, le=4, description="Traversal depth (1–4)"),
) -> dict:
    async with request.app.state.neo4j_driver.session(
        database=request.app.state.neo4j_database
    ) as session:
        svc = DetectionService(session)
        return await svc.entity_graph(entity_id, depth)
