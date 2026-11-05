"""
server.py - FastAPI Backend for Falcon Perch

REST API to serve CV tracking data and LLM outputs to the React frontend.

Endpoints:
    POST /api/upload-video          - Upload video for processing
    GET  /api/match/{id}/stats      - Get match statistics
    POST /api/match/{id}/coach      - Generate AI coach report for a player
    POST /api/match/{id}/commentary - Generate commentary with selectable persona
    POST /api/match/{id}/chat       - Conversational Q&A on match data

Install:
    pip install fastapi uvicorn python-multipart google-genai python-dotenv

Run:
    uvicorn server:app --reload --port 8000
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Literal, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our LLM modules
from coaching.ai_coach import generate_player_coach_report
from commentary.commentary_generator_v2 import generate_dynamic_commentary
from chat.match_agent import MatchAgent


app = FastAPI(
    title="Falcon Perch Backend",
    description="AI-powered football analytics backend",
    version="1.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default + CRA
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for requests
class CoachReportRequest(BaseModel):
    player_id: int
    player_name: Optional[str] = None


class CommentaryRequest(BaseModel):
    persona: Literal["broadcast", "tactical", "coach"] = "broadcast"
    player_names: Optional[dict[str, str]] = None  # {player_id: name}
    team_names: Optional[dict[str, str]] = None     # {team_id: name}
    language: str = "english"


class ChatRequest(BaseModel):
    question: str
    player_names: Optional[dict[str, str]] = None


# In-memory storage (replace with database in production)
STATS_DIR = Path("stats")
UPLOADS_DIR = Path("input_videos")
UPLOADS_DIR.mkdir(exist_ok=True)
MATCHES = {}


def load_match_data(match_id: str = "default") -> tuple[dict, list[dict]]:
    """Load match stats and events from files."""
    stats_path = STATS_DIR / f"{match_id}_match_stats.json"
    events_path = STATS_DIR / f"{match_id}_events.json"

    # Fallback to default if files don't exist
    if not stats_path.exists():
        stats_path = STATS_DIR / "match_stats.json"
    if not events_path.exists():
        events_path = STATS_DIR / "events.json"

    if not stats_path.exists() or not events_path.exists():
        raise HTTPException(status_code=404, detail="Match data not found")

    with open(stats_path) as f:
        match_stats = json.load(f)

    with open(events_path) as f:
        events = json.load(f)

    return match_stats, events


def run_cv_pipeline(video_path: str) -> tuple[str, dict, list]:
    """
    Run the CV pipeline on the uploaded video.
    Returns: (match_id, match_stats, events)
    """
    try:
        print(f"Running CV pipeline on {video_path}...")
        
        # Get absolute path to backend directory
        backend_dir = Path(__file__).parent
        
        # Run the CV pipeline with proper arguments
        # The script expects: python run_cv_shot_aware.py --video <path>
        # We use --skip-video to only generate JSON stats, not annotated video
        result = subprocess.run(
            ["python3", "run_cv_shot_aware.py", "--video", video_path, "--skip-video"],
            cwd=backend_dir,  # Run from backend directory so relative paths work
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print(f"CV Pipeline error: {result.stderr}")
            raise Exception(f"CV pipeline failed: {result.stderr}")
        
        # Generate unique match ID from timestamp
        match_id = f"upload_{int(time.time())}"
        
        # Load the generated stats and events
        match_stats, events = load_match_data("default")
        
        # Save with new ID
        stats_path = STATS_DIR / f"{match_id}_match_stats.json"
        events_path = STATS_DIR / f"{match_id}_events.json"
        
        with open(stats_path, "w") as f:
            json.dump(match_stats, f)
        with open(events_path, "w") as f:
            json.dump(events, f)
        
        print(f"✅ CV pipeline complete. Match ID: {match_id}")
        return match_id, match_stats, events
        
    except Exception as e:
        print(f"Error in CV pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"CV pipeline error: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Falcon Perch Backend",
        "version": "1.0.0",
        "endpoints": [
            "GET /api/match/{id}/stats",
            "POST /api/match/{id}/coach",
            "POST /api/match/{id}/commentary",
            "POST /api/match/{id}/chat",
            "POST /api/upload-video",
        ],
    }


@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video for CV processing.
    Returns match_id and initial stats.
    """
    try:
        # Save uploaded file with absolute path
        file_path = UPLOADS_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"Video saved: {file_path}")

        # Convert to absolute path for subprocess
        abs_video_path = str(file_path.absolute())
        
        # Run CV pipeline with absolute path
        match_id, match_stats, events = run_cv_pipeline(abs_video_path)

        return {
            "match_id": match_id,
            "filename": file.filename,
            "status": "processed",
            "message": "Video processed successfully with CV pipeline",
            "stats": match_stats,
            "events_count": len(events),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/match/{match_id}/stats")
async def get_match_stats(match_id: str):
    """
    Get full match statistics including players, teams, events.
    """
    try:
        match_stats, events = load_match_data(match_id)
        return {
            "match_id": match_id,
            "stats": match_stats,
            "events": events,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match/{match_id}/coach")
async def generate_coach_report(
    match_id: str,
    request: CoachReportRequest,
):
    """
    Generate AI coaching report for a specific player.

    Returns AnalysisResult compatible with frontend schema.
    """
    try:
        match_stats, events = load_match_data(match_id)

        report = generate_player_coach_report(
            match_stats=match_stats,
            player_id=request.player_id,
            events=events,
            player_name=request.player_name,
        )

        return {
            "match_id": match_id,
            "player_id": request.player_id,
            "report": report,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match/{match_id}/commentary")
async def generate_commentary(
    match_id: str,
    request: CommentaryRequest,
):
    """
    Generate multi-persona commentary for the match.

    Returns timestamped commentary lines with excitement levels.
    """
    try:
        match_stats, events = load_match_data(match_id)

        # Convert string keys to int for player/team names
        player_names = None
        if request.player_names:
            player_names = {int(k): v for k, v in request.player_names.items()}

        team_names = None
        if request.team_names:
            team_names = {int(k): v for k, v in request.team_names.items()}

        clip_duration = match_stats["meta"]["duration_s"]
        api_key = os.environ.get("GEMINI_API_KEY")

        commentary_lines = generate_dynamic_commentary(
            events=events,
            clip_duration_seconds=clip_duration,
            persona=request.persona,
            player_names=player_names,
            team_names=team_names,
            language=request.language,
            api_key=api_key,
        )

        return {
            "match_id": match_id,
            "persona": request.persona,
            "language": request.language,
            "commentary": commentary_lines,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match/{match_id}/chat")
async def chat_with_match(
    match_id: str,
    request: ChatRequest,
):
    """
    Conversational Q&A over match analytics data.

    Users can ask natural language questions about the match.
    """
    try:
        match_stats, events = load_match_data(match_id)

        # Convert string keys to int
        player_names = None
        if request.player_names:
            player_names = {int(k): v for k, v in request.player_names.items()}

        agent = MatchAgent(
            match_stats=match_stats,
            events=events,
            player_names=player_names,
        )

        answer = agent.chat(request.question)

        return {
            "match_id": match_id,
            "question": request.question,
            "answer": answer,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players")
async def list_players():
    """Get list of all tracked players across all matches."""
    try:
        match_stats, _ = load_match_data()
        players = [
            {
                "player_id": p["player_id"],
                "team": p["team"],
                "role": p["role"],
                "max_speed_kmh": p["max_speed_kmh"],
                "distance_m": p["distance_m"],
                "sprints": p["sprints"],
            }
            for p in match_stats["players"]
        ]
        return {"players": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print("\n🚀 Starting Falcon Perch Backend Server...")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
