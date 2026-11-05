import { useState, useEffect } from 'react'
import { generateCommentary } from '@/services/analysisService'

interface CommentaryLine {
  time: number
  text: string
  excitement_level: 'low' | 'medium' | 'high' | 'explosive'
  target_player_id?: number
}

export function CommentaryPlayer({ matchId = 'default' }: { matchId?: string }) {
  const [persona, setPersona] = useState<'broadcast' | 'tactical' | 'coach'>('broadcast')
  const [commentary, setCommentary] = useState<CommentaryLine[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadCommentary = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await generateCommentary(matchId, persona, {
        '1': 'Player 1',
        '7': 'Player 7',
        '12': 'Player 12',
        '16': 'Player 16',
      })
      
      if (response?.commentary) {
        setCommentary(response.commentary)
      } else {
        setError('Backend unavailable. Start the backend server to generate real commentary.')
      }
    } catch (err) {
      setError('Failed to generate commentary. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCommentary()
  }, [persona])

  const getExcitementColor = (level: string) => {
    switch (level) {
      case 'explosive':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
        <h3 className="text-lg font-semibold text-gray-900">AI Commentary Generator</h3>
        <p className="text-sm text-gray-600">Select a commentary style and generate narration</p>
      </div>

      {/* Persona Selector */}
      <div className="border-b border-gray-200 p-6">
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Commentary Style
        </label>
        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={() => setPersona('broadcast')}
            className={`rounded-lg border-2 p-4 text-left transition-all ${
              persona === 'broadcast'
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="mb-1 text-lg">🎙️</div>
            <div className="font-semibold text-gray-900">Broadcast</div>
            <div className="text-xs text-gray-600">Dramatic & poetic</div>
          </button>
          <button
            onClick={() => setPersona('tactical')}
            className={`rounded-lg border-2 p-4 text-left transition-all ${
              persona === 'tactical'
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="mb-1 text-lg">🧠</div>
            <div className="font-semibold text-gray-900">Tactical</div>
            <div className="text-xs text-gray-600">Analytical</div>
          </button>
          <button
            onClick={() => setPersona('coach')}
            className={`rounded-lg border-2 p-4 text-left transition-all ${
              persona === 'coach'
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="mb-1 text-lg">👨‍🏫</div>
            <div className="font-semibold text-gray-900">Coach</div>
            <div className="text-xs text-gray-600">Educational</div>
          </button>
        </div>
      </div>

      {/* Commentary Lines */}
      <div className="p-6">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
              <p className="text-sm text-gray-600">Generating {persona} commentary...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-yellow-50 p-4 text-sm text-yellow-800">
            {error}
          </div>
        )}

        {!loading && !error && commentary.length === 0 && (
          <div className="py-12 text-center text-gray-500">
            No commentary generated yet. Try selecting a different style.
          </div>
        )}

        {!loading && commentary.length > 0 && (
          <div className="space-y-3">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm font-medium text-gray-700">
                {commentary.length} commentary lines
              </p>
              <button
                onClick={loadCommentary}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Regenerate
              </button>
            </div>
            {commentary.map((line, idx) => (
              <div
                key={idx}
                className={`rounded-lg border p-4 ${getExcitementColor(line.excitement_level)}`}
              >
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-xs font-mono font-medium">
                    {formatTime(line.time)}
                  </span>
                  <span className="text-xs font-medium uppercase">
                    {line.excitement_level}
                  </span>
                </div>
                <p className="text-sm">{line.text}</p>
                {line.target_player_id && (
                  <p className="mt-1 text-xs opacity-75">
                    Focus: Player {line.target_player_id}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
