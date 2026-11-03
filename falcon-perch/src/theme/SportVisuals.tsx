import type { Sport } from '../types'

export function SportFieldBackground({ sport }: { sport: Sport }) {
  switch (sport) {
    case 'football':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-40 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="grassStripes" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#166534" stopOpacity="0.4" />
              <stop offset="25%" stopColor="#14532d" stopOpacity="0.6" />
              <stop offset="50%" stopColor="#166534" stopOpacity="0.4" />
              <stop offset="75%" stopColor="#14532d" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#166534" stopOpacity="0.4" />
            </linearGradient>
            <pattern id="goalNet" width="16" height="16" patternUnits="userSpaceOnUse">
              <path d="M 0,0 L 16,16 M 16,0 L 0,16" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
            </pattern>
          </defs>
          {/* Mowed lawn bands */}
          {Array.from({ length: 10 }).map((_, i) => (
            <rect
              key={i}
              x="0"
              y={i * 80}
              width="1000"
              height="80"
              fill={i % 2 === 0 ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.1)'}
            />
          ))}
          {/* Goal net at top */}
          <polygon points="360,0 640,0 600,60 400,60" fill="url(#goalNet)" stroke="rgba(255,255,255,0.4)" strokeWidth="2" />
          <line x1="360" y1="0" x2="400" y2="60" stroke="#fff" strokeWidth="4" />
          <line x1="640" y1="0" x2="600" y2="60" stroke="#fff" strokeWidth="4" />
          <line x1="400" y1="60" x2="600" y2="60" stroke="#fff" strokeWidth="4" />

          {/* Touchlines & Penalty Box */}
          <rect x="80" y="60" width="840" height="740" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="3" />
          {/* Penalty box at top */}
          <rect x="250" y="60" width="500" height="220" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="3" />
          {/* 6-yard box */}
          <rect x="360" y="60" width="280" height="90" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="3" />
          {/* Penalty spot */}
          <circle cx="500" cy="190" r="5" fill="#fff" />
          {/* Penalty arc */}
          <path d="M 430,280 A 80,80 0 0,0 570,280" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="3" />
          {/* Halfway line & center circle */}
          <line x1="80" y1="650" x2="920" y2="650" stroke="rgba(255,255,255,0.5)" strokeWidth="3" />
          <circle cx="500" cy="650" r="110" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="3" />
          <circle cx="500" cy="650" r="5" fill="#fff" />
        </svg>
      )

    case 'cricket':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-45 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Outfield radial ring */}
          <ellipse cx="500" cy="400" rx="460" ry="360" fill="none" stroke="rgba(255,255,255,0.3)" strokeDasharray="12,12" strokeWidth="3" />
          <ellipse cx="500" cy="400" rx="350" ry="270" fill="rgba(234, 179, 8, 0.05)" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
          {/* Pitch strip (clay/brown) */}
          <rect x="440" y="160" width="120" height="480" rx="6" fill="#854d0e" stroke="rgba(254, 240, 138, 0.4)" strokeWidth="3" />
          {/* Crease lines */}
          <line x1="420" y1="230" x2="580" y2="230" stroke="#fff" strokeWidth="3" />
          <line x1="420" y1="570" x2="580" y2="570" stroke="#fff" strokeWidth="3" />
          {/* Stumps & bails */}
          <circle cx="485" cy="225" r="4" fill="#fef08a" />
          <circle cx="500" cy="225" r="4" fill="#fef08a" />
          <circle cx="515" cy="225" r="4" fill="#fef08a" />
          <line x1="482" y1="225" x2="518" y2="225" stroke="#fef08a" strokeWidth="2" />
          {/* Bottom stumps */}
          <circle cx="485" cy="575" r="4" fill="#fef08a" />
          <circle cx="500" cy="575" r="4" fill="#fef08a" />
          <circle cx="515" cy="575" r="4" fill="#fef08a" />
          <line x1="482" y1="575" x2="518" y2="575" stroke="#fef08a" strokeWidth="2" />
        </svg>
      )

    case 'tennis':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-45 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Australian Open royal blue / purple court inner fill */}
          <rect x="150" y="80" width="700" height="640" fill="rgba(37, 99, 235, 0.15)" stroke="rgba(255,255,255,0.7)" strokeWidth="4" />
          {/* Singles sidelines */}
          <line x1="230" y1="80" x2="230" y2="720" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <line x1="770" y1="80" x2="770" y2="720" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          {/* Service boxes */}
          <line x1="230" y1="240" x2="770" y2="240" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <line x1="230" y1="560" x2="770" y2="560" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          {/* Center service line */}
          <line x1="500" y1="240" x2="500" y2="560" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          {/* Tennis Net with white headband */}
          <line x1="120" y1="400" x2="880" y2="400" stroke="#fff" strokeWidth="6" />
          <line x1="120" y1="400" x2="880" y2="400" stroke="rgba(192, 132, 252, 0.8)" strokeDasharray="4,4" strokeWidth="8" />
          {/* Net posts */}
          <circle cx="120" cy="400" r="8" fill="#facc15" />
          <circle cx="880" cy="400" r="8" fill="#facc15" />
        </svg>
      )

    case 'basketball':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-40 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Hardwood planks */}
          {Array.from({ length: 16 }).map((_, i) => (
            <line
              key={i}
              x1="0"
              y1={i * 50}
              x2="1000"
              y2={i * 50}
              stroke="rgba(254, 215, 170, 0.12)"
              strokeWidth="2"
            />
          ))}
          {/* Court boundary */}
          <rect x="80" y="60" width="840" height="680" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="4" />
          {/* Center line & circle */}
          <line x1="500" y1="60" x2="500" y2="740" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <circle cx="500" cy="400" r="80" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          {/* Left Key and 3-point line */}
          <rect x="80" y="280" width="190" height="240" fill="rgba(194, 65, 12, 0.2)" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <path d="M 80,160 L 190,160 A 240,240 0 0,1 190,640 L 80,640" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          {/* Hoop */}
          <circle cx="140" cy="400" r="16" fill="none" stroke="#f97316" strokeWidth="4" />
          {/* Right Key and 3-point line */}
          <rect x="730" y="280" width="190" height="240" fill="rgba(194, 65, 12, 0.2)" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <path d="M 920,160 L 810,160 A 240,240 0 0,0 810,640 L 920,640" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <circle cx="860" cy="400" r="16" fill="none" stroke="#f97316" strokeWidth="4" />
        </svg>
      )

    case 'badminton':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-45 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Green Court mat */}
          <rect x="180" y="100" width="640" height="600" fill="rgba(20, 184, 166, 0.2)" stroke="rgba(255,255,255,0.7)" strokeWidth="4" />
          {/* Singles lines */}
          <line x1="230" y1="100" x2="230" y2="700" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <line x1="770" y1="100" x2="770" y2="700" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          {/* Net Line */}
          <line x1="150" y1="400" x2="850" y2="400" stroke="#fff" strokeWidth="6" />
          <line x1="150" y1="400" x2="850" y2="400" stroke="rgba(56, 189, 248, 0.8)" strokeDasharray="3,3" strokeWidth="8" />
          {/* Short service lines */}
          <line x1="180" y1="330" x2="820" y2="330" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <line x1="180" y1="470" x2="820" y2="470" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          {/* Center line */}
          <line x1="500" y1="100" x2="500" y2="330" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
          <line x1="500" y1="470" x2="500" y2="700" stroke="rgba(255,255,255,0.6)" strokeWidth="3" />
        </svg>
      )

    case 'golf':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-45 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Rolling Fairway Contours */}
          <path d="M 0,350 Q 250,280 500,340 T 1000,300 L 1000,800 L 0,800 Z" fill="rgba(34, 197, 94, 0.2)" />
          <path d="M 0,480 Q 300,420 650,510 T 1000,460 L 1000,800 L 0,800 Z" fill="rgba(21, 128, 61, 0.3)" />
          {/* Sand Bunker */}
          <ellipse cx="320" cy="560" rx="90" ry="45" fill="rgba(253, 224, 71, 0.25)" stroke="rgba(250, 204, 21, 0.5)" strokeWidth="2" />
          {/* Putting Green */}
          <ellipse cx="680" cy="520" rx="140" ry="70" fill="rgba(74, 222, 128, 0.35)" stroke="rgba(255,255,255,0.4)" strokeWidth="3" />
          {/* Hole cup */}
          <ellipse cx="710" cy="520" rx="12" ry="6" fill="#0f172a" />
          {/* Flagstick & red pennant */}
          <line x1="710" y1="520" x2="710" y2="400" stroke="#fff" strokeWidth="4" />
          <polygon points="710,400 755,420 710,440" fill="#ef4444" />
        </svg>
      )

    case 'motorsport':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-45 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <pattern id="checkers" width="30" height="30" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="15" height="15" fill="#fff" />
              <rect x="15" y="15" width="15" height="15" fill="#fff" />
              <rect x="15" y="0" width="15" height="15" fill="#000" />
              <rect x="0" y="15" width="15" height="15" fill="#000" />
            </pattern>
            <pattern id="curbs" width="40" height="20" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="20" height="20" fill="#ef4444" />
              <rect x="20" y="0" width="20" height="20" fill="#ffffff" />
            </pattern>
          </defs>
          {/* High speed tracks with rumble curbs */}
          <path d="M -50,650 C 250,600 400,300 700,250 S 1050,450 1100,500" fill="none" stroke="rgba(15, 23, 42, 0.7)" strokeWidth="180" />
          <path d="M -50,650 C 250,600 400,300 700,250 S 1050,450 1100,500" fill="none" stroke="url(#curbs)" strokeWidth="18" strokeDasharray="20,20" />
          <path d="M -50,650 C 250,600 400,300 700,250 S 1050,450 1100,500" fill="none" stroke="#38bdf8" strokeWidth="4" strokeDasharray="16,30" opacity="0.8" />
          {/* Speed blur lines */}
          <line x1="50" y1="120" x2="350" y2="120" stroke="rgba(239, 68, 68, 0.6)" strokeWidth="3" strokeDasharray="20,10" />
          <line x1="120" y1="160" x2="520" y2="160" stroke="rgba(250, 204, 21, 0.6)" strokeWidth="2" strokeDasharray="40,20" />
          <line x1="80" y1="200" x2="400" y2="200" stroke="rgba(56, 189, 248, 0.7)" strokeWidth="3" strokeDasharray="30,15" />
          {/* Finish line checker strip */}
          <rect x="420" y="240" width="80" height="140" fill="url(#checkers)" transform="rotate(-25 420 240)" opacity="0.6" />
        </svg>
      )

    case 'athletics':
      return (
        <svg
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover pointer-events-none opacity-45 mix-blend-screen"
          preserveAspectRatio="none"
          viewBox="0 0 1000 800"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Tartan curved track lanes */}
          {Array.from({ length: 8 }).map((_, i) => {
            const offset = i * 26
            return (
              <g key={i}>
                <path
                  d={`M -50,${750 - offset} C 350,${750 - offset} 550,${200 + offset} 1050,${200 + offset}`}
                  fill="none"
                  stroke="rgba(255,255,255,0.45)"
                  strokeWidth="3"
                />
                <text
                  x={120 + i * 18}
                  y={680 - offset}
                  fill="#fef08a"
                  fontSize="22"
                  fontWeight="900"
                  fontFamily="'Anton', sans-serif"
                >
                  {i + 1}
                </text>
              </g>
            )
          })}
          {/* Finish Line */}
          <line x1="850" y1="180" x2="850" y2="450" stroke="#fff" strokeWidth="6" />
          <line x1="860" y1="180" x2="860" y2="450" stroke="#facc15" strokeDasharray="6,6" strokeWidth="4" />
        </svg>
      )

    default:
      return null
  }
}

