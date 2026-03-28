from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.graph_builder import payload_to_delta

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


# ─── Connection manager ───────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, data: dict) -> None:
        dead: set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self._connections -= dead

    @property
    def count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


# ─── Fraud check ─────────────────────────────────────────────────────────────

async def _quick_fraud_check(payload: dict, neo4j_driver, database: str) -> bool:
    """
    Velocity check: has this card fired >= 5 transactions in the last 60s?

    Looks up by card_id directly (not via transaction_id) so the check does not
    depend on the specific triggering transaction having been written yet.
    Waits 1s first to let the processor flush the batch to Neo4j.
    """
    await asyncio.sleep(1.0)
    try:
        card_id = payload.get("card", {}).get("card_id")
        if not card_id:
            return False
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
        async with neo4j_driver.session(database=database) as session:
            result = await session.run(
                """
                MATCH (c:Card {card_id: $card_id})-[:PERFORMED]->(t:Transaction)
                WHERE t.timestamp >= datetime($cutoff_iso)
                RETURN count(t) AS cnt
                """,
                card_id=card_id,
                cutoff_iso=cutoff,
            )
            record = await result.single()
            return bool(record and record["cnt"] >= 5)
    except Exception as exc:
        logger.debug("Fraud check failed (non-critical): %s", exc)
        return False


async def _persist_fraud(payload: dict, neo4j_driver, database: str) -> None:
    """
    Write isFraud = true permanently onto the Transaction and Card nodes in Neo4j
    so the flag survives service restarts and is visible in static graph queries.
    """
    txn_id = payload.get("transaction_id")
    card_id = payload.get("card", {}).get("card_id")
    if not txn_id:
        return
    try:
        async with neo4j_driver.session(database=database) as session:
            await session.run(
                """
                MATCH (t:Transaction {transaction_id: $txn_id})
                SET t.isFraud = true
                WITH t
                OPTIONAL MATCH (c:Card {card_id: $card_id})-[:PERFORMED]->(t)
                SET c.isFraud = true
                """,
                txn_id=txn_id,
                card_id=card_id or "",
            )
        logger.info("Persisted isFraud=true for txn=%s card=%s", txn_id, card_id)
    except Exception as exc:
        logger.error("Failed to persist fraud flag for txn=%s: %s", txn_id, exc)


# ─── Redis broadcast loop ─────────────────────────────────────────────────────

async def _process_entry(entry_id: str, fields: dict, neo4j_driver, database: str) -> None:
    try:
        payload = json.loads(fields.get("data", "{}"))
        is_fraud = await _quick_fraud_check(payload, neo4j_driver, database)
        if is_fraud:
            await _persist_fraud(payload, neo4j_driver, database)
        await manager.broadcast(payload_to_delta(payload, is_fraud))
        logger.debug(
            "Broadcasted txn=%s fraud=%s clients=%d",
            payload.get("transaction_id", "?"),
            is_fraud,
            manager.count,
        )
    except Exception as exc:
        logger.error("Error processing stream entry %s: %s", entry_id, exc)


async def _read_once(client, stream_name: str, last_id: str, neo4j_driver, database: str) -> str:
    results = await client.xread(streams={stream_name: last_id}, count=20, block=1000)
    for _stream, entries in (results or []):
        for entry_id, fields in entries:
            last_id = entry_id
            await _process_entry(entry_id, fields, neo4j_driver, database)
    return last_id


async def redis_broadcast_loop(
    redis_url: str,
    stream_name: str,
    neo4j_driver,
    database: str,
) -> None:
    """
    Background task: reads new entries from the Redis stream via XREAD
    (no consumer group — transparent to the processor's consumer group)
    and broadcasts GRAPH_UPDATE messages to all connected WebSocket clients.
    """
    client = aioredis.from_url(redis_url, decode_responses=True)
    last_id = "$"
    logger.info("WebSocket broadcaster started on stream '%s'", stream_name)

    try:
        while True:
            try:
                if manager.count == 0:
                    await asyncio.sleep(0.5)
                    continue
                last_id = await _read_once(client, stream_name, last_id, neo4j_driver, database)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Broadcaster loop error: %s — retrying in 2s", exc)
                await asyncio.sleep(2)
    finally:
        await client.aclose()
        logger.info("WebSocket broadcaster stopped")


# ─── Warm-up snapshot ────────────────────────────────────────────────────────

async def _send_snapshot(websocket: WebSocket, neo4j_driver, database: str) -> None:
    """
    On connect, replay the last 100 transactions as individual GRAPH_UPDATE
    messages so the client graph is warm without a separate REST call.
    """
    try:
        async with neo4j_driver.session(database=database) as session:
            result = await session.run(
                """
                MATCH (u:User)-[:OWNS_ACCOUNT]->(a:Account)-[:HAS_CARD]->(c:Card)
                      -[:PERFORMED]->(t:Transaction)-[:PAID_TO]->(m:Merchant)
                OPTIONAL MATCH (t)-[:FROM_DEVICE]->(d:Device)
                RETURN u, a, c, t, m, d
                ORDER BY t.timestamp DESC
                LIMIT 100
                """
            )
            records = await result.data()

        # Send newest-last so the graph builds chronologically on the client
        for row in reversed(records):
            t = dict(row["t"])
            c = dict(row["c"])
            a = dict(row["a"])
            u = dict(row["u"])
            m = dict(row["m"])
            raw_d = row["d"]
            d = dict(raw_d) if raw_d else {"device_id": "unknown", "device_type": "unknown", "device_fingerprint": ""}

            def iso(v):
                return v.isoformat() if hasattr(v, "isoformat") else str(v) if v is not None else None

            msg = {
                "type": "GRAPH_UPDATE",
                "is_fraud_alert": bool(t.get("isFraud")),
                "payload": {
                    "nodes": [
                        {"id": u["user_id"],        "label": "User",        **u},
                        {"id": a["account_id"],     "label": "Account",     **a},
                        {"id": c["card_id"],        "label": "Card",        **c},
                        {"id": t["transaction_id"], "label": "Transaction", **{k: iso(v) for k, v in t.items()}},
                        {"id": m["merchant_id"],    "label": "Merchant",    **m},
                        {"id": d["device_id"],      "label": "Device",      **d},
                    ],
                    "links": [
                        {"source": u["user_id"],        "target": a["account_id"],     "label": "OWNS_ACCOUNT"},
                        {"source": a["account_id"],     "target": c["card_id"],        "label": "HAS_CARD"},
                        {"source": c["card_id"],        "target": t["transaction_id"], "label": "PERFORMED"},
                        {"source": t["transaction_id"], "target": m["merchant_id"],    "label": "PAID_TO"},
                        {"source": t["transaction_id"], "target": d["device_id"],      "label": "FROM_DEVICE"},
                    ],
                },
            }
            await websocket.send_json(msg)

        logger.info("Sent snapshot (%d txns) to new WS client", len(records))
    except Exception as exc:
        logger.error("Snapshot send failed: %s", exc)


# ─── WebSocket endpoint ───────────────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, neo4j_driver=None, database: str = "") -> None:
    await manager.connect(websocket)
    logger.info("WS client connected (total: %d)", manager.count)

    # Inject app state — FastAPI doesn't inject request.app into WS easily
    from fastapi import Request  # noqa: PLC0415
    app_state = websocket.app.state
    await _send_snapshot(websocket, app_state.neo4j_driver, app_state.neo4j_database)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
        logger.info("WS client disconnected (total: %d)", manager.count)
