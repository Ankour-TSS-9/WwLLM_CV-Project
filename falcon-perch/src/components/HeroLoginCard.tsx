import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import type { SportThemeConfig } from '../theme/sportThemes'
import { TrophyBadge } from '../theme/SportVisuals'
import * as authService from '../services/authService'
import * as profileService from '../services/profileService'
import type { User, OnboardingProfile } from '../types'

interface HeroLoginCardProps {
  theme: SportThemeConfig
  onSuccess: (user: User, profile: OnboardingProfile) => Promise<void>
  onPreviewPro: () => void
}

export function HeroLoginCard({ theme, onSuccess, onPreviewPro }: HeroLoginCardProps) {
  const [busy, setBusy] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const navigate = useNavigate()

  async function handleGuest() {
    setBusy(true)
    setErrorMsg('')
    try {
      const res = await authService.loginAsGuest()
      await onSuccess(res.user, res.profile)
    } catch {
      setErrorMsg('Failed to start guest session.')
    } finally {
      setBusy(false)
    }
  }

  async function handleLogin(e: FormEvent) {
    e.preventDefault()
    if (!email || !password) return
    setBusy(true)
    setErrorMsg('')
    try {
      const lower = email.toLowerCase()
      const user = await authService.login(lower, password)
      // Check if this user already has a saved profile.
      const existingProfile = await profileService.getProfileForEmail(lower)
      if (existingProfile) {
        // Returning user — hand them off to the parent so it sets state and navigates.
        await onSuccess(user, existingProfile)
      } else {
        // New email via landing card — send them to the full auth/signup page
        // so they get proper onboarding.
        navigate('/auth')
      }
    } catch {
      setErrorMsg('Sign-in failed. Please try again or continue as guest.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 15 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -15 }}
      transition={{ duration: 0.4 }}
      className="relative w-full max-w-[560px] mx-auto rounded-3xl overflow-hidden p-6 sm:p-8 backdrop-blur-2xl shadow-2xl border-2 transition-colors"
      style={{
        background: 'linear-gradient(155deg, rgba(15, 23, 42, 0.92) 0%, rgba(30, 27, 75, 0.95) 100%)',
        borderColor: theme.borderColor,
        boxShadow: `0 20px 60px -15px ${theme.glowColor}, 0 0 35px 2px ${theme.borderColor}`,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-6 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <TrophyBadge size={34} color={theme.accentColor} className="drop-shadow-lg" />
          <div>
            <div className="text-[10px] tracking-widest uppercase font-black text-yellow-300">
              STEP 1: ATHLETE CHECK-IN
            </div>
            <div
              className="text-lg sm:text-xl font-black text-white tracking-wide uppercase"
              style={{ fontFamily: "'Bebas Neue', 'Anton', sans-serif" }}
            >
              ENTER YOUR PERCH TO UNLOCK BENCHMARKS
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-semibold text-white/90">
          <span>{theme.icon}</span>
          <span className="text-[11px] font-bold tracking-wider uppercase">{theme.name}</span>
        </div>
      </div>

      <p className="text-xs sm:text-sm text-slate-300 font-medium mb-5 leading-relaxed">
        Log in to calibrate your sport, level, and generate your personal head-to-head scorecard against world champions.
      </p>

      {errorMsg && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-bold">
          {errorMsg}
        </div>
      )}

      {/* Guest Button */}
      <button
        type="button"
        disabled={busy}
        onClick={handleGuest}
        className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 hover:from-emerald-400 hover:to-teal-400 text-white font-black text-xs sm:text-sm uppercase tracking-wider shadow-xl border-2 border-white/30 flex items-center justify-center gap-3 transition-transform active:translate-y-1 cursor-pointer mb-5"
        style={{ boxShadow: '0 5px 0 #064e3b, 0 0 25px rgba(16, 185, 129, 0.45)' }}
      >
        <span className="text-xl">🎮</span>
        <div className="text-left">
          <div className="leading-tight">CONTINUE AS GUEST (1-CLICK DEMO)</div>
          <div className="text-[10px] font-medium text-emerald-100 normal-case">
            Instant Demo Athlete · No sign-up needed
          </div>
        </div>
      </button>

      <div className="flex items-center gap-3 mb-5 text-[10px] font-bold tracking-widest text-slate-400 uppercase">
        <div className="h-px flex-1 bg-white/15" />
        <span>OR SIGN IN WITH EMAIL</span>
        <div className="h-px flex-1 bg-white/15" />
      </div>

      {/* Login form (returning users only) */}
      <form onSubmit={handleLogin} className="space-y-3.5">
        <input
          type="email"
          placeholder="Athlete Email (e.g. you@example.com)"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full h-11 px-4 rounded-xl border border-white/15 bg-slate-900/90 text-white text-xs font-medium placeholder-slate-500 outline-none focus:border-yellow-400 transition-colors"
        />
        <input
          type="password"
          placeholder="Password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full h-11 px-4 rounded-xl border border-white/15 bg-slate-900/90 text-white text-xs font-medium placeholder-slate-500 outline-none focus:border-yellow-400 transition-colors"
        />

        <button
          type="submit"
          disabled={busy}
          className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-yellow-400 to-amber-400 hover:from-yellow-300 hover:to-amber-300 text-slate-950 font-black text-xs uppercase tracking-wider shadow-lg border-2 border-white/40 transition-transform active:translate-y-1 cursor-pointer flex items-center justify-center gap-2"
          style={{ boxShadow: '0 4px 0 #b45309, 0 0 20px rgba(251, 191, 36, 0.4)' }}
        >
          {busy ? 'Processing…' : 'Sign In & Unlock Scorecard ⚡'}
        </button>
      </form>

      {/* Footer links */}
      <div className="mt-5 pt-4 border-t border-white/10 flex items-center justify-between text-[11px] text-slate-400 font-semibold">
        <button
          type="button"
          onClick={() => navigate('/auth')}
          className="text-yellow-400 hover:underline cursor-pointer"
        >
          New here? Create an account →
        </button>

        <button
          type="button"
          onClick={onPreviewPro}
          className="text-cyan-300 hover:underline cursor-pointer flex items-center gap-1"
        >
          <span>Preview Pro Matchup</span>
          <span>↗</span>
        </button>
      </div>
    </motion.div>
  )
}
