import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { NodeObject } from 'react-force-graph-2d'
import { useGraphStream } from '../hooks/useGraphStream'
import { FraudExplorer } from './FraudExplorer'
import { NodePanel } from './NodePanel'
import { StaticGraph } from './StaticGraph'
import { drawNode } from '../utils/drawNode'
import type { GraphLink, GraphMode, GraphNode, WsStatus } from '../types/graph'

// ─── WS status indicator ──────────────────────────────────────────────────────

const STATUS_DOT: Record<WsStatus, string> = {
  connected:    'bg-emerald-400',
  connecting:   'bg-amber-400 animate-pulse',
  disconnected: 'bg-red-500',
  error:        'bg-red-500',
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

type Tab = 'graph' | 'explorer'

function toLocalDatetimeValue(iso: string): string {
  return iso.slice(0, 16)
}

// ─── Chain traversal ─────────────────────────────────────────────────────────

type AdjMap = Map<string, string[]>

function linkId(endpoint: string | GraphNode): string {
  return typeof endpoint === 'string' ? endpoint : endpoint.id
}

function buildAdj(links: GraphLink[]): { fwd: AdjMap; bwd: AdjMap } {
  const fwd: AdjMap = new Map()
  const bwd: AdjMap = new Map()
  for (const l of links) {
    const s = linkId(l.source)
    const t = linkId(l.target)
    if (!fwd.has(s)) fwd.set(s, [])
    if (!bwd.has(t)) bwd.set(t, [])
    fwd.get(s)!.push(t)
    bwd.get(t)!.push(s)
  }
  return { fwd, bwd }
}

function bfsDir(startId: string, adj: AdjMap, visited: Set<string>): void {
  const queue = [startId]
  while (queue.length > 0) {
    const curr = queue.shift()!
    for (const nb of adj.get(curr) ?? []) {
      if (!visited.has(nb)) { visited.add(nb); queue.push(nb) }
    }
  }
}

function buildChain(startId: string, links: GraphLink[]): Set<string> {
  const { fwd, bwd } = buildAdj(links)
  const visited = new Set<string>([startId])
  bfsDir(startId, bwd, visited) // upstream: Transaction → Card → Account → User
  bfsDir(startId, fwd, visited) // downstream: Account → Card → Transaction → Merchant
  return visited
}

// ── Dynamic graph sub-component ───────────────────────────────────────────────

function DynamicGraph() {
  // pending = what the user is typing; applied = what the hook actually uses
  const [fromPending, setFromPending] = useState('')
  const [fromApplied, setFromApplied] = useState('')
  const startTime = fromApplied ? new Date(fromApplied).toISOString() : undefined

  const handleLoad = () => setFromApplied(fromPending)
  const handleClear = () => { setFromPending(''); setFromApplied('') }

  const { graph, wsStatus, fraudCount } = useGraphStream(startTime)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [showLabels, setShowLabels]     = useState(false)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef  = useRef<any>(null)
  const hasZoomed = useRef(false)

  // Reset zoom when start filter changes
  useEffect(() => { hasZoomed.current = false }, [startTime])

  const nodeById = useMemo(
    () => new Map<string, GraphNode>(graph.nodes.map(n => [n.id, n])),
    [graph.nodes],
  )

  const selectedChainIds = useMemo(
    () => selectedNode ? buildChain(selectedNode.id, graph.links) : null,
    [selectedNode, graph.links],
  )

  useEffect(() => {
    const fg = graphRef.current
    if (!fg) return
    fg.d3Force('charge')?.strength(-80)
    fg.d3Force('link')?.distance(50)
  }, [])

  const handleEngineStop = useCallback(() => {
    if (!hasZoomed.current && graph.nodes.length > 0) {
      graphRef.current?.zoomToFit(400, 40)
      hasZoomed.current = true
    }
  }, [graph.nodes.length])

  const paintNode = useCallback(
    (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const n          = node as GraphNode
      const isSelected = selectedNode?.id === n.id
      const isDimmed   = selectedNode !== null && !isSelected && !selectedChainIds?.has(n.id)
      drawNode(n, ctx, globalScale, isSelected, showLabels, isDimmed)
    },
    [selectedNode, showLabels, selectedChainIds],
  )

  const linkColorFn = useCallback((link: object) => {
    const l = link as { source: string | GraphNode; target: string | GraphNode }
    const s = typeof l.source === 'string' ? l.source : l.source.id
    const t = typeof l.target === 'string' ? l.target : l.target.id
    const isFraudLink = !!(nodeById.get(s)?.isFraud && nodeById.get(t)?.isFraud)
    if (selectedChainIds) {
      const onChain = selectedChainIds.has(s) && selectedChainIds.has(t)
      if (onChain) return isFraudLink ? '#ef4444' : 'rgba(255,255,255,0.8)'
      return 'rgba(148,163,184,0.04)'
    }
    return isFraudLink ? 'rgba(239,68,68,0.55)' : 'rgba(148,163,184,0.2)'
  }, [selectedChainIds, nodeById])

  const linkWidthFn = useCallback((link: object) => {
    if (!selectedChainIds) return 0.8
    const l = link as { source: string | GraphNode; target: string | GraphNode }
    const s = typeof l.source === 'string' ? l.source : l.source.id
    const t = typeof l.target === 'string' ? l.target : l.target.id
    return (selectedChainIds.has(s) && selectedChainIds.has(t)) ? 2 : 0.3
  }, [selectedChainIds])

  const paintNodePointer = useCallback((node: NodeObject, color: string, ctx: CanvasRenderingContext2D) => {
    const n = node as GraphNode
    const size = (n.isCluster ? 18 : 12) + 6
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(n.x ?? 0, n.y ?? 0, size, 0, Math.PI * 2)
    ctx.fill()
  }, [])

  const handleNodeClick = useCallback((node: NodeObject) => {
    const n = node as GraphNode
    setSelectedNode(prev => (prev?.id === n.id ? null : n))
    if (n.x !== undefined && n.y !== undefined) {
      graphRef.current?.centerAt(n.x, n.y, 600)
      graphRef.current?.zoom(3, 600)
    }
  }, [])

  return (
    <>
      {/* ── Dynamic controls + stats ── */}
      <div className="shrink-0 flex items-center gap-3 px-4 py-2 border-b border-slate-700/60 bg-slate-900">
        <label htmlFor="dynamic-from" className="text-xs text-slate-400">From</label>
        <input
          id="dynamic-from"
          type="datetime-local"
          value={fromPending}
          onChange={e => setFromPending(e.target.value)}
          className="px-2 py-1 rounded text-xs bg-slate-800 border border-slate-600 text-slate-200 focus:outline-none focus:border-slate-400"
        />
        <button
          onClick={handleLoad}
          className="px-3 py-1 rounded text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
        >
          Load
        </button>
        {fromApplied && (
          <button
            onClick={handleClear}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            Clear
          </button>
        )}

        <div className="ml-auto flex items-center gap-5">
          {fraudCount > 0 && (
            <span className="text-xs font-medium text-red-400">
              {fraudCount} fraud alert{fraudCount === 1 ? '' : 's'}
            </span>
          )}
          <span className="text-xs text-slate-400">
            {graph.nodes.length} nodes · {graph.links.length} links
          </span>
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${STATUS_DOT[wsStatus]}`} />
            <span className="text-xs text-slate-400">{wsStatus}</span>
          </div>
        </div>
      </div>

      {/* ── Canvas ── */}
      <div className="flex-1 relative overflow-hidden">
        <ForceGraph2D
          ref={graphRef}
          graphData={graph}
          nodeId="id"
          nodeLabel={() => ''}
          nodeCanvasObject={paintNode}
          nodeCanvasObjectMode={() => 'replace'}
          nodePointerAreaPaint={paintNodePointer}
          onNodeClick={handleNodeClick}
          onBackgroundClick={() => setSelectedNode(null)}
          linkLabel="label"
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkColor={linkColorFn}
          linkWidth={linkWidthFn}
          backgroundColor="#0f172a"
          d3VelocityDecay={0.6}
          cooldownTicks={200}
          onEngineStop={handleEngineStop}
        />

        <NodePanel node={selectedNode} onClose={() => setSelectedNode(null)} />

        <button
          onClick={() => setShowLabels(v => !v)}
          className="absolute bottom-5 right-5 z-10 px-3 py-1.5 rounded text-xs text-slate-300 bg-slate-800/90 border border-slate-700 hover:bg-slate-700 transition-colors"
        >
          {showLabels ? 'Hide labels' : 'Show labels'}
        </button>
      </div>
    </>
  )
}

// ─── Root Dashboard ───────────────────────────────────────────────────────────

export function Dashboard() {
  const [graphMode, setGraphMode] = useState<GraphMode>('dynamic')
  const [activeTab, setActiveTab] = useState<Tab>('graph')

  // Keep a stable "now" string for the static default end time, computed once
  const nowDefault = useRef(toLocalDatetimeValue(new Date().toISOString()))

  return (
    <div className="w-screen h-screen bg-slate-900 flex flex-col overflow-hidden">

      {/* ── Header ── */}
      <header className="shrink-0 flex items-center justify-between px-5 py-2.5 bg-slate-900/95 border-b border-slate-800 z-30">

        <div className="flex items-center gap-5">
          <h1 className="text-base font-semibold text-white tracking-wide">NeoFraudJ</h1>

          <nav className="flex gap-1">
            {(['graph', 'explorer'] as Tab[]).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  activeTab === tab
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {tab === 'graph' ? 'Graph' : 'Fraud Explorer'}
              </button>
            ))}
          </nav>

          {/* Mode switcher — only shown on the Graph tab */}
          {activeTab === 'graph' && (
            <div className="flex items-center gap-1 ml-2 p-0.5 rounded bg-slate-800 border border-slate-700">
              {(['dynamic', 'static'] as GraphMode[]).map(mode => (
                <button
                  key={mode}
                  onClick={() => setGraphMode(mode)}
                  className={`px-3 py-0.5 rounded text-xs font-medium transition-colors ${
                    graphMode === mode
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {mode === 'dynamic' ? 'Dynamic' : 'Static'}
                </button>
              ))}
            </div>
          )}
        </div>
      </header>

      {/* ── Content ── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {activeTab === 'graph' && graphMode === 'dynamic' && <DynamicGraph />}
        {activeTab === 'graph' && graphMode === 'static'  && <StaticGraph key={nowDefault.current} />}
        {activeTab === 'explorer' && (
          // FraudExplorer still uses the full live graph from the hook
          <ExplorerWrapper />
        )}

      </div>
    </div>
  )
}

// Thin wrapper so FraudExplorer keeps its own live graph independent of mode state
function ExplorerWrapper() {
  const { graph } = useGraphStream()
  return <FraudExplorer graph={graph} />
}
