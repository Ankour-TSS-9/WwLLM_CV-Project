import { FREE_ANALYSES } from '../config'
import { mockAnalysis } from '../mock/analysis'
import type { AnalysisRecord, AnalyzeInput } from '../types'

const ANALYSES_KEY = 'falcon-perch.analyses'
const COUNT_KEY = 'falcon-perch.analysis-count'

export class FreeAnalysisLimitError extends Error {
  constructor() {
    super('You have reached the free analysis limit.')
    this.name = 'FreeAnalysisLimitError'
  }
}

export async function getAnalysisCount(): Promise<number> {
  const count = Number(localStorage.getItem(COUNT_KEY) ?? 0)
  return Number.isFinite(count) ? count : 0
}

export async function resetFreeAnalyses(): Promise<void> {
  localStorage.setItem(COUNT_KEY, '0')
}

export async function getAnalyses(): Promise<AnalysisRecord[]> {
  const stored = localStorage.getItem(ANALYSES_KEY)
  return stored ? (JSON.parse(stored) as AnalysisRecord[]) : []
}

export async function getAnalysis(id: string): Promise<AnalysisRecord | null> {
  const analyses = await getAnalyses()
  return analyses.find((analysis) => analysis.id === id) ?? null
}

export async function analyze(input: AnalyzeInput): Promise<AnalysisRecord> {
  if ((await getAnalysisCount()) >= FREE_ANALYSES) {
    throw new FreeAnalysisLimitError()
  }

  await new Promise<void>((resolve) => window.setTimeout(resolve, 3000))
  const record: AnalysisRecord = {
    ...mockAnalysis,
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    sport: input.sport,
    skill: input.skill,
    thumbnail: input.thumbnail ?? '',
  }
  const analyses = await getAnalyses()
  localStorage.setItem(ANALYSES_KEY, JSON.stringify([record, ...analyses]))
  localStorage.setItem(COUNT_KEY, String((await getAnalysisCount()) + 1))
  return record
}
