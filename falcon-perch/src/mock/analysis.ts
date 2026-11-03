import type { AnalysisResult } from '../types'

export const mockAnalysis: AnalysisResult = {
  overall_score: 78,
  accuracy_percent: 82,
  phases: [
    { name: 'setup', score: 76 },
    { name: 'approach', score: 80 },
    { name: 'execution', score: 84 },
    { name: 'follow-through', score: 72 },
  ],
  key_moments: [
    { timestamp_seconds: 2, classification: 'Good', comment: 'Balanced starting position.' },
    { timestamp_seconds: 5, classification: 'Great', comment: 'Good control through the movement.' },
    { timestamp_seconds: 8, classification: 'Inaccuracy', comment: 'Keep your follow-through consistent.' },
  ],
  strengths: ['Strong balance', 'Good timing', 'Consistent movement'],
  weaknesses: ['Follow-through control', 'Upper-body alignment', 'Starting stance'],
  drills: ['Slow-motion technique reps', 'Single-leg balance holds', 'Targeted follow-through drill'],
  summary: 'A promising performance with a stable base and good timing. Focus on a consistent follow-through to improve control.',
  joint_angles: [
    { timestamp_seconds: 0, knee: 145, hip: 112, elbow: 96, shoulder: 38 },
    { timestamp_seconds: 2, knee: 128, hip: 104, elbow: 112, shoulder: 48 },
    { timestamp_seconds: 4, knee: 116, hip: 95, elbow: 136, shoulder: 62 },
    { timestamp_seconds: 6, knee: 132, hip: 108, elbow: 151, shoulder: 78 },
    { timestamp_seconds: 8, knee: 149, hip: 121, elbow: 134, shoulder: 65 },
  ],
}
