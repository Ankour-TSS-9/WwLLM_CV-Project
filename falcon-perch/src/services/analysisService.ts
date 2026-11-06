import { FREE_ANALYSES } from '../config'
import { mockAnalysis } from '../mock/analysis'
import type { AnalysisRecord, AnalyzeInput, AnalysisResult } from '../types'

const ANALYSES_KEY = 'falcon-perch.analyses'
const COUNT_KEY = 'falcon-perch.analysis-count'
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface VideoUploadResponse {
  match_id: string
  video_url: string
}

export async function uploadVideo(file: File): Promise<VideoUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/upload-video`, {
    method: 'POST',
    body: formData,
  })
  const data: unknown = await response.json()
  const payload = typeof data === 'object' && data !== null ? data : {}

  if (!response.ok) {
    const detail = 'detail' in payload && typeof payload.detail === 'string'
      ? payload.detail
      : 'Video upload failed'
    throw new Error(detail)
  }
  if (
    !('video_url' in payload)
    || typeof payload.video_url !== 'string'
    || !('match_id' in payload)
    || typeof payload.match_id !== 'string'
  ) {
    throw new Error('Backend response did not include the processed video URL')
  }

  return { match_id: payload.match_id, video_url: payload.video_url }
}

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
export interface CommentaryLine {
 time: number
 text: string
 excitement_level: 'low' | 'medium' | 'high' | 'explosive'
 target_player_id?: number | null
}

export interface CommentaryResponse {
 commentary: CommentaryLine[]
}

function isCommentaryLine(line: unknown): line is CommentaryLine {
 if (typeof line !== 'object' || line === null) {
   return false
 }

 return (
   'time' in line &&
   typeof line.time === 'number' &&
   'text' in line &&
   typeof line.text === 'string' &&
   'excitement_level' in line &&
   (
     line.excitement_level === 'low' ||
     line.excitement_level === 'medium' ||
     line.excitement_level === 'high' ||
     line.excitement_level === 'explosive'
   ) &&
   (!('target_player_id' in line) ||
     line.target_player_id === null ||
     typeof line.target_player_id === 'number')
 )
}

export async function generateCommentary(
 matchId: string = 'default',
 persona: 'broadcast' | 'tactical' | 'coach' = 'broadcast',
 playerNames?: Record<string, string>,
 teamNames?: Record<string, string>
): Promise<CommentaryResponse> {
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

  const data: unknown = await response.json()
  const payload = typeof data === 'object' && data !== null ? data : {}

  if (!response.ok) {
    const detail = 'detail' in payload && typeof payload.detail === 'string'
      ? payload.detail
      : `Commentary request failed (${response.status})`
    throw new Error(detail)
  }

  if (
    !('commentary' in payload) ||
    !Array.isArray(payload.commentary) ||
    !payload.commentary.every(isCommentaryLine)
  ) {
    throw new Error('The backend returned an invalid commentary response.')
  }

  return { commentary: payload.commentary }
}

export async function generateCommentaryAudio(
  matchId: string,
  text: string
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}/api/match/${matchId}/commentary/audio`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    }
  )

  if (!response.ok) {
    const data: unknown = await response.json()
    const payload = typeof data === 'object' && data !== null ? data : {}
    const detail = 'detail' in payload && typeof payload.detail === 'string'
      ? payload.detail
      : `Commentary audio request failed (${response.status})`
    throw new Error(detail)
  }

  return response.blob()
}

export async function createCommentaryVideo(
  matchId: string,
  commentary: CommentaryLine[]
): Promise<string> {
  const response = await fetch(
    `${API_BASE_URL}/api/match/${matchId}/commentary/video`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ commentary }),
    }
  )

  const data: unknown = await response.json()
  const payload = typeof data === 'object' && data !== null ? data : {}

  if (!response.ok) {
    const detail = 'detail' in payload && typeof payload.detail === 'string'
      ? payload.detail
      : `Commentary video request failed (${response.status})`
    throw new Error(detail)
  }
  if (!('video_url' in payload) || typeof payload.video_url !== 'string') {
    throw new Error('Backend response did not include the commentary video URL')
  }

  return new URL(payload.video_url, API_BASE_URL).toString()
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
