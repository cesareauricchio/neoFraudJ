import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { NodeObject } from 'react-force-graph-2d'
import { useStaticGraph } from '../hooks/useStaticGraph'
import { drawNode } from '../utils/drawNode'
import { clusterizeGraph } from '../utils/clusterize'
import { applyDagreLayout } from '../utils/dagreLayout'
import { NodePanel } from './NodePanel'
import type { GraphNode } from '../types/graph'

type Orientation = 'td' | 'lr'

function toLocalDatetimeValue(iso: string): string {
  return iso.slice(0, 16)
}

function nowIso(): string {
  return new Date().toISOString()
}

function hoursAgoIso(h: number): string {
  return new Date(Date.now() - h * 3_600_000).toISOString()
}

export function StaticGraph() {
  const { graph: rawGraph, loading, error, fetch: loadGraph, reset } = useStaticGraph()

  const [start,        setStart]        = useState(() => toLocalDatetimeValue(hoursAgoIso(6)))
  const [end,          setEnd]          = useState(() => toLocalDatetimeValue(nowIso()))
  const [orientation,  setOrientation]  = useState<Orientation>('td')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [showLabels,   setShowLabels]   = useState(false)
  const [canvasSize,   setCanvasSize]   = useState({ w: 1200, h: 800 })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef     = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Measure container so dagre can scale coordinates to fill it
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const obs = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setCanvasSize({ w: width, h: height })
    })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  // 1. Clusterize  2. Apply dagre layout scaled to canvas size
  const graph = useMemo(() => {
    if (!rawGraph) return null
    const clustered = clusterizeGraph(rawGraph)
    const rankdir   = orientation === 'td' ? 'TB' : 'LR'
    return applyDagreLayout(clustered, rankdir, canvasSize.w, canvasSize.h)
  }, [rawGraph, orientation, canvasSize])

  // Disable all physics — positions are pinned by fx/fy
  useEffect(() => {
    const fg = graphRef.current
    if (!fg) return
    fg.d3Force('charge',    null)
    fg.d3Force('link',      null)
    fg.d3Force('center',    null)
    fg.d3Force('collision', null)
  }, [graph])

  // Center the view at zoom=1 so dagre coordinates map 1:1 to pixels
  useEffect(() => {
    if (!graph || graph.nodes.length === 0) return
    const timer = setTimeout(() => {
      graphRef.current?.zoom(1, 0)
      graphRef.current?.centerAt(canvasSize.w / 2, canvasSize.h / 2, 0)
    }, 50)
    return () => clearTimeout(timer)
  }, [graph, canvasSize])

  const handleLoad = () => {
    setSelectedNode(null)
    reset()
    loadGraph(new Date(start).toISOString(), new Date(end).toISOString())
  }

  const paintNode = useCallback(
    (node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
      drawNode(node as GraphNode, ctx, globalScale, (node as GraphNode).id === selectedNode?.id, showLabels)
    },
    [selectedNode, showLabels],
  )

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
    setSelectedNode(prev => prev?.id === n.id ? null : n)
    if (n.x !== undefined && n.y !== undefined) {
      graphRef.current?.centerAt(n.x, n.y, 500)
      graphRef.current?.zoom(3, 500)
    }
  }, [])

  const linkColor = useCallback((link: object) => {
    const l = link as { source: string | GraphNode; target: string | GraphNode }
    const s = typeof l.source === 'string' ? l.source : l.source.id
    const t = typeof l.target === 'string' ? l.target : l.target.id
    const sNode = graph?.nodes.find(n => n.id === s)
    const tNode = graph?.nodes.find(n => n.id === t)
    return sNode?.isFraud && tNode?.isFraud ? 'rgba(239,68,68,0.7)' : 'rgba(148,163,184,0.25)'
  }, [graph])

  const fraudCount = graph?.nodes.filter(n => n.isFraud).length ?? 0

  return (
    <div className="flex flex-col h-full">

      {/* ── Controls bar ── */}
      <div className="shrink-0 flex items-center gap-3 px-4 py-2.5 border-b border-slate-700/60 bg-slate-900 flex-wrap">

        <label htmlFor="static-from" className="text-xs text-slate-400">From</label>
        <input
          id="static-from"
          type="datetime-local"
          value={start}
          onChange={e => setStart(e.target.value)}
          className="px-2 py-1 rounded text-xs bg-slate-800 border border-slate-600 text-slate-200 focus:outline-none focus:border-slate-400"
        />
        <label htmlFor="static-to" className="text-xs text-slate-400">To</label>
        <input
          id="static-to"
          type="datetime-local"
          value={end}
          onChange={e => setEnd(e.target.value)}
          className="px-2 py-1 rounded text-xs bg-slate-800 border border-slate-600 text-slate-200 focus:outline-none focus:border-slate-400"
        />
        <button
          onClick={handleLoad}
          disabled={loading}
          className="px-3 py-1 rounded text-xs font-medium bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition-colors"
        >
          {loading ? 'Loading…' : 'Load'}
        </button>

        {/* Orientation toggle */}
        <div className="flex items-center gap-1 p-0.5 rounded bg-slate-800 border border-slate-700">
          {(['td', 'lr'] as Orientation[]).map(o => (
            <button
              key={o}
              onClick={() => setOrientation(o)}
              className={`px-2.5 py-0.5 rounded text-xs font-medium transition-colors ${
                orientation === o ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {o === 'td' ? '↕ Vertical' : '↔ Horizontal'}
            </button>
          ))}
        </div>

        {graph && (
          <span className="ml-auto text-xs text-slate-400">
            {graph.nodes.length} nodes · {graph.links.length} links
            {fraudCount > 0 && <span className="ml-3 text-red-400">{fraudCount} fraud</span>}
          </span>
        )}
      </div>

      {/* ── Graph area ── */}
      <div ref={containerRef} className="flex-1 relative overflow-hidden bg-[#0f172a]">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-red-400 text-sm">{error}</span>
          </div>
        )}

        {!graph && !loading && !error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-slate-500 text-sm mb-1">Set a time range and press Load</div>
              <div className="text-slate-600 text-xs">Transactions and their connected entities will appear here</div>
            </div>
          </div>
        )}

        {graph && (
          <>
            <ForceGraph2D
              key={`${start}-${end}-${orientation}`}
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
              linkDirectionalArrowLength={6}
              linkDirectionalArrowRelPos={1}
              linkColor={linkColor}
              linkWidth={1.5}
              backgroundColor="#0f172a"
              cooldownTicks={0}
            />

            <NodePanel node={selectedNode} onClose={() => setSelectedNode(null)} />

            <button
              onClick={() => setShowLabels(v => !v)}
              className="absolute bottom-5 right-5 z-10 px-3 py-1.5 rounded text-xs text-slate-300 bg-slate-800/90 border border-slate-700 hover:bg-slate-700 transition-colors"
            >
              {showLabels ? 'Hide labels' : 'Show labels'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
