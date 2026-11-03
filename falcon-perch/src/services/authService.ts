import type { OnboardingProfile, User } from '../types'

// Session lives in sessionStorage — cleared when tab/browser closes.
const SESSION_KEY = 'falcon-perch.session'

// Per-user profile keyed by email so each account has its own data.
const profileKey = (email: string) => `falcon-perch.profile.${email}`

// Special guest key (never collides with a real email-based key).
const GUEST_SESSION_KEY = 'falcon-perch.session'
const GUEST_EMAIL = 'guest@falconperch.internal'

export const DEMO_GUEST_USER: User = {
  id: 'guest-athlete-demo',
  email: GUEST_EMAIL,
  name: 'Alex Rivera',
  isGuest: true,
}

export const DEMO_GUEST_PROFILE: OnboardingProfile = {
  preferredSport: 'football',
  age: 17,
  country: 'India',
  state: 'Maharashtra',
  city: 'Mumbai',
  level: 'intermediate',
  role: 'Forward / Striker',
  yearsPlaying: 4,
  goal: 'national',
  experience_details: '4 years youth academy training · School squad captain',
}

function createUser(email: string): User {
  const raw = email.split('@')[0]?.replace(/[._-]/g, ' ') ?? ''
  const name = raw.replace(/\b\w/g, (l) => l.toUpperCase()) || 'Athlete'
  return { id: crypto.randomUUID(), email, name, isGuest: false }
}

/** Returns the profile key for the currently-stored session user (if any). */
function currentProfileKey(): string | null {
  const stored = sessionStorage.getItem(SESSION_KEY)
  if (!stored) return null
  try {
    const user = JSON.parse(stored) as User
    return profileKey(user.email)
  } catch {
    return null
  }
}

// ── Auth actions ─────────────────────────────────────────────────────────────

export async function login(email: string, _password: string): Promise<User> {
  const lower = email.toLowerCase()
  const existing = localStorage.getItem(profileKey(lower))
  // If this email has a stored profile, restore the same user id so data matches.
  let user: User
  if (existing) {
    // Re-use stored identity if it was previously persisted under this email.
    const storedUser = localStorage.getItem(`falcon-perch.identity.${lower}`)
    user = storedUser ? (JSON.parse(storedUser) as User) : createUser(lower)
  } else {
    user = createUser(lower)
  }
  user.isGuest = false
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(user))
  // Persist identity for future logins.
  localStorage.setItem(`falcon-perch.identity.${lower}`, JSON.stringify(user))
  return user
}

export async function signup(email: string, _password: string): Promise<User> {
  const lower = email.toLowerCase()
  const user = createUser(lower)
  user.isGuest = false
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(user))
  localStorage.setItem(`falcon-perch.identity.${lower}`, JSON.stringify(user))
  return user
}

export async function loginAsGuest(): Promise<{ user: User; profile: OnboardingProfile }> {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(DEMO_GUEST_USER))
  // Guest profile is always the demo profile — never stored under a real email key.
  localStorage.setItem(profileKey(GUEST_EMAIL), JSON.stringify(DEMO_GUEST_PROFILE))
  return { user: DEMO_GUEST_USER, profile: DEMO_GUEST_PROFILE }
}

export async function getCurrentUser(): Promise<User | null> {
  const stored = sessionStorage.getItem(SESSION_KEY)
  return stored ? (JSON.parse(stored) as User) : null
}

/** Returns the per-user localStorage profile key for whoever is logged in. */
export function getActiveProfileKey(): string | null {
  return currentProfileKey()
}

export async function logout(): Promise<void> {
  sessionStorage.removeItem(GUEST_SESSION_KEY)
}
