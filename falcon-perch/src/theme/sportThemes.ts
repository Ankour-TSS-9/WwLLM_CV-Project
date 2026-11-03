import type { Sport } from '../types'

export interface SportStat {
  label: string
  userVal: number
  proVal: number
  unit?: string
}

export interface SportScoreboard {
  tournamentName: string
  proName: string
  proSlug: string
  proRating: number
  userRating: number
  proRole: string
  proImage: string
  proSilhouetteColor: string
  stats: SportStat[]
}

export interface SportThemeConfig {
  id: Sport
  name: string
  icon: string
  tagline: string
  headlineAccent: string
  primaryColor: string
  secondaryColor: string
  accentColor: string
  glowColor: string
  bgGradient: string
  cardGlass: string
  borderColor: string
  btnShadow: string
  courtType: 'football' | 'cricket' | 'tennis' | 'basketball' | 'badminton' | 'golf' | 'motorsport' | 'athletics'
  floatingObject: {
    type: 'football' | 'cricket_ball' | 'tennis_ball' | 'basketball' | 'shuttlecock' | 'golf_ball' | 'chequered_flag' | 'running_spikes'
    label: string
  }
  scoreboard: SportScoreboard
}

export const SPORT_THEMES: Record<Sport, SportThemeConfig> = {
  football: {
    id: 'football',
    name: 'Football',
    icon: '⚽',
    tagline: 'Master the Beautiful Game',
    headlineAccent: 'from-emerald-400 via-green-300 to-yellow-300',
    primaryColor: '#10b981',
    secondaryColor: '#047857',
    accentColor: '#facc15',
    glowColor: 'rgba(16, 185, 129, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #15803d 0%, #064e3b 50%, #022c22 100%)',
    cardGlass: 'rgba(6, 78, 59, 0.65)',
    borderColor: 'rgba(52, 211, 153, 0.4)',
    btnShadow: '#065f46',
    courtType: 'football',
    floatingObject: {
      type: 'football',
      label: 'Pro Match Ball',
    },
    scoreboard: {
      tournamentName: 'CHAMPIONS LEAGUE SHOWDOWN',
      proName: 'Cristiano Ronaldo',
      proSlug: 'ronaldo',
      proRating: 94,
      userRating: 78,
      proRole: '5x Ballon d’Or · Real Madrid Legend',
      proImage: '/idols/ronaldo.jpeg',
      proSilhouetteColor: '#10b981',
      stats: [
        { label: 'Overall Technique', userVal: 78, proVal: 94, unit: 'pts' },
        { label: 'Shot Velocity & Dip', userVal: 72, proVal: 96, unit: 'km/h' },
        { label: 'Hip Rotation & Whip', userVal: 81, proVal: 93, unit: 'deg' },
        { label: 'Target Corner Accuracy', userVal: 75, proVal: 97, unit: '%' },
      ],
    },
  },

  cricket: {
    id: 'cricket',
    name: 'Cricket',
    icon: '🏏',
    tagline: 'Precision at the Crease',
    headlineAccent: 'from-amber-400 via-yellow-200 to-red-400',
    primaryColor: '#eab308',
    secondaryColor: '#15803d',
    accentColor: '#ef4444',
    glowColor: 'rgba(234, 179, 8, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #854d0e 0%, #166534 45%, #052e16 100%)',
    cardGlass: 'rgba(22, 101, 52, 0.7)',
    borderColor: 'rgba(250, 204, 21, 0.45)',
    btnShadow: '#713f12',
    courtType: 'cricket',
    floatingObject: {
      type: 'cricket_ball',
      label: 'Kookaburra Red Ball',
    },
    scoreboard: {
      tournamentName: 'WORLD CUP CRICKET CLASH',
      proName: 'Virat Kohli',
      proSlug: 'kohli',
      proRating: 93,
      userRating: 76,
      proRole: 'ICC Player of the Decade · India',
      proImage: '/idols/kohli.jpeg',
      proSilhouetteColor: '#eab308',
      stats: [
        { label: 'Cover Drive Flow', userVal: 76, proVal: 95, unit: 'pts' },
        { label: 'Head Position at Impact', userVal: 80, proVal: 98, unit: '%' },
        { label: 'Wrist Snap Velocity', userVal: 71, proVal: 92, unit: 'km/h' },
        { label: 'Gap Finding Placement', userVal: 74, proVal: 96, unit: '%' },
      ],
    },
  },

  tennis: {
    id: 'tennis',
    name: 'Tennis',
    icon: '🎾',
    tagline: 'Championship Court Domination',
    headlineAccent: 'from-cyan-400 via-indigo-300 to-purple-400',
    primaryColor: '#6366f1',
    secondaryColor: '#2563eb',
    accentColor: '#a855f7',
    glowColor: 'rgba(168, 85, 247, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #4338ca 0%, #1e1b4b 50%, #0f172a 100%)',
    cardGlass: 'rgba(30, 27, 75, 0.75)',
    borderColor: 'rgba(168, 85, 247, 0.45)',
    btnShadow: '#312e81',
    courtType: 'tennis',
    floatingObject: {
      type: 'tennis_ball',
      label: 'Optic Yellow Tennis Ball',
    },
    scoreboard: {
      tournamentName: 'AUSTRALIAN OPEN FINAL',
      proName: 'Novak Djokovic',
      proSlug: 'novak',
      proRating: 96,
      userRating: 79,
      proRole: '24x Grand Slam Champion',
      proImage: '/idols/novak.jpeg',
      proSilhouetteColor: '#818cf8',
      stats: [
        { label: 'First Serve Penetration', userVal: 79, proVal: 96, unit: 'pts' },
        { label: 'Deep Return of Serve', userVal: 73, proVal: 99, unit: '%' },
        { label: 'Open Stance Forehand', userVal: 82, proVal: 95, unit: 'pts' },
        { label: 'Court Recovery Speed', userVal: 77, proVal: 94, unit: 'm/s' },
      ],
    },
  },

  basketball: {
    id: 'basketball',
    name: 'Basketball',
    icon: '🏀',
    tagline: 'Own the Hardwood',
    headlineAccent: 'from-orange-400 via-amber-300 to-rose-400',
    primaryColor: '#f97316',
    secondaryColor: '#c2410c',
    accentColor: '#fbbf24',
    glowColor: 'rgba(249, 115, 22, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #c2410c 0%, #7c2d12 45%, #271008 100%)',
    cardGlass: 'rgba(124, 45, 18, 0.75)',
    borderColor: 'rgba(251, 146, 60, 0.45)',
    btnShadow: '#7c2d12',
    courtType: 'basketball',
    floatingObject: {
      type: 'basketball',
      label: 'Spalding Official Ball',
    },
    scoreboard: {
      tournamentName: 'NBA FINALS SHOWCASE',
      proName: 'LeBron James',
      proSlug: 'lebron',
      proRating: 95,
      userRating: 77,
      proRole: '4x NBA Champion · All-Time Scoring Leader',
      proImage: '/idols/lebron.jpeg',
      proSilhouetteColor: '#f97316',
      stats: [
        { label: 'Jump Shot Release Arc', userVal: 77, proVal: 95, unit: 'deg' },
        { label: 'Crossover Drive Burst', userVal: 74, proVal: 96, unit: 'm/s' },
        { label: 'Rim Finishing Touch', userVal: 81, proVal: 97, unit: '%' },
        { label: 'Defensive Stance Balance', userVal: 75, proVal: 93, unit: 'pts' },
      ],
    },
  },

  badminton: {
    id: 'badminton',
    name: 'Badminton',
    icon: '🏸',
    tagline: 'Lightning Fast Rallies',
    headlineAccent: 'from-teal-300 via-cyan-200 to-indigo-400',
    primaryColor: '#14b8a6',
    secondaryColor: '#0f766e',
    accentColor: '#38bdf8',
    glowColor: 'rgba(20, 184, 166, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #0f766e 0%, #1e1b4b 50%, #042f2e 100%)',
    cardGlass: 'rgba(15, 118, 110, 0.65)',
    borderColor: 'rgba(45, 212, 191, 0.4)',
    btnShadow: '#115e59',
    courtType: 'badminton',
    floatingObject: {
      type: 'shuttlecock',
      label: 'Yonex Feather Shuttle',
    },
    scoreboard: {
      tournamentName: 'ALL ENGLAND SUPER SERIES',
      proName: 'PV Sindhu',
      proSlug: 'pv sindhu',
      proRating: 93,
      userRating: 75,
      proRole: 'World Champion · 2x Olympic Medalist',
      proImage: '/idols/pv%20sindhu.jpeg',
      proSilhouetteColor: '#14b8a6',
      stats: [
        { label: 'Jump Smash Steepness', userVal: 75, proVal: 96, unit: 'deg' },
        { label: 'Smash Speed', userVal: 70, proVal: 98, unit: 'km/h' },
        { label: 'Net Tumbling Spin', userVal: 78, proVal: 91, unit: 'pts' },
        { label: 'Footwork Split Step', userVal: 76, proVal: 94, unit: 'ms' },
      ],
    },
  },

  golf: {
    id: 'golf',
    name: 'Golf',
    icon: '⛳',
    tagline: 'The Perfect Kinetic Swing',
    headlineAccent: 'from-emerald-300 via-sky-200 to-yellow-300',
    primaryColor: '#22c55e',
    secondaryColor: '#0284c7',
    accentColor: '#fbbf24',
    glowColor: 'rgba(34, 197, 94, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #0369a1 0%, #15803d 45%, #052e16 100%)',
    cardGlass: 'rgba(21, 128, 61, 0.7)',
    borderColor: 'rgba(74, 222, 128, 0.45)',
    btnShadow: '#166534',
    courtType: 'golf',
    floatingObject: {
      type: 'golf_ball',
      label: 'Titleist Pro V1',
    },
    scoreboard: {
      tournamentName: 'THE MASTERS TOURNAMENT',
      proName: 'Tiger Woods',
      proSlug: 'tiger',
      proRating: 95,
      userRating: 76,
      proRole: '15x Major Champion · 82 PGA Wins',
      proImage: '/idols/tiger.jpeg',
      proSilhouetteColor: '#22c55e',
      stats: [
        { label: 'Clubhead Swing Speed', userVal: 76, proVal: 96, unit: 'mph' },
        { label: 'Hip Clearance at Impact', userVal: 72, proVal: 98, unit: 'deg' },
        { label: 'Fairway Driving Accuracy', userVal: 79, proVal: 93, unit: '%' },
        { label: 'Putting Green Distance Control', userVal: 78, proVal: 95, unit: 'pts' },
      ],
    },
  },

  motorsport: {
    id: 'motorsport',
    name: 'Motorsport',
    icon: '🏎️',
    tagline: 'Apex Speed & Precision',
    headlineAccent: 'from-red-400 via-amber-300 to-cyan-400',
    primaryColor: '#ef4444',
    secondaryColor: '#0284c7',
    accentColor: '#facc15',
    glowColor: 'rgba(239, 68, 68, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #991b1b 0%, #1e293b 50%, #090d16 100%)',
    cardGlass: 'rgba(153, 27, 27, 0.65)',
    borderColor: 'rgba(248, 113, 113, 0.45)',
    btnShadow: '#7f1d1d',
    courtType: 'motorsport',
    floatingObject: {
      type: 'chequered_flag',
      label: 'Chequered Finish Flag',
    },
    scoreboard: {
      tournamentName: 'MONACO GRAND PRIX',
      proName: 'Lewis Hamilton',
      proSlug: 'hamilton',
      proRating: 97,
      userRating: 80,
      proRole: '7x Formula 1 World Champion',
      proImage: '/idols/hamilton.jpeg',
      proSilhouetteColor: '#ef4444',
      stats: [
        { label: 'Apex Braking Deceleration', userVal: 80, proVal: 98, unit: 'G' },
        { label: 'Throttle Smoothness', userVal: 75, proVal: 97, unit: '%' },
        { label: 'Corner Entry Steering Lock', userVal: 83, proVal: 95, unit: 'deg' },
        { label: 'Sector Delta Time', userVal: 81, proVal: 99, unit: 'pts' },
      ],
    },
  },

  athletics: {
    id: 'athletics',
    name: 'Athletics',
    icon: '🏃',
    tagline: 'Pure Explosive Power',
    headlineAccent: 'from-amber-400 via-orange-300 to-red-400',
    primaryColor: '#f59e0b',
    secondaryColor: '#b91c1c',
    accentColor: '#38bdf8',
    glowColor: 'rgba(245, 158, 11, 0.45)',
    bgGradient: 'radial-gradient(ellipse at 50% 20%, #b91c1c 0%, #78350f 45%, #180903 100%)',
    cardGlass: 'rgba(185, 28, 28, 0.65)',
    borderColor: 'rgba(251, 191, 36, 0.45)',
    btnShadow: '#92400e',
    courtType: 'athletics',
    floatingObject: {
      type: 'running_spikes',
      label: 'Gold Track Spikes',
    },
    scoreboard: {
      tournamentName: 'OLYMPIC 100M FINAL',
      proName: 'Usain Bolt',
      proSlug: 'usain bolt',
      proRating: 98,
      userRating: 77,
      proRole: '8x Olympic Gold · 9.58s WR Holder',
      proImage: '/idols/usain%20bolt.jpeg',
      proSilhouetteColor: '#f59e0b',
      stats: [
        { label: 'Sprint Stride Frequency', userVal: 77, proVal: 99, unit: 'Hz' },
        { label: 'Ground Contact Efficiency', userVal: 74, proVal: 98, unit: 'ms' },
        { label: 'Torso Drive Angle', userVal: 81, proVal: 96, unit: 'deg' },
        { label: 'Top End Acceleration', userVal: 76, proVal: 100, unit: 'm/s' },
      ],
    },
  },
}

export function getSportTheme(sport: Sport = 'football'): SportThemeConfig {
  return SPORT_THEMES[sport] ?? SPORT_THEMES.football
}

