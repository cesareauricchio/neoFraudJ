"""
bulk_seed.py — Wipe Neo4j and populate it with a realistic initial dataset.

Connects directly to Neo4j to wipe all data first, then sends ~500 transactions
through the ingestion service (which writes to Neo4j via the processor).
Includes deliberate fraud patterns for the detection service to find.

Usage:
    pip install httpx neo4j
    python scripts/bulk_seed.py [--url http://localhost:8001] [--concurrency 20]
                                [--neo4j-uri bolt://localhost:7687]
                                [--neo4j-user neo4j] [--neo4j-password neofraudj_secret]
"""

from __future__ import annotations

import argparse
import asyncio
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from neo4j import AsyncGraphDatabase

from seed_data import CARDS, DEVICES, IP_POOL, MERCHANTS

# ─── Transaction builder ──────────────────────────────────────────────────────

def make_transaction(
    *,
    card: dict,
    merchant: dict,
    device: dict,
    ip: dict,
    amount: float | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    ts = timestamp or (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 72)))
    return {
        "transaction_id": str(uuid.uuid4()),
        "amount":         str(round(amount or random.uniform(1.0, 2000.0), 2)),
        "currency":       random.choice(["USD", "EUR", "GBP"]),
        "timestamp":      ts.isoformat(),
        "user_id":        card["user_id"],
        "account_id":     card["account_id"],
        "card": {
            "card_id":        card["card_id"],
            "card_last_four": card["card_last_four"],
            "card_type":      card["card_type"],
        },
        "merchant": merchant,
        "device": {
            "device_id":          device["device_id"],
            "device_type":        device["device_type"],
            "device_fingerprint": device["device_fingerprint"],
        },
        "ip_address": ip["ip_address"],
        "ip_country": ip["ip_country"],
    }


# ─── Fraud pattern injectors ──────────────────────────────────────────────────

def inject_velocity_fraud(transactions: list[dict]) -> None:
    """crd_luca_amex fires 8 rapid transactions at Starbucks → velocity alert."""
    card     = next(c for c in CARDS if c["card_id"] == "crd_luca_amex")
    merchant = next(m for m in MERCHANTS if m["merchant_id"] == "mrc_starbucks")
    device   = next(d for d in DEVICES if d["device_id"] == "dev_luca_android")
    ip       = {"ip_address": "203.0.113.10", "ip_country": "US"}
    base     = datetime.now(timezone.utc) - timedelta(seconds=40)
    for i in range(8):
        transactions.append(make_transaction(
            card=card, merchant=merchant, device=device, ip=ip,
            amount=4.75, timestamp=base + timedelta(seconds=i * 4),
        ))
    print("  [fraud] Velocity  — Luca Ferrari / crd_luca_amex: 8 rapid txns at Starbucks")


def inject_device_sharing(transactions: list[dict]) -> None:
    """dev_shared_pos used by 4 different cards → device sharing alert."""
    shared_device = next(d for d in DEVICES if d["device_id"] == "dev_shared_pos")
    cards_to_use  = CARDS[:4]
    for card in cards_to_use:
        transactions.append(make_transaction(
            card=card,
            merchant=random.choice(MERCHANTS),
            device=shared_device,
            ip=random.choice(IP_POOL),
            timestamp=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 20)),
        ))
    names = ", ".join(c["card_id"] for c in cards_to_use)
    print(f"  [fraud] Device sharing — dev_shared_pos used by: {names}")


def inject_ip_sharing(transactions: list[dict]) -> None:
    """100.64.1.10 (ES) used by 4 different accounts → IP sharing alert."""
    shared_ip    = {"ip_address": "100.64.1.10", "ip_country": "ES"}
    seen_accounts: set[str] = set()
    used_cards: list[dict] = []
    for card in CARDS:
        if card["account_id"] not in seen_accounts:
            seen_accounts.add(card["account_id"])
            used_cards.append(card)
        if len(used_cards) == 4:
            break
    for card in used_cards:
        transactions.append(make_transaction(
            card=card,
            merchant=random.choice(MERCHANTS),
            device=random.choice(DEVICES),
            ip=shared_ip,
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 55)),
        ))
    print("  [fraud] IP sharing  — 100.64.1.10 (ES) used by 4 different accounts")