export function FloatingSportObject({
  type,
  className = '',
}: {
  type: string
  className?: string
}) {
  switch (type) {
    case 'football':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="ballShine" cx="35%" cy="30%" r="65%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="60%" stopColor="#e2e8f0" />
              <stop offset="100%" stopColor="#64748b" />
            </radialGradient>
            <filter id="ballShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="8" stdDeviation="6" floodColor="#022c22" floodOpacity="0.6" />
            </filter>
          </defs>
          <circle cx="50" cy="50" r="44" fill="url(#ballShine)" filter="url(#ballShadow)" stroke="#0f172a" strokeWidth="2" />
          {/* Classic 32-panel football pentagons */}
          <polygon points="50,22 62,32 58,45 42,45 38,32" fill="#0f172a" />
          <polygon points="50,78 62,68 58,55 42,55 38,68" fill="#0f172a" />
          <polygon points="20,50 28,38 40,43 39,57 26,62" fill="#0f172a" />
          <polygon points="80,50 72,38 60,43 61,57 74,62" fill="#0f172a" />
          {/* Seams */}
          <line x1="50" y1="22" x2="50" y2="6" stroke="#0f172a" strokeWidth="2.5" />
          <line x1="62" y1="32" x2="72" y2="38" stroke="#0f172a" strokeWidth="2.5" />
          <line x1="58" y1="45" x2="60" y2="55" stroke="#0f172a" strokeWidth="2.5" />
          <line x1="42" y1="45" x2="40" y2="55" stroke="#0f172a" strokeWidth="2.5" />
          <line x1="38" y1="32" x2="28" y2="38" stroke="#0f172a" strokeWidth="2.5" />
        </svg>
      )

    case 'cricket_ball':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="cricketRed" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#f87171" />
              <stop offset="45%" stopColor="#dc2626" />
              <stop offset="100%" stopColor="#7f1d1d" />
            </radialGradient>
          </defs>
          <circle cx="50" cy="50" r="44" fill="url(#cricketRed)" stroke="#991b1b" strokeWidth="2" />
          {/* Stitched Seam */}
          <path d="M 12,30 Q 50,65 88,30" fill="none" stroke="#fff" strokeWidth="3" />
          <path d="M 12,30 Q 50,65 88,30" fill="none" stroke="#fef08a" strokeDasharray="3,3" strokeWidth="5" />
          {/* Highlights */}
          <ellipse cx="36" cy="28" rx="8" ry="4" fill="rgba(255,255,255,0.4)" transform="rotate(-15 36 28)" />
        </svg>
      )

    case 'tennis_ball':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="tennisFelt" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#bef264" />
              <stop offset="55%" stopColor="#a3e635" />
              <stop offset="100%" stopColor="#4d7c0f" />
            </radialGradient>
          </defs>
          <circle cx="50" cy="50" r="44" fill="url(#tennisFelt)" stroke="#3f6212" strokeWidth="2" />
          {/* Curved tennis seams */}
          <path d="M 22,18 C 36,36 36,64 22,82" fill="none" stroke="#ffffff" strokeWidth="4.5" strokeLinecap="round" />
          <path d="M 78,18 C 64,36 64,64 78,82" fill="none" stroke="#ffffff" strokeWidth="4.5" strokeLinecap="round" />
          <ellipse cx="38" cy="26" rx="7" ry="4" fill="rgba(255,255,255,0.5)" transform="rotate(-25 38 26)" />
        </svg>
      )

    case 'basketball':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="bballOrange" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#fb923c" />
              <stop offset="50%" stopColor="#ea580c" />
              <stop offset="100%" stopColor="#9a3412" />
            </radialGradient>
          </defs>
          <circle cx="50" cy="50" r="44" fill="url(#bballOrange)" stroke="#7c2d12" strokeWidth="2.5" />
          {/* Basketball Ribs */}
          <line x1="6" y1="50" x2="94" y2="50" stroke="#1c1917" strokeWidth="3" />
          <line x1="50" y1="6" x2="50" y2="94" stroke="#1c1917" strokeWidth="3" />
          <path d="M 20,18 C 38,36 38,64 20,82" fill="none" stroke="#1c1917" strokeWidth="3" />
          <path d="M 80,18 C 62,36 62,64 80,82" fill="none" stroke="#1c1917" strokeWidth="3" />
          <ellipse cx="34" cy="24" rx="8" ry="4" fill="rgba(255,255,255,0.35)" transform="rotate(-20 34 24)" />
        </svg>
      )

    case 'shuttlecock':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          {/* Feathers fan */}
          <polygon points="50,60 18,15 82,15" fill="rgba(255,255,255,0.95)" stroke="#cbd5e1" strokeWidth="2" />
          {/* Feather ribs */}
          {Array.from({ length: 6 }).map((_, i) => (
            <line
              key={i}
              x1={26 + i * 9.5}
              y1="16"
              x2="50"
              y2="60"
              stroke="#94a3b8"
              strokeWidth="1.5"
            />
          ))}
          {/* Thread rings */}
          <path d="M 26,28 Q 50,33 74,28" fill="none" stroke="#38bdf8" strokeWidth="2.5" />
          <path d="M 33,42 Q 50,46 67,42" fill="none" stroke="#38bdf8" strokeWidth="2.5" />
          {/* Cork dome */}
          <path d="M 40,60 Q 50,85 60,60 Z" fill="#fde047" stroke="#ca8a04" strokeWidth="2" />
          <circle cx="50" cy="72" r="12" fill="#fef08a" stroke="#ca8a04" strokeWidth="2" />
        </svg>
      )

    case 'golf_ball':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="golfShine" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="65%" stopColor="#f1f5f9" />
              <stop offset="100%" stopColor="#94a3b8" />
            </radialGradient>
          </defs>
          <circle cx="50" cy="50" r="44" fill="url(#golfShine)" stroke="#64748b" strokeWidth="1.5" />
          {/* Dimple matrix */}
          {[
            [30, 30], [50, 25], [70, 30],
            [25, 50], [40, 45], [60, 45], [75, 50],
            [32, 68], [50, 65], [68, 68],
          ].map(([cx, cy], idx) => (
            <circle key={idx} cx={cx} cy={cy} r="3.5" fill="#cbd5e1" opacity="0.8" />
          ))}
        </svg>
      )

    case 'chequered_flag':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          {/* Flagpole */}
          <line x1="20" y1="15" x2="20" y2="92" stroke="#e2e8f0" strokeWidth="5" strokeLinecap="round" />
          <circle cx="20" cy="14" r="5" fill="#facc15" />
          {/* Waving checkered flag */}
          <path d="M 20,20 C 45,15 55,28 80,22 L 80,62 C 55,68 45,55 20,60 Z" fill="#0f172a" stroke="#ffffff" strokeWidth="2" />
          <rect x="22" y="24" width="12" height="12" fill="#fff" />
          <rect x="46" y="22" width="12" height="12" fill="#fff" />
          <rect x="68" y="26" width="10" height="12" fill="#fff" />
          <rect x="34" y="36" width="12" height="12" fill="#fff" />
          <rect x="58" y="34" width="12" height="12" fill="#fff" />
          <rect x="22" y="48" width="12" height="10" fill="#fff" />
          <rect x="46" y="46" width="12" height="10" fill="#fff" />
          <rect x="68" y="50" width="10" height="10" fill="#fff" />
        </svg>
      )

    case 'running_spikes':
      return (
        <svg viewBox="0 0 100 100" className={className} xmlns="http://www.w3.org/2000/svg">
          {/* Golden running shoe profile */}
          <path
            d="M 12,65 Q 22,45 42,42 L 56,38 Q 65,48 76,52 L 92,62 Q 88,72 70,72 L 20,72 Q 10,72 12,65 Z"
            fill="#facc15"
            stroke="#b45309"
            strokeWidth="3"
          />
          {/* Sprint track spikes at sole */}
          <polygon points="26,72 30,82 34,72" fill="#94a3b8" />
          <polygon points="42,72 46,84 50,72" fill="#94a3b8" />
          <polygon points="58,72 62,84 66,72" fill="#94a3b8" />
          <polygon points="74,72 78,82 82,72" fill="#94a3b8" />
          {/* Dynamic wing / swoosh */}
          <path d="M 32,55 Q 52,48 74,58" fill="none" stroke="#ef4444" strokeWidth="4" strokeLinecap="round" />
        </svg>
      )

    default:
      return null
  }
}

export function TrophyBadge({
  size = 36,
  color = '#facc15',
  className = '',
}: {
  size?: number
  color?: string
  className?: string
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M16 12H48V28C48 36.8366 40.8366 44 32 44C23.1634 44 16 36.8366 16 28V12Z"
        fill={color}
        stroke="#fff"
        strokeWidth="3"
      />
      <path
        d="M16 16H8C8 26 14 30 18 32"
        stroke={color}
        strokeWidth="4"
        strokeLinecap="round"
      />
      <path
        d="M48 16H56C56 26 50 30 46 32"
        stroke={color}
        strokeWidth="4"
        strokeLinecap="round"
      />
      <rect x="28" y="44" width="8" height="10" fill={color} />
      <rect x="20" y="54" width="24" height="6" rx="2" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="2" />
      <polygon points="32,20 34,25 39,25 35,28 37,33 32,30 27,33 29,28 25,25 30,25" fill="#ffffff" />
    </svg>
  )
}
