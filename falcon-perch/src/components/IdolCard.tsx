import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import type { Idol } from '../types'
import { SPORT_THEMES } from '../theme/sportThemes'

interface IdolCardProps {
  idol: Idol
  isFollowed?: boolean
  onToggleFollow?: (id: string, e: React.MouseEvent) => void
}

export function IdolCard({ idol, isFollowed = false, onToggleFollow }: IdolCardProps) {
  const [imgError, setImgError] = useState(false)
  const theme = SPORT_THEMES[idol.sport] ?? SPORT_THEMES.football

  // Encode URI safely for filenames with spaces (e.g. pv sindhu.jpeg)
  const candidateImg = idol.image_url
    ? encodeURI(decodeURI(idol.image_url))
    : idol.slug
      ? `/idols/${encodeURIComponent(idol.slug)}.jpeg`
      : ''

  return (
    <motion.div
      whileHover={{ scale: 1.08, y: -8 }}
      transition={{ type: 'spring', stiffness: 350, damping: 22 }}
      className="relative shrink-0 w-[260px] h-[380px] rounded-3xl overflow-hidden cursor-pointer select-none border-2 transition-shadow group"
      style={{
        borderColor: theme.borderColor,
        boxShadow: `0 10px 30px -10px ${theme.glowColor}`,
      }}
    >
      <Link to={`/idols/${idol.id}`} className="block w-full h-full">
        {/* Background Artwork: Photo or Stylized Sport Placeholder */}
        {!imgError && candidateImg ? (
          <img
            src={candidateImg}
            alt={idol.name}
            onError={() => setImgError(true)}
            className="w-full h-full object-cover object-top filter brightness-95 group-hover:brightness-105 group-hover:scale-105 transition-all duration-500"
          />
        ) : (
          <div
            className="w-full h-full relative flex flex-col justify-between p-6 overflow-hidden"
            style={{ background: theme.bgGradient }}
          >
            {/* Athlete Silhouette Artwork */}
            <svg
              className="absolute -right-6 -bottom-6 w-56 h-56 opacity-25 mix-blend-overlay pointer-events-none"
              viewBox="0 0 100 100"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle cx="50" cy="24" r="16" fill="#fff" />
              <path d="M 20,95 Q 35,50 50,45 Q 65,50 80,95 Z" fill="#fff" />
            </svg>

            {/* Giant Jersey Number in Background */}
            <div
              className="absolute top-12 -left-4 text-[130px] font-black leading-none text-white/10 select-none pointer-events-none"
              style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
            >
              {idol.jersey_number ?? 0}
            </div>

            {/* Huge Initials */}
            <div className="relative z-10 pt-8 flex items-center justify-center h-44">
              <div
                className="text-7xl font-black text-white/80 tracking-tighter drop-shadow-md"
                style={{ fontFamily: "'Anton', sans-serif" }}
              >
                {idol.name
                  .split(' ')
                  .map((n) => n[0])
                  .join('')}
              </div>
            </div>
          </div>
        )}

        {/* Gradient Overlay for Readable Text */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-black/20 pointer-events-none" />

        {/* Top Badges: Sport pill + Rating */}
        <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-20 pointer-events-none">
          <div
            className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider text-white shadow-md flex items-center gap-1.5"
            style={{
              background: theme.primaryColor,
              boxShadow: `0 3px 0 ${theme.btnShadow}`,
            }}
          >
            <span>{theme.icon}</span>
            <span>{idol.sport}</span>
          </div>

          {idol.rating && (
            <div className="px-2.5 py-1 rounded-full bg-slate-900/80 backdrop-blur-md border border-yellow-400/50 text-yellow-300 text-xs font-black shadow flex items-center gap-1">
              <span className="text-[10px]">★</span>
              <span>{idol.rating}</span>
            </div>
          )}
        </div>

        {/* Play Icon hover overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-20 pointer-events-none">
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center text-slate-950 text-2xl font-black shadow-2xl transform scale-90 group-hover:scale-110 transition-transform"
            style={{
              background: theme.accentColor,
              boxShadow: `0 0 25px ${theme.accentColor}`,
            }}
          >
            ▶
          </div>
        </div>

        {/* Bottom Metadata: Name, Tagline, Follow heart */}
        <div className="absolute bottom-0 left-0 right-0 p-5 z-20">
          <div className="flex items-end justify-between gap-2">
            <div className="min-w-0">
              <h3
                className="text-2xl font-black text-white leading-tight drop-shadow tracking-wide truncate"
                style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
              >
                {idol.name}
              </h3>
              <p className="text-xs text-yellow-300 font-semibold truncate mt-0.5">
                {idol.signature_move || idol.titles || `${idol.sport.toUpperCase()} PRO`}
              </p>
              {idol.followers_count && (
                <div className="text-[10px] text-slate-400 font-mono mt-1">
                  {idol.followers_count} Athletes Studying
                </div>
              )}
            </div>

            {/* Follow Heart Button (clickable separately) */}
            <button
              type="button"
              aria-label={isFollowed ? 'Unfollow' : 'Follow'}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onToggleFollow?.(idol.id, e)
              }}
              className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg transition-transform active:scale-90 shadow-lg ${isFollowed
                  ? 'bg-rose-500 text-white shadow-rose-500/50'
                  : 'bg-white/20 hover:bg-white/30 text-white backdrop-blur-md border border-white/20'
                }`}
            >
              {isFollowed ? '❤️' : '🤍'}
            </button>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

