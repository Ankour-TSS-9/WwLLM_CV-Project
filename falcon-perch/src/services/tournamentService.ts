import { mockTournaments } from '../mock/tournaments'
import type { Sport, Tournament } from '../types'

export async function getTournaments(sport?: Sport): Promise<Tournament[]> {
  return sport ? mockTournaments.filter((tournament) => tournament.sport === sport) : mockTournaments
}
