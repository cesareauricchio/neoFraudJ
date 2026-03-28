from __future__ import annotations

import logging

from neo4j import AsyncDriver

logger = logging.getLogger(__name__)

# Uniqueness constraints — one per node label.
# IF NOT EXISTS makes these idempotent (safe to re-run on startup).
CONSTRAINTS: list[str] = [
    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
    "CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.account_id IS UNIQUE",
    "CREATE CONSTRAINT card_id_unique IF NOT EXISTS FOR (c:Card) REQUIRE c.card_id IS UNIQUE",
    "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE",
    "CREATE CONSTRAINT merchant_id_unique IF NOT EXISTS FOR (m:Merchant) REQUIRE m.merchant_id IS UNIQUE",
    "CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE",
    "CREATE CONSTRAINT ip_address_unique IF NOT EXISTS FOR (ip:IPAddress) REQUIRE ip.ip_address IS UNIQUE",
]

# Property indexes for performance.
# txn_timestamp_idx is CRITICAL — used in every fraud detection WHERE clause.
INDEXES: list[str] = [
    "CREATE INDEX txn_timestamp_idx IF NOT EXISTS FOR (t:Transaction) ON (t.timestamp)",
    "CREATE INDEX device_type_idx IF NOT EXISTS FOR (d:Device) ON (d.device_type)",
    "CREATE INDEX ip_country_idx IF NOT EXISTS FOR (ip:IPAddress) ON (ip.ip_country)",
    "CREATE INDEX merchant_country_idx IF NOT EXISTS FOR (m:Merchant) ON (m.merchant_country)",
]


async def apply_schema(driver: AsyncDriver, database: str = "neo4j") -> None:
    """Apply all constraints and indexes idempotently. Called once at startup."""
    async with driver.session(database=database) as session:
        for stmt in CONSTRAINTS + INDEXES:
            await session.run(stmt)
            logger.debug("Applied: %s", stmt)
    logger.info("Neo4j schema constraints and indexes applied.")
