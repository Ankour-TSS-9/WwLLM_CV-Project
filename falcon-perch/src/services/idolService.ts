import { mockIdols } from '../mock/idols'
import type { Idol } from '../types'

const FOLLOWED_KEY = 'falcon-perch.followed-idols'

export async function getIdols(sport?: Idol['sport']): Promise<Idol[]> {
  return sport ? mockIdols.filter((idol) => idol.sport === sport) : mockIdols
}

export async function getIdolById(id: string): Promise<Idol | undefined> {
  return mockIdols.find((idol) => idol.id === id || idol.slug === id)
}

export async function getFollowedIdolIds(): Promise<string[]> {
  const stored = localStorage.getItem(FOLLOWED_KEY)
  return stored ? (JSON.parse(stored) as string[]) : []
}

export async function toggleFollowIdol(idolId: string): Promise<string[]> {
  const followed = await getFollowedIdolIds()
  const updated = followed.includes(idolId)
    ? followed.filter((id) => id !== idolId)
    : [...followed, idolId]
  localStorage.setItem(FOLLOWED_KEY, JSON.stringify(updated))
  return updated
}
