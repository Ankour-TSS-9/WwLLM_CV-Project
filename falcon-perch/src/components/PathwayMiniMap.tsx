import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export function PathwayMiniMap() {
  const [activeNode, setActiveNode] = useState(3)

  // Auto-animate avatar pin hopping along nodes
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveNode((cur) => (cur >= 4 ? 2 : cur + 1))
    }, 2800)
    return () => clearInterval(timer)
  }, [])

  const nodes = [
    { num: 1, x: 200, y: 380, stars: 3, status: 'completed', label: 'Grassroots' },
    { num: 2, x: 420, y: 330, stars: 3, status: 'completed', label: 'District' },
    { num: 3, x: 260, y: 220, stars: 2, status: 'current', label: 'State Camp' },
    { num: 4, x: 520, y: 150, stars: 0, status: 'locked', label: 'National Combine' },
    { num: 5, x: 360, y: 60, stars: 0, status: 'goal', label: 'Pro National Team' },
  ]

  return (
    <section className="py-20 px-4 sm:px-8 max-w-[1200px] mx-auto">
      <div className="flex flex-col items-center text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-emerald-400/10 border border-emerald-400/30 text-emerald-300 text-xs font-black uppercase tracking-widest mb-3">
          <span>🗺️</span> SCORE HERO ROADMAP <span>🗺️</span>
        </div>
        <h2
          className="text-4xl sm:text-5xl font-black text-white tracking-tight uppercase"
          style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
        >
          FIND YOUR NEXT STEP
        </h2>
        <p className="text-slate-300 text-sm sm:text-base max-w-xl mt-1">
          Gamified stages from school pitch to the national stadium. Collect stars, complete drills, and level up.
        </p>
      </div>

      {/* Mini Score Hero Pitch Container */}
      <div
        className="relative w-full max-w-[850px] mx-auto rounded-3xl overflow-hidden border-4 border-emerald-400/50 shadow-2xl p-4 sm:p-6"
        style={{
          background: 'linear-gradient(180deg, #15803d 0%, #166534 50%, #14532d 100%)',
          boxShadow: '0 25px 60px -15px rgba(22, 101, 52, 0.8), 0 0 30px rgba(52, 211, 153, 0.3)',
        }}
      >
        {/* Pitch mowed stripes */}
        <div className="absolute inset-0 pointer-events-none opacity-20">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className={`w-full h-1/8 ${i % 2 === 0 ? 'bg-white/10' : 'bg-black/10'}`}
              style={{ height: '12.5%' }}
            />
          ))}
        </div>

        {/* Top Score Hero HUD Bar (Reference 2 style) */}
        <div className="relative z-20 flex items-center justify-between gap-3 p-3 mb-4 rounded-2xl bg-black/40 backdrop-blur-md border border-white/20">
          {/* Hearts HUD */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-900/80 border border-rose-500/30">
            <span className="text-rose-500 text-base">❤️</span>
            <div className="flex gap-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <span key={i} className="text-rose-400 text-xs">♥</span>
              ))}
            </div>
          </div>

          {/* Season Title */}
          <div className="text-center font-black text-white uppercase text-xs sm:text-sm tracking-wider">
            SEASON 1 · <span className="text-yellow-400">DISTRICT COMBINE</span>
          </div>

          {/* Stars & Camera Badge */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 px-3 py-1 rounded-xl bg-slate-900/80 border border-yellow-400/30 text-yellow-300 font-black text-xs">
              <span>⭐</span>
              <span>41</span>
            </div>
            <div className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded-xl bg-blue-600/80 text-white font-black text-xs border border-blue-400/40">
              <span>+1 📹</span>
            </div>
          </div>
        </div>

        {/* Pitch Canvas with Winding SVG Path & Nodes */}
        <div className="relative w-full h-[460px] sm:h-[500px]">
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none"
            viewBox="0 0 700 460"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Goal net at top */}
            <rect x="280" y="8" width="140" height="40" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="3" />
            <line x1="280" y1="8" x2="420" y2="48" stroke="rgba(255,255,255,0.3)" strokeDasharray="4,4" />
            <line x1="420" y1="8" x2="280" y2="48" stroke="rgba(255,255,255,0.3)" strokeDasharray="4,4" />

            {/* Winding Dashed Path */}
            <path
              d="M 200,380 C 320,380 340,330 420,330 C 500,330 360,220 260,220 C 180,220 440,150 520,150 C 580,150 420,70 360,60"
              fill="none"
              stroke="#ffffff"
              strokeDasharray="10,8"
              strokeWidth="5"
              strokeLinecap="round"
            />
          </svg>

          {/* Polaroid Milestone Card (Reference 2 style) */}
          <motion.div
            initial={{ rotate: -8 }}
            whileHover={{ rotate: 0, scale: 1.05 }}
            className="absolute right-4 sm:right-12 top-28 sm:top-24 w-36 sm:w-44 p-2 sm:p-2.5 bg-white text-slate-900 rounded-lg shadow-2xl border-2 border-slate-200 transform -rotate-6 cursor-pointer z-10"
          >
            <div className="relative w-full h-24 sm:h-28 rounded overflow-hidden bg-slate-900">
              <div className="w-full h-full bg-gradient-to-tr from-emerald-800 to-teal-500 flex items-center justify-center text-3xl">
                ⚽
              </div>
              <span className="absolute top-1 right-1 px-1.5 py-0.5 rounded-full bg-black/60 text-white text-[8px] font-mono">
                23 NOV
              </span>
            </div>
            <div className="mt-2 text-center">
              <span
                className="font-bold text-[11px] sm:text-xs text-slate-800 tracking-wide block"
                style={{ fontFamily: "'Poppins', sans-serif" }}
              >
                District Selection!
              </span>
              <span className="text-[9px] text-emerald-600 font-extrabold uppercase">
                Bouncing Back ★★★
              </span>
            </div>
          </motion.div>

          {/* Interactive Nodes */}
          {nodes.map((node) => {
            const isCurrent = node.num === activeNode
            const isCompleted = node.num < activeNode

            return (
              <div
                key={node.num}
                className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer z-20"
                style={{ left: `${(node.x / 700) * 100}%`, top: `${(node.y / 460) * 100}%` }}
                onClick={() => setActiveNode(node.num)}
              >
                {/* 3 Stars atop Node */}
                <div className="flex justify-center gap-0.5 mb-1">
                  {Array.from({ length: 3 }).map((_, starIdx) => {
                    const filled = starIdx < node.stars
                    return (
                      <span
                        key={starIdx}
                        className={`text-xs ${filled ? 'text-yellow-300 drop-shadow' : 'text-white/30'}`}
                      >
                        ★
                      </span>
                    )
                  })}
                </div>

                {/* Node Circle */}
                <div className="relative">
                  {/* Pulsing ring on current node */}
                  {isCurrent && (
                    <motion.div
                      animate={{ scale: [1, 1.45, 1], opacity: [0.8, 0, 0.8] }}
                      transition={{ duration: 1.8, repeat: Infinity }}
                      className="absolute -inset-2.5 rounded-full bg-yellow-400 pointer-events-none"
                    />
                  )}

                  {/* Avatar pin marker on active node */}
                  {isCurrent && (
                    <motion.div
                      initial={{ y: -10 }}
                      animate={{ y: [0, -6, 0] }}
                      transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
                      className="absolute -top-7 left-1/2 transform -translate-x-1/2 px-2 py-0.5 rounded-full bg-yellow-400 text-slate-950 font-black text-[9px] uppercase shadow-md flex items-center gap-1 whitespace-nowrap"
                    >
                      <span>🏃</span> YOU
                    </motion.div>
                  )}

                  <div
                    className={`w-11 h-11 sm:w-12 sm:h-12 rounded-full flex items-center justify-center font-black text-sm sm:text-base border-3 shadow-xl transition-transform active:scale-95 ${
                      node.status === 'goal'
                        ? 'bg-gradient-to-tr from-amber-400 to-yellow-300 text-slate-950 border-white'
                        : isCompleted
                        ? 'bg-emerald-500 text-white border-white'
                        : isCurrent
                        ? 'bg-rose-500 text-white border-yellow-300'
                        : 'bg-slate-700/80 text-white/50 border-white/40'
                    }`}
                    style={{
                      boxShadow: isCurrent ? '0 0 20px rgba(245, 158, 11, 0.8)' : undefined,
                    }}
                  >
                    {node.status === 'goal' ? '🏆' : node.num}
                  </div>
                </div>

                {/* Node Label */}
                <div className="text-center mt-1">
                  <span className="text-[10px] sm:text-[11px] font-bold text-white bg-black/40 px-2 py-0.5 rounded-full backdrop-blur-sm whitespace-nowrap">
                    {node.label}
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Bottom CTA to open full pathway */}
        <div className="relative z-20 mt-4 pt-4 border-t border-white/20 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-white text-xs sm:text-sm font-medium text-center sm:text-left">
            🎯 Stage 3: <strong className="text-yellow-300">State Training Camp</strong> · 2 Checklists Left
          </div>

          <Link
            to="/pathways"
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl font-black text-slate-950 uppercase tracking-wider text-xs sm:text-sm bg-gradient-to-r from-yellow-400 to-amber-400 hover:from-yellow-300 hover:to-amber-300 transition-transform active:translate-y-1 text-center shadow-xl cursor-pointer"
            style={{
              boxShadow: '0 5px 0 #b45309, 0 0 20px rgba(251, 191, 36, 0.5)',
            }}
          >
            OPEN MY MAP 🚀
          </Link>
        </div>
      </div>
    </section>
  )
}
