from fastapi import APIRouter, Depends, HTTPException, Request, status

from shared.models.payloads import TransactionPayload

from app.services.publisher import RedisPublisher

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])


def get_publisher(request: Request) -> RedisPublisher:
    return request.app.state.publisher


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a financial transaction",
    response_description="Accepted — transaction queued for graph processing",
)
async def ingest_transaction(
    payload: TransactionPayload,
    publisher: RedisPublisher = Depends(get_publisher),
) -> dict:
    try:
        entry_id = await publisher.publish_transaction(payload.model_dump(mode="json"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to publish to message broker: {exc}",
        )
    return {
        "status": "accepted",
        "transaction_id": payload.transaction_id,
        "stream_entry_id": entry_id,
    }
