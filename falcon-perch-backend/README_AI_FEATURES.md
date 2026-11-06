# Falcon Perch AI Features - Implementation Guide

This document explains the LLM-powered features added to Falcon Perch and how to use them.

## 🚀 New Features

### 1. **AI Performance Coach** (`coaching/ai_coach.py`)
Generates comprehensive player performance reports using LLM analysis of CV tracking data.

**Features:**
- Overall performance score (0-100)
- Strengths and weaknesses identification
- Key moment analysis (Brilliant/Great/Good/Inaccuracy/Mistake/Blunder)
- Personalized training drill recommendations
- Phase-by-phase breakdown

**API Endpoint:**
```http
POST /api/match/{match_id}/coach
Content-Type: application/json

{
  "player_id": 1,
  "player_name": "Optional Player Name"
}
```

**Response:**
```json
{
  "overall_score": 85,
  "accuracy_percent": 82,
  "summary": "Strong attacking performance with excellent pace...",
  "strengths": ["High-speed sprints", "Box penetration", "Work rate"],
  "weaknesses": ["Pass completion under pressure", "Defensive tracking"],
  "key_moments": [
    {
      "timestamp_seconds": 3.2,
      "classification": "Brilliant",
      "comment": "Explosive 34.7 km/h sprint into final third"
    }
  ],
  "drills": ["Progressive passing under pressure drill", "..."],
  "phases": [...],
  "joint_angles": []
}
```

### 2. **Multi-Persona Commentary** (`commentary/commentary_generator_v2.py`)
Enhanced from the original commentary generator with persona selection.

**Personas:**
- **Broadcast**: Dramatic, poetic commentary (Peter Drury style)
- **Tactical**: Analytical, spatial analysis (Gary Neville style)
- **Coach**: Educational, developmental feedback

**Features:**
- Player name enrichment (no more "number 22")
- Team context and match stakes
- Excitement level calibration (low/medium/high/explosive)
- Multi-language support foundation (Spanish, Arabic, Hindi)

**API Endpoint:**
```http
POST /api/match/{match_id}/commentary
Content-Type: application/json

{
  "persona": "broadcast",
  "player_names": {"1": "De Bruyne", "7": "Sterling"},
  "team_names": {"1": "City", "2": "United"},
  "language": "english"
}
```

**Response:**
```json
{
  "commentary": [
    {
      "time": 3.2,
      "text": "And there's the burst! Number 7 with lightning pace!",
      "excitement_level": "high",
      "target_player_id": 7
    }
  ]
}
```

For uploaded matches, the frontend can also synthesize these lines into the annotated video. `POST /api/match/{match_id}/commentary/video` accepts the `commentary` array, and `GET /api/match/{match_id}/commentary-video` serves the resulting MP4. This requires `ELEVENLABS_API_KEY` and FFmpeg; source match audio is mixed underneath the narration at reduced volume.

### 3. **Match Chat Agent** (`chat/match_agent.py`)
Conversational Q&A system using RAG over match telemetry.

**Features:**
- Natural language queries
- Function calling to query match data
- Player comparisons
- Event filtering (sprints, shots, passes, etc.)
- Team summaries

**API Endpoint:**
```http
POST /api/match/{match_id}/chat
Content-Type: application/json

{
  "question": "How many sprints did player 7 make above 33 km/h?",
  "player_names": {"7": "Sterling"}
}
```

**Example Questions:**
- "Who was the fastest player in the match?"
- "Show me all box entries by our team"
- "Compare player 1 and player 12's work rate"
- "Which player covered the most distance in the final third?"

### 4. **FastAPI Backend** (`server.py`)
REST API server connecting CV pipeline to React frontend.

**Endpoints:**
- `GET /` - Health check
- `GET /api/match/{id}/stats` - Match statistics
- `POST /api/match/{id}/coach` - AI coach report
- `POST /api/match/{id}/commentary` - Generate commentary
- `POST /api/match/{id}/commentary/audio` - Generate a spoken commentary line
- `POST /api/match/{id}/commentary/video` - Render commentary into an uploaded match video
- `GET /api/match/{id}/commentary-video` - Stream the rendered commentary video
- `POST /api/match/{id}/chat` - Match Q&A
- `POST /api/upload-video` - Process an uploaded video and return match stats and a video URL
- `GET /api/match/{id}/video` - Stream the annotated MP4 for an uploaded match
- `GET /api/players` - List all players

## 📦 Installation

### Backend Setup

1. **Create the Python environment and install dependencies:**
```bash
cd falcon-perch-backend
py -3.12 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
copy .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Get a Groq API key at: https://console.groq.com/keys

3. **Verify data files exist:**
```bash
ls stats/
# Should show: match_stats.json, events.json, shots.json
```

### Frontend Setup

1. **Set up environment:**
```bash
cd ../falcon-perch
cp .env.example .env
# Edit .env if backend runs on different port
```

2. **Install dependencies** (if not already done):
```bash
npm ci
```

The backend renders an annotated AVI for each upload, converts it to a browser-playable H.264 MP4 with FFmpeg/libx264, and returns `video_url` in the upload response. The AI Features page embeds the video after processing; the source match audio is not included.

## 🧪 Testing

### Test AI Coach (Backend Only)

```bash
cd falcon-perch-backend

# Test with player 1
python3 test_ai_coach.py 1

