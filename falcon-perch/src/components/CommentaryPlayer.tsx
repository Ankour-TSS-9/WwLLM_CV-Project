import { useState, useEffect, useCallback, useRef } from 'react'
import {
  createCommentaryVideo,
  generateCommentary,
  generateCommentaryAudio,
  type CommentaryLine,
} from '@/services/analysisService'

export function CommentaryPlayer({
  matchId = 'default',
  onVideoCreated,
}: {
  matchId?: string
  onVideoCreated?: (videoUrl: string) => void
}) {
  const [persona, setPersona] = useState<'broadcast' | 'tactical' | 'coach'>('broadcast')
  const [commentary, setCommentary] = useState<CommentaryLine[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [audioLoadingIndex, setAudioLoadingIndex] = useState<number | null>(null)
  const [activeAudioIndex, setActiveAudioIndex] = useState<number | null>(null)
  const [audioError, setAudioError] = useState<string | null>(null)
  const [videoLoading, setVideoLoading] = useState(false)
  const [videoError, setVideoError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioUrlRef = useRef<string | null>(null)
  const audioLineIndexRef = useRef<number | null>(null)

  const playCommentaryAudio = async (line: CommentaryLine, index: number) => {
    setAudioError(null)

    if (audioRef.current && audioLineIndexRef.current === index) {
      if (!audioRef.current.paused) {
        audioRef.current.pause()
        setActiveAudioIndex(null)
        return
      }

      try {
        await audioRef.current.play()
        setActiveAudioIndex(index)
      } catch (err) {
        setAudioError(err instanceof Error ? err.message : 'Could not play commentary audio.')
      }
      return
    }

    setAudioLoadingIndex(index)
    audioRef.current?.pause()
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current)
      audioUrlRef.current = null
    }
    audioRef.current = null
    audioLineIndexRef.current = null
    setActiveAudioIndex(null)

    try {
      const audioBlob = await generateCommentaryAudio(matchId, line.text)
      const audioUrl = URL.createObjectURL(audioBlob)
      const audio = new Audio(audioUrl)
      audioUrlRef.current = audioUrl
      audioRef.current = audio
      audioLineIndexRef.current = index
      audio.onended = () => setActiveAudioIndex(null)
      audio.onerror = () => {
        setActiveAudioIndex(null)
        setAudioError('The generated commentary audio could not be played.')
      }
      await audio.play()
      setActiveAudioIndex(index)
    } catch (err) {
      setAudioError(err instanceof Error ? err.message : 'Failed to generate commentary audio.')
    } finally {
      setAudioLoadingIndex(null)
    }
  }

  const loadCommentary = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await generateCommentary(matchId, persona, {
        '1': 'Player 1',
        '7': 'Player 7',
        '12': 'Player 12',
        '16': 'Player 16',
      })
      
      setCommentary(response.commentary)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate commentary.')
    } finally {
      setLoading(false)
    }
  }, [matchId, persona])

  const embedCommentaryInVideo = async () => {
    setVideoLoading(true)
    setVideoError(null)
    try {
      const videoUrl = await createCommentaryVideo(matchId, commentary)
      onVideoCreated?.(videoUrl)
    } catch (err) {
      setVideoError(err instanceof Error ? err.message : 'Failed to create commentary video.')
    } finally {
      setVideoLoading(false)
    }
  }

  useEffect(() => {
    void loadCommentary()
  }, [loadCommentary])

  useEffect(() => () => {
    audioRef.current?.pause()
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current)
    }
  }, [])

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
        <p className="text-sm text-gray-600">
          Generate timestamped match commentary, preview spoken lines, or add narration to the analyzed video.
        </p>
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

        {audioError && (
          <div className="mb-4 rounded-lg bg-yellow-50 p-4 text-sm text-yellow-800">
            {audioError}
          </div>
        )}

        {videoError && (
          <div className="mb-4 rounded-lg bg-yellow-50 p-4 text-sm text-yellow-800">
            {videoError}
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
              <div className="flex items-center gap-4">
                {matchId !== 'default' && (
                  <button
                    type="button"
                    onClick={() => void embedCommentaryInVideo()}
                    disabled={videoLoading}
                    className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-wait disabled:opacity-60"
                  >
                    {videoLoading ? 'Creating video...' : 'Add voice to video'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => void loadCommentary()}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Regenerate
                </button>
              </div>
            </div>
            {matchId !== 'default' && (
              <p className="mb-4 text-xs text-gray-500">
                Creates a downloadable video with narration and the original match audio quieter underneath. Uses ElevenLabs credits.
              </p>
            )}
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
                <button
                  type="button"
                  onClick={() => void playCommentaryAudio(line, idx)}
                  disabled={audioLoadingIndex !== null}
                  className="mt-3 rounded-md border border-current/20 px-3 py-1.5 text-xs font-semibold hover:bg-black/5 disabled:cursor-wait disabled:opacity-60"
                >
                  {audioLoadingIndex === idx
                    ? 'Generating voice...'
                    : activeAudioIndex === idx
                      ? 'Pause voice'
                      : 'Play voice'}
                </button>
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
