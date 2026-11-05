import { FREE_ANALYSES } from '../config'
import { mockAnalysis } from '../mock/analysis'
import type { AnalysisRecord, AnalyzeInput, AnalysisResult } from '../types'

const ANALYSES_KEY = 'falcon-perch.analyses'
const COUNT_KEY = 'falcon-perch.analysis-count'
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

/**
 * Analyze using AI Coach backend (if available) or fallback to mock
 */
export async function analyze(input: AnalyzeInput, playerId?: number, matchId: string = 'default'): Promise<AnalysisRecord> {
  if ((await getAnalysisCount()) >= FREE_ANALYSES) {
    throw new FreeAnalysisLimitError()
  }

  let analysisResult: AnalysisResult
  
  // Try backend first if playerId provided
  if (playerId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/match/${matchId}/coach`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId,
          player_name: `Athlete ${playerId}`,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        analysisResult = data.report as AnalysisResult
        console.log('✅ AI Coach report generated from backend')
      } else {
        console.warn('Backend unavailable, using mock data')
        await new Promise<void>((resolve) => window.setTimeout(resolve, 3000))
        analysisResult = mockAnalysis
      }
    } catch (error) {
      console.warn('Backend error, using mock data:', error)
      await new Promise<void>((resolve) => window.setTimeout(resolve, 3000))
      analysisResult = mockAnalysis
    }
  } else {
    // No playerId, use mock
    await new Promise<void>((resolve) => window.setTimeout(resolve, 3000))
    analysisResult = mockAnalysis
  }

  const record: AnalysisRecord = {
    ...analysisResult,
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

/**
 * Get match statistics from backend
 */
export async function getMatchStats(matchId: string = 'default') {
  try {
    const response = await fetch(`${API_BASE_URL}/api/match/${matchId}/stats`)
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to fetch match stats:', error)
    return null
  }
}

/**
 * Generate commentary with selected persona
 */
export async function generateCommentary(
  matchId: string = 'default',
  persona: 'broadcast' | 'tactical' | 'coach' = 'broadcast',
  playerNames?: Record<string, string>,
  teamNames?: Record<string, string>
) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/match/${matchId}/commentary`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          persona,
          player_names: playerNames,
          team_names: teamNames,
          language: 'english',
        }),
      }
    )

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to generate commentary:', error)
    return null
  }
}

/**
 * Chat with match data (Q&A)
 */
export async function chatWithMatch(
  question: string,
  matchId: string = 'default',
  playerNames?: Record<string, string>
) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/match/${matchId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        player_names: playerNames,
      }),
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Failed to chat with match:', error)
    return null
  }
}
