import { useEffect, useState } from 'react'
import type { GraphNode, NodeLabel } from '../types/graph'

interface NodePanelProps {
  node: GraphNode | null
  onClose: () => void
}

const NODE_COLORS: Record<NodeLabel, string> = {
  User:        '#3b82f6',
  Account:     '#10b981',
  Card:        '#6ee7b7',
  Transaction: '#f59e0b',
  Merchant:    '#8b5cf6',
  Device:      '#4b5563',
  IPAddress:   '#374151',
}

// Force-graph internal keys — not useful to display
const INTERNAL_KEYS = new Set([
  'x', 'y', 'vx', 'vy', 'fx', 'fy', '__indexColor', 'index',
])

interface RiskScore {
  risk_score: number
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW'
  signals: Array<{ type: string; value: number }>
}

const RISK_COLORS: Record<string, string> = {
  HIGH:   'text-red-400',
  MEDIUM: 'text-amber-400',
  LOW:    'text-emerald-400',
}

export function NodePanel({ node, onClose }: NodePanelProps) {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null)
  const [loadingRisk, setLoadingRisk] = useState(false)

  // Reset risk score whenever the selected node changes
  useEffect(() => {
    setRiskScore(null)
  }, [node?.id])

  const fetchRiskScore = async () => {
    if (!node) return
    setLoadingRisk(true)
    try {
      const r = await fetch(`http://localhost:8002/v1/transactions/${node.id}/risk-score`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setRiskScore(await r.json())
    } catch (err) {
      console.error('Risk score fetch failed:', err)
    } finally {
      setLoadingRisk(false)
    }
  }

  const color = node ? (NODE_COLORS[node.label] ?? '#6b7280') : '#6b7280'

  return (
    <div
      className={`
        fixed right-0 top-0 h-full w-80 bg-slate-800/95 backdrop-blur-sm
        border-l border-slate-700 transform transition-transform duration-300 ease-in-out z-20
        flex flex-col
        ${node ? 'translate-x-0' : 'translate-x-full'}
      `}
    >
      {node && (
        <>
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 shrink-0">
            <div className="flex items-center gap-2">
              <span
                className="px-2 py-0.5 rounded text-xs font-bold text-white"
                style={{ backgroundColor: color }}
              >
                {node.label}
              </span>
              {node.isFraud && (
                <span className="px-2 py-0.5 rounded text-xs font-bold text-white bg-red-600">
                  FRAUD
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors text-xl leading-none"
              aria-label="Close panel"
            >
              ×
            </button>
          </div>

          {/* Properties */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {Object.entries(node)
              .filter(([k]) => !INTERNAL_KEYS.has(k))
              .map(([k, v]) => (
                <div key={k}>
                  <div className="text-xs text-slate-400 mb-0.5">{k}</div>
                  <div className="text-sm text-slate-100 font-mono break-all">
                    {v === null || v === undefined ? '—' : String(v)}
                  </div>
                </div>
              ))}
          </div>

          {/* Risk score — Transaction nodes only */}
          {node.label === 'Transaction' && (
            <div className="px-4 py-3 border-t border-slate-700 shrink-0">
              {riskScore === null ? (
                <button
                  onClick={fetchRiskScore}
                  disabled={loadingRisk}
                  className="
                    w-full py-2 px-4 rounded text-sm text-slate-100
                    bg-slate-700 hover:bg-slate-600 disabled:opacity-50
                    transition-colors
                  "
                >
                  {loadingRisk ? 'Fetching...' : 'Fetch Risk Score'}
                </button>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">Risk Score</span>
                    <span className={`text-sm font-bold ${RISK_COLORS[riskScore.risk_level] ?? 'text-slate-300'}`}>
                      {riskScore.risk_level} ({riskScore.risk_score}/100)
                    </span>
                  </div>
                  {riskScore.signals.length > 0 && (
                    <div className="space-y-1">
                      {riskScore.signals.map(s => (
                        <div key={s.type} className="flex justify-between text-xs text-slate-400">
                          <span>{s.type.replace(/_/g, ' ')}</span>
                          <span className="text-slate-300">{s.value}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={() => setRiskScore(null)}
                    className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    clear
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
