import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import type { User, OnboardingProfile, Sport } from '../types'
import { SPORTS } from '../types'
import { getSportTheme } from '../theme/sportThemes'
import { SportFieldBackground, FloatingSportObject, TrophyBadge } from '../theme/SportVisuals'
import { ScoreboardCard } from '../components/ScoreboardCard'
import { PathwayMiniMap } from '../components/PathwayMiniMap'
import * as profileService from '../services/profileService'

interface DashboardPageProps {
  user: User
  profile: OnboardingProfile
  onProfileUpdate?: (profile: OnboardingProfile) => Promise<void>
}

export function DashboardPage({ user, profile, onProfileUpdate }: DashboardPageProps) {
  const [currentSport, setCurrentSport] = useState<Sport>(profile.preferredSport)

  const activeTheme = getSportTheme(currentSport)

  async function handleSportSwitch(sport: Sport) {
    if (sport === currentSport) return
    setCurrentSport(sport)
    const updated: OnboardingProfile = {
      ...profile,
      preferredSport: sport,
    }
    await profileService.saveProfile(updated)
    if (onProfileUpdate) {
      await onProfileUpdate(updated)
    }
  }

  const firstName = user.name.split(' ')[0]

  return (
    <div
      className="relative min-h-[calc(100vh-76px)] text-slate-100 overflow-hidden pb-20 transition-colors duration-700"
      style={{
        background: activeTheme.bgGradient,
        fontFamily: "'Poppins', sans-serif",
      }}
    >
      {/* Background Sport Court / Pitch / Track Illustration */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentSport}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.6 }}
          className="absolute inset-0 pointer-events-none z-0"
        >
          <SportFieldBackground sport={currentSport} />
          {/* Ambient ambient glow circles */}
          <div
            className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full blur-3xl opacity-35"
            style={{ background: activeTheme.primaryColor }}
          />
          <div
            className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full blur-3xl opacity-30"
            style={{ background: activeTheme.accentColor }}
          />
        </motion.div>
      </AnimatePresence>

      <div className="relative z-10 max-w-[1400px] mx-auto px-4 sm:px-8 pt-8">
        {/* Top Sport Switcher Pill Bar for Quick Customization */}
        <div className="flex items-center justify-between gap-4 flex-wrap mb-8 pb-4 border-b border-white/15">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-extrabold tracking-widest text-yellow-300">
              ACTIVE ARENA SPORT:
            </span>
            <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-black/40 backdrop-blur-md border border-white/20 overflow-x-auto max-w-full">
              {SPORTS.map((sport) => {
                const sTheme = getSportTheme(sport)
                const isSelected = sport === currentSport
                return (
                  <button
                    key={sport}
                    type="button"
                    onClick={() => handleSportSwitch(sport)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-black text-xs uppercase tracking-wider transition-all cursor-pointer whitespace-nowrap ${
                      isSelected
                        ? 'text-slate-950 shadow-md'
                        : 'text-white/80 hover:text-white hover:bg-white/10'
                    }`}
                    style={{
                      background: isSelected
                        ? `linear-gradient(135deg, ${sTheme.primaryColor}, ${sTheme.accentColor})`
                        : undefined,
                      boxShadow: isSelected
                        ? `0 3px 0 ${sTheme.btnShadow}`
                        : undefined,
                    }}
                  >
                    <span>{sTheme.icon}</span>
                    <span>{sTheme.name}</span>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/settings"
              className="text-xs font-bold text-white/80 hover:text-yellow-300 uppercase tracking-wider bg-white/10 px-3.5 py-1.5 rounded-xl border border-white/20 hover:bg-white/20 transition-colors"
            >
              ⚙ Edit Profile
            </Link>
          </div>
        </div>

        {/* Hero Athlete HUD Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center mb-12">
          {/* Left: Athlete Passport & Greeting */}
          <div className="lg:col-span-6 flex flex-col items-center lg:items-start text-center lg:text-left">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/15 backdrop-blur-md border border-white/25 text-white font-black text-xs uppercase tracking-widest mb-3 shadow-md">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>{activeTheme.name.toUpperCase()} ATHLETE PASSPORT · {profile.level.toUpperCase()} RANK</span>
            </div>

            <h1
              className="text-5xl sm:text-6xl lg:text-7xl font-black text-white uppercase tracking-tight leading-[0.95] drop-shadow-xl"
              style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
            >
              WELCOME BACK, <br />
              <span className={`bg-gradient-to-r ${activeTheme.headlineAccent} bg-clip-text text-transparent`}>
                {firstName}!
              </span>
            </h1>

            <p className="mt-4 text-slate-200 text-sm sm:text-base max-w-xl font-medium leading-relaxed drop-shadow">
              Your personalized {activeTheme.name} training ground is active. Analyze new video reps, track your kinematics against {activeTheme.scoreboard.proName}, and continue climbing your pathway.
            </p>

            {/* Athlete Bio Chips */}
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-2.5 mt-6">
              <span className="px-3.5 py-1.5 rounded-xl bg-slate-950/70 border border-white/20 text-xs font-bold text-white flex items-center gap-1.5">
                <span>🎂</span> Age: {profile.age}
              </span>
              <span className="px-3.5 py-1.5 rounded-xl bg-slate-950/70 border border-white/20 text-xs font-bold text-emerald-300 flex items-center gap-1.5 capitalize">
                <span>⚡</span> Role: {profile.role || 'Player'}
              </span>
              <span className="px-3.5 py-1.5 rounded-xl bg-slate-950/70 border border-white/20 text-xs font-bold text-yellow-300 flex items-center gap-1.5">
                <span>⏳</span> Exp: {profile.yearsPlaying} Years
              </span>
              <span className="px-3.5 py-1.5 rounded-xl bg-slate-950/70 border border-white/20 text-xs font-bold text-cyan-300 flex items-center gap-1.5 uppercase">
                <span>🎯</span> Goal: {profile.goal}
              </span>
            </div>

            {/* Previous Experiences Highlight */}
            {profile.experience_details && (
              <div className="mt-4 p-3.5 rounded-2xl bg-black/40 backdrop-blur-md border border-yellow-400/30 text-xs font-medium text-slate-200 max-w-xl">
                <strong className="text-yellow-300 font-bold uppercase tracking-wider block mb-1">
                  🏅 Track Record & Past Experience:
                </strong>
                "{profile.experience_details}"
              </div>
            )}

            {/* Quick CTAs */}
            <div className="flex items-center gap-4 mt-8 flex-wrap">
              <Link
                to="/analyze"
                className="px-8 py-3.5 rounded-2xl font-black text-slate-950 text-xs sm:text-sm uppercase tracking-wider bg-gradient-to-r from-yellow-400 to-amber-400 hover:from-yellow-300 hover:to-amber-300 transition-all active:translate-y-1 shadow-xl flex items-center gap-2 cursor-pointer border-2 border-white/40"
                style={{
                  boxShadow: '0 5px 0 #b45309, 0 0 25px rgba(251, 191, 36, 0.45)',
                }}
              >
                <span>ANALYZE MY VIDEO</span>
                <span>⚡</span>
              </Link>

              <Link
                to="/pathways"
                className="px-8 py-3.5 rounded-2xl font-black text-white text-xs sm:text-sm uppercase tracking-wider bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 transition-all active:translate-y-1 shadow-xl flex items-center gap-2 cursor-pointer border-2 border-white/30"
                style={{
                  boxShadow: '0 5px 0 #064e3b, 0 0 20px rgba(16, 185, 129, 0.4)',
                }}
              >
                <span>MY PATHWAY MAP</span>
                <span>🗺️</span>
              </Link>
            </div>
          </div>

          {/* Right: Floating Sport Object & Personalized Scoreboard Card */}
          <div className="lg:col-span-6 relative flex items-center justify-center">
            {/* Floating Equipment Icon for this sport */}
            <motion.div
              animate={{ y: [0, -12, 0], rotate: [0, 8, -4, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute -top-10 -left-6 z-30 pointer-events-none drop-shadow-2xl"
            >
              <FloatingSportObject
                type={activeTheme.floatingObject.type}
                className="w-20 h-20 sm:w-24 sm:h-24"
              />
            </motion.div>

            {/* Floating Trophy */}
            <motion.div
              animate={{ rotate: [-6, 6, -6], y: [0, -6, 0] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute -top-8 -right-4 z-30 pointer-events-none"
            >
              <TrophyBadge size={48} color="#facc15" className="filter drop-shadow-xl" />
            </motion.div>

            {/* The Live Personalized Scoreboard */}
            <ScoreboardCard
              theme={activeTheme}
              user={user}
              profile={profile}
            />
          </div>
        </div>

        {/* 3 Game-Like Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-12">
          {/* Card 1: Analyze */}
          <Link
            to="/analyze"
            className="group relative rounded-3xl p-6 border-2 transition-all duration-300 hover:-translate-y-2 overflow-hidden shadow-xl"
            style={{
              background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.85), rgba(6, 78, 59, 0.9))',
              borderColor: 'rgba(52, 211, 153, 0.4)',
              boxShadow: '0 15px 35px -10px rgba(16, 185, 129, 0.3)',
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="font-mono text-xs font-black text-emerald-400">01 / DRILLS</span>
              <span className="text-2xl group-hover:scale-120 transition-transform">📹</span>
            </div>
            <h3
              className="text-2xl font-black text-white uppercase tracking-wide mb-1"
              style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
            >
              Analyze Your Video
            </h3>
            <p className="text-xs text-slate-300 font-medium leading-relaxed mb-4">
              Upload your {activeTheme.name} practice reps. Our pose-tracker checks angles against {activeTheme.scoreboard.proName}.
            </p>
            <span className="inline-flex items-center gap-1 text-xs font-black uppercase text-emerald-300 tracking-wider">
              Launch Video Studio ↗
            </span>
          </Link>

          {/* Card 2: Idols */}
          <Link
            to="/idols"
            className="group relative rounded-3xl p-6 border-2 transition-all duration-300 hover:-translate-y-2 overflow-hidden shadow-xl"
            style={{
              background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.85), rgba(88, 28, 135, 0.9))',
              borderColor: 'rgba(168, 85, 247, 0.4)',
              boxShadow: '0 15px 35px -10px rgba(168, 85, 247, 0.3)',
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="font-mono text-xs font-black text-purple-300">02 / BENCHMARK</span>
              <span className="text-2xl group-hover:scale-120 transition-transform">🌟</span>
            </div>
            <h3
              className="text-2xl font-black text-white uppercase tracking-wide mb-1"
              style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
            >
              Study {activeTheme.name} Greats
            </h3>
            <p className="text-xs text-slate-300 font-medium leading-relaxed mb-4">
              Explore signature footwork and mechanics from world champions in {activeTheme.name}.
            </p>
            <span className="inline-flex items-center gap-1 text-xs font-black uppercase text-purple-300 tracking-wider">
              Explore Idols Library ↗
            </span>
          </Link>

          {/* Card 3: Pathways */}
          <Link
            to="/pathways"
            className="group relative rounded-3xl p-6 border-2 transition-all duration-300 hover:-translate-y-2 overflow-hidden shadow-xl"
            style={{
              background: 'linear-gradient(145deg, rgba(15, 23, 42, 0.85), rgba(120, 53, 15, 0.9))',
              borderColor: 'rgba(251, 191, 36, 0.4)',
              boxShadow: '0 15px 35px -10px rgba(245, 158, 11, 0.3)',
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="font-mono text-xs font-black text-yellow-300">03 / ROADMAP</span>
              <span className="text-2xl group-hover:scale-120 transition-transform">🗺️</span>
            </div>
            <h3
              className="text-2xl font-black text-white uppercase tracking-wide mb-1"
              style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
            >
              Climb {activeTheme.name} Pathway
            </h3>
            <p className="text-xs text-slate-300 font-medium leading-relaxed mb-4">
              Check off your stage milestones and target your next {profile.goal} level trials.
            </p>
            <span className="inline-flex items-center gap-1 text-xs font-black uppercase text-yellow-300 tracking-wider">
              Open Score Hero Map ↗
            </span>
          </Link>
        </div>

        {/* Embedded Score Hero Pitch Map for their active sport */}
        <div className="my-12">
          <PathwayMiniMap />
        </div>
      </div>
    </div>
  )
}
