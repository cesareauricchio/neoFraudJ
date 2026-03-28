import { useState } from 'react'
import type { GraphData } from '../types/graph'

const REST_URL = 'http://localhost:8002/v1/graph'

export interface UseStaticGraphReturn {
  graph: GraphData | null
  loading: boolean
  error: string | null
  fetch: (start: string, end: string) => void
  reset: () => void
}

function filterIpNodes(data: GraphData): GraphData {
  const validNodes = data.nodes.filter(n => n.label !== 'IPAddress')
  const validIds   = new Set(validNodes.map(n => n.id))
  const validLinks = data.links.filter(l => {
    const s = typeof l.source === 'string' ? l.source : (l.source as { id: string }).id
    const t = typeof l.target === 'string' ? l.target : (l.target as { id: string }).id
    return validIds.has(s) && validIds.has(t)
  })
  const linkedIds = new Set(validLinks.flatMap(l => [
    typeof l.source === 'string' ? l.source : (l.source as { id: string }).id,
    typeof l.target === 'string' ? l.target : (l.target as { id: string }).id,
  ]))
  return {
    nodes: validNodes.filter(n => n.label !== 'Transaction' || linkedIds.has(n.id)),
    links: validLinks,
  }
}

export function useStaticGraph(): UseStaticGraphReturn {
  const [graph, setGraph]     = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const fetchGraph = (start: string, end: string) => {
    setLoading(true)
    setError(null)
    const url = `${REST_URL}?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<GraphData>
      })
      .then(data => setGraph(filterIpNodes(data)))
      .catch(err => setError((err as Error).message))
      .finally(() => setLoading(false))
  }

  const reset = () => { setGraph(null); setError(null) }

  return { graph, loading, error, fetch: fetchGraph, reset }
}
