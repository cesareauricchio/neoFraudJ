import type { GraphNode, NodeLabel } from '../types/graph'

export const NODE_COLORS: Record<NodeLabel, string> = {
  User:        '#3b82f6',
  Account:     '#10b981',
  Card:        '#6ee7b7',
  Transaction: '#f59e0b',
  Merchant:    '#8b5cf6',
  Device:      '#4b5563',
  IPAddress:   '#374151',
}

const FRAUD_COLOR = '#ef4444'
const FRAUD_GLOW  = '#ef4444'
const SELECT_GLOW = 'rgba(255,255,255,0.9)'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function applyShadow(ctx: CanvasRenderingContext2D, node: GraphNode, isSelected: boolean): void {
  if (node.isFraud) {
    ctx.shadowBlur  = node.isCluster ? 24 : 18
    ctx.shadowColor = FRAUD_GLOW
  } else if (isSelected) {
    ctx.shadowBlur  = 14
    ctx.shadowColor = SELECT_GLOW
  } else {
    ctx.shadowBlur  = 0
    ctx.shadowColor = 'transparent'
  }
}

function applyStroke(ctx: CanvasRenderingContext2D, node: GraphNode, isSelected: boolean, globalScale: number): void {
  if (isSelected)          ctx.strokeStyle = '#ffffff'
  else if (node.isCluster) ctx.strokeStyle = 'rgba(255,255,255,0.4)'
  else                     ctx.strokeStyle = 'rgba(255,255,255,0.15)'

  if (isSelected || node.isFraud) ctx.lineWidth = 1.5 / globalScale
  else if (node.isCluster)        ctx.lineWidth = 1   / globalScale
  else                            ctx.lineWidth = 0.5 / globalScale
}

function traceShape(ctx: CanvasRenderingContext2D, label: NodeLabel, x: number, y: number, size: number): void {
  ctx.beginPath()
  if (label === 'Account') {
    ctx.rect(x - size, y - size, size * 2, size * 2)
  } else if (label === 'Card') {
    ctx.rect(x - size * 1.5, y - size * 0.8, size * 3, size * 1.6)
  } else if (label === 'Transaction') {
    ctx.moveTo(x,        y - size)
    ctx.lineTo(x + size, y)
    ctx.lineTo(x,        y + size)
    ctx.lineTo(x - size, y)
    ctx.closePath()
  } else {
    ctx.arc(x, y, size, 0, Math.PI * 2)
  }
}

function drawClusterCount(ctx: CanvasRenderingContext2D, node: GraphNode, x: number, y: number, globalScale: number): void {
  if (!node.isCluster || node.clusterCount === undefined) return
  const fontSize = Math.max(8 / globalScale, 2)
  ctx.font         = `bold ${fontSize}px Inter, ui-sans-serif, sans-serif`
  ctx.textAlign    = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle    = '#ffffff'
  ctx.fillText(String(node.clusterCount), x, y)
}

function drawLabels(ctx: CanvasRenderingContext2D, node: GraphNode, x: number, y: number, size: number, globalScale: number): void {
  const fontSize = Math.max(10 / globalScale, 2.5)
  ctx.font         = `${fontSize}px Inter, ui-sans-serif, sans-serif`
  ctx.textAlign    = 'center'
  ctx.textBaseline = 'top'
  ctx.fillStyle    = 'rgba(226,232,240,0.8)'

  const text = node.isCluster ? `${node.clusterCount}× txn` : node.id.slice(0, 14)
  ctx.fillText(text, x, y + size + 2 / globalScale)

  if (node.isCluster && node.clusterTotalAmount !== undefined) {
    const amtSize = Math.max(8 / globalScale, 2)
    ctx.font      = `${amtSize}px Inter, ui-sans-serif, sans-serif`
    ctx.fillStyle = 'rgba(148,163,184,0.7)'
    ctx.fillText(`$${node.clusterTotalAmount.toFixed(0)}`, x, y + size + fontSize + 3 / globalScale)
  }
}

// ─── Public ───────────────────────────────────────────────────────────────────

export function drawNode(
  node: GraphNode,
  ctx: CanvasRenderingContext2D,
  globalScale: number,
  isSelected: boolean,
  showLabels: boolean,
  dimmed = false,
): void {
  const prevAlpha = ctx.globalAlpha
  if (dimmed) ctx.globalAlpha = 0.12

  const x    = node.x ?? 0
  const y    = node.y ?? 0
  const size = node.isCluster ? 18 : 12

  applyShadow(ctx, node, isSelected)
  applyStroke(ctx, node, isSelected, globalScale)
  ctx.fillStyle = node.isFraud ? FRAUD_COLOR : (NODE_COLORS[node.label] ?? '#6b7280')

  traceShape(ctx, node.label, x, y, size)
  ctx.fill()
  ctx.stroke()

  ctx.shadowBlur  = 0
  ctx.shadowColor = 'transparent'

  drawClusterCount(ctx, node, x, y, globalScale)
  if (showLabels) drawLabels(ctx, node, x, y, size, globalScale)

  ctx.globalAlpha = prevAlpha
}
