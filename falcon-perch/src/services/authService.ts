import { mockUser } from '../mock/auth'
import type { OnboardingProfile, User } from '../types'

const USER_KEY = 'falcon-perch.user'
const PROFILE_KEY = 'falcon-perch.profile'

function createUser(email: string): User {
  const nameFromEmail = email.split('@')[0]?.replace(/[._-]/g, ' ')
  const name = nameFromEmail
    ? nameFromEmail.replace(/\b\w/g, (letter) => letter.toUpperCase())
    : mockUser.name

  return { id: crypto.randomUUID(), email, name }
}

export const DEMO_GUEST_USER: User = {
  id: 'guest-athlete-demo',
  email: 'demo@falconperch.com',
  name: 'Alex Rivera (Guest)',
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

export async function login(email: string, _password: string): Promise<User> {
  const user = createUser(email)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  return user
}

export async function signup(email: string, _password: string): Promise<User> {
  const user = createUser(email)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  return user
}

export async function loginAsGuest(): Promise<{ user: User; profile: OnboardingProfile }> {
  localStorage.setItem(USER_KEY, JSON.stringify(DEMO_GUEST_USER))
  localStorage.setItem(PROFILE_KEY, JSON.stringify(DEMO_GUEST_PROFILE))
  return { user: DEMO_GUEST_USER, profile: DEMO_GUEST_PROFILE }
}

export async function getCurrentUser(): Promise<User | null> {
  const stored = localStorage.getItem(USER_KEY)
  return stored ? (JSON.parse(stored) as User) : null
}

export async function logout(): Promise<void> {
  localStorage.removeItem(USER_KEY)
}
