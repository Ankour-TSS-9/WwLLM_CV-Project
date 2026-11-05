# Falcon Perch Backend Environment Variables

Get a free API key at: https://console.groq.com/keys

## Required Variables

```
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=  # Optional for TTS
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Setup

1. Copy `.env.example` to `.env`
2. Add your Groq API key to `.env`
3. Start the server: `python3 -m uvicorn server:app --reload --port 8000`
