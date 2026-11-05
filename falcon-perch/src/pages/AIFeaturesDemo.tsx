import { useState, useRef } from 'react'
import { MatchChat } from '@/components/MatchChat'
import { CommentaryPlayer } from '@/components/CommentaryPlayer'
import { analyze } from '@/services/analysisService'
import type { AnalysisRecord } from '@/types'

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
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Fetch players from match data
  const fetchPlayersFromMatch = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/match/${id}/stats`)
      if (response.ok) {
        const data = await response.json()
        const matchPlayers = data.stats?.players || []
        // Map player data to include names
        const playerList = matchPlayers.map((p: any) => ({
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
      setReport(null) // Clear previous report

      // Fetch players from the new match
      await fetchPlayersFromMatch(data.match_id)

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Upload failed'
      setUploadStatus(`❌ Error: ${errorMsg}`)
      console.error('Upload error:', error)
    } finally {
      setUploadLoading(false)
    }
  }

  const generateReport = async () => {
    console.log('🔘 Generate Report clicked!')
    console.log('Selected Player:', selectedPlayer)
    console.log('Match ID:', matchId)
    
    setLoading(true)
    try {
      const result = await analyze(
        { sport: 'football', skill: 'match-analysis' },
        selectedPlayer,
        matchId
      )
      console.log('✅ Report received:', result)
      setReport(result)
    } catch (error) {
      console.error('❌ Failed to generate report:', error)
      alert(`Error: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      setLoading(false)
    }
  }

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'Brilliant':
        return 'bg-purple-100 text-purple-800'
      case 'Great':
        return 'bg-green-100 text-green-800'
      case 'Good':
        return 'bg-blue-100 text-blue-800'
      case 'Inaccuracy':
        return 'bg-yellow-100 text-yellow-800'
      case 'Mistake':
        return 'bg-orange-100 text-orange-800'
      case 'Blunder':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Falcon Perch AI Features Demo</h1>
          <p className="mt-2 text-gray-600">
            Explore AI-powered match analysis, commentary, and analytics chat
          </p>
        </div>

        {/* Backend Status */}
        <div className="mb-6 rounded-lg bg-blue-50 p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <strong>Backend Required:</strong> Make sure to run{' '}
                <code className="rounded bg-blue-100 px-2 py-1 text-xs">
                  uvicorn server:app --reload
                </code>{' '}
                in falcon-perch-backend directory
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('coach')}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                activeTab === 'coach'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              🏋️ AI Performance Coach
            </button>
            <button
              onClick={() => setActiveTab('commentary')}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                activeTab === 'commentary'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              🎙️ AI Commentary
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                activeTab === 'chat'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              💬 Match Analytics Chat
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* AI Coach Tab */}
          {activeTab === 'coach' && (
            <div className="space-y-6">
              {/* Video Upload Section */}
              <div className="rounded-lg border-2 border-dashed border-blue-300 bg-blue-50 p-6 shadow-sm">
                <h3 className="mb-4 flex items-center text-lg font-semibold text-gray-900">
                  <span className="mr-2 text-2xl">📹</span>
                  Upload Football Video
                </h3>
                <p className="mb-4 text-sm text-gray-600">
                  Upload a football match video. The CV pipeline will extract player tracking data,
                  and then AI will generate coaching insights.
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
                  className={`mb-4 inline-block rounded-lg px-6 py-3 font-medium text-white transition-all ${
                    uploadLoading
                      ? 'cursor-not-allowed bg-gray-400'
                      : 'cursor-pointer bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {uploadLoading ? (
                    <span className="flex items-center">
                      <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25" />
                        <path
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          opacity="0.75"
                        />
                      </svg>
                      Uploading & Processing...
                    </span>
                  ) : (
                    'Choose Video File'
                  )}
                </label>

                {uploadStatus && (
                  <div
                    className={`mt-4 rounded-lg p-3 text-sm ${
                      uploadStatus.includes('❌')
                        ? 'bg-red-100 text-red-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {uploadStatus}
                  </div>
                )}

                {matchId !== 'default' && (
                  <div className="mt-4 rounded-lg bg-white p-3">
                    <p className="text-sm text-gray-600">
                      <strong>Current Match:</strong> {matchId}
                    </p>
                  </div>
                )}
              </div>

              {/* Player Selection */}
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">
                  Select Player for Analysis
                </h3>
                <div className="grid grid-cols-4 gap-4">
                  {players.map((player) => (
                    <button
                      key={player.id}
                      onClick={() => setSelectedPlayer(player.id)}
                      className={`rounded-lg border-2 p-4 text-left transition-all ${
                        selectedPlayer === player.id
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="mb-1 text-2xl">⚽</div>
                      <div className="font-semibold text-gray-900">{player.name}</div>
                      <div className="text-xs text-gray-600">
                        Team {player.team} • {player.role}
                      </div>
                    </button>
                  ))}
                </div>
                <button
                  onClick={generateReport}
                  disabled={loading}
                  className="mt-4 w-full rounded-lg bg-blue-600 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-gray-300"
                >
                  {loading ? 'Generating AI Report...' : 'Generate AI Coach Report'}
                </button>
              </div>

              {/* Report Display */}
              {report && (
                <div className="space-y-6">
                  {/* Overall Score */}
                  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-gray-900">
                      Performance Summary
                    </h3>
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <div className="text-sm text-gray-600">Overall Score</div>
                        <div className="mt-1 text-4xl font-bold text-blue-600">
                          {report.overall_score}
                          <span className="text-xl text-gray-400">/100</span>
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Accuracy</div>
                        <div className="mt-1 text-4xl font-bold text-green-600">
                          {report.accuracy_percent}
                          <span className="text-xl text-gray-400">%</span>
                        </div>
                      </div>
                    </div>
                    <p className="mt-4 text-gray-700">{report.summary}</p>
                  </div>

                  {/* Strengths & Weaknesses */}
                  <div className="grid grid-cols-2 gap-6">
                    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                      <h3 className="mb-4 text-lg font-semibold text-gray-900">💪 Strengths</h3>
                      <ul className="space-y-2">
                        {report.strengths.map((strength: string, idx: number) => (
                          <li key={idx} className="flex items-start">
                            <span className="mr-2 text-green-600">✓</span>
                            <span className="text-sm text-gray-700">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                      <h3 className="mb-4 text-lg font-semibold text-gray-900">
                        ⚠️ Areas for Improvement
                      </h3>
                      <ul className="space-y-2">
                        {report.weaknesses.map((weakness: string, idx: number) => (
                          <li key={idx} className="flex items-start">
                            <span className="mr-2 text-orange-600">•</span>
                            <span className="text-sm text-gray-700">{weakness}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Key Moments */}
                  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-gray-900">🎯 Key Moments</h3>
                    <div className="space-y-3">
                      {report.key_moments.map((moment: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex items-start space-x-3 rounded-lg border border-gray-200 p-4"
                        >
                          <div className="flex-shrink-0">
                            <span className="text-xs font-mono font-medium text-gray-600">
                              {formatTime(moment.timestamp_seconds)}
                            </span>
                          </div>
                          <div className="flex-1">
                            <div className="mb-1">
                              <span
                                className={`inline-block rounded px-2 py-1 text-xs font-medium ${getClassificationColor(
                                  moment.classification
                                )}`}
                              >
                                {moment.classification}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700">{moment.comment}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Training Drills */}
                  <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-semibold text-gray-900">
                      🏋️ Recommended Training Drills
                    </h3>
                    <ol className="space-y-2">
                      {report.drills.map((drill: string, idx: number) => (
                        <li key={idx} className="flex items-start">
                          <span className="mr-3 font-medium text-blue-600">{idx + 1}.</span>
                          <span className="text-sm text-gray-700">{drill}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Commentary Tab */}
          {activeTab === 'commentary' && <CommentaryPlayer />}

          {/* Chat Tab */}
          {activeTab === 'chat' && <MatchChat />}
        </div>
      </div>
    </div>
  )
}
