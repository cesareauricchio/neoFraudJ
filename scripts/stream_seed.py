"""
stream_seed.py — Simulate a continuous flow of incoming transactions.

Uses the same data pool as bulk_seed.py so node IDs match the initial graph.
Sends transactions at a configurable rate and periodically injects fraud signals.

Usage:
    pip install httpx
    python scripts/stream_seed.py [--url http://localhost:8001] [--rate 1.0] [--fraud-rate 0.05]

Controls:
    Ctrl+C  — stop the stream and print a summary
"""

from __future__ import annotations

import argparse
import asyncio
import random
import signal
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from seed_data import CARDS, DEVICES, IP_POOL, MERCHANTS

# ─── Transaction factories ────────────────────────────────────────────────────

def normal_transaction() -> dict[str, Any]:
    card = random.choice(CARDS)
    ip   = random.choice(IP_POOL)
    return {
        "transaction_id": str(uuid.uuid4()),
        "amount":         str(round(random.uniform(1.0, 1500.0), 2)),
        "currency":       random.choice(["USD", "EUR", "GBP"]),
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "user_id":        card["user_id"],
        "account_id":     card["account_id"],
        "card": {
            "card_id":        card["card_id"],
            "card_last_four": card["card_last_four"],
            "card_type":      card["card_type"],
        },
        "merchant": random.choice(MERCHANTS),
        "device":   random.choice(DEVICES),
        "ip_address": ip["ip_address"],
        "ip_country": ip["ip_country"],
    }


def velocity_burst() -> list[dict[str, Any]]:
    """6 rapid transactions on the same card — triggers velocity detection."""
    card   = random.choice(CARDS)
    device = random.choice(DEVICES)
    ip     = random.choice(IP_POOL)
    now    = datetime.now(timezone.utc)
    return [
        {
            "transaction_id": str(uuid.uuid4()),
            "amount":         str(round(random.uniform(10.0, 200.0), 2)),
            "currency":       "USD",
            "timestamp":      (now + timedelta(seconds=i * 2)).isoformat(),
            "user_id":        card["user_id"],
            "account_id":     card["account_id"],
            "card": {
                "card_id":        card["card_id"],
                "card_last_four": card["card_last_four"],
                "card_type":      card["card_type"],
            },
            "merchant":   random.choice(MERCHANTS),
            "device":     device,
            "ip_address": ip["ip_address"],
            "ip_country": ip["ip_country"],
        }
        for i in range(6)
    ]


def geo_anomaly() -> list[dict[str, Any]]:
    """Same card from two different countries within 3 minutes — impossible travel."""
    card      = random.choice(CARDS)
    device    = random.choice(DEVICES)
    now       = datetime.now(timezone.utc)
    countries = random.sample(["US", "GB", "DE", "FR", "JP", "BR", "AU"], 2)
    ips       = [
        f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        for _ in range(2)
    ]
    return [
        {
            "transaction_id": str(uuid.uuid4()),
            "amount":         str(round(random.uniform(50.0, 500.0), 2)),
            "currency":       random.choice(["USD", "EUR", "GBP"]),
            "timestamp":      (now + timedelta(minutes=i * 3)).isoformat(),
            "user_id":        card["user_id"],
            "account_id":     card["account_id"],
            "card": {
                "card_id":        card["card_id"],
                "card_last_four": card["card_last_four"],
                "card_type":      card["card_type"],
            },
            "merchant":   random.choice(MERCHANTS),
            "device":     device,
            "ip_address": ips[i],
            "ip_country": countries[i],
        }
        for i in range(2)
    ]


FRAUD_FACTORIES = {
    "velocity_burst": velocity_burst,
    "geo_anomaly":    geo_anomaly,
}

# ─── Stream loop ──────────────────────────────────────────────────────────────

class Stats:
    sent: int = 0
    accepted: int = 0
    failed: int = 0
    fraud_events: int = 0


async def send_one(client: httpx.AsyncClient, url: str, payload: dict, stats: Stats, label: str = "") -> None:
    try:
        r = await client.post(url, json=payload, timeout=10.0)
        if r.status_code == 202:
            stats.accepted += 1
            tag      = f"  [{label}]" if label else ""
            card     = payload["card"]
            merchant = payload["merchant"]["merchant_name"]
            print(
                f"  ✓{tag} {payload['transaction_id'][:8]}… | "
                f"{card['card_id']} (···· {card['card_last_four']}) | "
                f"{payload['amount']} {payload['currency']} @ {merchant} ({payload['ip_country']})"
            )
        else:
            stats.failed += 1
            print(f"  ✗ HTTP {r.status_code}")
    except Exception as exc:
        stats.failed += 1
        print(f"  ✗ {exc}")
    finally:
        stats.sent += 1


async def run(base_url: str, rate: float, fraud_rate: float) -> None:
    endpoint   = f"{base_url}/v1/transactions"
    stats      = Stats()
    interval   = 1.0 / rate
    stop_event = asyncio.Event()

    def _handle_sigint(*_):
        print("\n\nStopping stream...")
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_sigint)

    print("NeoFraudJ stream seeder started")
    print(f"  Rate:       {rate} txn/sec")
    print(f"  Fraud rate: {fraud_rate * 100:.0f}% of ticks inject a fraud burst")
    print(f"  Endpoint:   {endpoint}")
    print("─" * 60)

    async with httpx.AsyncClient() as client:
        while not stop_event.is_set():
            tick_start = asyncio.get_event_loop().time()

            if random.random() < fraud_rate:
                fraud_type = random.choice(list(FRAUD_FACTORIES))
                payloads   = FRAUD_FACTORIES[fraud_type]()
                stats.fraud_events += 1
                print(f"\n  ⚠ Injecting fraud: {fraud_type} ({len(payloads)} txns)")
                await asyncio.gather(*[
                    send_one(client, endpoint, p, stats, label=fraud_type)
                    for p in payloads
                ])
                print()
            else:
                await send_one(client, endpoint, normal_transaction(), stats)

            elapsed   = asyncio.get_event_loop().time() - tick_start
            sleep_for = max(0.0, interval - elapsed)
            try:
                await asyncio.wait_for(asyncio.shield(stop_event.wait()), timeout=sleep_for)
            except asyncio.TimeoutError:
                pass

    print("─" * 60)
    print(f"Stream stopped.")
    print(f"  Total sent:   {stats.sent}")
    print(f"  Accepted:     {stats.accepted}")
    print(f"  Failed:       {stats.failed}")
    print(f"  Fraud bursts: {stats.fraud_events}")


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream live transactions into NeoFraudJ")
    parser.add_argument("--url",        default="http://localhost:8001", help="Ingestion service base URL")
    parser.add_argument("--rate",       type=float, default=1.0,         help="Transactions per second")
    parser.add_argument("--fraud-rate", type=float, default=0.05,        help="Probability of fraud burst per tick")
    args = parser.parse_args()

    asyncio.run(run(args.url, args.rate, args.fraud_rate))
