import { useEffect, useRef, useState } from 'react'
import type { Idol, Sport } from '../types'
import { SPORTS } from '../types'
import { IdolCard } from './IdolCard'
import * as idolService from '../services/idolService'

interface IdolCarouselProps {
  idols: Idol[]
}

export function IdolCarousel({ idols }: IdolCarouselProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [isPaused, setIsPaused] = useState(false)
  const [selectedSport, setSelectedSport] = useState<Sport | 'all'>('all')
  const [followedIds, setFollowedIds] = useState<string[]>([])

  useEffect(() => {
    let active = true
    async function loadFollowed() {
      const ids = await idolService.getFollowedIdolIds()
      if (active) setFollowedIds(ids)
    }
    void loadFollowed()
    return () => {
      active = false
    }
  }, [])

  // Silky smooth, slow, and calm auto-scrolling with requestAnimationFrame
  useEffect(() => {
    let animId: number
    let lastTime: number | null = null

    function step(currentTime: number) {
      if (lastTime !== null && !isPaused && scrollContainerRef.current) {
        const delta = Math.min(currentTime - lastTime, 50)
        const el = scrollContainerRef.current

        // Very calm 28px per second drift
        el.scrollLeft += (28 * delta) / 1000

        // If reaching end, smoothly wrap back to start
        if (el.scrollLeft + el.clientWidth >= el.scrollWidth - 10) {
          el.scrollLeft = 0
        }
      }
      lastTime = currentTime
      animId = requestAnimationFrame(step)
    }

    animId = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animId)
  }, [isPaused])

  const filteredIdols =
    selectedSport === 'all'
      ? idols
      : idols.filter((idol) => idol.sport === selectedSport)

  function scroll(direction: 'left' | 'right') {
    const el = scrollContainerRef.current
    if (!el) return
    const offset = direction === 'left' ? -340 : 340
    el.scrollBy({ left: offset, behavior: 'smooth' })
  }

  async function handleToggleFollow(id: string) {
    const next = await idolService.toggleFollowIdol(id)
    setFollowedIds(next)
  }

  return (
    <section className="relative py-16 px-4 sm:px-8 max-w-[1400px] mx-auto overflow-hidden">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-yellow-400/10 border border-yellow-400/30 text-yellow-300 text-xs font-black uppercase tracking-widest mb-3">
            <span>★</span> WORLD-CLASS BENCHMARKS <span>★</span>
          </div>
          <h2
            className="text-4xl sm:text-5xl font-black text-white tracking-tight uppercase"
            style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
          >
            FOLLOW YOUR IDOLS
          </h2>
          <p className="text-slate-300 text-sm sm:text-base max-w-xl mt-1">
            Study signature moves, footwork, and biomechanics from the greatest athletes across 8 sports.
          </p>
        </div>

        {/* Sport filter tabs & Arrow buttons */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-slate-900/80 border border-white/10 overflow-x-auto max-w-full">
            <button
              type="button"
              onClick={() => setSelectedSport('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                selectedSport === 'all'
                  ? 'bg-yellow-400 text-slate-950 shadow-md'
                  : 'text-slate-300 hover:text-white hover:bg-white/5'
              }`}
            >
              All Sports
            </button>
            {SPORTS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSelectedSport(s)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition-colors cursor-pointer whitespace-nowrap ${
                  selectedSport === s
                    ? 'bg-yellow-400 text-slate-950 shadow-md'
                    : 'text-slate-300 hover:text-white hover:bg-white/5'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Scroll left"
              onClick={() => scroll('left')}
              className="w-11 h-11 rounded-2xl bg-slate-800/80 hover:bg-slate-700 text-white flex items-center justify-center font-black text-lg border border-white/10 shadow-lg active:scale-95 transition-all cursor-pointer"
            >
              ◀
            </button>
            <button
              type="button"
              aria-label="Scroll right"
              onClick={() => scroll('right')}
              className="w-11 h-11 rounded-2xl bg-yellow-400 hover:bg-yellow-300 text-slate-950 flex items-center justify-center font-black text-lg border-2 border-yellow-500 shadow-lg active:scale-95 transition-all cursor-pointer"
              style={{ boxShadow: '0 4px 0 #b45309' }}
            >
              ▶
            </button>
          </div>
        </div>
      </div>

      {/* Smooth, calm drift carousel strip (no snap classes to prevent shaking) */}
      <div
        ref={scrollContainerRef}
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        className="flex gap-6 overflow-x-auto pb-8 pt-4 scrollbar-none"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          scrollBehavior: 'auto',
        }}
      >
        {filteredIdols.map((idol) => (
          <div key={idol.id} className="shrink-0">
            <IdolCard
              idol={idol}
              isFollowed={followedIds.includes(idol.id)}
              onToggleFollow={handleToggleFollow}
            />
          </div>
        ))}
      </div>
    </section>
  )
}
