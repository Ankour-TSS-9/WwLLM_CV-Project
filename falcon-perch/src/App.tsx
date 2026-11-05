import { useEffect, useState, type FormEvent } from 'react'
import {
  BrowserRouter,
  Link,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import * as authService from './services/authService'
import * as analysisService from './services/analysisService'
import * as profileService from './services/profileService'
import { SPORTS, type OnboardingProfile, type SkillLevel, type Sport, type User, type AthleteGoal } from './types'
import { LandingPage } from './pages/LandingPage'
import { DashboardPage } from './pages/DashboardPage'
import { AIFeaturesDemo } from './pages/AIFeaturesDemo'
import { getSportTheme } from './theme/sportThemes'
import './App.css'

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: '⌂' },
  { label: 'Idols', to: '/idols', icon: '◉' },
  { label: 'Analyze My Video', to: '/analyze', icon: '▶' },
  { label: 'Pathways', to: '/pathways', icon: '⌁' },
  { label: 'Insights', to: '/insights', icon: '↗' },
]

const laterRoutes: Record<string, { title: string; eyebrow: string; description: string }> = {
  '/idols': { title: 'Learn from the greats.', eyebrow: 'YOUR INSPIRATION', description: 'Explore athlete profiles and technique videos matched to your sport.' },
  '/analyze': { title: 'Make every rep count.', eyebrow: 'VIDEO ANALYSIS', description: 'Choose a reference video and compare your technique side by side.' },
  '/analyze-own': { title: 'Your game, in focus.', eyebrow: 'SOLO ANALYSIS', description: 'Upload a clip and get a closer look at your technique.' },
  '/pathways': { title: 'See where your sport can take you.', eyebrow: 'YOUR NEXT LEVEL', description: 'Explore practical routes from local play to the competitive stage.' },
  '/tournaments': { title: 'Find your next competition.', eyebrow: 'ON THE CALENDAR', description: 'Discover tournaments by sport, level and location.' },
  '/insights': { title: 'Progress you can see.', eyebrow: 'YOUR INSIGHTS', description: 'Your analysis history and progress will come together here.' },
  '/pricing': { title: 'More room to grow.', eyebrow: 'FALCON PERCH DIAMOND', description: 'Unlock more ways to understand your game and stay on track.' },
}

function Logo({ small = false }: { small?: boolean }) {
  return (
    <Link aria-label="Falcon-Perch home" className={`brand ${small ? 'brand-small' : ''}`} to="/">
      <span className="brand-mark">F</span>
      <span>FALCON<span className="brand-separator">—</span>PERCH</span>
    </Link>
  )
}

