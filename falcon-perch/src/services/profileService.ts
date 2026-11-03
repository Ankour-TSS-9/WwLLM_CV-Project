import type { OnboardingProfile } from '../types'
import * as authService from './authService'

// Fallback in case the caller hasn't set up a session yet (shouldn't happen).
const FALLBACK_KEY = 'falcon-perch.profile.__unknown__'

function activeKey(): string {
  return authService.getActiveProfileKey() ?? FALLBACK_KEY
}

export async function getProfile(): Promise<OnboardingProfile | null> {
  const stored = localStorage.getItem(activeKey())
  return stored ? (JSON.parse(stored) as OnboardingProfile) : null
}

export async function saveProfile(profile: OnboardingProfile): Promise<OnboardingProfile> {
  localStorage.setItem(activeKey(), JSON.stringify(profile))
  return profile
}

/** Load a profile for a specific email (used right after login to check if returning user). */
export async function getProfileForEmail(email: string): Promise<OnboardingProfile | null> {
  const key = `falcon-perch.profile.${email.toLowerCase()}`
  const stored = localStorage.getItem(key)
  return stored ? (JSON.parse(stored) as OnboardingProfile) : null
}
