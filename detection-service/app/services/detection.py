from __future__ import annotations

from datetime import datetime, timedelta, timezone

from neo4j import AsyncSession

from app.services import fraud_queries as q


class DetectionService:
    """
    Runs all fraud detection Cypher queries against Neo4j.
    Each method is a standalone async call returning plain dicts for JSON serialization.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _cutoff(seconds: int) -> str:
        """Return an ISO 8601 UTC datetime string for `now - seconds`."""
        return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()

    # ── Fraud detection patterns ──────────────────────────────────────────────

    async def velocity_fraud(
        self, window_seconds: int = 60, threshold: int = 5
    ) -> list[dict]:
        result = await self._session.run(
            q.QUERY_VELOCITY_FRAUD,
            cutoff_iso=self._cutoff(window_seconds),
            threshold=threshold,
        )
        return [r.data() async for r in result]

    async def device_sharing(
        self, window_hours: int = 24, threshold: int = 3
    ) -> list[dict]:
        result = await self._session.run(
            q.QUERY_DEVICE_SHARING,
            cutoff_iso=self._cutoff(window_hours * 3600),
            threshold=threshold,
        )
        return [r.data() async for r in result]

    async def ip_sharing(
        self, window_hours: int = 1, threshold: int = 3
    ) -> list[dict]:
        result = await self._session.run(
            q.QUERY_IP_SHARING,
            cutoff_iso=self._cutoff(window_hours * 3600),
            threshold=threshold,
        )
        return [r.data() async for r in result]

    async def circular_transfer(
        self, window_hours: int = 24, min_txns: int = 3
    ) -> list[dict]:
        result = await self._session.run(
            q.QUERY_CIRCULAR_TRANSFER,
            cutoff_iso=self._cutoff(window_hours * 3600),
            min_txns=min_txns,
        )
        return [r.data() async for r in result]

    async def geo_anomaly(self, window_minutes: int = 10) -> list[dict]:
        result = await self._session.run(
            q.QUERY_GEO_ANOMALY,
            window_minutes=window_minutes,
        )
        return [r.data() async for r in result]

    # ── Composite risk score ──────────────────────────────────────────────────

    async def risk_score(self, transaction_id: str) -> dict:
        """
        Compute a composite risk score (0–100) for a single transaction.

        Three signals are checked:
          - Velocity  (+40 if card had >5 txns in last 60s)
          - Device    (+30 if device shared by >3 cards in last 24h)
          - IP        (+20 if IP shared by >3 accounts in last 1h)

        risk_level: HIGH (>=60) | MEDIUM (>=30) | LOW (<30)
        """
        score = 0
        signals: list[dict] = []

        # Velocity check
        res = await self._session.run(
            q.RISK_VELOCITY_CHECK,
            txn_id=transaction_id,
            cutoff_iso=self._cutoff(60),
        )
        record = await res.single()
        if record and record["cnt"] > 5:
            score += 40
            signals.append({"type": "VELOCITY", "value": record["cnt"]})

        # Device sharing check
        res = await self._session.run(
            q.RISK_DEVICE_CHECK,
            txn_id=transaction_id,
            cutoff_iso=self._cutoff(86_400),
        )
        record = await res.single()
        if record and record["cnt"] > 3:
            score += 30
            signals.append({"type": "DEVICE_SHARING", "value": record["cnt"]})

        # IP sharing check
        res = await self._session.run(
            q.RISK_IP_CHECK,
            txn_id=transaction_id,
            cutoff_iso=self._cutoff(3_600),
        )
        record = await res.single()
        if record and record["cnt"] > 3:
            score += 20
            signals.append({"type": "IP_SHARING", "value": record["cnt"]})

        final_score = min(score, 100)
        return {
            "transaction_id": transaction_id,
            "risk_score": final_score,
            "risk_level": (
                "HIGH" if final_score >= 60 else "MEDIUM" if final_score >= 30 else "LOW"
            ),
            "signals": signals,
        }

    # ── Entity subgraph ───────────────────────────────────────────────────────

    async def entity_graph(self, entity_id: str, depth: int = 2) -> dict:
        """
        Return the neighbourhood subgraph of a given entity for visualization.
        Resolves the entity across all possible ID property names.
        """
        # Inject depth directly into query string (not user input via parameters —
        # Neo4j does not support variable-length range params like [*1..$depth]).
        # depth is validated by FastAPI to be 1–4, so this is safe.
        cypher = q.ENTITY_SUBGRAPH.replace("{depth}", str(depth))
        result = await self._session.run(cypher, eid=entity_id)
        records = [r.data() async for r in result]
        return {
            "entity_id": entity_id,
            "depth": depth,
            "subgraph": records,
        }
