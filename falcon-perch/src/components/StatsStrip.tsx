import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

function Counter({ end, suffix = '', duration = 1.5 }: { end: number; suffix?: string; duration?: number }) {
  const [val, setVal] = useState(0)

  useEffect(() => {
    let start: number | null = null
    let frame: number

    function tick(now: number) {
      if (!start) start = now
      const p = Math.min((now - start) / (duration * 1000), 1)
      const ease = 1 - Math.pow(1 - p, 3)
      setVal(Math.round(ease * end))
      if (p < 1) frame = requestAnimationFrame(tick)
    }

    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [end, duration])

  return (
    <span>
      {val}
      {suffix}
    </span>
  )
}

export function StatsStrip() {
  const stats = [
    {
      num: 8,
      suffix: '',
      label: 'MAJOR SPORTS',
      desc: 'Football, Cricket, Tennis & more',
      icon: '🏆',
      color: 'from-amber-400 to-yellow-500',
    },
    {
      num: 150,
      suffix: '+',
      label: 'PRO MASTERCLASS CLIPS',
      desc: 'Slow-motion signature breakdowns',
      icon: '📹',
      color: 'from-cyan-400 to-blue-500',
    },
    {
      num: 2,
      suffix: ' FREE',
      label: 'AI VIDEO ANALYSES',
      desc: 'Instant pose & angle breakdown',
      icon: '⚡',
      color: 'from-emerald-400 to-teal-500',
    },
    {
      num: 18,
      suffix: 'K+',
      label: 'ASPIRING ATHLETES',
      desc: 'Climbing amateur-to-pro ranks',
      icon: '🔥',
      color: 'from-rose-400 to-orange-500',
    },
  ]

  return (
    <section className="py-14 px-4 sm:px-8 border-y border-white/10 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-[1300px] mx-auto grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
        {stats.map((item, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: idx * 0.1 }}
            className="flex flex-col items-center text-center p-5 rounded-3xl bg-white/5 border border-white/10 hover:border-white/20 transition-all shadow-lg group"
          >
            <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">{item.icon}</div>
            <div
              className={`text-3xl sm:text-4xl lg:text-5xl font-black bg-gradient-to-r ${item.color} bg-clip-text text-transparent mb-1`}
              style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
            >
              <Counter end={item.num} suffix={item.suffix} />
            </div>
            <div className="text-xs sm:text-sm font-black text-white uppercase tracking-wider">
              {item.label}
            </div>
            <div className="text-[11px] text-slate-400 font-medium mt-0.5">{item.desc}</div>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