def inject_geo_anomaly(transactions: list[dict]) -> None:
    """crd_sofia_visa: Amazon US then Tesco GB within 4 minutes → impossible travel."""
    card    = next(c for c in CARDS if c["card_id"] == "crd_sofia_visa")
    device  = next(d for d in DEVICES if d["device_id"] == "dev_sofia_macbook")
    base    = datetime.now(timezone.utc) - timedelta(minutes=10)
    transactions.append(make_transaction(
        card=card,
        merchant=next(m for m in MERCHANTS if m["merchant_id"] == "mrc_amazon"),
        device=device,
        ip={"ip_address": "203.0.113.11", "ip_country": "US"},
        timestamp=base,
    ))
    transactions.append(make_transaction(
        card=card,
        merchant=next(m for m in MERCHANTS if m["merchant_id"] == "mrc_tesco"),
        device=device,
        ip={"ip_address": "198.51.100.10", "ip_country": "GB"},
        timestamp=base + timedelta(minutes=4),
    ))
    print("  [fraud] Geo anomaly — Sofia Garcia / crd_sofia_visa: US → GB in 4 min")


# ─── Neo4j wipe ───────────────────────────────────────────────────────────────

async def wipe_neo4j(uri: str, user: str, password: str) -> None:
    print(f"Connecting to Neo4j at {uri}...")
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    try:
        async with driver.session() as session:
            result = await session.run("MATCH (n) DETACH DELETE n")
            await result.consume()
        print("  ✓ All existing nodes and relationships deleted")
    finally:
        await driver.close()


# ─── HTTP sender ──────────────────────────────────────────────────────────────

async def send(client: httpx.AsyncClient, url: str, payload: dict, sem: asyncio.Semaphore) -> bool:
    async with sem:
        try:
            r = await client.post(url, json=payload, timeout=10.0)
            return r.status_code == 202
        except Exception as exc:
            print(f"  [error] {exc}")
            return False


async def wait_for_ingestion(base_url: str, retries: int = 15, delay: float = 2.0) -> None:
    print(f"Waiting for ingestion service at {base_url}...")
    async with httpx.AsyncClient() as client:
        for i in range(retries):
            try:
                r = await client.get(f"{base_url}/health", timeout=3.0)
                if r.status_code < 500:
                    print("  ✓ Ingestion service ready")
                    return
            except Exception:
                pass
            print(f"  … retry {i+1}/{retries}")
            await asyncio.sleep(delay)
    raise RuntimeError("Ingestion service did not become ready in time")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def run(base_url: str, concurrency: int, neo4j_uri: str, neo4j_user: str, neo4j_password: str) -> None:
    # 1. Wipe
    await wipe_neo4j(neo4j_uri, neo4j_user, neo4j_password)

    # 2. Wait for ingestion service
    await wait_for_ingestion(base_url)

    # 3. Build transactions
    transactions: list[dict] = []

    print("\nGenerating normal transactions...")
    for _ in range(460):
        transactions.append(make_transaction(
            card=random.choice(CARDS),
            merchant=random.choice(MERCHANTS),
            device=random.choice(DEVICES),
            ip=random.choice(IP_POOL),
        ))

    print("Injecting fraud patterns...")
    inject_velocity_fraud(transactions)
    inject_device_sharing(transactions)
    inject_ip_sharing(transactions)
    inject_geo_anomaly(transactions)

    random.shuffle(transactions)
    total = len(transactions)
    print(f"\nSending {total} transactions (concurrency={concurrency})...")

    # 4. Send
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(base_url=base_url) as client:
        results = await asyncio.gather(*[
            send(client, "/v1/transactions", txn, sem) for txn in transactions
        ])

    ok     = sum(results)
    failed = total - ok
    print(f"\nDone.  Accepted: {ok}  |  Failed: {failed}")
    print("\nFraud patterns seeded:")
    print("  • Velocity fraud (Luca Ferrari / crd_luca_amex)")
    print("  • Device sharing (dev_shared_pos across 4 cards)")
    print("  • IP sharing    (100.64.1.10 across 4 accounts)")
    print("  • Geo anomaly   (Sofia Garcia / crd_sofia_visa: US → GB)")


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wipe Neo4j and bulk-seed NeoFraudJ")
    parser.add_argument("--url",            default="http://localhost:8001",  help="Ingestion service base URL")
    parser.add_argument("--concurrency",    type=int, default=20,             help="Max concurrent requests")
    parser.add_argument("--neo4j-uri",      default="bolt://localhost:7687",  help="Neo4j Bolt URI")
    parser.add_argument("--neo4j-user",     default="neo4j",                  help="Neo4j username")
    parser.add_argument("--neo4j-password", default="neofraudj_secret",       help="Neo4j password")
    args = parser.parse_args()

    asyncio.run(run(
        args.url, args.concurrency,
        args.neo4j_uri, args.neo4j_user, args.neo4j_password,
    ))