# Test with player 12
python3 test_ai_coach.py 12
```

This will:
- Load match data from `stats/`
- Generate AI coaching report
- Display formatted output in terminal
- Save report to `stats/player_{id}_coach_report.json`

### Test Commentary Generation

```bash
cd falcon-perch-backend

# Broadcast style
python3 commentary/commentary_generator_v2.py stats/events.json broadcast 30

# Tactical style
python3 commentary/commentary_generator_v2.py stats/events.json tactical 30

# Coach style
python3 commentary/commentary_generator_v2.py stats/events.json coach 30
```

### Test Match Chat Agent

```bash
cd falcon-perch-backend
python3 chat/match_agent.py
```

Then ask questions interactively.

## 🚀 Running the Full Stack

### 1. Start Backend Server

```bash
cd falcon-perch-backend
uvicorn server:app --reload --port 8000
```

API documentation available at: http://localhost:8000/docs

### 2. Start Frontend Dev Server

```bash
cd ../falcon-perch
npm run dev
```

Frontend available at: http://localhost:5173

### 3. Test the Integration

**Option A: Use the React UI**
- Navigate to dashboard
- Upload a video or use existing analysis
- View AI-generated coach reports

**Option B: Test API directly**
```bash
# Get match stats
curl http://localhost:8000/api/match/default/stats

# Generate coach report for player 1
curl -X POST http://localhost:8000/api/match/default/coach \
  -H "Content-Type: application/json" \
  -d '{"player_id": 1}'

# Ask a question
curl -X POST http://localhost:8000/api/match/default/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Who was the fastest player?"}'
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│    Computer Vision Pipeline (YOLO + Tracks)   │
│         run_cv_shot_aware.py                  │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  stats/              │
         │  ├─ match_stats.json │
         │  ├─ events.json      │
         │  └─ shots.json       │
         └──────────┬────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐      ┌──────────────────┐
│ FastAPI      │      │ LLM Modules      │
│ server.py    │◄────►│ ├─ ai_coach.py   │
│              │      │ ├─ commentary_v2 │
│ Endpoints:   │      │ └─ match_agent   │
│ /coach       │      └──────────────────┘
│ /commentary  │                │
│ /chat        │                ▼
└──────┬───────┘      ┌──────────────────┐
       │              │ Groq API         │
       │              │ (commentary)     │
       ▼              └──────────────────┘
┌──────────────────────────────┐
│ React Frontend               │
│ ├─ DashboardPage             │
│ ├─ AnalysisResult display    │
│ └─ Video player + commentary │
└──────────────────────────────┘
```

## 🎯 Frontend Integration Points

The frontend already has the TypeScript types defined (`src/types.ts`). The updated `analysisService.ts` now connects to the backend:

```typescript
// Usage in React components:
import { analyzeVideo, generateCommentary, chatWithMatch } from '@/services/analysisService'

// Get AI coach report
const report = await analyzeVideo(input, playerId, matchId)

// Generate commentary
const commentary = await generateCommentary(matchId, 'broadcast', playerNames)

// Ask questions
const answer = await chatWithMatch("Who scored?", matchId)
```

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```env
GROQ_API_KEY=your_key_here       # Commentary endpoint
GEMINI_API_KEY=your_key_here     # Other/standalone AI modules, if used
PORT=8000
```

**Frontend** (`.env`):
```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_AI_COACH=true
```

### Model Configuration

The app's commentary endpoint uses Groq's `llama-3.3-70b-versatile` model. Set `GROQ_API_KEY` in the backend `.env` file. Other standalone modules may use Gemini separately.

## 📊 Data Flow

1. **Video Upload** → CV Pipeline → `match_stats.json` + `events.json`
2. **Player Analysis Request** → AI Coach → LLM Analysis → `AnalysisResult`
3. **Commentary Request** → Groq Commentary Generator → Timestamped persona-specific text lines
4. **Chat Question** → Match Agent → Function calls → Natural answer

## 🔮 Future Enhancements

1. **Idol Benchmark Comparison**: Compare user vs pro athlete profiles
2. **Real-time Commentary**: WebSocket streaming for live matches
3. **Multi-match Analytics**: Historical performance tracking
4. **Advanced RAG**: Vector embeddings for semantic search over match history
5. **Custom Training Plans**: Multi-week development roadmaps
6. **Video Timestamp Links**: Click key moment → jump to video frame

## 🐛 Troubleshooting

**"Module not found" errors:**
```bash
# Ensure you're in the backend directory
cd falcon-perch-backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**"GROQ_API_KEY not found" or commentary generation failed:**
```bash
export GROQ_API_KEY="your-key-here"
```

**Backend not connecting:**
- Check server is running: `curl http://localhost:8000`
- Verify CORS origins in `server.py`
- Check frontend `.env` has correct `VITE_API_URL`

**No match data:**
- Run CV pipeline first: `python3 run_cv_shot_aware.py input_videos/your_video.mp4`
- Or use existing `stats/*.json` files

## 📚 Resources

- Groq API Docs: https://console.groq.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- React Query (optional): For better API state management

## ✅ Next Steps

1. ✅ Backend LLM modules created
2. ✅ FastAPI server implemented
3. ✅ Frontend services updated
4. ⏳ Test with real match data
5. ⏳ Deploy backend (Railway, Render, or AWS)
6. ⏳ Build UI components for chat & commentary
7. ⏳ Add WebSocket for real-time features

---

**Made with ⚡ by Falcon Perch Team**