function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} | Falcon-Perch Intelligence`
  }, [title])
}

function Toast({ message }: { message: string }) {
  return message ? <div className="toast" role="status"><span className="pulse-dot" />{message}</div> : null
}

// ─── Auth Page ────────────────────────────────────────────────────────────────

function AuthPage({
  onAuthenticated,
  onGuest,
  notify,
}: {
  onAuthenticated: (user: User, isNewUser: boolean, returnPath?: string) => Promise<void>
  onGuest: (returnPath?: string) => Promise<void>
  notify: (message: string) => void
}) {
  usePageTitle('Sign in')
  const [signup, setSignup] = useState(false)
  const [busy, setBusy] = useState(false)
  const [selectedSport, setSelectedSport] = useState<Sport>('football')
  const location = useLocation()
  const returnPath = (location.state as { from?: { pathname: string } })?.from?.pathname

  const activeTheme = getSportTheme(selectedSport)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const email = String(data.get('email') ?? '').trim().toLowerCase()
    const password = String(data.get('password') ?? '')

    setBusy(true)
    try {
      if (signup) {
        // ── Signup: collect full profile from form, persist, go to dashboard ──
        const name = String(data.get('name') ?? '').trim()
        const age = Number(data.get('age') ?? 17)
        const level = (data.get('level') as SkillLevel) || 'intermediate'
        const role = String(data.get('role') ?? '').trim()
        const yearsPlaying = Number(data.get('yearsPlaying') ?? 3)
        const experience = String(data.get('experience') ?? '').trim()
        const goal = (data.get('goal') as AthleteGoal) || 'national'
        const country = String(data.get('country') ?? '').trim()
        const state = String(data.get('state') ?? '').trim()
        const city = String(data.get('city') ?? '').trim()

        const user = await authService.signup(email, password)
        // Override the email-derived name with the typed full name.
        if (name) {
          user.name = name
          // Persist the name override so it survives session restore.
          localStorage.setItem(`falcon-perch.identity.${email}`, JSON.stringify(user))
        }

        const newProfile: OnboardingProfile = {
          preferredSport: selectedSport,
          age,
          country: country || 'India',
          state: state || '',
          city: city || '',
          level,
          role: role || 'Player',
          yearsPlaying,
          goal,
          experience_details: experience || undefined,
        }
        await profileService.saveProfile(newProfile)
        await onAuthenticated(user, true, returnPath)
      } else {
        // ── Login: check for existing profile to decide route ──
        const user = await authService.login(email, password)
        const existingProfile = await profileService.getProfileForEmail(email)
        const isNew = !existingProfile
        await onAuthenticated(user, isNew, returnPath)
      }
    } finally {
      setBusy(false)
    }
  }

  async function handleGuest() {
    setBusy(true)
    try {
      await onGuest(returnPath)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main
      className="auth-page transition-colors duration-700"
      style={{
        background: `radial-gradient(ellipse at 35% 25%, ${activeTheme.primaryColor}22 0%, #090d16 80%)`,
      }}
    >
      <header className="auth-top">
        <Logo />
        <Link className="text-link" to="/">
          ← Back to Arena
        </Link>
      </header>

      <div className={`auth-layout ${signup ? '!grid-cols-1 max-w-[780px]' : ''}`}>
        {!signup && (
          <section className="auth-aside">
            <div className="eyebrow">
              <span className="eyebrow-line" /> INSTANT ATHLETE ACCESS
            </div>
            <h1>
              Built for the<br />
              <span>ones who</span><br />
              keep showing up.
            </h1>
            <p>
              Whether you are on the school pitch or eyeing the national combine,
              your reps speak for themselves. Jump straight into the demo to test our AI vision engine.
            </p>
            <div className="auth-aside-mark">
              FP <span>/ 2026</span>
            </div>
          </section>
        )}

        <section className="auth-card !max-w-none">
          <div className="form-eyebrow">
            {signup ? 'ATHLETE PASSPORT CALIBRATION' : 'CHOOSE YOUR ENTRY POINT'}
          </div>
          <h2>{signup ? 'Create Your Athlete Profile' : 'Enter the Perch'}</h2>
          <p className="form-intro">
            {signup
              ? 'Fill in your sport and details to build your personalized dashboard.'
              : 'Test the live experience in 1 click or log into your athlete account.'}
          </p>

          {!signup && (
            <>
              <button
                className="button-guest-demo"
                type="button"
                disabled={busy}
                onClick={handleGuest}
              >
                <span>🎮</span> Continue as Guest (Skip to Demo)
              </button>

              <button
                className="button-google"
                type="button"
                onClick={() => notify('Google sign-in demo connection: Use email or guest login.')}
              >
                <span className="google-g">G</span> Continue with Google
              </button>

              <div className="form-divider">
                <span>OR SIGN IN WITH EMAIL</span>
              </div>
            </>
          )}

          <form onSubmit={submit} className="stack-form">
            {signup && (
              <>
                <label>
                  Full Name
                  <input
                    name="name"
                    placeholder="e.g. Rahul Sharma"
                    required
                    type="text"
                  />
                </label>

                {/* Sport Selector */}
                <div>
                  <div className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                    Select Your Sport
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2">
                    {SPORTS.map((sport) => {
                      const sTheme = getSportTheme(sport)
                      const isSelected = sport === selectedSport
                      return (
                        <button
                          key={sport}
                          type="button"
                          onClick={() => setSelectedSport(sport)}
                          className={`flex items-center gap-2 p-2.5 rounded-xl font-black text-xs uppercase tracking-wider transition-all cursor-pointer ${isSelected
                            ? 'text-slate-950 shadow-lg scale-102 border-2 border-white'
                            : 'bg-slate-900/80 hover:bg-slate-800 text-white/80 border border-white/10'
                          }`}
                          style={{
                            background: isSelected
                              ? `linear-gradient(135deg, ${sTheme.primaryColor}, ${sTheme.accentColor})`
                              : undefined,
                            boxShadow: isSelected ? `0 3px 0 ${sTheme.btnShadow}` : undefined,
                          }}
                        >
                          <span className="text-base">{sTheme.icon}</span>
                          <span className="truncate">{sTheme.name}</span>
                        </button>
                      )
                    })}
                  </div>
                  <div className="text-[11px] text-yellow-300 font-medium">
                    ⚡ Your dashboard will transform with {activeTheme.name} stadiums and pro benchmarks.
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <label>
                    Age
                    <input max="55" min="8" name="age" defaultValue={17} required type="number" />
                  </label>
                  <label>
                    Skill Level
                    <select name="level" defaultValue="intermediate">
                      <option value="beginner">Beginner (Grassroots)</option>
                      <option value="intermediate">Intermediate (School / Club)</option>
                      <option value="advanced">Advanced (District / Academy)</option>
                      <option value="pro">Pro (State / National)</option>
                    </select>
                  </label>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <label>
                    Position / Role
                    <input
                      name="role"
                      placeholder="e.g. Striker, Top-order Batsman"
                      required
                      type="text"
                    />
                  </label>
                  <label>
                    Years Playing
                    <input max="40" min="0" name="yearsPlaying" defaultValue={3} required type="number" />
                  </label>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <label>
                    Country
                    <input name="country" placeholder="e.g. India" required type="text" />
                  </label>
                  <label>
                    State / Region
                    <input name="state" placeholder="e.g. Maharashtra" required type="text" />
                  </label>
                  <label>
                    City
                    <input name="city" placeholder="e.g. Pune" required type="text" />
                  </label>
                </div>

                <label>
                  Track Record or Past Experience <span className="text-slate-400 font-normal normal-case">(optional)</span>
                  <textarea
                    name="experience"
                    rows={2}
                    placeholder="e.g. 3 years school squad, local academy training, district championship finalist"
                    className="w-full p-3 rounded-2xl border-2 border-white/15 bg-slate-900/90 text-white text-xs font-medium outline-none focus:border-yellow-400 resize-none"
                  />
                </label>

                <label>
                  Goal
                  <select name="goal" defaultValue="national">
                    <option value="district">District Level Trials</option>
                    <option value="state">State Team Selection</option>
                    <option value="national">National Combine</option>
                    <option value="international">International / Professional</option>
                  </select>
                </label>
              </>
            )}

            <label>
              Email address
              <input autoComplete="email" name="email" placeholder="athlete@example.com" required type="email" />
            </label>
            <label>
              Password
              <input
                autoComplete={signup ? 'new-password' : 'current-password'}
                minLength={1}
                name="password"
                placeholder="Enter password"
                required
                type="password"
              />
            </label>

            <button className="button-primary-3d" disabled={busy} type="submit">
              {busy
                ? 'Processing…'
                : signup
                  ? `Launch My ${activeTheme.name} Arena ⚡`
                  : 'Sign In & Enter Dashboard ⚡'}
            </button>
          </form>

          <p className="auth-switch">
            {signup ? 'Already have an account?' : 'New to Falcon-Perch?'}
            <button onClick={() => setSignup(!signup)} type="button">
              {signup ? 'Sign in' : 'Create an athlete account'}
            </button>
          </p>
          <p className="auth-terms">
            By continuing, you agree to use Falcon-Perch as an athletic training companion. Progress is saved on this browser.
          </p>
        </section>
      </div>

      <Footer />
    </main>
  )
}

