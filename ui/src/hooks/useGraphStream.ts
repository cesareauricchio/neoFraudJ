import { useEffect, useRef, useState } from 'react'
import type { GraphData, GraphLink, GraphNode, WsMessage, WsStatus } from '../types/graph'

const REST_URL = 'http://localhost:8002/v1/graph'
const WS_URL   = 'ws://localhost:8002/ws'

export interface UseGraphStreamReturn {
  graph: GraphData
  wsStatus: WsStatus
  fraudCount: number
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const getNodeId = (node: unknown): string => {
  if (typeof node === 'string') return node
  if (node && typeof node === 'object' && 'id' in node) return (node as { id: string }).id
  return ''
}

function sanitize(data: GraphData): GraphData {
  const nodeIds = new Set(data.nodes.map(n => n.id))
  return {
    nodes: data.nodes,
    links: data.links.filter(l => nodeIds.has(getNodeId(l.source)) && nodeIds.has(getNodeId(l.target))),
  }
}

// ─── State Merge ──────────────────────────────────────────────────────────────
//
// Each WS message carries the FULL hierarchy for one transaction:
//   User → Account → Card → Transaction → Merchant
//
// All nodes in the message arrive together, so we no longer need an anchor
// check — the Card will always be present in the same delta as the Transaction.
// We simply skip IPAddress nodes and deduplicate everything else.

function mergeGraphDelta(
  prev: GraphData,
  newNodes: GraphNode[],
  newLinks: GraphLink[],
  isFraud: boolean,
  startTime?: string,
): GraphData {
  const ipIds = new Set(newNodes.filter(n => n.label === 'IPAddress').map(n => n.id))

  // If a dynamic start filter is set, drop transactions that pre-date it
  const startMs = startTime ? new Date(startTime).getTime() : null
  const filteredNodes = newNodes.filter(n => {
    if (ipIds.has(n.id)) return false
    if (n.label === 'Transaction' && startMs !== null) {
      const ts = typeof n.timestamp === 'string' ? new Date(n.timestamp).getTime() : Number.NaN
      if (!Number.isNaN(ts) && ts < startMs) return false
    }
    return true
  })

  // Mutate isFraud on existing objects to preserve D3 coordinates
  if (isFraud) {
    const deltaIds = new Set(filteredNodes.map(n => n.id))
    for (const n of prev.nodes) {
      if (deltaIds.has(n.id)) n.isFraud = true
    }
  }

  const existingById = new Map<string, GraphNode>(prev.nodes.map(n => [n.id, n]))

  // Add every node from this delta that isn't already in the graph.
  // No anchor check — the full hierarchy arrives in every message.
  const brandNewNodes = filteredNodes
    .filter(n => !existingById.has(n.id))
    .map(n => ({ ...n, isFraud: isFraud || Boolean(n.isFraud) }))

  const finalNodes   = [...prev.nodes, ...brandNewNodes]
  const finalNodeIds = new Set(finalNodes.map(n => n.id))

  const existingLinkKeys = new Set(
    prev.links.map(l => `${getNodeId(l.source)}→${getNodeId(l.target)}`),
  )
  const brandNewLinks = newLinks.filter(l => {
    const s = getNodeId(l.source)
    const t = getNodeId(l.target)
    return (
      finalNodeIds.has(s) &&
      finalNodeIds.has(t) &&
      !ipIds.has(s) && !ipIds.has(t) &&
      !existingLinkKeys.has(`${s}→${t}`)
    )
  })

  if (brandNewNodes.length === 0 && brandNewLinks.length === 0) return prev

  return {
    nodes: finalNodes,
    links: [...prev.links, ...brandNewLinks],
  }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useGraphStream(startTime?: string): UseGraphStreamReturn {
  const [graph, setGraph]           = useState<GraphData>({ nodes: [], links: [] })
  const [wsStatus, setWsStatus]     = useState<WsStatus>('connecting')
  const [fraudCount, setFraudCount] = useState(0)
  const reconnectRef                = useRef<ReturnType<typeof setTimeout> | null>(null)
  const startTimeRef  = useRef(startTime)
  const prevStartRef  = useRef<string | undefined>(undefined)
  startTimeRef.current = startTime

  // When startTime changes: reset graph, then fetch all history from that point via REST
  useEffect(() => {
    if (startTime === prevStartRef.current) return
    prevStartRef.current = startTime
    setGraph({ nodes: [], links: [] })
    setFraudCount(0)

    if (!startTime) return
    fetch(`${REST_URL}?start=${encodeURIComponent(startTime)}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<GraphData>
      })
      .then(data => {
        // Filter IP nodes and unanchored transactions, then seed the graph
        const validNodes = data.nodes.filter(n => n.label !== 'IPAddress')
        const validIds   = new Set(validNodes.map(n => n.id))
        const validLinks = data.links.filter(l =>
          validIds.has(getNodeId(l.source)) && validIds.has(getNodeId(l.target))
        )
        const linkedIds = new Set(validLinks.flatMap(l => [getNodeId(l.source), getNodeId(l.target)]))
        setGraph({
          nodes: validNodes.filter(n => n.label !== 'Transaction' || linkedIds.has(n.id)),
          links: validLinks,
        })
      })
      .catch(err => console.error('[useGraphStream] History load failed:', err))
  }, [startTime])

  // WebSocket — reconnects on disconnect, no initial REST load
  useEffect(() => {
    let ws: WebSocket | null = null
    let cancelled = false

    const handleMessage = (event: MessageEvent<string>) => {
      if (cancelled) return
      try {
        const msg = JSON.parse(event.data) as WsMessage
        if (msg.type !== 'GRAPH_UPDATE') return
        if (msg.is_fraud_alert) setFraudCount(c => c + 1)
        setGraph(prev => sanitize(
          mergeGraphDelta(prev, msg.payload.nodes, msg.payload.links, msg.is_fraud_alert, startTimeRef.current),
        ))
      } catch (err) {
        console.error('[useGraphStream] Message parse error:', err)
      }
    }

    const connect = () => {
      if (cancelled) return
      setWsStatus('connecting')
      ws = new WebSocket(WS_URL)
      ws.onopen    = () => { if (!cancelled) setWsStatus('connected') }
      ws.onmessage = handleMessage
      ws.onerror   = () => { if (!cancelled) setWsStatus('error') }
      ws.onclose   = () => {
        if (!cancelled) {
          setWsStatus('disconnected')
          reconnectRef.current = setTimeout(connect, 3000)
        }
      }
    }

    connect()
    return () => {
      cancelled = true
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      ws?.close()
    }
  }, [])

  return { graph, wsStatus, fraudCount }
}
