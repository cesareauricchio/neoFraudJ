from __future__ import annotations

# Maps each Neo4j node label to its unique key property.
_KEY_PROPS: dict[str, str] = {
    "User": "user_id",
    "Account": "account_id",
    "Card": "card_id",
    "Transaction": "transaction_id",
    "Merchant": "merchant_id",
    "Device": "device_id",
    "IPAddress": "ip_address",
}


def get_node_id(label: str, props: dict) -> str | None:
    """Return the stable string ID for a node given its label and properties dict."""
    key = _KEY_PROPS.get(label)
    value = props.get(key) if key else None
    return str(value) if value is not None else None


def payload_to_delta(payload: dict, is_fraud_alert: bool) -> dict:
    """
    Build a GRAPH_UPDATE WebSocket message directly from a raw TransactionPayload dict.

    Does not query Neo4j — avoids the timing race where the processor may not
    have written the nodes yet when the detection service receives the stream entry.
    """
    card = payload.get("card", {})
    merchant = payload.get("merchant", {})
    device = payload.get("device", {})

    nodes = [
        {"id": payload["user_id"], "label": "User",
         "user_id": payload["user_id"]},
        {"id": payload["account_id"], "label": "Account",
         "account_id": payload["account_id"]},
        {"id": card["card_id"], "label": "Card",
         "card_id": card["card_id"],
         "card_last_four": card.get("card_last_four"),
         "card_type": card.get("card_type")},
        {"id": payload["transaction_id"], "label": "Transaction",
         "transaction_id": payload["transaction_id"],
         "amount": payload.get("amount"),
         "currency": payload.get("currency"),
         "timestamp": payload.get("timestamp")},
        {"id": merchant["merchant_id"], "label": "Merchant",
         "merchant_id": merchant["merchant_id"],
         "merchant_name": merchant.get("merchant_name"),
         "merchant_category": merchant.get("merchant_category"),
         "merchant_country": merchant.get("merchant_country")},
        {"id": device["device_id"], "label": "Device",
         "device_id": device["device_id"],
         "device_type": device.get("device_type")},
        {"id": payload["ip_address"], "label": "IPAddress",
         "ip_address": payload["ip_address"],
         "ip_country": payload.get("ip_country")},
    ]

    links = [
        {"source": payload["user_id"],        "target": payload["account_id"],       "label": "OWNS_ACCOUNT"},
        {"source": payload["account_id"],      "target": card["card_id"],             "label": "HAS_CARD"},
        {"source": card["card_id"],            "target": payload["transaction_id"],   "label": "PERFORMED"},
        {"source": payload["transaction_id"],  "target": merchant["merchant_id"],     "label": "PAID_TO"},
        {"source": payload["transaction_id"],  "target": device["device_id"],         "label": "FROM_DEVICE"},
        {"source": payload["transaction_id"],  "target": payload["ip_address"],       "label": "FROM_IP"},
    ]

    return {
        "type": "GRAPH_UPDATE",
        "is_fraud_alert": is_fraud_alert,
        "payload": {"nodes": nodes, "links": links},
    }
