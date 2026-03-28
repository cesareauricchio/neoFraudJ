from fastapi import APIRouter, Request

from app.services.detection import DetectionService

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.get("", summary="Run all fraud detection patterns")
async def get_all_alerts(request: Request) -> dict:
    async with request.app.state.neo4j_driver.session(
        database=request.app.state.neo4j_database
    ) as session:
        svc = DetectionService(session)
        return {
            "velocity": await svc.velocity_fraud(),
            "device_sharing": await svc.device_sharing(),
            "ip_sharing": await svc.ip_sharing(),
            "circular_transfer": await svc.circular_transfer(),
            "geo_anomaly": await svc.geo_anomaly(),
        }
