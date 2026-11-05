import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MatchChat } from '@/components/MatchChat'
import { CommentaryPlayer } from '@/components/CommentaryPlayer'
import { analyze } from '@/services/analysisService'
import type { AnalysisRecord } from '@/types'
import { SPORTS, type Sport } from '@/types'
import { getSportTheme } from '@/theme/sportThemes'
import { SportFieldBackground, FloatingSportObject } from '@/theme/SportVisuals'

// Auto-cycle interval in milliseconds
const CYCLE_INTERVAL = 4000

export function AIFeaturesDemo() {
  const [selectedPlayer, setSelectedPlayer] = useState<number>(1)
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<AnalysisRecord | null>(null)
  const [activeTab, setActiveTab] = useState<'coach' | 'commentary' | 'chat'>('coach')
  const [matchId, setMatchId] = useState<string>('default')
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [players, setPlayers] = useState<Array<{ id: number; name: string; team: number; role: string }>>([
    { id: 1, name: 'Player 1', team: 1, role: 'Attacker' },
    { id: 12, name: 'Player 12', team: 1, role: 'Midfielder' },
    { id: 16, name: 'Player 16', team: 1, role: 'Forward' },
    { id: 7, name: 'Player 7', team: 1, role: 'Winger' },
  ])

  // Auto-cycling sport background
  const [currentSportIndex, setCurrentSportIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const currentSport: Sport = SPORTS[currentSportIndex]
  const activeTheme = getSportTheme(currentSport)

  // Auto-cycle through sports
  useEffect(() => {
    if (isPaused) return
    timerRef.current = setTimeout(() => {
      setCurrentSportIndex((prev) => (prev + 1) % SPORTS.length)
    }, CYCLE_INTERVAL)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [currentSportIndex, isPaused])

  function handleSportClick(index: number) {
    setCurrentSportIndex(index)
    setIsPaused(true)
    // Resume cycling after 10 seconds of manual pause
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setIsPaused(false), 10000)
  }

  // Fetch players from match data
  const fetchPlayersFromMatch = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/match/${id}/stats`)
      if (response.ok) {
        const data = await response.json()
        const matchPlayers = data.stats?.players || []
        const playerList = matchPlayers.map((p: { player_id: number; team: number; role?: string }) => ({
          id: p.player_id,
          name: `Player ${p.player_id}`,
          team: p.team,
          role: p.role || 'Player',
        }))
        if (playerList.length > 0) {
          setPlayers(playerList)
          setSelectedPlayer(playerList[0].id)
        }
      }
    } catch (error) {
      console.error('Failed to fetch players:', error)
    }
  }

  const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setUploadLoading(true)
    setUploadStatus('Uploading video...')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch('http://localhost:8000/api/upload-video', {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }
      const data = await response.json()
      setMatchId(data.match_id)
      setUploadStatus(`✅ Video processed! Match ID: ${data.match_id}`)
      setReport(null)
      await fetchPlayersFromMatch(data.match_id)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Upload failed'
      setUploadStatus(`❌ Error: ${errorMsg}`)
      console.error('Upload error:', error)
    } finally {
      setUploadLoading(false)
    }
  }

  const generateReport = async () => {
    setLoading(true)
    try {
      const result = await analyze(
        { sport: 'football', skill: 'match-analysis' },
        selectedPlayer,
        matchId
      )
      setReport(result)
    } catch (error) {
      console.error('Failed to generate report:', error)
      alert(`Error: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      setLoading(false)
    }
  }

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'Brilliant': return 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
      case 'Great': return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
      case 'Good': return 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
      case 'Inaccuracy': return 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40'
      case 'Mistake': return 'bg-orange-500/20 text-orange-300 border border-orange-500/40'
      case 'Blunder': return 'bg-red-500/20 text-red-300 border border-red-500/40'
      default: return 'bg-white/10 text-white/60 border border-white/20'
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const tabs = [
    { key: 'coach' as const, label: 'AI Performance Coach', icon: '🏋️' },
    { key: 'commentary' as const, label: 'AI Commentary', icon: '🎙️' },
    { key: 'chat' as const, label: 'Match Analytics Chat', icon: '💬' },
  ]

  return (
    <div
      className="relative min-h-[calc(100vh-76px)] text-slate-100 overflow-hidden pb-20 transition-colors duration-700"
      style={{ background: activeTheme.bgGradient, fontFamily: "'Poppins', sans-serif" }}
    >
      {/* ── Animated Sport Background ── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentSport}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8 }}
          className="absolute inset-0 pointer-events-none z-0"
        >
          <SportFieldBackground sport={currentSport} />
          {/* Ambient glow blobs */}
          <div
            className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full blur-3xl opacity-30"
            style={{ background: activeTheme.primaryColor }}
          />
          <div
            className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full blur-3xl opacity-25"
            style={{ background: activeTheme.accentColor }}
          />
        </motion.div>
      </AnimatePresence>

      <div className="relative z-10 max-w-[1200px] mx-auto px-4 sm:px-8 pt-8">

        {/* ── Sport Indicator Strip ── */}
        <div className="flex items-center justify-between gap-4 flex-wrap mb-8 pb-4 border-b border-white/15">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-extrabold tracking-widest text-yellow-300">
              ARENA MODE:
            </span>
            <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-black/40 backdrop-blur-md border border-white/20 overflow-x-auto max-w-full">
              {SPORTS.map((sport, index) => {
                const sTheme = getSportTheme(sport)
                const isSelected = sport === currentSport
                return (
                  <button
                    key={sport}
                    type="button"
                    onClick={() => handleSportClick(index)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-black text-xs uppercase tracking-wider transition-all cursor-pointer whitespace-nowrap ${
                      isSelected
                        ? 'text-slate-950 shadow-md'
                        : 'text-white/70 hover:text-white hover:bg-white/10'
                    }`}
                    style={{
                      background: isSelected
                        ? `linear-gradient(135deg, ${sTheme.primaryColor}, ${sTheme.accentColor})`
                        : undefined,
                      boxShadow: isSelected ? `0 3px 0 ${sTheme.btnShadow}` : undefined,
                    }}
                  >
                    <span>{sTheme.icon}</span>
                    <span>{sTheme.name}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Auto-cycling indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-black/30 border border-white/15 backdrop-blur-md">
            <span
              className={`w-2 h-2 rounded-full ${isPaused ? 'bg-yellow-400' : 'bg-emerald-400 animate-pulse'}`}
            />
            <span className="text-xs font-bold text-white/60 uppercase tracking-wider">
              {isPaused ? 'Manual' : 'Auto-Cycling'}
            </span>
          </div>
        </div>

        {/* ── Hero Header ── */}
        <div className="flex items-start justify-between gap-6 mb-10">
          <div className="flex-1">
            {/* Floating sport object */}
            <AnimatePresence mode="wait">
              <motion.div
                key={currentSport + '-obj'}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.5 }}
                className="inline-block mb-4"
              >
                <motion.div
                  animate={{ y: [0, -10, 0], rotate: [0, 6, -4, 0] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <FloatingSportObject type={activeTheme.floatingObject.type} className="w-16 h-16" />
                </motion.div>
              </motion.div>
            </AnimatePresence>

            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/15 backdrop-blur-md border border-white/25 text-white font-black text-xs uppercase tracking-widest mb-3 shadow-md">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>VIDEO ANALYSIS STUDIO · {activeTheme.name.toUpperCase()}</span>
            </div>

            <AnimatePresence mode="wait">
              <motion.h1
                key={currentSport + '-title'}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.5 }}
                className="text-5xl sm:text-6xl font-black text-white uppercase tracking-tight leading-[0.95] drop-shadow-xl mb-3"
                style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
              >
                ANALYZE YOUR <br />
                <span
                  className={`bg-gradient-to-r ${activeTheme.headlineAccent} bg-clip-text text-transparent`}
                >
                  {activeTheme.name} GAME
                </span>
              </motion.h1>
            </AnimatePresence>

            <AnimatePresence mode="wait">
              <motion.p
                key={currentSport + '-desc'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="text-slate-200 text-sm max-w-xl font-medium leading-relaxed drop-shadow"
              >
                Upload your {activeTheme.name} footage, select a player, and let the AI coach generate
                kinematic insights benchmarked against {activeTheme.scoreboard.proName}.
              </motion.p>
            </AnimatePresence>
          </div>
        </div>

        {/* ── Tab Navigation ── */}
        <div className="flex items-center gap-1 p-1 mb-8 rounded-2xl bg-black/40 backdrop-blur-md border border-white/15 w-fit">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.key
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-black text-xs uppercase tracking-wider transition-all whitespace-nowrap ${
                  isActive
                    ? 'text-slate-950 shadow-md'
                    : 'text-white/70 hover:text-white hover:bg-white/10'
                }`}
                style={{
                  background: isActive
                    ? `linear-gradient(135deg, ${activeTheme.primaryColor}, ${activeTheme.accentColor})`
                    : undefined,
                  boxShadow: isActive ? `0 3px 0 ${activeTheme.btnShadow}` : undefined,
                }}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* ── Tab Content ── */}
        <div className="space-y-6">

          {/* ── AI Coach Tab ── */}
          {activeTab === 'coach' && (
            <div className="space-y-6">

              {/* Video Upload Card */}
              <div
                className="rounded-3xl p-6 border-2 border-dashed backdrop-blur-md shadow-xl"
                style={{
                  background: 'linear-gradient(145deg, rgba(0,0,0,0.5), rgba(15,23,42,0.75))',
                  borderColor: activeTheme.borderColor,
                  boxShadow: `0 15px 35px -10px ${activeTheme.glowColor}`,
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <span
                    className="font-mono text-xs font-black uppercase tracking-wider"
                    style={{ color: activeTheme.primaryColor }}
                  >
                    01 / UPLOAD FOOTAGE
                  </span>
                  <span className="text-2xl">📹</span>
                </div>
                <h3
                  className="text-2xl font-black text-white uppercase tracking-wide mb-2"
                  style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
                >
                  Upload {activeTheme.name} Video
                </h3>
                <p className="text-xs text-slate-300 font-medium leading-relaxed mb-5">
                  Upload a {activeTheme.name.toLowerCase()} match video. The CV pipeline will extract player
                  tracking data and AI will generate coaching insights.
                </p>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  onChange={handleVideoUpload}
                  disabled={uploadLoading}
                  className="hidden"
                  id="video-upload"
                />

                <label
                  htmlFor="video-upload"
                  className={`inline-flex items-center gap-2 px-7 py-3 rounded-2xl font-black text-sm uppercase tracking-wider transition-all cursor-pointer border-2 border-white/30 shadow-lg ${
                    uploadLoading ? 'opacity-60 cursor-not-allowed' : 'hover:scale-105 active:translate-y-1'
                  }`}
                  style={{
                    background: uploadLoading
                      ? 'rgba(255,255,255,0.1)'
                      : `linear-gradient(135deg, ${activeTheme.primaryColor}, ${activeTheme.accentColor})`,
                    color: uploadLoading ? '#fff' : '#0f172a',
                    boxShadow: uploadLoading ? 'none' : `0 5px 0 ${activeTheme.btnShadow}, 0 0 25px ${activeTheme.glowColor}`,
                  }}
                >
                  {uploadLoading ? (
                    <>
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25" />
                        <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" opacity="0.75" />
                      </svg>
                      Processing...
                    </>
                  ) : (
                    <>
                      <span>⚡</span>
                      <span>Choose Video File</span>
                    </>
                  )}
                </label>

                {uploadStatus && (
                  <motion.div
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`mt-4 rounded-2xl p-3 text-xs font-bold border ${
                      uploadStatus.includes('❌')
                        ? 'bg-red-500/20 text-red-300 border-red-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    }`}
                  >
                    {uploadStatus}
                  </motion.div>
                )}

                {matchId !== 'default' && (
                  <div className="mt-4 rounded-2xl bg-white/10 border border-white/20 p-3">
                    <p className="text-xs font-bold text-white/70">
                      <span className="text-yellow-300">CURRENT MATCH:</span> {matchId}
                    </p>
                  </div>
                )}
              </div>

              {/* Player Selection Card */}
              <div
                className="rounded-3xl p-6 border backdrop-blur-md shadow-xl"
                style={{
                  background: 'linear-gradient(145deg, rgba(0,0,0,0.5), rgba(15,23,42,0.75))',
                  borderColor: activeTheme.borderColor,
                  boxShadow: `0 15px 35px -10px ${activeTheme.glowColor}`,
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <span
                    className="font-mono text-xs font-black uppercase tracking-wider"
                    style={{ color: activeTheme.primaryColor }}
                  >
                    02 / SELECT PLAYER
                  </span>
                  <span className="text-2xl">{activeTheme.icon}</span>
                </div>
                <h3
                  className="text-2xl font-black text-white uppercase tracking-wide mb-4"
                  style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
                >
                  Select Player for Analysis
                </h3>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {players.map((player) => (
                    <button
                      key={player.id}
                      type="button"
                      onClick={() => setSelectedPlayer(player.id)}
                      className={`rounded-2xl p-4 text-left transition-all border-2 font-bold ${
                        selectedPlayer === player.id
                          ? 'text-slate-950 shadow-lg scale-[1.03]'
                          : 'bg-white/5 hover:bg-white/10 text-white/80 border-white/15'
                      }`}
                      style={
                        selectedPlayer === player.id
                          ? {
                              background: `linear-gradient(135deg, ${activeTheme.primaryColor}, ${activeTheme.accentColor})`,
                              borderColor: activeTheme.primaryColor,
                              boxShadow: `0 4px 0 ${activeTheme.btnShadow}, 0 0 20px ${activeTheme.glowColor}`,
                            }
                          : undefined
                      }
                    >
                      <div className="mb-1 text-2xl">{activeTheme.icon}</div>
                      <div className="text-sm font-black uppercase">{player.name}</div>
                      <div className="text-xs opacity-70 mt-0.5">
                        Team {player.team} · {player.role}
                      </div>
                    </button>
                  ))}
                </div>

                <button
                  onClick={generateReport}
                  disabled={loading}
                  className={`mt-5 w-full rounded-2xl py-3.5 font-black text-sm uppercase tracking-wider transition-all border-2 border-white/30 shadow-lg ${
                    loading ? 'opacity-60 cursor-not-allowed' : 'hover:scale-[1.01] active:translate-y-1'
                  }`}
                  style={{
                    background: loading
                      ? 'rgba(255,255,255,0.1)'
                      : `linear-gradient(135deg, ${activeTheme.primaryColor}, ${activeTheme.accentColor})`,
                    color: loading ? '#fff' : '#0f172a',
                    boxShadow: loading ? 'none' : `0 5px 0 ${activeTheme.btnShadow}, 0 0 25px ${activeTheme.glowColor}`,
                  }}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25" />
                        <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" opacity="0.75" />
                      </svg>
                      Generating AI Report...
                    </span>
                  ) : (
                    '⚡ Generate AI Coach Report'
                  )}
                </button>
              </div>

              {/* Report Display */}
              {report && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="space-y-5"
                >
                  {/* Overall Score */}
                  <div
                    className="rounded-3xl p-6 border backdrop-blur-md shadow-xl"
                    style={{
                      background: 'linear-gradient(145deg, rgba(0,0,0,0.5), rgba(15,23,42,0.75))',
                      borderColor: activeTheme.borderColor,
                    }}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <span
                        className="font-mono text-xs font-black uppercase tracking-wider"
                        style={{ color: activeTheme.primaryColor }}
                      >
                        03 / PERFORMANCE SUMMARY
                      </span>
                      <span className="text-2xl">📊</span>
                    </div>
                    <h3
                      className="text-2xl font-black text-white uppercase tracking-wide mb-5"
                      style={{ fontFamily: "'Anton', 'Bebas Neue', sans-serif" }}
                    >
                      Performance Summary
                    </h3>
                    <div className="grid grid-cols-2 gap-6 mb-4">
                      <div
                        className="rounded-2xl p-4 border"
                        style={{ background: 'rgba(0,0,0,0.3)', borderColor: activeTheme.borderColor }}
                      >
                        <div className="text-xs font-bold text-white/50 uppercase tracking-wider mb-1">Overall Score</div>
                        <div
                          className="text-5xl font-black"
                          style={{ fontFamily: "'Anton', sans-serif", color: activeTheme.primaryColor }}
                        >
                          {report.overall_score}
                          <span className="text-xl text-white/40">/100</span>
                        </div>
                      </div>
                      <div
                        className="rounded-2xl p-4 border"
                        style={{ background: 'rgba(0,0,0,0.3)', borderColor: activeTheme.borderColor }}
                      >
                        <div className="text-xs font-bold text-white/50 uppercase tracking-wider mb-1">Accuracy</div>
                        <div
                          className="text-5xl font-black"
                          style={{ fontFamily: "'Anton', sans-serif", color: activeTheme.accentColor }}
                        >
                          {report.accuracy_percent}
                          <span className="text-xl text-white/40">%</span>
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-slate-300 font-medium leading-relaxed">{report.summary}</p>
                  </div>

                  {/* Strengths & Weaknesses */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div
                      className="rounded-3xl p-6 border backdrop-blur-md shadow-xl"
                      style={{
                        background: 'linear-gradient(145deg, rgba(6,78,59,0.4), rgba(0,0,0,0.5))',
                        borderColor: 'rgba(52, 211, 153, 0.3)',
                      }}
                    >
                      <h3
                        className="text-xl font-black text-white uppercase tracking-wide mb-4 flex items-center gap-2"
                        style={{ fontFamily: "'Anton', sans-serif" }}
                      >
                        <span>💪</span> Strengths
                      </h3>
                      <ul className="space-y-2.5">
                        {report.strengths.map((strength: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-emerald-400 font-black mt-0.5">✓</span>
                            <span className="text-sm text-slate-200 font-medium">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div
                      className="rounded-3xl p-6 border backdrop-blur-md shadow-xl"
                      style={{
                        background: 'linear-gradient(145deg, rgba(120,53,15,0.4), rgba(0,0,0,0.5))',
                        borderColor: 'rgba(251, 146, 60, 0.3)',
                      }}
                    >
                      <h3
                        className="text-xl font-black text-white uppercase tracking-wide mb-4 flex items-center gap-2"
                        style={{ fontFamily: "'Anton', sans-serif" }}
                      >
                        <span>⚠️</span> Areas to Improve
                      </h3>
                      <ul className="space-y-2.5">
                        {report.weaknesses.map((weakness: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-orange-400 font-black mt-0.5">•</span>
                            <span className="text-sm text-slate-200 font-medium">{weakness}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Key Moments */}
                  <div
                    className="rounded-3xl p-6 border backdrop-blur-md shadow-xl"
                    style={{
                      background: 'linear-gradient(145deg, rgba(0,0,0,0.5), rgba(15,23,42,0.75))',
                      borderColor: activeTheme.borderColor,
                    }}
                  >
                    <h3
                      className="text-2xl font-black text-white uppercase tracking-wide mb-5 flex items-center gap-2"
                      style={{ fontFamily: "'Anton', sans-serif" }}
                    >
                      <span>🎯</span> Key Moments
                    </h3>
                    <div className="space-y-3">
                      {report.key_moments.map((moment: { timestamp_seconds: number; classification: string; comment: string }, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start gap-3 rounded-2xl p-4 border border-white/10 bg-white/5 backdrop-blur"
                        >
                          <span
                            className="flex-shrink-0 font-mono text-xs font-black px-2.5 py-1 rounded-xl"
                            style={{
                              background: activeTheme.cardGlass,
                              color: activeTheme.primaryColor,
                              border: `1px solid ${activeTheme.borderColor}`,
                            }}
                          >
                            {formatTime(moment.timestamp_seconds)}
                          </span>
                          <div className="flex-1">
                            <span
                              className={`inline-block rounded-xl px-2.5 py-0.5 text-xs font-black uppercase tracking-wider mb-1 ${getClassificationColor(moment.classification)}`}
                            >
                              {moment.classification}
                            </span>
                            <p className="text-sm text-slate-200 font-medium">{moment.comment}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Training Drills */}
                  <div
                    className="rounded-3xl p-6 border backdrop-blur-md shadow-xl"
                    style={{
                      background: 'linear-gradient(145deg, rgba(0,0,0,0.5), rgba(15,23,42,0.75))',
                      borderColor: activeTheme.borderColor,
                    }}
                  >
                    <h3
                      className="text-2xl font-black text-white uppercase tracking-wide mb-5 flex items-center gap-2"
                      style={{ fontFamily: "'Anton', sans-serif" }}
                    >
                      <span>🏋️</span> Recommended Training Drills
                    </h3>
                    <ol className="space-y-3">
                      {report.drills.map((drill: string, idx: number) => (
                        <li
                          key={idx}
                          className="flex items-start gap-3 rounded-2xl p-3 bg-white/5 border border-white/10"
                        >
                          <span
                            className="flex-shrink-0 w-7 h-7 rounded-xl flex items-center justify-center font-black text-xs"
                            style={{
                              background: `linear-gradient(135deg, ${activeTheme.primaryColor}, ${activeTheme.accentColor})`,
                              color: '#0f172a',
                            }}
                          >
                            {idx + 1}
                          </span>
                          <span className="text-sm text-slate-200 font-medium pt-0.5">{drill}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                </motion.div>
              )}
            </div>
          )}

          {/* ── Commentary Tab ── */}
          {activeTab === 'commentary' && (
            <div
              className="rounded-3xl border backdrop-blur-md overflow-hidden shadow-xl"
              style={{
                background: 'linear-gradient(145deg, rgba(0,0,0,0.5), rgba(15,23,42,0.75))',
                borderColor: activeTheme.borderColor,
              }}
            >
              <div
                className="px-6 pt-6 pb-3 border-b"
                style={{ borderColor: activeTheme.borderColor }}
              >
                <span
                  className="font-mono text-xs font-black uppercase tracking-wider"
                  style={{ color: activeTheme.primaryColor }}
                >
                  AI COMMENTARY ENGINE
                </span>
                <h3
                  className="text-2xl font-black text-white uppercase tracking-wide mt-1"
                  style={{ fontFamily: "'Anton', sans-serif" }}
                >
                  Live {activeTheme.name} Commentary
                </h3>
              </div>
              <div className="p-6">
                <CommentaryPlayer />
              </div>
            </div>
          )}

          {/* ── Chat Tab ── */}
          {activeTab === 'chat' && (
            <div
              className="rounded-3xl border backdrop-blur-md overflow-hidden shadow-xl"
              style={{
                background: 'linear-gradient(145deg, rgba(0,0,0,0.5), rgba(15,23,42,0.75))',
                borderColor: activeTheme.borderColor,
              }}
            >
              <div
                className="px-6 pt-6 pb-3 border-b"
                style={{ borderColor: activeTheme.borderColor }}
              >
                <span
                  className="font-mono text-xs font-black uppercase tracking-wider"
                  style={{ color: activeTheme.primaryColor }}
                >
                  MATCH ANALYTICS
                </span>
                <h3
                  className="text-2xl font-black text-white uppercase tracking-wide mt-1"
                  style={{ fontFamily: "'Anton', sans-serif" }}
                >
                  {activeTheme.name} Analytics Chat
                </h3>
              </div>
              <div className="p-6">
                <MatchChat />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
