from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class UserNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str
    created_at: datetime | None = None


class AccountNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    account_id: str
    user_id: str
    created_at: datetime | None = None


class CardNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    card_id: str
    card_last_four: str
    card_type: str
    account_id: str


class TransactionNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    transaction_id: str
    amount: Decimal
    currency: str
    timestamp: datetime
    card_id: str


class MerchantNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    merchant_id: str
    merchant_name: str
    merchant_category: str
    merchant_country: str


class DeviceNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    device_id: str
    device_type: str
    device_fingerprint: str | None = None


class IPAddressNode(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ip_address: str
    ip_country: str
