import type { GraphData, GraphLink, GraphNode } from '../types/graph'

function linkId(node: string | GraphNode): string {
  return typeof node === 'string' ? node : node.id
}

function buildTxnCardMap(links: GraphLink[], nodeById: Map<string, GraphNode>): Map<string, string> {
  const txnCard = new Map<string, string>()
  for (const link of links) {
    const s = linkId(link.source)
    const t = linkId(link.target)
    if (nodeById.get(s)?.label === 'Card' && nodeById.get(t)?.label === 'Transaction') {
      txnCard.set(t, s)
    }
  }
  return txnCard
}

function buildCardTxnGroups(nodes: GraphNode[], txnCard: Map<string, string>): Map<string, string[]> {
  const cardTxns = new Map<string, string[]>()
  for (const node of nodes) {
    if (node.label !== 'Transaction') continue
    const cardId = txnCard.get(node.id)
    if (!cardId) continue
    const bucket = cardTxns.get(cardId)
    if (bucket) bucket.push(node.id)
    else cardTxns.set(cardId, [node.id])
  }
  return cardTxns
}

function buildClusters(
  cardTxns: Map<string, string[]>,
  nodeById: Map<string, GraphNode>,
): { txnToCluster: Map<string, string>; clusterNodes: GraphNode[]; clusteredTxns: Set<string> } {
  const txnToCluster  = new Map<string, string>()
  const clusterNodes: GraphNode[] = []
  const clusteredTxns = new Set<string>()

  for (const [cardId, txnIds] of cardTxns) {
    if (txnIds.length < 2) continue

    const clusterId = `cluster_${cardId}`
    const txns      = txnIds.map(id => nodeById.get(id)).filter((n): n is GraphNode => n !== undefined)
    const card      = nodeById.get(cardId)
    // Fraud if any constituent transaction is fraud OR if the card itself is marked fraud
    // (the card is permanently marked even if only one transaction triggered it)
    const isFraud   = txns.some(t => t.isFraud) || Boolean(card?.isFraud)
    const totalAmt  = txns.reduce((sum, t) => {
      const v = Number.parseFloat(t.amount as string)
      return sum + (Number.isNaN(v) ? 0 : v)
    }, 0)

    clusterNodes.push({ id: clusterId, label: 'Transaction', isCluster: true, clusterCount: txnIds.length, clusterTotalAmount: totalAmt, isFraud })
    for (const id of txnIds) { txnToCluster.set(id, clusterId); clusteredTxns.add(id) }
  }

  return { txnToCluster, clusterNodes, clusteredTxns }
}

function remapLinks(
  links: GraphLink[],
  validIds: Set<string>,
  allNodeIds: Set<string>,
  txnToCluster: Map<string, string>,
): GraphLink[] {
  const seenLinks = new Set<string>()
  const newLinks: GraphLink[] = []

  for (const link of links) {
    let s = linkId(link.source)
    let t = linkId(link.target)
    if (!validIds.has(s) || !validIds.has(t)) continue
    s = txnToCluster.get(s) ?? s
    t = txnToCluster.get(t) ?? t
    if (!allNodeIds.has(s) || !allNodeIds.has(t) || s === t) continue
    const key = `${s}→${t}`
    if (!seenLinks.has(key)) { seenLinks.add(key); newLinks.push({ source: s, target: t, label: link.label }) }
  }

  return newLinks
}

/**
 * Collapses all Transaction nodes belonging to the same Card into one cluster
 * diamond (one per card). Device/IPAddress nodes are excluded — they sit outside
 * the fraud-relevant hierarchy and break the DAG layout.
 *
 *   User → Account → Card → [TxnCluster] → Merchant
 */
export function clusterizeGraph(data: GraphData): GraphData {
  const nodes    = data.nodes.filter(n => n.label !== 'Device' && n.label !== 'IPAddress')
  const validIds = new Set(nodes.map(n => n.id))
  const nodeById = new Map<string, GraphNode>(nodes.map(n => [n.id, n]))

  const txnCard  = buildTxnCardMap(data.links, nodeById)
  const cardTxns = buildCardTxnGroups(nodes, txnCard)
  const { txnToCluster, clusterNodes, clusteredTxns } = buildClusters(cardTxns, nodeById)

  const keptNodes  = nodes.filter(n => n.label !== 'Transaction' || !clusteredTxns.has(n.id))
  const allNodes   = [...keptNodes, ...clusterNodes]
  const allNodeIds = new Set(allNodes.map(n => n.id))

  const remapped = remapLinks(data.links, validIds, allNodeIds, txnToCluster)

  // Drop any Transaction node that has no Card parent in the final link set —
  // these are DAG-orphans and float to the top row.
  const hasCardParent = new Set<string>()
  const finalNodeById = new Map(allNodes.map(n => [n.id, n]))
  for (const l of remapped) {
    const s = linkId(l.source)
    const t = linkId(l.target)
    if (finalNodeById.get(s)?.label === 'Card' && finalNodeById.get(t)?.label === 'Transaction') {
      hasCardParent.add(t)
    }
  }
  const anchoredNodes  = allNodes.filter(n => n.label !== 'Transaction' || hasCardParent.has(n.id))
  const anchoredIds    = new Set(anchoredNodes.map(n => n.id))
  const anchoredLinks  = remapped.filter(l => anchoredIds.has(linkId(l.source)) && anchoredIds.has(linkId(l.target)))

  return { nodes: anchoredNodes, links: anchoredLinks }
}
