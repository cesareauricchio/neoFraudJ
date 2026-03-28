.PHONY: up down build restart logs ps \
        logs-ingestion logs-processor logs-detection \
        neo4j-shell redis-cli restart-processor

# ── Lifecycle ─────────────────────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart

ps:
	docker compose ps

# ── Logs ──────────────────────────────────────────────────────────────────────

logs:
	docker compose logs -f

logs-ingestion:
	docker compose logs -f ingestion-service

logs-processor:
	docker compose logs -f processor-service

logs-detection:
	docker compose logs -f detection-service

# ── Database shells ───────────────────────────────────────────────────────────

neo4j-shell:
	docker exec -it neofraudj-neo4j \
	  cypher-shell -u neo4j -p $${NEO4J_PASSWORD:-neofraudj_secret}

redis-cli:
	docker exec -it neofraudj-redis redis-cli

# ── Service shortcuts ─────────────────────────────────────────────────────────

restart-processor:
	docker compose restart processor-service

# ── Quick test ────────────────────────────────────────────────────────────────

test-ingest:
	curl -s -X POST http://localhost:8001/v1/transactions \
	  -H "Content-Type: application/json" \
	  -d '{ \
	    "transaction_id": "txn_test_001", \
	    "amount": "99.99", \
	    "currency": "USD", \
	    "timestamp": "2026-03-28T12:00:00Z", \
	    "user_id": "usr_001", \
	    "account_id": "acc_001", \
	    "card": {"card_id": "crd_001", "card_last_four": "4242", "card_type": "VISA"}, \
	    "merchant": {"merchant_id": "mrc_001", "merchant_name": "Test Shop", "merchant_category": "5999", "merchant_country": "US"}, \
	    "device": {"device_id": "dev_001", "device_type": "mobile"}, \
	    "ip_address": "203.0.113.1", \
	    "ip_country": "US" \
	  }' | python3 -m json.tool

test-alerts:
	curl -s http://localhost:8002/v1/alerts | python3 -m json.tool

test-health-ingestion:
	curl -s http://localhost:8001/health | python3 -m json.tool

test-health-detection:
	curl -s http://localhost:8002/health | python3 -m json.tool
