# ─── a) Velocity Fraud ────────────────────────────────────────────────────────
# Detect cards that have performed more than $threshold transactions
# within the last $window_seconds seconds.
# Params: cutoff_iso (ISO datetime string), threshold (int)

QUERY_VELOCITY_FRAUD = """
MATCH (c:Card)-[:PERFORMED]->(t:Transaction)
WHERE t.timestamp >= datetime($cutoff_iso)
WITH c, count(t) AS txn_count
WHERE txn_count > $threshold
RETURN c.card_id AS card_id, txn_count
ORDER BY txn_count DESC
"""

# ─── b) Device Sharing ────────────────────────────────────────────────────────
# Detect devices used by more than $threshold distinct cards in the last 24h.
# Params: cutoff_iso (ISO datetime string), threshold (int)

QUERY_DEVICE_SHARING = """
MATCH (c:Card)-[:PERFORMED]->(t:Transaction)-[:FROM_DEVICE]->(d:Device)
WHERE t.timestamp >= datetime($cutoff_iso)
WITH d, collect(DISTINCT c.card_id) AS card_ids
WHERE size(card_ids) > $threshold
RETURN d.device_id          AS device_id,
       size(card_ids)       AS distinct_cards,
       card_ids
ORDER BY distinct_cards DESC
"""

# ─── c) IP Sharing ────────────────────────────────────────────────────────────
# Detect IP addresses used by more than $threshold distinct accounts in 1h.
# Params: cutoff_iso (ISO datetime string), threshold (int)

QUERY_IP_SHARING = """
MATCH (c:Card)-[:PERFORMED]->(t:Transaction)-[:FROM_IP]->(ip:IPAddress)
WHERE t.timestamp >= datetime($cutoff_iso)
MATCH (a:Account)-[:HAS_CARD]->(c)
WITH ip, collect(DISTINCT a.account_id) AS account_ids
WHERE size(account_ids) > $threshold
RETURN ip.ip_address         AS ip_address,
       ip.ip_country         AS ip_country,
       size(account_ids)     AS distinct_accounts,
       account_ids
ORDER BY distinct_accounts DESC
"""

# ─── d) Circular Transfer ─────────────────────────────────────────────────────
# Detect accounts that paid the same merchant more than $min_txns times
# within the window — a proxy for circular/laundering patterns.
# Params: cutoff_iso (ISO datetime string), min_txns (int)

QUERY_CIRCULAR_TRANSFER = """
MATCH (a:Account)-[:HAS_CARD]->(c:Card)-[:PERFORMED]->(t:Transaction)-[:PAID_TO]->(m:Merchant)
WHERE t.timestamp >= datetime($cutoff_iso)
WITH a, m, collect(t.transaction_id) AS txns
WHERE size(txns) > $min_txns
RETURN a.account_id          AS account_id,
       m.merchant_id         AS merchant_id,
       m.merchant_name       AS merchant_name,
       size(txns)            AS transaction_count,
       txns
ORDER BY transaction_count DESC
LIMIT 50
"""

# ─── e) Geographic Anomaly ────────────────────────────────────────────────────
# Detect when the same card performs two transactions from different IP countries
# within $window_minutes minutes — impossible travel / stolen card signal.
# Params: window_minutes (int)

QUERY_GEO_ANOMALY = """
MATCH (c:Card)-[:PERFORMED]->(t1:Transaction)-[:FROM_IP]->(ip1:IPAddress)
MATCH (c)-[:PERFORMED]->(t2:Transaction)-[:FROM_IP]->(ip2:IPAddress)
WHERE t1.transaction_id <> t2.transaction_id
  AND t1.timestamp < t2.timestamp
  AND t2.timestamp <= datetime(t1.timestamp) + duration({minutes: $window_minutes})
  AND ip1.ip_country <> ip2.ip_country
RETURN
    c.card_id             AS card_id,
    t1.transaction_id     AS txn1_id,
    t1.timestamp          AS txn1_time,
    ip1.ip_country        AS country1,
    t2.transaction_id     AS txn2_id,
    t2.timestamp          AS txn2_time,
    ip2.ip_country        AS country2
ORDER BY t1.timestamp DESC
LIMIT 100
"""

# ─── Risk sub-queries (used in composite risk score) ─────────────────────────

RISK_VELOCITY_CHECK = """
MATCH (c:Card)-[:PERFORMED]->(t:Transaction {transaction_id: $txn_id})
WITH c
MATCH (c)-[:PERFORMED]->(t2:Transaction)
WHERE t2.timestamp >= datetime($cutoff_iso)
RETURN count(t2) AS cnt
"""

RISK_DEVICE_CHECK = """
MATCH (t:Transaction {transaction_id: $txn_id})-[:FROM_DEVICE]->(d:Device)
MATCH (c2:Card)-[:PERFORMED]->(t2:Transaction)-[:FROM_DEVICE]->(d)
WHERE t2.timestamp >= datetime($cutoff_iso)
RETURN count(DISTINCT c2.card_id) AS cnt
"""

RISK_IP_CHECK = """
MATCH (t:Transaction {transaction_id: $txn_id})-[:FROM_IP]->(ip:IPAddress)
MATCH (c2:Card)-[:PERFORMED]->(t2:Transaction)-[:FROM_IP]->(ip)
MATCH (a:Account)-[:HAS_CARD]->(c2)
WHERE t2.timestamp >= datetime($cutoff_iso)
RETURN count(DISTINCT a.account_id) AS cnt
"""

# ─── Entity subgraph query ────────────────────────────────────────────────────
# Returns the 1..depth neighbourhood of any entity node for visualization.
# Variable-length path — keep depth <= 4 in production.

ENTITY_SUBGRAPH = """
MATCH path = (n)-[*1..{depth}]-(m)
WHERE n.user_id = $eid
   OR n.account_id = $eid
   OR n.card_id = $eid
   OR n.transaction_id = $eid
   OR n.merchant_id = $eid
   OR n.device_id = $eid
   OR n.ip_address = $eid
RETURN nodes(path) AS nodes, relationships(path) AS rels
LIMIT 200
"""
