import { useState, useEffect } from 'react'
import type { MouseEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { SPORTS, type Sport, type Idol, type User, type OnboardingProfile } from '../types'
import { getSportTheme } from '../theme/sportThemes'
import { SportFieldBackground, FloatingSportObject, TrophyBadge } from '../theme/SportVisuals'
import { ScoreboardCard } from '../components/ScoreboardCard'
import { HeroLoginCard } from '../components/HeroLoginCard'
import { IdolCarousel } from '../components/IdolCarousel'
import { HowItWorks } from '../components/HowItWorks'
import { PathwayMiniMap } from '../components/PathwayMiniMap'
import { StatsStrip } from '../components/StatsStrip'
import { Navbar } from '../components/Navbar'
import * as idolService from '../services/idolService'
import * as authService from '../services/authService'

interface LandingPageProps {
  user?: User | null
  profile?: OnboardingProfile | null
  onGuestLogin?: () => Promise<void>
  onUserLogin?: (user: User, profile: OnboardingProfile) => Promise<void>
}

export function LandingPage({ user, profile, onGuestLogin, onUserLogin }: LandingPageProps) {
  const [selectedSport, setSelectedSport] = useState<Sport>(profile?.preferredSport ?? 'football')
  const [idols, setIdols] = useState<Idol[]>([])
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const [showPreviewPro, setShowPreviewPro] = useState(false)
  const navigate = useNavigate()

  const currentTheme = getSportTheme(selectedSport)

  useEffect(() => {
    let active = true
    async function loadData() {
      const data = await idolService.getIdols()
      if (active) setIdols(data)
    }
    void loadData()
    return () => {
      active = false
    }
  }, [])

  function handleMouseMove(e: MouseEvent) {
    const { clientX, clientY } = e
    const { innerWidth, innerHeight } = window
    setMousePos({
      x: (clientX / innerWidth - 0.5) * 30,
      y: (clientY / innerHeight - 0.5) * 30,
    })
  }

  async function handleGuest() {
    if (onGuestLogin) {
      await onGuestLogin()
    } else {
      await authService.loginAsGuest()
      navigate('/dashboard')
    }
  }

  async function handleCardLoginSuccess(nextUser: User, nextProfile: OnboardingProfile) {
    if (onUserLogin) {
      await onUserLogin(nextUser, nextProfile)
    } else {
      navigate('/dashboard')
    }
  }

  return (
    <div
      onMouseMove={handleMouseMove}
      className="min-h-screen text-slate-100 overflow-x-hidden selection:bg-yellow-400 selection:text-slate-950"
      style={{
        background: '#090d16',
        fontFamily: "'Poppins', sans-serif",
      }}
    >
      {/* Sticky Navigation */}
      <Navbar user={user} onGuestLogin={handleGuest} />

      {/* HERO SECTION */}
      <section className="relative min-h-[calc(100vh-80px)] flex flex-col justify-between overflow-hidden pt-6 pb-16 px-4 sm:px-8">
        {/* Dynamic Sport Stadium/Court Background */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedSport}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6 }}
            className="absolute inset-0 z-0 pointer-events-none"
            style={{ background: currentTheme.bgGradient }}
          >
            {/* Sport Court/Pitch Illustrated SVG lines */}
            <SportFieldBackground sport={selectedSport} />

            {/* Glowing radial ambient lights */}
            <div
              className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl opacity-30 pointer-events-none"
              style={{ background: currentTheme.primaryColor }}
            />
            <div
              className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full blur-3xl opacity-25 pointer-events-none"
              style={{ background: currentTheme.accentColor }}
            />
          </motion.div>
        </AnimatePresence>

        {/* Floating animated Confetti & Star Dust particles */}
        <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
          {Array.from({ length: 18 }).map((_, i) => (
            <motion.div
              key={i}
              initial={{
                x: Math.random() * 1200,
                y: Math.random() * 800,
                scale: 0.6 + Math.random() * 0.8,
              }}
              animate={{
                y: [Math.random() * 800, Math.random() * 800 - 100],
                rotate: [0, 360],
              }}
              transition={{
                duration: 10 + Math.random() * 15,
                repeat: Infinity,
                ease: 'linear',
              }}
              className="absolute w-3 h-3 rounded-sm opacity-40"
              style={{
                background:
                  i % 3 === 0 ? '#facc15' : i % 3 === 1 ? '#38bdf8' : '#ec4899',
              }}
            />
          ))}
        </div>

        <div className="relative z-20 max-w-[1400px] mx-auto w-full">
          {/* Sport Switcher Row of 8 Pill Buttons with Icons */}
          <div className="flex items-center justify-center gap-2 sm:gap-3 flex-wrap mb-8 sm:mb-12">
            {SPORTS.map((sport) => {
              const theme = getSportTheme(sport)
              const isSelected = sport === selectedSport

              return (
                <button
                  key={sport}
                  type="button"
                  onClick={() => setSelectedSport(sport)}
                  className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-2xl font-black text-xs sm:text-sm uppercase tracking-wider transition-all active:scale-95 cursor-pointer ${
                    isSelected
                      ? 'text-slate-950 scale-105 shadow-xl'
                      : 'bg-slate-900/70 hover:bg-slate-800/80 text-white/80 border border-white/10'
                  }`}
                  style={{
                    background: isSelected
                      ? `linear-gradient(135deg, ${theme.primaryColor}, ${theme.accentColor})`
                      : undefined,
                    boxShadow: isSelected
                      ? `0 6px 0 ${theme.btnShadow}, 0 0 25px ${theme.glowColor}`
                      : undefined,
                    border: isSelected ? '2px solid rgba(255,255,255,0.6)' : undefined,
                  }}
                >
                  <span className="text-base sm:text-lg">{theme.icon}</span>
                  <span>{theme.name}</span>
                </button>
              )
            })}
          </div>

          {/* Main Hero Split Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
            {/* Left Hero Headline & CTAs */}
            <div className="lg:col-span-6 flex flex-col items-center lg:items-start text-center lg:text-left">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-white font-extrabold text-xs uppercase tracking-widest mb-4 shadow-sm">
                <span className="text-yellow-400">⚡</span>
                <span>AI Computer Vision + Pro Kinematics</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>

              {/* Big Bold Headline */}
              <h1
                className="text-5xl sm:text-6xl md:text-7xl xl:text-8xl font-black leading-[0.92] tracking-tight text-white uppercase drop-shadow-xl"
                style={{
                  fontFamily: "'Anton', 'Bebas Neue', sans-serif",
                  textShadow: '0 4px 20px rgba(0,0,0,0.6)',
                }}
              >
                PLAY LIKE <br />
                <span className={`bg-gradient-to-r ${currentTheme.headlineAccent} bg-clip-text text-transparent`}>
                  YOUR IDOLS.
                </span> <br />
                TRAIN LIKE A PRO.
              </h1>

              {/* Subtitle */}
              <p className="mt-5 text-slate-200 text-sm sm:text-base md:text-lg max-w-xl font-medium leading-relaxed drop-shadow">
                Log in to calibrate your game, match your release velocity frame-by-frame against world champions, and advance from school pitch to the national combine.
              </p>

              {/* Two Big 3D Buttons (Duolingo Style 3D Press Effect) */}
              <div className="flex flex-col sm:flex-row items-center gap-4 mt-8 w-full sm:w-auto">
                <Link
                  to="/auth"
                  className="w-full sm:w-auto px-8 py-4 rounded-3xl font-black text-slate-950 text-sm sm:text-base uppercase tracking-wider bg-gradient-to-r from-yellow-400 via-amber-300 to-yellow-500 hover:from-yellow-300 hover:to-amber-200 transition-all active:translate-y-1 shadow-2xl flex items-center justify-center gap-2 cursor-pointer border-2 border-white/40"
                  style={{
                    boxShadow: '0 6px 0 #b45309, 0 0 30px rgba(251, 191, 36, 0.6)',
                  }}
                >
                  <span>GET STARTED FREE</span>
                  <span className="text-lg">⚡</span>
                </Link>

                <button
                  type="button"
                  onClick={handleGuest}
                  className="w-full sm:w-auto px-8 py-4 rounded-3xl font-black text-white text-sm sm:text-base uppercase tracking-wider bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 transition-all active:translate-y-1 shadow-2xl flex items-center justify-center gap-2 cursor-pointer border-2 border-white/30"
                  style={{
                    boxShadow: '0 6px 0 #064e3b, 0 0 25px rgba(16, 185, 129, 0.4)',
                  }}
                >
                  <span>CONTINUE AS GUEST</span>
                  <span className="text-lg">🎮</span>
                </button>
              </div>

              {/* Trust Indicators */}
              <div className="flex items-center gap-4 mt-6 text-xs text-white/80 font-bold">
                <div className="flex items-center gap-1 text-yellow-300">
                  <span>★★★★★</span>
                  <span className="text-white ml-1">4.9/5 RATING</span>
                </div>
                <span>•</span>
                <span>2 FREE ANALYSES ON SIGN UP</span>
              </div>
            </div>

            {/* Right Hero: Login / Check-In Card FIRST, then personalized Scoreboard comes based on login */}
            <div className="lg:col-span-6 relative flex items-center justify-center">
              {/* Floating Sports Equipment (Parallax on mouse move) */}
              <motion.div
                style={{
                  x: mousePos.x * -1.2,
                  y: mousePos.y * -1.2,
                }}
                className="absolute -top-12 -left-8 sm:-left-12 z-30 pointer-events-none drop-shadow-2xl"
              >
                <motion.div
                  animate={{ y: [0, -14, 0], rotate: [0, 8, -4, 0] }}
                  transition={{ duration: 4.5, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <FloatingSportObject
                    type={currentTheme.floatingObject.type}
                    className="w-20 h-20 sm:w-28 sm:h-28"
                  />
                </motion.div>
              </motion.div>

              {/* Floating Golden Trophy at top right */}
              <motion.div
                style={{
                  x: mousePos.x * 0.8,
                  y: mousePos.y * 0.8,
                }}
                className="absolute -top-8 -right-4 sm:-right-8 z-30 pointer-events-none"
              >
                <motion.div
                  animate={{ rotate: [-6, 6, -6], y: [0, -8, 0] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <TrophyBadge size={54} color="#facc15" className="filter drop-shadow-xl" />
                </motion.div>
              </motion.div>

              {/* If not logged in, Login Card comes in the beginning. Once logged in, Head-to-Head comes based on it! */}
              <AnimatePresence mode="wait">
                {user ? (
                  <ScoreboardCard
                    key="logged-in-scoreboard"
                    theme={currentTheme}
                    user={user}
                    profile={profile}
                  />
                ) : showPreviewPro ? (
                  <ScoreboardCard
                    key="pro-preview-scoreboard"
                    theme={currentTheme}
                    user={null}
                    profile={null}
                    onSwitchToLogin={() => setShowPreviewPro(false)}
                  />
                ) : (
                  <HeroLoginCard
                    key="hero-login-gate"
                    theme={currentTheme}
                    onSuccess={handleCardLoginSuccess}
                    onPreviewPro={() => setShowPreviewPro(true)}
                  />
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </section>

      {/* IDOL CAROUSEL SECTION */}
      <IdolCarousel idols={idols} />

      {/* HOW IT WORKS SECTION */}
      <HowItWorks />

      {/* PATHWAY PREVIEW SECTION (SCORE HERO MAP) */}
      <PathwayMiniMap />

      {/* ANIMATED STATS STRIP */}
      <StatsStrip />

      {/* SITE FOOTER */}
      <footer className="py-12 px-4 sm:px-8 border-t border-white/10 bg-slate-950 text-center text-xs text-slate-400">
        <div className="max-w-[1200px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-yellow-400 text-slate-950 font-black flex items-center justify-center font-mono">
              F
            </span>
            <span
              className="text-base font-black text-white"
              style={{ fontFamily: "'Anton', sans-serif" }}
            >
              FALCON-PERCH
            </span>
          </div>
          <div>
            Not affiliated with any professional athlete or sports league. Videos, when available, are embedded from YouTube.
          </div>
          <div className="text-slate-500 font-mono">
            © 2026 FALCON-PERCH INTELLIGENCE
          </div>
        </div>
      </footer>
    </div>
  )
}
