from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Query, Request
from neo4j.time import Date, DateTime, Duration, Time

from app.services.graph_builder import get_node_id

_NEO4J_TEMPORAL = (DateTime, Date, Time, Duration)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["graph-rest"])


def _sanitize(props: dict) -> dict:
    """Convert Neo4j temporal types to ISO strings so Pydantic can serialize them."""
    return {
        k: v.isoformat() if isinstance(v, _NEO4J_TEMPORAL) else v
        for k, v in props.items()
    }


def _build_where(start: Optional[str], end: Optional[str]) -> tuple[str, dict]:
    clauses, params = [], {}
    if start:
        clauses.append("t.timestamp >= datetime($start)")
        params["start"] = start
    if end:
        clauses.append("t.timestamp <= datetime($end)")
        params["end"] = end
    return " AND ".join(clauses), params


async def _load_nodes(session: AsyncSession, where_str: str, params: dict, nodes_map: dict) -> None:
    result = await session.run(
        f"""
        MATCH (t:Transaction)
        WHERE {where_str}
        WITH t ORDER BY t.isFraud DESC, t.timestamp DESC
        LIMIT 500
        MATCH (u:User)-[:OWNS_ACCOUNT]->(a:Account)-[:HAS_CARD]->(c:Card)-[:PERFORMED]->(t)
        OPTIONAL MATCH (t)-[:PAID_TO]->(m:Merchant)
        WITH u, a, c, t, m
        UNWIND [u, a, c, t] + CASE WHEN m IS NOT NULL THEN [m] ELSE [] END AS n
        RETURN DISTINCT labels(n)[0] AS label, properties(n) AS props
        """,
        **params,
    )
    async for record in result:
        label: str = record["label"]
        props: dict = _sanitize(dict(record["props"]))
        node_id = get_node_id(label, props)
        if node_id and node_id not in nodes_map:
            nodes_map[node_id] = {"id": node_id, "label": label, **props}


async def _load_links(session: AsyncSession, where_str: str, params: dict) -> tuple[list[dict], set[str]]:
    links: list[dict] = []
    seen: set[str] = set()
    result = await session.run(
        f"""
        MATCH (t:Transaction)
        WHERE {where_str}
        WITH t
        LIMIT 500
        MATCH (u:User)-[r1:OWNS_ACCOUNT]->(a:Account)-[r2:HAS_CARD]->(c:Card)-[r3:PERFORMED]->(t)
        OPTIONAL MATCH (t)-[r4:PAID_TO]->(m:Merchant)
        WITH u, a, c, t, m, r1, r2, r3, r4
        UNWIND [
            {{src: u, rel: r1, tgt: a}},
            {{src: a, rel: r2, tgt: c}},
            {{src: c, rel: r3, tgt: t}}
        ] + CASE WHEN m IS NOT NULL THEN [{{src: t, rel: r4, tgt: m}}] ELSE [] END AS row
        RETURN labels(row.src)[0] AS src_label, properties(row.src) AS src_props,
               type(row.rel)      AS rel_type,
               labels(row.tgt)[0] AS tgt_label, properties(row.tgt) AS tgt_props
        """,
        **params,
    )
    async for record in result:
        src_id = get_node_id(record["src_label"], dict(record["src_props"]))
        tgt_id = get_node_id(record["tgt_label"], dict(record["tgt_props"]))
        if not src_id or not tgt_id:
            continue
        key = f"{src_id}\u2192{tgt_id}"
        if key not in seen:
            seen.add(key)
            links.append({"source": src_id, "target": tgt_id, "label": record["rel_type"]})
    return links, seen


async def _load_full_snapshot(session: AsyncSession, nodes_map: dict) -> tuple[list[dict], set[str]]:
    node_result = await session.run(
        "MATCH (n) RETURN labels(n)[0] AS label, properties(n) AS props LIMIT 1000"
    )
    async for record in node_result:
        label = record["label"]
        props = _sanitize(dict(record["props"]))
        node_id = get_node_id(label, props)
        if node_id and node_id not in nodes_map:
            nodes_map[node_id] = {"id": node_id, "label": label, **props}

    links: list[dict] = []
    seen: set[str] = set()
    rel_result = await session.run(
        """
        MATCH (a)-[r]->(b)
        RETURN labels(a)[0]  AS src_label,  properties(a) AS src_props,
               type(r)       AS rel_type,
               labels(b)[0]  AS tgt_label,  properties(b) AS tgt_props
        LIMIT 3000
        """
    )
    async for record in rel_result:
        src_id = get_node_id(record["src_label"], dict(record["src_props"]))
        tgt_id = get_node_id(record["tgt_label"], dict(record["tgt_props"]))
        if not src_id or not tgt_id:
            continue
        key = f"{src_id}\u2192{tgt_id}"
        if key not in seen:
            seen.add(key)
            links.append({"source": src_id, "target": tgt_id, "label": record["rel_type"]})
    return links, seen



@router.get("/graph", summary="Full graph snapshot for initial dashboard load")
async def get_full_graph(
    request: Request,
    start: Annotated[Optional[str], Query(description="ISO datetime — include only transactions at or after this time")] = None,
    end: Annotated[Optional[str], Query(description="ISO datetime — include only transactions at or before this time")] = None,
) -> dict:
    """
    Returns nodes and relationships as { nodes: [...], links: [...] }.

    Without start/end: full snapshot (all nodes, LIMIT 1000/3000).
    With start/end: returns Transaction nodes in the window plus their immediate
    neighbours, with isFraud=True annotated on high-velocity cards and their txns.
    """
    driver   = request.app.state.neo4j_driver
    database = request.app.state.neo4j_database

    nodes_map: dict[str, dict] = {}

    async with driver.session(database=database) as session:
        if start is not None or end is not None:
            where_str, params = _build_where(start, end)
            await _load_nodes(session, where_str, params, nodes_map)
            links, _ = await _load_links(session, where_str, params)
        else:
            links, _ = await _load_full_snapshot(session, nodes_map)

    logger.info(
        "Graph snapshot: %d nodes, %d links (start=%s end=%s)",
        len(nodes_map), len(links), start, end,
    )
    return {"nodes": list(nodes_map.values()), "links": links}