// ─── Onboarding Page (4-step wizard, also used as /settings) ─────────────────

const steps = [
  { title: 'What do you play?', subtitle: "We'll make your perch feel like yours." },
  { title: 'Where are you based?', subtitle: "We'll keep your journey close to home." },
  { title: 'Tell us your starting point.', subtitle: "There's no wrong place to begin." },
  { title: 'What are you reaching for?', subtitle: 'Set a goal that gives your practice direction.' },
]

function OnboardingPage({
  initial,
  onSave,
  settings = false,
}: {
  initial: OnboardingProfile
  onSave: (profile: OnboardingProfile) => Promise<void>
  settings?: boolean
}) {
  usePageTitle(settings ? 'Settings' : 'Your athlete profile')
  const [profile, setProfile] = useState(initial)
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  function update<K extends keyof OnboardingProfile>(key: K, value: OnboardingProfile[K]) {
    setProfile((current) => ({ ...current, [key]: value }))
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (step < steps.length - 1) {
      setStep((current) => current + 1)
      return
    }
    setBusy(true)
    try {
      await onSave(profile)
      if (settings) navigate('/dashboard')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className={`onboarding-page ${settings ? 'settings-page' : ''}`}>
      {!settings && (
        <header className="auth-top">
          <Logo />
          <span className="header-note">
            PROFILE WIZARD · {String(step + 1).padStart(2, '0')} / 04
          </span>
        </header>
      )}
      <div className="onboarding-layout">
        <aside className="onboarding-aside">
          <div className="eyebrow">
            <span className="eyebrow-line" /> {settings ? 'YOUR PROFILE' : 'THE START OF YOUR STORY'}
          </div>
          <h1>
            {settings ? (
              <>Keep your<br /><span>profile in play.</span></>
            ) : (
              <>Every athlete<br />has a <span>starting<br />point.</span></>
            )}
          </h1>
          <p>
            {settings
              ? 'Update your details whenever your game or goals change.'
              : 'A few details help us shape a journey around your sport, your level and the goal you have in mind.'}
          </p>
          <div className="onboarding-sport-stamp">
            FP <span>ATHLETE PROFILE / 2026</span>
          </div>
        </aside>

        <section className="onboarding-card">
          {!settings && (
            <div className="step-track" aria-label={`Step ${step + 1} of 4`}>
              {steps.map((item, index) => (
                <span className={index <= step ? 'step-fill' : ''} key={item.title} />
              ))}
            </div>
          )}
          <div className="form-eyebrow">
            {settings ? 'PROFILE SETTINGS' : `STEP ${String(step + 1).padStart(2, '0')} / 04`}
          </div>
          <h2>{settings ? 'Your athlete profile' : steps[step]?.title}</h2>
          <p className="form-intro">
            {settings ? 'Small updates keep your pathway relevant.' : steps[step]?.subtitle}
          </p>
          <form className="stack-form onboarding-form" onSubmit={submit}>
            {(settings || step === 0) && (
              <>
                <label>
                  Preferred sport
                  <select
                    value={profile.preferredSport}
                    onChange={(event) => update('preferredSport', event.target.value as Sport)}
                  >
                    {SPORTS.map((sport) => (
                      <option key={sport} value={sport}>
                        {sport[0]?.toUpperCase()}{sport.slice(1)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Age
                  <input
                    max="50"
                    min="8"
                    onChange={(event) => update('age', Number(event.target.value))}
                    required
                    type="number"
                    value={profile.age}
                  />
                </label>
              </>
            )}
            {(settings || step === 1) && (
              <>
                <label>
                  Country
                  <input
                    onChange={(event) => update('country', event.target.value)}
                    placeholder="e.g. India"
                    required
                    value={profile.country}
                  />
                </label>
                <div className="form-row">
                  <label>
                    State / region
                    <input
                      onChange={(event) => update('state', event.target.value)}
                      placeholder="e.g. Maharashtra"
                      required
                      value={profile.state}
                    />
                  </label>
                  <label>
                    City
                    <input
                      onChange={(event) => update('city', event.target.value)}
                      placeholder="e.g. Pune"
                      required
                      value={profile.city}
                    />
                  </label>
                </div>
              </>
            )}
            {(settings || step === 2) && (
              <>
                <label>
                  Current level
                  <select
                    value={profile.level}
                    onChange={(event) => update('level', event.target.value as SkillLevel)}
                  >
                    {(['beginner', 'intermediate', 'advanced', 'pro'] as const).map((level) => (
                      <option key={level} value={level}>
                        {level[0]?.toUpperCase()}{level.slice(1)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-row">
                  <label>
                    Position or role
                    <input
                      onChange={(event) => update('role', event.target.value)}
                      placeholder="e.g. Midfielder"
                      required
                      value={profile.role}
                    />
                  </label>
                  <label>
                    Years playing
                    <input
                      max="60"
                      min="0"
                      onChange={(event) => update('yearsPlaying', Number(event.target.value))}
                      required
                      type="number"
                      value={profile.yearsPlaying}
                    />
                  </label>
                </div>
                <label>
                  Track record or past experience <span className="text-slate-400 font-normal normal-case">(optional)</span>
                  <textarea
                    rows={2}
                    onChange={(event) => update('experience_details', event.target.value)}
                    placeholder="e.g. 3 years school squad, local academy, tournament wins"
                    value={profile.experience_details || ''}
                    className="w-full p-3 rounded-2xl border-2 border-white/15 bg-slate-900/90 text-white text-xs font-medium outline-none focus:border-yellow-400 resize-none"
                  />
                </label>
              </>
            )}
            {(settings || step === 3) && (
              <>
                <label>
                  Your goal
                  <select
                    value={profile.goal}
                    onChange={(event) => update('goal', event.target.value as OnboardingProfile['goal'])}
                  >
                    {(['district', 'state', 'national', 'international'] as const).map((goal) => (
                      <option key={goal} value={goal}>
                        {goal[0]?.toUpperCase()}{goal.slice(1)} level
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}
            <div className="form-actions">
              {!settings && step > 0 && (
                <button
                  className="button button-secondary"
                  onClick={() => setStep((current) => current - 1)}
                  type="button"
                >
                  ← Back
                </button>
              )}
              <button className="button-primary-3d" disabled={busy} type="submit">
                {busy ? 'Saving…' : settings ? 'Save changes' : step === steps.length - 1 ? 'Build my profile ⚡' : 'Continue →'}
              </button>
            </div>
          </form>
        </section>
      </div>
      {settings && (
        <div className="reset-analyses">
          <div>
            <strong>Free analyses</strong>
            <span>Reset your local demo analysis count.</span>
          </div>
          <ResetAnalysesButton />
        </div>
      )}
      {!settings && <Footer />}
    </main>
  )
}

function ResetAnalysesButton() {
  const [done, setDone] = useState(false)
  async function reset() {
    await analysisService.resetFreeAnalyses()
    setDone(true)
    window.setTimeout(() => setDone(false), 2500)
  }
  return (
    <button className="button button-secondary reset-button" onClick={reset} type="button">
      {done ? 'Reset complete' : 'Reset free analyses'}
    </button>
  )
}

// ─── Guards ───────────────────────────────────────────────────────────────────

function RequireAuth({ user, ready }: { user: User | null; ready: boolean }) {
  const location = useLocation()
  if (!ready) return <LoadingPage />
  return user ? <Outlet /> : <Navigate replace to="/auth" state={{ from: location }} />
}

// Guest users have a profile but skip the onboarding step.
function RequireProfile({ profile }: { user: User | null; profile: OnboardingProfile | null }) {
  const location = useLocation()
  // Guests always have a profile injected — skip onboarding.
  if (!profile && location.pathname !== '/onboarding') return <Navigate replace to="/onboarding" />
  if (profile && location.pathname === '/onboarding') return <Navigate replace to="/dashboard" />
  return <Outlet />
}

// ─── App Shell (authenticated layout) ────────────────────────────────────────

function AppShell({
  user,
  profile,
  onLogout,
}: {
  user: User
  profile: OnboardingProfile
  onLogout: () => Promise<void>
}) {
  const navigate = useNavigate()
  async function signOut() {
    await onLogout()
    navigate('/auth')
  }
  return (
    <div className="app-shell">
      <header className="app-header">
        <Logo />
        <nav className="desktop-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <details className="profile-menu">
          <summary>
            {/* Guest badge */}
            {user.isGuest && (
              <span className="guest-badge">🎮 Guest</span>
            )}
            <span className="avatar">{user.name[0]?.toUpperCase()}</span>
            <span className="profile-name">{user.isGuest ? 'Guest' : user.name}</span>
            <span className="menu-chevron">⌄</span>
          </summary>
          <div className="profile-dropdown">
            {user.isGuest ? (
              <span className="dropdown-email guest-mode-label">🎮 Guest Mode</span>
            ) : (
              <span className="dropdown-email">{user.email}</span>
            )}
            {!user.isGuest && <NavLink to="/settings">Athlete profile</NavLink>}
            <button onClick={signOut} type="button">
              {user.isGuest ? 'Exit Guest Mode' : 'Log out'}
            </button>
          </div>
        </details>
      </header>
      <div className="app-content">
        <Outlet context={{ user, profile }} />
      </div>
      <Footer />
      <nav className="mobile-tabs" aria-label="Mobile navigation">
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to}>
            <span>{item.icon}</span>
            <small>{item.label === 'Analyze My Video' ? 'Analyze' : item.label}</small>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

// ─── Utility Pages ────────────────────────────────────────────────────────────

function LaterPage({ path }: { path: string }) {
  const page = laterRoutes[path] ?? laterRoutes['/idols']
  usePageTitle(page?.title ?? 'Falcon-Perch')
  return (
    <main className="later-page">
      <div className="eyebrow">
        <span className="eyebrow-line" /> {page?.eyebrow}
      </div>
      <h1>{page?.title}</h1>
      <p>{page?.description}</p>
      <div className="coming-soon">
        <span>FP / IN PROGRESS</span>
        <div className="coming-line" />
        <small>This part of your perch is taking shape.</small>
      </div>
      <Link className="text-link" to="/dashboard">
        ← Back to dashboard
      </Link>
    </main>
  )
}

function LoadingPage() {
  return (
    <main className="loading-page" aria-label="Loading">
      <div className="skeleton skeleton-title" />
      <div className="skeleton skeleton-copy" />
      <div className="skeleton skeleton-card" />
    </main>
  )
}

function Footer() {
  return (
    <footer className="site-footer">
      <Logo small />
      <span>Not affiliated with any athlete or league. Videos, when available, are embedded from YouTube.</span>
      <span>© 2026 FALCON-PERCH INTELLIGENCE</span>
    </footer>
  )
}

// ─── Route Tree ───────────────────────────────────────────────────────────────

function AppRoutes({
  user,
  profile,
  ready,
  notify,
  setUser,
  setProfile,
}: {
  user: User | null
  profile: OnboardingProfile | null
  ready: boolean
  notify: (message: string) => void
  setUser: (user: User | null) => void
  setProfile: (profile: OnboardingProfile | null) => void
}) {
  const navigate = useNavigate()

  /**
   * Called after login or signup.
   * isNewUser = true  → no profile stored yet → go to onboarding (shouldn't
   *                      happen for signup since we already saved the profile,
   *                      but handles edge cases for login of brand-new email).
   * isNewUser = false → profile already saved → go straight to dashboard.
   */
  async function onAuthenticated(nextUser: User, _isNewUser: boolean, returnPath?: string) {
    setUser(nextUser)
    const savedProfile = await profileService.getProfile()
    setProfile(savedProfile)
    if (returnPath) {
      navigate(returnPath, { replace: true })
    } else if (savedProfile) {
      navigate('/dashboard', { replace: true })
    } else {
      navigate('/onboarding', { replace: true })
    }
  }

  async function onGuestLogin(returnPath?: string) {
    const res = await authService.loginAsGuest()
    setUser(res.user)
    setProfile(res.profile)
    navigate(returnPath || '/dashboard', { replace: true })
  }

  async function saveProfile(nextProfile: OnboardingProfile) {
    const saved = await profileService.saveProfile(nextProfile)
    setProfile(saved)
    if (!profile) navigate('/dashboard', { replace: true })
  }

  async function logout() {
    await authService.logout()
    setUser(null)
    setProfile(null)
  }

  // Fallback profile/user values for TypeScript — RequireAuth/RequireProfile
  // prevent these routes from rendering when user or profile is actually null.
  const safeUser = user ?? { id: '', email: '', name: 'Athlete', isGuest: false }
  const safeProfile = profile ?? {
    preferredSport: 'football' as Sport,
    age: 17,
    country: '',
    state: '',
    city: '',
    level: 'intermediate' as SkillLevel,
    role: '',
    yearsPlaying: 0,
    goal: 'district' as AthleteGoal,
  }

  return (
    <Routes>
      {/* ── Public ── */}
      <Route
        path="/"
        element={
          <LandingPage
            user={user}
            profile={profile}
            onGuestLogin={async () => {
              const res = await authService.loginAsGuest()
              setUser(res.user)
              setProfile(res.profile)
            }}
            onUserLogin={async (nextUser, nextProfile) => {
              setUser(nextUser)
              setProfile(nextProfile)
            }}
          />
        }
      />
      <Route
        path="/auth"
        element={
          <AuthPage
            notify={notify}
            onAuthenticated={onAuthenticated}
            onGuest={onGuestLogin}
          />
        }
      />

      {/* ── Protected ── */}
      <Route element={<RequireAuth ready={ready} user={user} />}>
        <Route element={<RequireProfile user={user} profile={profile} />}>
          {/* Onboarding (only reached if no profile yet) */}
          <Route
            path="/onboarding"
            element={
              profile ? (
                <Navigate replace to="/dashboard" />
              ) : (
                <OnboardingPage
                  initial={{
                    preferredSport: 'football',
                    age: 17,
                    country: 'India',
                    state: '',
                    city: '',
                    level: 'intermediate',
                    role: '',
                    yearsPlaying: 3,
                    goal: 'national',
                    experience_details: '',
                  }}
                  onSave={saveProfile}
                />
              )
            }
          />

          {/* App Shell — all routes that need the persistent header */}
          <Route
            element={
              <AppShell
                onLogout={logout}
                profile={safeProfile}
                user={safeUser}
              />
            }
          >
            <Route
              path="/dashboard"
              element={
                <DashboardPage
                  profile={safeProfile}
                  user={safeUser}
                  onProfileUpdate={saveProfile}
                />
              }
            />
            <Route
              path="/settings"
              element={
                profile ? (
                  <OnboardingPage initial={profile} onSave={saveProfile} settings />
                ) : (
                  <Navigate replace to="/onboarding" />
                )
              }
            />
            <Route path="/idols" element={<LaterPage path="/idols" />} />
            <Route path="/idols/:id" element={<LaterPage path="/idols" />} />
            <Route path="/analyze" element={<AIFeaturesDemo />} />
            <Route path="/analyze/review/:id" element={<AIFeaturesDemo />} />
            <Route path="/analyze-own" element={<LaterPage path="/analyze-own" />} />
            <Route path="/pathways" element={<LaterPage path="/pathways" />} />
            <Route path="/pathways/:sport" element={<LaterPage path="/pathways" />} />
            <Route path="/tournaments" element={<LaterPage path="/tournaments" />} />
            <Route path="/insights" element={<LaterPage path="/insights" />} />
            <Route path="/pricing" element={<LaterPage path="/pricing" />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  )
}

// ─── App Frame (session restore) ──────────────────────────────────────────────

function AppFrame() {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<OnboardingProfile | null>(null)
  const [ready, setReady] = useState(false)
  const [toast, setToast] = useState('')

  useEffect(() => {
    let active = true
    async function restoreSession() {
      // Session lives in sessionStorage — null on fresh tab open.
      const currentUser = await authService.getCurrentUser()
      const currentProfile = currentUser ? await profileService.getProfile() : null
      if (active) {
        setUser(currentUser)
        setProfile(currentProfile)
        setReady(true)
      }
    }
    void restoreSession()
    return () => {
      active = false
    }
  }, [])

  function notify(message: string) {
    setToast(message)
    window.setTimeout(() => setToast(''), 3500)
  }

  return (
    <>
      <AppRoutes
        notify={notify}
        profile={profile}
        ready={ready}
        setProfile={setProfile}
        setUser={setUser}
        user={user}
      />
      <Toast message={toast} />
    </>
  )
}

// ─── Root ─────────────────────────────────────────────────────────────────────

function App() {
  return (
    <BrowserRouter>
      <AppFrame />
    </BrowserRouter>
  )
}

export default App
