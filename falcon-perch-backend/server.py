"""
server.py - FastAPI Backend for Falcon Perch

REST API to serve CV tracking data and LLM outputs to the React frontend.

Endpoints:
    POST /api/upload-video          - Upload video for processing
    GET  /api/match/{id}/stats      - Get match statistics
    POST /api/match/{id}/coach      - Generate AI coach report for a player
    POST /api/match/{id}/commentary - Generate commentary with selectable persona
    POST /api/match/{id}/commentary/video - Render a video with spoken commentary
    POST /api/match/{id}/chat       - Conversational Q&A on match data
    GET  /api/match/{id}/video      - Stream the annotated MP4

Install:
    python -m pip install -r requirements.txt

Run:
    python -m uvicorn server:app --reload --port 8000
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
import time
from dotenv import load_dotenv

# Load environment variables from .env file
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

# Import our LLM modules
from coaching.ai_coach import generate_player_coach_report
from commentary.audio_merger import merge_commentary_into_video
from commentary.commentary_generator_v2 import generate_dynamic_commentary
from commentary.tts_generator import generate_audio_bytes
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


class CommentaryAudioRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class CommentaryLineRequest(BaseModel):
    time: float = Field(ge=0)
    text: str = Field(min_length=1, max_length=1000)


class CommentaryVideoRequest(BaseModel):
    commentary: list[CommentaryLineRequest] = Field(min_length=1, max_length=100)


class ChatRequest(BaseModel):
    question: str
    player_names: Optional[dict[str, str]] = None


# In-memory storage (replace with database in production)
STATS_DIR = BACKEND_DIR / "stats"
UPLOADS_DIR = BACKEND_DIR / "input_videos"
OUTPUT_VIDEOS_DIR = BACKEND_DIR / "output_videos"
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


def _uploaded_video_path(match_id: str) -> Path:
    if not re.fullmatch(r"upload_\d+", match_id):
        raise HTTPException(status_code=404, detail="Video not found")

    for path in UPLOADS_DIR.iterdir():
        if path.is_file() and (
            path.name == match_id or path.name.startswith(f"{match_id}.")
        ):
            return path
    raise HTTPException(status_code=404, detail="Uploaded source video not found")


def _render_commentary_video(
    match_id: str,
    source_video_path: Path,
    commentary: list[CommentaryLineRequest],
) -> Path:
    output_path = OUTPUT_VIDEOS_DIR / f"{match_id}_commentary.mp4"
    OUTPUT_VIDEOS_DIR.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f".{match_id}_commentary_", dir=OUTPUT_VIDEOS_DIR
    ) as temp_dir:
        audio_clips = []
        for index, line in enumerate(commentary):
            audio = generate_audio_bytes(line.text.strip())
            if not audio:
                raise RuntimeError(f"Voice synthesis returned no audio for line {index + 1}")

            audio_path = Path(temp_dir) / f"line_{index:03d}.mp3"
            audio_path.write_bytes(audio)
            audio_clips.append({"time": line.time, "audio_path": str(audio_path)})

        rendered_path = Path(temp_dir) / "commentary.mp4"
        merge_commentary_into_video(
            video_path=str(OUTPUT_VIDEOS_DIR / f"{match_id}.mp4"),
            audio_clips=audio_clips,
            output_path=str(rendered_path),
            original_audio_path=str(source_video_path),
            original_audio_volume=0.15,
        )
        os.replace(rendered_path, output_path)

    return output_path


def run_cv_pipeline(video_path: str, match_id: str) -> tuple[dict, list]:
    """
    Run the CV pipeline on the uploaded video.
    Returns: (match_stats, events)
    """
    try:
        print(f"Running CV pipeline on {video_path}...")

        avi_path = OUTPUT_VIDEOS_DIR / f"{match_id}.avi"
        mp4_path = OUTPUT_VIDEOS_DIR / f"{match_id}.mp4"
        OUTPUT_VIDEOS_DIR.mkdir(exist_ok=True)
        try:
            timeout_seconds = int(os.environ.get("CV_PIPELINE_TIMEOUT_SECONDS", "1800"))
        except ValueError as e:
            raise RuntimeError("CV_PIPELINE_TIMEOUT_SECONDS must be a positive integer") from e
        if timeout_seconds <= 0:
            raise RuntimeError("CV_PIPELINE_TIMEOUT_SECONDS must be a positive integer")

        process_env = os.environ.copy()
        process_env["PYTHONIOENCODING"] = "utf-8"
        process_env["PYTHONUNBUFFERED"] = "1"
        result = subprocess.run(
            [
                sys.executable,
                "-u",
                "run_cv_shot_aware.py",
                "--video",
                video_path,
                "--no-stub",
                "--output-video",
                str(avi_path),
            ],
            cwd=BACKEND_DIR,
            env=process_env,
            timeout=timeout_seconds,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"CV pipeline exited with status {result.returncode}; see backend logs above."
            )

        if not avi_path.is_file() or avi_path.stat().st_size == 0:
            raise RuntimeError("CV pipeline completed without producing its annotated video")

        conversion = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(avi_path),
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(mp4_path),
            ],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        if conversion.returncode != 0 or not mp4_path.is_file() or mp4_path.stat().st_size == 0:
            raise RuntimeError(
                "Could not convert the annotated video to browser-compatible MP4. "
                f"Check that FFmpeg with libx264 is installed. {conversion.stderr}"
            )

        match_stats, events = load_match_data("default")

        stats_path = STATS_DIR / f"{match_id}_match_stats.json"
        events_path = STATS_DIR / f"{match_id}_events.json"

        with stats_path.open("w", encoding="utf-8") as f:
            json.dump(match_stats, f)
        with events_path.open("w", encoding="utf-8") as f:
            json.dump(events, f)

        print(f"CV pipeline complete. Match ID: {match_id}")
        return match_stats, events

    except subprocess.TimeoutExpired as e:
        detail = (
            f"CV processing exceeded its {e.timeout}-second time limit. "
            "Check the backend terminal for live progress and increase "
            "CV_PIPELINE_TIMEOUT_SECONDS in .env if needed."
        )
        print(f"CV pipeline timed out for {video_path} after {e.timeout} seconds.")
        raise HTTPException(status_code=504, detail=detail) from e
    except HTTPException:
        raise
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
            "POST /api/match/{id}/commentary/audio",
            "POST /api/match/{id}/commentary/video",
            "GET /api/match/{id}/commentary-video",
            "POST /api/match/{id}/chat",
            "POST /api/upload-video",
            "GET /api/match/{id}/video",
        ],
    }


@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video for CV processing.
    Returns match_id and initial stats.
    """
    try:
        match_id = f"upload_{time.time_ns()}"
        suffix = Path(file.filename or "").suffix.lower()
        file_path = UPLOADS_DIR / f"{match_id}{suffix}"
        with file_path.open("wb") as f:
            while content := await file.read(1024 * 1024):
                f.write(content)

        print(f"Video saved: {file_path}")

        match_stats, events = await run_in_threadpool(
            run_cv_pipeline, str(file_path), match_id
        )

        return {
            "match_id": match_id,
            "filename": file.filename,
            "status": "processed",
            "message": "Video processed successfully with CV pipeline",
            "stats": match_stats,
            "events_count": len(events),
            "video_url": f"/api/match/{match_id}/video",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/match/{match_id}/video")
async def get_match_video(match_id: str):
    """Stream the browser-compatible annotated video for an uploaded match."""
    if not match_id.startswith("upload_") or not match_id.removeprefix("upload_").isdigit():
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = OUTPUT_VIDEOS_DIR / f"{match_id}.mp4"
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=video_path.name,
        content_disposition_type="inline",
    )


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
        api_key = os.environ.get("GROQ_API_KEY")

        commentary_lines = generate_dynamic_commentary(
            events=events,
            clip_duration_seconds=clip_duration,
            persona=request.persona,
            player_names=player_names,
            team_names=team_names,
            language=request.language,
            api_key=api_key,
        )
        if not commentary_lines and events:
            raise RuntimeError("The LLM returned no commentary for the match events")

        return {
            "match_id": match_id,
            "persona": request.persona,
            "language": request.language,
            "commentary": commentary_lines,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Commentary generation failed for match {match_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match/{match_id}/commentary/audio")
async def generate_commentary_audio(
    match_id: str,
    request: CommentaryAudioRequest,
):
    """Generate one spoken commentary line and return it as MP3 audio."""
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Commentary text cannot be blank")

    try:
        load_match_data(match_id)
        audio = await run_in_threadpool(generate_audio_bytes, request.text.strip())
        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )
    except HTTPException:
        raise
    except RuntimeError as e:
        if "ELEVENLABS_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        print(f"ElevenLabs audio generation failed for match {match_id}: {e}")
        raise HTTPException(status_code=502, detail=f"ElevenLabs audio generation failed: {e}") from e
    except Exception as e:
        print(f"ElevenLabs audio generation failed for match {match_id}: {e}")
        raise HTTPException(status_code=502, detail=f"ElevenLabs audio generation failed: {e}") from e


@app.post("/api/match/{match_id}/commentary/video")
async def create_commentary_video(
    match_id: str,
    request: CommentaryVideoRequest,
):
    """Create an annotated MP4 with timestamped spoken commentary and quiet match audio."""
    try:
        source_video_path = _uploaded_video_path(match_id)
        match_stats, _ = load_match_data(match_id)
        duration = float(match_stats["meta"]["duration_s"])

        if any(not line.text.strip() for line in request.commentary):
            raise HTTPException(status_code=422, detail="Commentary text cannot be blank")
        if any(line.time >= duration for line in request.commentary):
            raise HTTPException(
                status_code=422,
                detail="Commentary timestamps must be within the video duration",
            )

        await run_in_threadpool(
            _render_commentary_video,
            match_id,
            source_video_path,
            request.commentary,
        )
        return {
            "video_url": f"/api/match/{match_id}/commentary-video",
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        if "ELEVENLABS_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        print(f"Commentary video generation failed for match {match_id}: {e}")
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        print(f"Commentary video generation failed for match {match_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Could not generate the commentary video: {e}",
        ) from e


@app.get("/api/match/{match_id}/commentary-video")
async def get_commentary_video(match_id: str):
    """Stream the annotated video with generated spoken commentary."""
    if not re.fullmatch(r"upload_\d+", match_id):
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = OUTPUT_VIDEOS_DIR / f"{match_id}_commentary.mp4"
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Commentary video not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=video_path.name,
        content_disposition_type="inline",
    )


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
