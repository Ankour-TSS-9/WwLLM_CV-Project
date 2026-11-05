"""
ai_coach.py - AI Performance Coach Engine

Generates comprehensive player performance reports using LLM analysis of tracking data.
Produces structured output matching the frontend AnalysisResult schema.

Requires:
    pip install groq

Set your API key as an environment variable:
    export GROQ_API_KEY="your-key-here"
"""

import json
import os
from typing import Optional
from groq import Groq


COACH_SYSTEM_PROMPT = """
You are an elite UEFA Pro football performance coach with expertise in player development, 
tactical analysis, and sports science. You analyze player tracking data from computer vision 
systems to provide actionable feedback.

Your task is to evaluate a player's performance based on their match statistics and events.

IMPORTANT EVALUATION CRITERIA:
- Sprint speed & frequency: Elite = 33+ km/h, Good = 28-32 km/h, Average = <28 km/h
- Work rate: Distance covered, on-ball vs off-ball movement
- Decision making: Shot selection, pass choices, carries into dangerous areas
- Positioning: Zone occupancy (attacking third presence for forwards, defensive shape for defenders)
- Technical execution: Pass accuracy, shot quality, ball control during carries

OUTPUT REQUIREMENTS:
Return ONLY a JSON object (no markdown fences) matching this exact schema:
{
  "overall_score": <number 0-100>,
  "accuracy_percent": <number 0-100>,
  "summary": "<2-3 sentence executive summary>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "phases": [
    {"name": "setup", "score": <0-100>},
    {"name": "approach", "score": <0-100>},
    {"name": "execution", "score": <0-100>},
    {"name": "follow-through", "score": <0-100>}
  ],
  "key_moments": [
    {
      "timestamp_seconds": <float>,
      "classification": "<Brilliant|Great|Good|Inaccuracy|Mistake|Blunder>",
      "comment": "<brief tactical observation>"
    }
  ],
  "drills": [
    "<specific drill name with coaching instruction to address weaknesses>"
  ],
  "joint_angles": []
}

CLASSIFICATION GUIDE:
- Brilliant: Exceptional play (35+ km/h sprint, perfect shot, box entry leading to goal)
- Great: High-quality action (progressive pass, dangerous carry, good recovery sprint)
- Good: Solid play (accurate pass, effective positioning)
- Inaccuracy: Minor error (misplaced pass under no pressure, poor first touch)
- Mistake: Clear error (turnover in dangerous area, missed defensive assignment)
- Blunder: Critical error (giving away goal-scoring opportunity)

Focus on the 4-6 most significant moments. Be specific with timestamps.
For drills, prescribe exercises that directly address identified weaknesses.
"""


def generate_player_coach_report(
    match_stats: dict,
    player_id: int,
    events: list[dict],
    player_name: Optional[str] = None,
    model: str = "qwen/qwen3.8-27b",
    api_key: Optional[str] = None,
) -> dict:
    """
    Generate an AI coaching report for a specific player.

    Args:
        match_stats: Full match statistics JSON (from match_stats.json)
        player_id: ID of the player to analyze
        events: List of match events (from events.json)
        player_name: Optional player name (defaults to "Player {id}")
        model: Gemini model to use
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)

    Returns:
        Dictionary matching AnalysisResult schema

    Raises:
        ValueError: If player not found in stats
    """
    # Find player data
    player_data = next(
        (p for p in match_stats.get("players", []) if p["player_id"] == player_id),
        None,
    )

    if not player_data:
        raise ValueError(f"Player {player_id} not found in match statistics.")

    # Filter events for this player
    player_events = [
        e for e in events
        if e.get("player_id") == player_id or e.get("passer_id") == player_id
    ]

    # Get team context
    team_id = player_data["team"]
    team_data = match_stats.get("teams", {}).get(str(team_id), {})

    # Build context for LLM
    context = {
        "player_name": player_name or f"Player {player_id}",
        "player_id": player_id,
        "team": team_id,
        "match_duration": match_stats["meta"]["duration_s"],
        "player_metrics": {
            "minutes_played": round(player_data["minutes_visible"], 2),
            "distance_m": round(player_data["distance_m"], 2),
            "max_speed_kmh": round(player_data["max_speed_kmh"], 2),
            "avg_speed_kmh": round(player_data["avg_speed_kmh"], 2),
            "sprints": player_data["sprints"],
            "passes": player_data["passes"],
            "passes_received": player_data["passes_received"],
            "progressive_passes": player_data["progressive_passes"],
            "touches": player_data["touches"],
            "carries": player_data["carries"],
            "box_entries": player_data["box_entries"],
            "shots": player_data["shots"],
            "distance_on_ball_m": round(player_data["distance_on_ball_m"], 2),
            "distance_off_ball_m": round(player_data["distance_off_ball_m"], 2),
            "zone_frames": player_data["zone_frames"],
        },
        "team_context": {
            "possession_percent": round(team_data.get("possession", 0) * 100, 1),
            "team_sprints": team_data.get("sprints", 0),
            "team_passes": team_data.get("passes", 0),
            "attack_direction": team_data.get("attack_direction", {}),
        },
        "player_events": player_events[:50],  # Limit to 50 most relevant events
    }

    # Call Groq
    client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": COACH_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"Analyze this player performance data and provide a detailed coaching report:\n\n{json.dumps(context, indent=2)}",
                },
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        raw_text = response.choices[0].message.content.strip()

        result = json.loads(raw_text)

        # Validate and ensure required fields
        result.setdefault("joint_angles", [])
        result.setdefault("phases", [
            {"name": "setup", "score": 75},
            {"name": "approach", "score": 75},
            {"name": "execution", "score": 75},
            {"name": "follow-through", "score": 75},
        ])

        return result

    except Exception as e:
        # Fallback response on error
        print(f"⚠️ AI Coach error: {e}")
        return {
            "overall_score": 70,
            "accuracy_percent": 70,
            "summary": f"Analysis incomplete due to error: {str(e)}",
            "strengths": ["Work rate", "Effort"],
            "weaknesses": ["Analysis failed - please retry"],
            "phases": [
                {"name": "setup", "score": 70},
                {"name": "approach", "score": 70},
                {"name": "execution", "score": 70},
                {"name": "follow-through", "score": 70},
            ],
            "key_moments": [],
            "drills": ["Retry analysis"],
            "joint_angles": [],
        }


if __name__ == "__main__":
    import sys

    # Test script: python ai_coach.py <player_id>
    stats_path = "stats/match_stats.json"
    events_path = "stats/events.json"
    player_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    with open(stats_path) as f:
        match_stats = json.load(f)

    with open(events_path) as f:
        events = json.load(f)

    print(f"\n=== Generating AI Coach Report for Player {player_id} ===\n")

    report = generate_player_coach_report(match_stats, player_id, events)

    print(json.dumps(report, indent=2))
    print(f"\n✅ Overall Score: {report['overall_score']}/100")
    print(f"📊 Accuracy: {report['accuracy_percent']}%")
    print(f"\n📝 Summary: {report['summary']}")
