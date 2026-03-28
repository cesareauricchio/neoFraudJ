export type NodeLabel =
  | 'User'
  | 'Account'
  | 'Card'
  | 'Transaction'
  | 'Merchant'
  | 'Device'
  | 'IPAddress'

export interface GraphNode {
  id: string
  label: NodeLabel
  isFraud?: boolean
  // Cluster fields — set when this node represents multiple collapsed transactions
  isCluster?: boolean
  clusterCount?: number
  clusterTotalAmount?: number
  // Fields injected by the force simulation
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number
  fy?: number
  // All other properties from Neo4j
  [key: string]: unknown
}

export interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
  label: string
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export type GraphMode = 'dynamic' | 'static'

export type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface WsMessage {
  type: 'GRAPH_UPDATE'
  is_fraud_alert: boolean
  payload: {
    nodes: GraphNode[]
    links: GraphLink[]
  }
}
