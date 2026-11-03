import { mockPathways } from '../mock/pathways'
import type { PathwayNode, Sport } from '../types'

const COMPLETED_KEY = 'falcon-perch.completed-pathways'

export async function getPathway(sport?: Sport): Promise<PathwayNode[]> {
  return sport ? mockPathways.filter((node) => node.sport === sport) : mockPathways
}

export async function getCompletedPathwayNodeIds(): Promise<string[]> {
  const stored = localStorage.getItem(COMPLETED_KEY)
  return stored ? (JSON.parse(stored) as string[]) : []
}

export async function togglePathwayNode(nodeId: string): Promise<string[]> {
  const completed = await getCompletedPathwayNodeIds()
  const updated = completed.includes(nodeId)
    ? completed.filter((id) => id !== nodeId)
    : [...completed, nodeId]
  localStorage.setItem(COMPLETED_KEY, JSON.stringify(updated))
  return updated
}
