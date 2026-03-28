from __future__ import annotations

import logging

import redis.asyncio as aioredis
from neo4j import AsyncGraphDatabase

from shared.models.payloads import TransactionPayload

from app.config import get_settings
from app.graph.constraints import apply_schema
from app.graph.writer import GraphWriter

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "neofraudj-processors"
CONSUMER_NAME = "processor-1"   # Use hostname in multi-replica deployments
BLOCK_MS = 2_000                # Block up to 2s waiting for new messages
BATCH_COUNT = 10                # Read up to 10 messages per iteration
CLAIM_MIN_IDLE_MS = 30_000      # Reclaim messages idle >30s (crash recovery)


async def ensure_consumer_group(client: aioredis.Redis, stream: str) -> None:
    """Create consumer group idempotently. MKSTREAM creates the stream if absent."""
    try:
        await client.xgroup_create(
            name=stream,
            groupname=CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
        logger.info("Consumer group '%s' created on stream '%s'", CONSUMER_GROUP, stream)
    except aioredis.ResponseError as exc:
        if "BUSYGROUP" in str(exc):
            logger.info("Consumer group '%s' already exists", CONSUMER_GROUP)
        else:
            raise


async def run_consumer() -> None:
    settings = get_settings()

    redis_client = await aioredis.from_url(settings.redis_url, decode_responses=True)
    neo4j_driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        max_connection_pool_size=50,
        connection_acquisition_timeout=30.0,
    )

    # Apply Neo4j constraints and indexes before starting the consumer loop
    await apply_schema(neo4j_driver, database=settings.neo4j_database)

    writer = GraphWriter()
    await ensure_consumer_group(redis_client, settings.redis_stream_name)
    logger.info("Processor consumer started. Waiting for messages...")

    try:
        async with neo4j_driver.session(database=settings.neo4j_database) as session:
            while True:
                # ── 1. Reclaim pending messages idle > CLAIM_MIN_IDLE_MS ──
                # Handles messages that were delivered but not ACKed (e.g. crash)
                claimed_result = await redis_client.xautoclaim(
                    name=settings.redis_stream_name,
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    min_idle_time=CLAIM_MIN_IDLE_MS,
                    start_id="0-0",
                    count=BATCH_COUNT,
                )
                # xautoclaim returns (next_start_id, [(id, fields), ...], deleted_ids)
                pending_entries: list = claimed_result[1] if claimed_result else []

                # ── 2. Read new messages from the stream ──────────────────
                new_raw = await redis_client.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={settings.redis_stream_name: ">"},
                    count=BATCH_COUNT,
                    block=BLOCK_MS,
                )
                new_entries: list = []
                if new_raw:
                    # Shape: [[stream_name, [(id, fields), ...]]]
                    new_entries = new_raw[0][1]

                all_entries = pending_entries + new_entries

                for entry_id, fields in all_entries:
                    try:
                        payload = TransactionPayload.model_validate_json(
                            fields.get("data", "{}")
                        )
                        await writer.write_transaction(session, payload)
                        await redis_client.xack(
                            settings.redis_stream_name, CONSUMER_GROUP, entry_id
                        )
                        logger.debug(
                            "Processed and ACKed entry %s (txn=%s)",
                            entry_id,
                            payload.transaction_id,
                        )
                    except Exception as exc:
                        # Do NOT ACK — message stays in PEL for reclaim/retry
                        logger.error(
                            "Failed to process entry %s: %s",
                            entry_id,
                            exc,
                            exc_info=True,
                        )

    finally:
        await redis_client.aclose()
        await neo4j_driver.close()
