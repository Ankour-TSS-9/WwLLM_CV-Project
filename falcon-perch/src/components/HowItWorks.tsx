import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export function HowItWorks() {
  const cards = [
    {
      step: '01 / LEARN',
      title: 'Study the details',
      description:
        'Break down frame-by-frame masterclasses from the world’s best. Inspect release angles, footwork, and kinetic sequencing.',
      badge: 'PRO REPS REPOSITORY',
      link: '/idols',
      actionText: 'Browse 100+ Idols',
      gradient: 'from-purple-900/80 via-indigo-900/70 to-slate-900',
      border: 'rgba(168, 85, 247, 0.4)',
      btnBg: 'bg-gradient-to-r from-purple-500 to-indigo-500',
      btnShadow: '#581c87',
      glow: 'rgba(168, 85, 247, 0.35)',
      illustration: (
        <svg viewBox="0 0 200 120" className="w-full h-32" xmlns="http://www.w3.org/2000/svg">
          {/* Video player graphic with scrub bar & slow mo pins */}
          <rect x="20" y="10" width="160" height="90" rx="14" fill="#1e1b4b" stroke="#818cf8" strokeWidth="2" />
          <circle cx="100" cy="50" r="18" fill="#a855f7" />
          <polygon points="95,42 110,50 95,58" fill="#fff" />
          {/* Progress scrub bar */}
          <line x1="35" y1="85" x2="165" y2="85" stroke="#475569" strokeWidth="4" strokeLinecap="round" />
          <line x1="35" y1="85" x2="115" y2="85" stroke="#facc15" strokeWidth="4" strokeLinecap="round" />
          <circle cx="115" cy="85" r="5" fill="#facc15" />
          {/* Slow-mo frames */}
          <rect x="35" y="22" width="22" height="16" rx="4" fill="#312e81" stroke="#6366f1" strokeWidth="1" />
          <rect x="63" y="22" width="22" height="16" rx="4" fill="#312e81" stroke="#6366f1" strokeWidth="1" />
          <rect x="143" y="22" width="22" height="16" rx="4" fill="#312e81" stroke="#6366f1" strokeWidth="1" />
        </svg>
      ),
    },
    {
      step: '02 / IMPROVE',
      title: 'Know your game',
      description:
        'Upload your own practice footage. Our pose-tracking vision engine compares your kinematics side-by-side with champion benchmarks.',
      badge: 'AI KINEMATIC ANALYSIS',
      link: '/analyze',
      actionText: 'Analyze Your Video',
      gradient: 'from-emerald-950/80 via-teal-950/70 to-slate-900',
      border: 'rgba(52, 211, 153, 0.45)',
      btnBg: 'bg-gradient-to-r from-emerald-500 to-teal-500',
      btnShadow: '#064e3b',
      glow: 'rgba(16, 185, 129, 0.35)',
      illustration: (
        <svg viewBox="0 0 200 120" className="w-full h-32" xmlns="http://www.w3.org/2000/svg">
          {/* Skeleton tracking graphic */}
          <rect x="20" y="10" width="160" height="90" rx="14" fill="#042f2e" stroke="#34d399" strokeWidth="2" />
          {/* Head */}
          <circle cx="100" cy="30" r="8" fill="#34d399" />
          {/* Torso */}
          <line x1="100" y1="38" x2="100" y2="65" stroke="#34d399" strokeWidth="3" />
          {/* Arms */}
          <line x1="100" y1="44" x2="80" y2="52" stroke="#38bdf8" strokeWidth="3" />
          <line x1="80" y1="52" x2="68" y2="40" stroke="#38bdf8" strokeWidth="3" />
          <line x1="100" y1="44" x2="122" y2="48" stroke="#38bdf8" strokeWidth="3" />
          <line x1="122" y1="48" x2="138" y2="35" stroke="#38bdf8" strokeWidth="3" />
          {/* Legs */}
          <line x1="100" y1="65" x2="86" y2="82" stroke="#facc15" strokeWidth="3" />
          <line x1="86" y1="82" x2="80" y2="94" stroke="#facc15" strokeWidth="3" />
          <line x1="100" y1="65" x2="114" y2="80" stroke="#facc15" strokeWidth="3" />
          <line x1="114" y1="80" x2="128" y2="92" stroke="#facc15" strokeWidth="3" />
          {/* Angle tracker tag */}
          <rect x="135" y="55" width="40" height="18" rx="4" fill="#facc15" />
          <text x="140" y="68" fontSize="10" fontWeight="bold" fill="#022c22">132° KNEE</text>
        </svg>
      ),
    },
    {
      step: '03 / ADVANCE',
      title: 'Find your next step',
      description:
        'Climb the gamified athlete pathway. Complete stage checklists, unlock verified tournament trials, and bridge the amateur-to-pro gap.',
      badge: 'SCORE HERO PATHWAY',
      link: '/pathways',
      actionText: 'Explore Pathways',
      gradient: 'from-amber-950/80 via-orange-950/70 to-slate-900',
      border: 'rgba(251, 191, 36, 0.45)',
      btnBg: 'bg-gradient-to-r from-amber-400 to-yellow-500',
      btnShadow: '#78350f',
      glow: 'rgba(245, 158, 11, 0.35)',
      illustration: (
        <svg viewBox="0 0 200 120" className="w-full h-32" xmlns="http://www.w3.org/2000/svg">
          {/* Score Hero winding road with nodes */}
          <rect x="20" y="10" width="160" height="90" rx="14" fill="#451a03" stroke="#f59e0b" strokeWidth="2" />
          <path d="M 40,85 Q 80,45 120,75 T 160,35" fill="none" stroke="#fff" strokeDasharray="6,4" strokeWidth="3" />
          {/* Node 1 */}
          <circle cx="40" cy="85" r="9" fill="#10b981" stroke="#fff" strokeWidth="2" />
          <text x="37" y="89" fontSize="10" fontWeight="bold" fill="#fff">1</text>
          {/* Node 2 */}
          <circle cx="100" cy="60" r="10" fill="#f59e0b" stroke="#fff" strokeWidth="2" />
          <text x="96" y="64" fontSize="10" fontWeight="bold" fill="#fff">2</text>
          {/* Node 3 Goal */}
          <circle cx="160" cy="35" r="13" fill="#e11d48" stroke="#fff" strokeWidth="2" />
          <polygon points="160,26 162,31 167,31 163,34 165,39 160,36 155,39 157,34 153,31 158,31" fill="#facc15" />
        </svg>
      ),
    },
  ]

  return (
    <section className="py-20 px-4 sm:px-8 max-w-[1400px] mx-auto">
      <div className="text-center max-w-2xl mx-auto mb-14">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-emerald-400/10 border border-emerald-400/30 text-emerald-300 text-xs font-black uppercase tracking-widest mb-3">
          <span>⚡</span> THE 3-STEP GAME PLAN <span>⚡</span>
        </div>
        <h2
          className="text-4xl sm:text-5xl font-black text-white tracking-tight uppercase"
          style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
        >
          HOW IT WORKS
        </h2>
        <p className="text-slate-300 text-sm sm:text-base mt-2">
          Everything you need to turn raw athletic talent into elite, measured execution.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {cards.map((card, idx) => (
          <motion.div
            key={idx}
            whileHover={{ y: -10, rotate: idx === 1 ? 0 : idx === 0 ? -1 : 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="flex flex-col justify-between rounded-3xl p-7 border-2 backdrop-blur-xl shadow-xl transition-shadow"
            style={{
              background: `linear-gradient(160deg, ${card.gradient})`,
              borderColor: card.border,
              boxShadow: `0 15px 40px -15px ${card.glow}`,
            }}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-xs font-black tracking-widest text-yellow-300">
                  {card.step}
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-white/10 text-white/80 border border-white/10">
                  {card.badge}
                </span>
              </div>

              <div className="my-4">{card.illustration}</div>

              <h3
                className="text-2xl sm:text-3xl font-black text-white mb-2 tracking-wide"
                style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
              >
                {card.title}
              </h3>
              <p className="text-slate-300 text-xs sm:text-sm leading-relaxed mb-6">
                {card.description}
              </p>
            </div>

            <Link
              to={card.link}
              className={`w-full py-3.5 px-6 rounded-2xl font-black text-slate-950 text-center uppercase tracking-wider text-xs transition-transform active:translate-y-1 block shadow-lg ${card.btnBg}`}
              style={{
                boxShadow: `0 4px 0 ${card.btnShadow}`,
              }}
            >
              {card.actionText} →
            </Link>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
