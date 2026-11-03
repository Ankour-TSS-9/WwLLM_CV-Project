import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import type { SportThemeConfig } from '../theme/sportThemes'
import { TrophyBadge } from '../theme/SportVisuals'
import type { User, OnboardingProfile } from '../types'

interface ScoreboardCardProps {
  theme: SportThemeConfig
  user?: User | null
  profile?: OnboardingProfile | null
  onSwitchToLogin?: () => void
}

function CounterNumber({ value, duration = 1.2 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    let startTime: number | null = null
    let frameId: number

    function step(timestamp: number) {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1)
      const easeOut = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(easeOut * value))
      if (progress < 1) {
        frameId = requestAnimationFrame(step)
      }
    }

    frameId = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frameId)
  }, [value, duration])

  return <span>{display}</span>
}

export function ScoreboardCard({ theme, user, profile, onSwitchToLogin }: ScoreboardCardProps) {
  const { scoreboard } = theme
  const [imageError, setImageError] = useState(false)

  // Reset image error state whenever theme/pro changes
  useEffect(() => {
    setImageError(false)
  }, [scoreboard.proSlug])

  const userName = user?.name ? `${user.name.split(' ')[0]} (You)` : 'You (Preview)'
  const userRole = profile?.role || (profile?.level ? `${profile.level} Rank` : 'Challenger Rank')
  const userAge = profile?.age ? `LVL ${profile.age}` : 'LVL 17'

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="relative w-full max-w-[560px] mx-auto rounded-3xl overflow-hidden p-6 sm:p-8 backdrop-blur-2xl shadow-2xl border-2 transition-colors duration-500"
      style={{
        background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.88) 0%, rgba(30, 27, 75, 0.92) 100%)',
        borderColor: theme.borderColor,
        boxShadow: `0 20px 60px -15px ${theme.glowColor}, 0 0 35px 2px ${theme.borderColor}`,
      }}
    >
      {/* Top Tournament Pill & Trophies (Reference 1 style) */}
      <div className="flex items-center justify-between gap-3 mb-6 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <TrophyBadge size={34} color={theme.accentColor} className="drop-shadow-lg" />
          <div>
            <div className="text-[10px] tracking-widest uppercase font-black text-yellow-300">
              OFFICIAL HEAD-TO-HEAD BENCHMARK
            </div>
            <div
              className="text-sm sm:text-base font-extrabold text-white tracking-wide"
              style={{ fontFamily: "'Bebas Neue', 'Anton', sans-serif" }}
            >
              {scoreboard.tournamentName}
            </div>
          </div>
        </div>

        {/* Sport Pill */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-semibold text-white/90">
          <span>{theme.icon}</span>
          <span className="text-[11px] font-bold tracking-wider uppercase">{theme.name}</span>
        </div>
      </div>

      {/* Matchup Banner: You vs Pro */}
      <div className="grid grid-cols-5 items-center gap-2 mb-6 text-center">
        {/* Left: You */}
        <div className="col-span-2 flex flex-col items-center">
          <div className="relative group">
            <div
              className="w-16 h-16 sm:w-20 sm:h-20 rounded-full p-1 border-2 border-emerald-400 shadow-lg flex items-center justify-center bg-gradient-to-tr from-emerald-600 to-teal-400"
              style={{ boxShadow: '0 0 20px rgba(52, 211, 153, 0.6)' }}
            >
              <div className="w-full h-full rounded-full bg-slate-900 flex items-center justify-center text-white text-lg sm:text-xl font-black">
                {user ? user.name[0]?.toUpperCase() : 'YOU'}
              </div>
            </div>
            <span className="absolute -bottom-2 -right-1 bg-emerald-500 text-slate-950 font-black text-[10px] px-2 py-0.5 rounded-full shadow">
              {userAge}
            </span>
          </div>
          <span className="mt-2.5 font-bold text-white text-sm sm:text-base tracking-wide truncate max-w-full">
            {userName}
          </span>
          <span className="text-[11px] text-emerald-300 font-medium truncate max-w-full capitalize">
            {userRole}
          </span>
        </div>

        {/* Center: VS Badge */}
        <div className="col-span-1 flex flex-col items-center justify-center">
          <div
            className="w-12 h-12 rounded-2xl bg-gradient-to-br from-yellow-400 to-amber-600 text-slate-950 flex items-center justify-center font-black text-xl shadow-xl transform rotate-3 hover:rotate-12 transition-transform cursor-pointer"
            style={{
              fontFamily: "'Anton', sans-serif",
              boxShadow: '0 4px 0 #b45309, 0 0 20px rgba(251, 191, 36, 0.6)',
            }}
          >
            VS
          </div>
          <span className="mt-1 text-[9px] uppercase tracking-wider text-white/60 font-semibold">
            METRICS
          </span>
        </div>

        {/* Right: Pro */}
        <div className="col-span-2 flex flex-col items-center">
          <div className="relative group">
            <div
              className="w-16 h-16 sm:w-20 sm:h-20 rounded-full p-1 border-2 shadow-lg flex items-center justify-center overflow-hidden bg-gradient-to-tr from-purple-600 to-blue-500"
              style={{
                borderColor: theme.accentColor,
                boxShadow: `0 0 20px ${theme.glowColor}`,
              }}
            >
              {!imageError ? (
                <img
                  src={scoreboard.proImage}
                  alt={scoreboard.proName}
                  onError={() => setImageError(true)}
                  className="w-full h-full object-cover rounded-full"
                />
              ) : (
                <div
                  className="w-full h-full rounded-full flex items-center justify-center font-black text-white text-lg"
                  style={{ background: theme.primaryColor }}
                >
                  {scoreboard.proName
                    .split(' ')
                    .map((n) => n[0])
                    .join('')}
                </div>
              )}
            </div>
            <span className="absolute -bottom-2 -left-1 bg-yellow-400 text-slate-950 font-black text-[10px] px-2 py-0.5 rounded-full shadow flex items-center gap-0.5">
              <span>★</span> PRO
            </span>
          </div>
          <span className="mt-2.5 font-bold text-white text-sm sm:text-base tracking-wide truncate max-w-full">
            {scoreboard.proName}
          </span>
          <span className="text-[11px] text-yellow-300 font-medium truncate max-w-full">
            {scoreboard.proRole.split('·')[0]}
          </span>
        </div>
      </div>

      {/* Main Score Display Bar (Overall Comparison) */}
      <div className="p-3.5 mb-5 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between">
        <div className="text-left">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold">Your Score</div>
          <div
            className="text-2xl sm:text-3xl font-black text-emerald-400"
            style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
          >
            <CounterNumber value={scoreboard.userRating} />
            <span className="text-xs text-white/50 ml-1 font-sans">/ 100</span>
          </div>
        </div>

        <div className="text-center">
          <div className="text-[10px] uppercase tracking-widest text-white/50 font-extrabold px-3 py-1 rounded-full bg-white/10">
            OVERALL TECH RATING
          </div>
        </div>

        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold">Pro Benchmark</div>
          <div
            className="text-2xl sm:text-3xl font-black text-yellow-400"
            style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
          >
            <CounterNumber value={scoreboard.proRating} />
            <span className="text-xs text-white/50 ml-1 font-sans">/ 100</span>
          </div>
        </div>
      </div>

      {/* Detailed Stat Rows (Reference 1 style with Left Value, Label, Right Value & Dual Progress Bars) */}
      <div className="space-y-3.5">
        {scoreboard.stats.map((stat, idx) => {
          const userPct = Math.min(stat.userVal, 100)
          const proPct = Math.min(stat.proVal, 100)
          return (
            <div key={idx} className="group">
              <div className="flex items-center justify-between text-xs sm:text-sm font-bold text-white mb-1.5">
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <span>{stat.userVal}</span>
                  {stat.unit && <span className="text-[10px] text-white/50">{stat.unit}</span>}
                </span>
                <span className="text-slate-300 font-semibold tracking-wide text-[11px] sm:text-xs uppercase">
                  {stat.label}
                </span>
                <span className="text-yellow-400 font-mono flex items-center gap-1">
                  <span>{stat.proVal}</span>
                  {stat.unit && <span className="text-[10px] text-white/50">{stat.unit}</span>}
                </span>
              </div>

              {/* Dual mirrored progress bar */}
              <div className="grid grid-cols-2 gap-2 h-2.5 rounded-full bg-black/40 p-0.5 border border-white/10 overflow-hidden">
                {/* Left bar (User) */}
                <div className="flex justify-end">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${userPct}%` }}
                    transition={{ duration: 1, delay: 0.1 * idx, ease: 'easeOut' }}
                    className="h-full rounded-full bg-gradient-to-l from-emerald-400 to-teal-500 shadow-sm"
                  />
                </div>
                {/* Right bar (Pro) */}
                <div className="flex justify-start">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${proPct}%` }}
                    transition={{ duration: 1, delay: 0.1 * idx, ease: 'easeOut' }}
                    className="h-full rounded-full bg-gradient-to-r from-yellow-400 to-amber-500 shadow-sm"
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Bottom Status & Switch Action */}
      <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs">
        {user ? (
          <div className="flex items-center gap-2 text-white/80">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-[11px] font-semibold">Calibrated for {user.name}</span>
          </div>
        ) : (
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-emerald-400 hover:text-emerald-300 font-bold text-[11px] flex items-center gap-1 cursor-pointer"
          >
            <span>← Sign in to save your personal score</span>
          </button>
        )}

        <div className="flex items-center gap-2">
          <span className="text-white/60 text-[11px]">Pro Delta:</span>
          <span className="px-2 py-0.5 rounded-md bg-yellow-400/20 text-yellow-300 font-bold font-mono text-xs border border-yellow-400/30">
            +{scoreboard.proRating - scoreboard.userRating} PTS GAP
          </span>
        </div>
      </div>
    </motion.div>
  )
}
