import { Link, NavLink, useNavigate } from 'react-router-dom'
import * as authService from '../services/authService'
import type { User } from '../types'

interface NavbarProps {
  user?: User | null
  onGuestLogin?: () => Promise<void>
  onLogout?: () => Promise<void>
}

export function Navbar({ user, onGuestLogin, onLogout }: NavbarProps) {
  const navigate = useNavigate()

  async function handleGuest() {
    if (onGuestLogin) {
      await onGuestLogin()
    } else {
      await authService.loginAsGuest()
      navigate('/dashboard')
    }
  }

  async function handleLogout() {
    if (onLogout) {
      await onLogout()
    } else {
      await authService.logout()
    }
    navigate('/auth')
  }

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-slate-950/75 border-b border-white/10 transition-all">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-8 h-20 flex items-center justify-between gap-4">
        {/* Brand Crest */}
        <Link to="/" className="flex items-center gap-3 group">
          <div
            className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-yellow-400 via-amber-500 to-rose-500 flex items-center justify-center text-slate-950 font-black text-2xl shadow-lg transform group-hover:scale-105 group-hover:rotate-3 transition-transform"
            style={{
              fontFamily: "'Anton', sans-serif",
              boxShadow: '0 4px 0 #b45309, 0 0 20px rgba(245, 158, 11, 0.5)',
            }}
          >
            F
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span
                className="text-xl sm:text-2xl font-black tracking-wider text-white"
                style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
              >
                FALCON<span className="text-yellow-400">—</span>PERCH
              </span>
              <span className="px-1.5 py-0.5 rounded-md bg-yellow-400 text-slate-950 text-[9px] font-black uppercase tracking-tight">
                2.0
              </span>
            </div>
            <span className="text-[10px] tracking-widest text-emerald-400 font-mono font-bold uppercase">
              AI ATHLETE INTELLIGENCE
            </span>
          </div>
        </Link>

        {/* Public Nav Links */}
        <nav className="hidden md:flex items-center gap-1 p-1.5 rounded-full bg-slate-900/80 border border-white/10">
          <NavLink
            to="/idols"
            className={({ isActive }) =>
              `px-5 py-2 rounded-full text-xs font-black uppercase tracking-wider transition-all ${isActive
                ? 'bg-yellow-400 text-slate-950 shadow-md'
                : 'text-slate-200 hover:text-white hover:bg-white/10'
              }`
            }
          >
            🌟 Idols
          </NavLink>
          <NavLink
            to="/analyze"
            className={({ isActive }) =>
              `px-5 py-2 rounded-full text-xs font-black uppercase tracking-wider transition-all ${isActive
                ? 'bg-emerald-400 text-slate-950 shadow-md'
                : 'text-slate-200 hover:text-white hover:bg-white/10'
              }`
            }
          >
            ⚡ Analyze
          </NavLink>
          <NavLink
            to="/pathways"
            className={({ isActive }) =>
              `px-5 py-2 rounded-full text-xs font-black uppercase tracking-wider transition-all ${isActive
                ? 'bg-purple-500 text-white shadow-md'
                : 'text-slate-200 hover:text-white hover:bg-white/10'
              }`
            }
          >
            🗺️ Pathways
          </NavLink>
        </nav>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          {user ? (
            // Logged-in state: show name/guest badge + logout
            <div className="flex items-center gap-2">
              {user.isGuest && (
                <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-black text-[10px] uppercase tracking-wider">
                  🎮 Guest Mode
                </span>
              )}
              <Link
                to="/dashboard"
                className="px-5 py-2.5 rounded-2xl bg-yellow-400 hover:bg-yellow-300 text-slate-950 font-black text-xs uppercase tracking-wider transition-transform active:translate-y-1 shadow-md"
                style={{ boxShadow: '0 4px 0 #b45309' }}
              >
                Dashboard ↗
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="px-4 py-2.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-white font-black text-xs uppercase tracking-wider border border-white/20 transition-colors cursor-pointer"
              >
                {user.isGuest ? 'Exit' : 'Log out'}
              </button>
            </div>
          ) : (
            // Logged-out state: guest demo + sign-in + get started
            <>
              <button
                type="button"
                onClick={handleGuest}
                className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-xs uppercase tracking-wider transition-transform active:translate-y-1 shadow-md cursor-pointer"
                style={{ boxShadow: '0 4px 0 #064e3b' }}
              >
                <span>🎮</span> Guest Demo
              </button>

              <Link
                to="/auth"
                className="text-xs font-bold text-slate-200 hover:text-yellow-300 px-3 py-2 transition-colors uppercase tracking-wider"
              >
                Sign in
              </Link>
              <Link
                to="/auth"
                className="px-5 py-2.5 rounded-2xl bg-gradient-to-r from-yellow-400 to-amber-400 hover:from-yellow-300 hover:to-amber-300 text-slate-950 font-black text-xs uppercase tracking-wider transition-transform active:translate-y-1 shadow-lg"
                style={{ boxShadow: '0 4px 0 #b45309, 0 0 20px rgba(251, 191, 36, 0.4)' }}
              >
                Get Started ⚡
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
