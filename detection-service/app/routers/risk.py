from fastapi import APIRouter, Request

from app.services.detection import DetectionService

router = APIRouter(prefix="/v1/transactions", tags=["risk"])


@router.get(
    "/{transaction_id}/risk-score",
    summary="Get composite fraud risk score for a transaction",
)
async def get_risk_score(transaction_id: str, request: Request) -> dict:
    async with request.app.state.neo4j_driver.session(
        database=request.app.state.neo4j_database
    ) as session:
        svc = DetectionService(session)
        return await svc.risk_score(transaction_id)
