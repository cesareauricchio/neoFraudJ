import dagre from '@dagrejs/dagre'
import type { GraphData } from '../types/graph'

export type DagreRankDir = 'TB' | 'LR'

const NODE_WIDTH  = 36
const NODE_HEIGHT = 36
const PADDING     = 80

/**
 * Runs dagre layout and scales the resulting positions so the graph fills
 * the given canvas dimensions at zoom=1. Nodes are pinned with fx/fy.
 */
export function applyDagreLayout(
  data: GraphData,
  rankdir: DagreRankDir,
  canvasW: number,
  canvasH: number,
): GraphData {
  if (data.nodes.length === 0) return data

  const g = new dagre.graphlib.Graph({ multigraph: true })
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({
    rankdir,
    ranksep: rankdir === 'TB' ? 200 : 320,
    nodesep: rankdir === 'TB' ? 120 : 100,
    edgesep: 20,
    marginx: PADDING,
    marginy: PADDING,
  })

  const nodeIds = new Set(data.nodes.map(n => n.id))
  for (const node of data.nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }
  for (const link of data.links) {
    const s = typeof link.source === 'string' ? link.source : link.source.id
    const t = typeof link.target === 'string' ? link.target : link.target.id
    if (nodeIds.has(s) && nodeIds.has(t)) {
      g.setEdge(s, t, {}, `${s}→${t}`)
    }
  }

  dagre.layout(g)

  // Collect raw positions from dagre
  const positions = data.nodes.map(n => g.node(n.id)).filter(Boolean)
  const rawMinX = Math.min(...positions.map(p => p.x))
  const rawMaxX = Math.max(...positions.map(p => p.x))
  const rawMinY = Math.min(...positions.map(p => p.y))
  const rawMaxY = Math.max(...positions.map(p => p.y))
  const rawW    = rawMaxX - rawMinX || 1
  const rawH    = rawMaxY - rawMinY || 1

  // Scale so the layout fills the canvas, keeping some padding
  const scaleX = (canvasW - PADDING * 2) / rawW
  const scaleY = (canvasH - PADDING * 2) / rawH

  const nodes = data.nodes.map(node => {
    const pos = g.node(node.id)
    if (!pos) return node
    const x = PADDING + (pos.x - rawMinX) * scaleX
    const y = PADDING + (pos.y - rawMinY) * scaleY
    return { ...node, x, y, fx: x, fy: y }
  })

  return { nodes, links: data.links }
}
