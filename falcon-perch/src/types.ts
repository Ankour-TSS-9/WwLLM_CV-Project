export const SPORTS = [
  'football',
  'cricket',
  'tennis',
  'badminton',
  'golf',
  'basketball',
  'motorsport',
  'athletics',
] as const

export type Sport = (typeof SPORTS)[number]
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'pro'
export type AthleteGoal = 'district' | 'state' | 'national' | 'international'

export interface User {
  id: string
  email: string
  name: string
  isGuest?: boolean
}

export interface OnboardingProfile {
  preferredSport: Sport
  age: number
  country: string
  state: string
  city: string
  level: SkillLevel
  role: string
  yearsPlaying: number
  goal: AthleteGoal
  experience_details?: string
}

export interface Idol {
  id: string
  name: string
  sport: Sport
  image_url: string
  bio: string
  slug?: string
  rating?: number
  jersey_number?: number
  signature_move?: string
  titles?: string
  followers_count?: string
}

export interface Video {
  id: string
  idol_id: string
  sport: Sport
  category: string
  title: string
  duration_seconds: number
  youtube_id: string
  thumbnail_url: string
}

export type MomentClassification =
  | 'Brilliant'
  | 'Great'
  | 'Good'
  | 'Inaccuracy'
  | 'Mistake'
  | 'Blunder'

export interface AnalysisPhase {
  name: 'setup' | 'approach' | 'execution' | 'follow-through'
  score: number
}

export interface KeyMoment {
  timestamp_seconds: number
  classification: MomentClassification
  comment: string
}

export interface JointAngleSample {
  timestamp_seconds: number
  knee: number
  hip: number
  elbow: number
  shoulder: number
}

export interface AnalysisResult {
  overall_score: number
  accuracy_percent: number
  phases: AnalysisPhase[]
  key_moments: KeyMoment[]
  strengths: string[]
  weaknesses: string[]
  drills: string[]
  summary: string
  joint_angles: JointAngleSample[]
}

export interface AnalysisRecord extends AnalysisResult {
  id: string
  created_at: string
  sport: Sport
  skill: string
  thumbnail: string
}

export interface AnalyzeInput {
  sport: Sport
  skill: string
  thumbnail?: string
}

export interface PathwayNode {
  id: string
  sport: Sport
  title: string
  description: string
  age_range: string
  difficulty: string
  order: number
  qualification: string
  checklist: string[]
}

export interface Tournament {
  id: string
  name: string
  sport: Sport
  level: SkillLevel
  region: string
  date: string
  location: string
  url: string
  last_verified: string
}

export interface PricingPlan {
  id: 'monthly' | 'yearly'
  name: string
  price: number
  interval: 'month' | 'year'
}
