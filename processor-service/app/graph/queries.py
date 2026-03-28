# ─── Node MERGE Queries ───────────────────────────────────────────────────────
# All queries use parameterized values only ($param) — no string formatting.
# ON CREATE SET sets properties only when the node is first created.
# ON MATCH SET updates mutable properties when the node already exists.

MERGE_USER = """
MERGE (u:User {user_id: $user_id})
ON CREATE SET u.created_at = $created_at
RETURN u
"""

MERGE_ACCOUNT = """
MERGE (a:Account {account_id: $account_id})
ON CREATE SET a.user_id = $user_id, a.created_at = $created_at
RETURN a
"""

MERGE_CARD = """
MERGE (c:Card {card_id: $card_id})
ON CREATE SET
    c.card_last_four = $card_last_four,
    c.card_type      = $card_type,
    c.account_id     = $account_id
RETURN c
"""

MERGE_TRANSACTION = """
MERGE (t:Transaction {transaction_id: $transaction_id})
ON CREATE SET
    t.amount    = $amount,
    t.currency  = $currency,
    t.timestamp = datetime($timestamp)
RETURN t
"""

MERGE_MERCHANT = """
MERGE (m:Merchant {merchant_id: $merchant_id})
ON CREATE SET
    m.merchant_name     = $merchant_name,
    m.merchant_category = $merchant_category,
    m.merchant_country  = $merchant_country
ON MATCH SET
    m.merchant_name     = $merchant_name,
    m.merchant_category = $merchant_category
RETURN m
"""

MERGE_DEVICE = """
MERGE (d:Device {device_id: $device_id})
ON CREATE SET
    d.device_type        = $device_type,
    d.device_fingerprint = $device_fingerprint
RETURN d
"""

MERGE_IP = """
MERGE (ip:IPAddress {ip_address: $ip_address})
ON CREATE SET ip.ip_country = $ip_country
RETURN ip
"""

# ─── Relationship MERGE Queries ───────────────────────────────────────────────
# Each query MATCHes both endpoint nodes by their unique ID,
# then MERGEs the relationship to ensure full idempotency.

REL_USER_OWNS_ACCOUNT = """
MATCH (u:User {user_id: $user_id})
MATCH (a:Account {account_id: $account_id})
MERGE (u)-[:OWNS_ACCOUNT]->(a)
"""

REL_ACCOUNT_HAS_CARD = """
MATCH (a:Account {account_id: $account_id})
MATCH (c:Card {card_id: $card_id})
MERGE (a)-[:HAS_CARD]->(c)
"""

REL_CARD_PERFORMED = """
MATCH (c:Card {card_id: $card_id})
MATCH (t:Transaction {transaction_id: $transaction_id})
MERGE (c)-[:PERFORMED]->(t)
"""

REL_TXN_PAID_TO = """
MATCH (t:Transaction {transaction_id: $transaction_id})
MATCH (m:Merchant {merchant_id: $merchant_id})
MERGE (t)-[:PAID_TO]->(m)
"""

REL_TXN_FROM_DEVICE = """
MATCH (t:Transaction {transaction_id: $transaction_id})
MATCH (d:Device {device_id: $device_id})
MERGE (t)-[:FROM_DEVICE]->(d)
"""

REL_TXN_FROM_IP = """
MATCH (t:Transaction {transaction_id: $transaction_id})
MATCH (ip:IPAddress {ip_address: $ip_address})
MERGE (t)-[:FROM_IP]->(ip)
"""
