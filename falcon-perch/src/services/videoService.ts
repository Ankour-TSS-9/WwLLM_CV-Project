import { mockVideos } from '../mock/videos'
import type { Video } from '../types'

export async function getVideos(filters: { sport?: Video['sport']; idolId?: string } = {}): Promise<Video[]> {
  return mockVideos.filter((video) => {
    return (!filters.sport || video.sport === filters.sport)
      && (!filters.idolId || video.idol_id === filters.idolId)
  })
}
