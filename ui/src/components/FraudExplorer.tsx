import { useCallback, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { NodeObject } from 'react-force-graph-2d'
import type { GraphData, GraphNode, NodeLabel } from '../types/graph'
import { drawNode, NODE_COLORS } from '../utils/drawNode'

// ─── Helpers ──────────────────────────────────────────────────────────────────

type FilterLabel = 'All' | NodeLabel
const FILTER_OPTIONS: FilterLabel[] = ['All', 'User', 'Account', 'Card', 'Merchant']
const ENTITY_LABELS = new Set<NodeLabel>(['User', 'Account', 'Card', 'Merchant'])

function linkEndpoints(link: GraphData['links'][number]): [string, string] {
  const s = typeof link.source === 'string' ? link.source : link.source.id
  const t = typeof link.target === 'string' ? link.target : link.target.id
  return [s, t]
}

function expandFrontier(
  frontier: Set<string>,
  nodeSet: Set<string>,
  links: GraphData['links'],
): Set<string> {
  const next = new Set<string>()
  for (const link of links) {
    const [s, t] = linkEndpoints(link)
    if (frontier.has(s) && !nodeSet.has(t)) { next.add(t); nodeSet.add(t) }
    if (frontier.has(t) && !nodeSet.has(s)) { next.add(s); nodeSet.add(s) }
  }
  return next
}

function extractSubgraph(graph: GraphData, nodeId: string, depth = 2): GraphData {
  const nodeSet = new Set<string>([nodeId])
  let frontier  = new Set<string>([nodeId])

  for (let d = 0; d < depth; d++) {
    frontier = expandFrontier(frontier, nodeSet, graph.links)
    if (frontier.size === 0) break
  }

  return {
    nodes: graph.nodes.filter(n => nodeSet.has(n.id)),
    links: graph.links.filter(l => {
      const [s, t] = linkEndpoints(l)
      return nodeSet.has(s) && nodeSet.has(t)
    }),
  }
}

// ─── Component ────────────────────────────────────────────────────────────────

interface FraudExplorerProps {
  readonly graph: GraphData
}

export function FraudExplorer({ graph }: FraudExplorerProps) {
  const [filter, setFilter]         = useState<FilterLabel>('All')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showLabels, setShowLabels] = useState(false)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null)

  const fraudEntities = graph.nodes.filter(
    n => n.isFraud && ENTITY_LABELS.has(n.label) && (filter === 'All' || n.label === filter),
  )

  const subgraph = selectedId ? extractSubgraph(graph, selectedId) : null

  const paintNode = useCallback(
    (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const n = node as GraphNode
      drawNode(n, ctx, globalScale, n.id === selectedId, showLabels)
    },
    [selectedId, showLabels],
  )

  return (
    <div className="flex h-full">

      {/* ── Sidebar ── */}
      <div className="w-64 shrink-0 flex flex-col border-r border-slate-700/60 bg-slate-900">

        {/* Filter bar */}
        <div className="flex flex-wrap gap-1 px-3 py-2.5 border-b border-slate-700/60">
          {FILTER_OPTIONS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filter === f
                  ? 'bg-slate-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Count */}
        <div className="px-3 py-1.5 text-xs text-slate-500 border-b border-slate-700/60">
          {fraudEntities.length === 1 ? '1 entry' : `${fraudEntities.length} entries`} flagged
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {fraudEntities.length === 0 ? (
            <div className="px-4 py-8 text-sm text-slate-500 text-center">
              No fraud detected yet
            </div>
          ) : (
            fraudEntities.map(node => (
              <button
                key={node.id}
                onClick={() => setSelectedId(prev => prev === node.id ? null : node.id)}
                className={`w-full text-left px-3 py-2.5 border-b border-slate-800 transition-colors ${
                  selectedId === node.id ? 'bg-slate-700' : 'hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <span
                    className="px-1.5 py-0.5 rounded text-xs font-bold text-white"
                    style={{ backgroundColor: NODE_COLORS[node.label] ?? '#6b7280' }}
                  >
                    {node.label}
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-xs font-bold text-white bg-red-600">
                    FRAUD
                  </span>
                </div>

                <div className="text-sm text-slate-100 font-mono truncate">{node.id}</div>

                {node.label === 'Merchant' && typeof node.merchant_name === 'string' && (
                  <div className="text-xs text-slate-400 mt-0.5 truncate">{node.merchant_name}</div>
                )}
                {node.label === 'Card' && typeof node.card_last_four === 'string' && (
                  <div className="text-xs text-slate-400 mt-0.5">
                    ···· {node.card_last_four}
                    {typeof node.card_type === 'string' && ` · ${node.card_type}`}
                  </div>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* ── Subgraph area ── */}
      <div className="flex-1 relative overflow-hidden bg-[#0f172a]">
        {selectedId && subgraph ? (
          <>
            <div className="absolute top-3 left-3 z-10 flex items-center gap-2 text-xs text-slate-400 pointer-events-none">
              <span>{subgraph.nodes.length} nodes</span>
              <span className="text-slate-600">·</span>
              <span>{subgraph.links.length} links</span>
              <span className="text-slate-600">·</span>
              <span className="text-slate-500">2-hop neighbourhood</span>
            </div>

            <ForceGraph2D
              key={selectedId}
              ref={graphRef}
              graphData={subgraph}
              nodeId="id"
              nodeLabel={() => ''}
              nodeCanvasObject={paintNode}
              nodeCanvasObjectMode={() => 'replace'}
              linkLabel="label"
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              linkColor={() => 'rgba(148,163,184,0.25)'}
              linkWidth={0.8}
              backgroundColor="#0f172a"
              d3VelocityDecay={0.35}
              cooldownTicks={150}
              onEngineStop={() => graphRef.current?.zoomToFit(400, 50)}
            />

            <button
              onClick={() => setShowLabels(v => !v)}
              className="absolute bottom-5 right-5 z-10 px-3 py-1.5 rounded text-xs text-slate-300 bg-slate-800/90 border border-slate-700 hover:bg-slate-700 transition-colors"
            >
              {showLabels ? 'Hide labels' : 'Show labels'}
            </button>
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-slate-500 text-sm mb-1">
                Select an entity to explore its subgraph
              </div>
              <div className="text-slate-600 text-xs">
                Shows the 2-hop neighbourhood around the selected node
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
