import { mockProfile } from '../mock/profile'
import type { OnboardingProfile } from '../types'

const PROFILE_KEY = 'falcon-perch.profile'

export async function getProfile(): Promise<OnboardingProfile | null> {
  const stored = localStorage.getItem(PROFILE_KEY)
  return stored ? (JSON.parse(stored) as OnboardingProfile) : null
}

export async function saveProfile(profile: OnboardingProfile): Promise<OnboardingProfile> {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
  return profile
}

export async function getDefaultProfile(): Promise<OnboardingProfile> {
  return { ...mockProfile }
}
