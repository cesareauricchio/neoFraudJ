from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CardDetails(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    card_id: str
    card_last_four: Annotated[str, Field(min_length=4, max_length=4, pattern=r"^\d{4}$")]
    card_type: str  # "VISA" | "MASTERCARD" | "AMEX"


class MerchantDetails(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    merchant_id: str
    merchant_name: str
    merchant_category: str   # MCC code or description
    merchant_country: str    # ISO 3166-1 alpha-2


class DeviceDetails(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    device_id: str
    device_type: str          # "mobile" | "desktop" | "tablet" | "pos"
    device_fingerprint: str | None = None


class TransactionPayload(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "transaction_id": "txn_abc123",
                "amount": "150.75",
                "currency": "USD",
                "timestamp": "2026-03-28T12:00:00Z",
                "user_id": "usr_001",
                "account_id": "acc_001",
                "card": {
                    "card_id": "crd_001",
                    "card_last_four": "4242",
                    "card_type": "VISA",
                },
                "merchant": {
                    "merchant_id": "mrc_001",
                    "merchant_name": "Coffee Co",
                    "merchant_category": "5812",
                    "merchant_country": "US",
                },
                "device": {
                    "device_id": "dev_001",
                    "device_type": "mobile",
                    "device_fingerprint": None,
                },
                "ip_address": "203.0.113.42",
                "ip_country": "US",
            }
        },
    )

    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: Decimal = Field(gt=Decimal("0"))
    currency: Annotated[str, Field(min_length=3, max_length=3)]  # ISO 4217
    timestamp: datetime
    user_id: str
    account_id: str
    card: CardDetails
    merchant: MerchantDetails
    device: DeviceDetails
    ip_address: str
    ip_country: Annotated[str, Field(min_length=2, max_length=2)]

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_utc(cls, v: datetime | str) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v
