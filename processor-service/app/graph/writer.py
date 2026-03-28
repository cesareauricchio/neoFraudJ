from __future__ import annotations

from datetime import datetime, timezone

from neo4j import AsyncSession

from shared.models.payloads import TransactionPayload

from app.graph import queries


class GraphWriter:
    """
    Writes a fully decomposed TransactionPayload into Neo4j as a graph.

    All 7 nodes and 6 relationships are merged within a single explicit
    transaction, guaranteeing atomicity and full idempotency.
    """

    async def write_transaction(
        self, session: AsyncSession, payload: TransactionPayload
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()

        async with await session.begin_transaction() as tx:
            # ── 1. Merge all nodes ────────────────────────────────────────
            await tx.run(
                queries.MERGE_USER,
                user_id=payload.user_id,
                created_at=now_iso,
            )
            await tx.run(
                queries.MERGE_ACCOUNT,
                account_id=payload.account_id,
                user_id=payload.user_id,
                created_at=now_iso,
            )
            await tx.run(
                queries.MERGE_CARD,
                card_id=payload.card.card_id,
                card_last_four=payload.card.card_last_four,
                card_type=payload.card.card_type,
                account_id=payload.account_id,
            )
            await tx.run(
                queries.MERGE_TRANSACTION,
                transaction_id=payload.transaction_id,
                amount=str(payload.amount),  # Decimal → str preserves exact precision
                currency=payload.currency,
                timestamp=payload.timestamp.isoformat(),
            )
            await tx.run(
                queries.MERGE_MERCHANT,
                merchant_id=payload.merchant.merchant_id,
                merchant_name=payload.merchant.merchant_name,
                merchant_category=payload.merchant.merchant_category,
                merchant_country=payload.merchant.merchant_country,
            )
            await tx.run(
                queries.MERGE_DEVICE,
                device_id=payload.device.device_id,
                device_type=payload.device.device_type,
                device_fingerprint=payload.device.device_fingerprint,
            )
            await tx.run(
                queries.MERGE_IP,
                ip_address=payload.ip_address,
                ip_country=payload.ip_country,
            )

            # ── 2. Merge all relationships ────────────────────────────────
            await tx.run(
                queries.REL_USER_OWNS_ACCOUNT,
                user_id=payload.user_id,
                account_id=payload.account_id,
            )
            await tx.run(
                queries.REL_ACCOUNT_HAS_CARD,
                account_id=payload.account_id,
                card_id=payload.card.card_id,
            )
            await tx.run(
                queries.REL_CARD_PERFORMED,
                card_id=payload.card.card_id,
                transaction_id=payload.transaction_id,
            )
            await tx.run(
                queries.REL_TXN_PAID_TO,
                transaction_id=payload.transaction_id,
                merchant_id=payload.merchant.merchant_id,
            )
            await tx.run(
                queries.REL_TXN_FROM_DEVICE,
                transaction_id=payload.transaction_id,
                device_id=payload.device.device_id,
            )
            await tx.run(
                queries.REL_TXN_FROM_IP,
                transaction_id=payload.transaction_id,
                ip_address=payload.ip_address,
            )

            await tx.commit()
