"""
commentary_generator_v2.py - Multi-Persona Dynamic Commentary

Enhanced commentary generation with:
- Multiple commentator personas (broadcast, tactical, coach)
- Player identity enrichment
- Excitement level calibration
- Multi-language support foundation

Requires:
    pip install groq

Set your API key:
    export GROQ_API_KEY="your-key-here"
"""

import json
import logging
import os
from typing import Literal, Optional
from groq import Groq

MAX_COMMENTARY_EVENTS_CHARS = 5000
COMMENTARY_EVENT_FIELDS = (
    "time",
    "type",
    "team",
    "player_id",
    "from_player_id",
    "to_player_id",
    "progressive",
    "distance",
    "speed_kmh",
    "ball_speed_kmh",
    "duration_s",
    "zone",
    "pressing_team",
    "n_markers",
    "end_time",
)
PRIORITY_EVENT_TYPES = {
    "box_entry",
    "clearance",
    "pass",
    "pressure",
    "shot_or_clearance",
    "turnover",
}
VALID_EXCITEMENT_LEVELS = {"low", "medium", "high", "explosive"}
EXCITEMENT_LEVEL_ALIASES = {
    "calm": "low",
    "routine": "low",
    "moderate": "medium",
    "normal": "medium",
    "very high": "high",
    "extreme": "explosive",
    "peak": "explosive",
}


def _normalize_excitement_level(value: object, line_index: int) -> str:
    if isinstance(value, str):
        level = value.strip().lower()
        if level in VALID_EXCITEMENT_LEVELS:
            return level
        if level in EXCITEMENT_LEVEL_ALIASES:
            return EXCITEMENT_LEVEL_ALIASES[level]

    logging.warning(
        "Groq commentary item %d returned invalid excitement_level %r; "
        "using 'medium'.",
        line_index,
        value,
    )
    return "medium"


def _compact_commentary_events(events: list[dict]) -> list[dict]:
    compact_events = []
    sprint_groups: dict[tuple[int, object], dict] = {}

    for event in events:
        if not isinstance(event, dict) or event.get("type") == "possession_start":
            continue

        compact = {}
        for key in COMMENTARY_EVENT_FIELDS:
            value = event.get(key)
            if value is None or (key == "zone" and value == "unknown"):
                continue
            if isinstance(value, float):
                value = round(value, 1)
            elif isinstance(value, str):
                value = value[:40]
            elif not isinstance(value, (str, int, float, bool)):
                continue
            compact[key] = value

        if not compact:
            continue

        if compact.get("type") == "sprint":
            time_seconds = compact.get("time", 0)
            team = compact.get("team")
            bucket = (int(float(time_seconds) // 5), team)
            group = sprint_groups.get(bucket)
            if group is None:
                compact["count"] = 1
                sprint_groups[bucket] = compact
            else:
                group["count"] += 1
                if compact.get("speed_kmh", 0) > group.get("speed_kmh", 0):
                    count = group["count"]
                    group.update(compact)
                    group["count"] = count
        else:
            compact_events.append(compact)

    compact_events.extend(sprint_groups.values())
    return sorted(compact_events, key=lambda event: event.get("time", 0))


def _fit_commentary_events(
    events: list[dict], clip_duration_seconds: float
) -> list[dict]:
    compact_events = _compact_commentary_events(events)
    if len(json.dumps(compact_events, separators=(",", ":"))) <= MAX_COMMENTARY_EVENTS_CHARS:
        return compact_events

    priority_events = [
        event for event in compact_events
        if event.get("type") in PRIORITY_EVENT_TYPES
    ]
    other_events = [
        event for event in compact_events
        if event.get("type") not in PRIORITY_EVENT_TYPES
    ]

    def thin(events_to_thin: list[dict]) -> list[dict]:
        if len(events_to_thin) == 1:
            return []
        if len(events_to_thin) == 2:
            return events_to_thin[len(events_to_thin) // 2 : len(events_to_thin) // 2 + 1]
        sampled = events_to_thin[::2]
        return sampled if sampled[-1] is events_to_thin[-1] else sampled + [events_to_thin[-1]]

    while True:
        selected = sorted(priority_events + other_events, key=lambda event: event.get("time", 0))
        if not selected:
            raise ValueError(
                "The match contains too many high-priority events to fit the "
                "commentary model's request limit."
            )
        if len(json.dumps(selected, separators=(",", ":"))) <= MAX_COMMENTARY_EVENTS_CHARS:
            return selected

        if other_events:
            other_events = thin(other_events)
        elif priority_events:
            priority_events = thin(priority_events)
        else:
            raise ValueError(
                "The match contains too many high-priority events to fit the "
                "commentary model's request limit."
            )


# Persona definitions
PERSONA_PROMPTS = {
    "broadcast": """You are a poetic, highly enthusiastic football commentator. Your commentary is:
- Dramatic and emotionally charged
- Uses vivid metaphors and poetic language
- Builds tension during attacking plays
- Celebrates skill with passionate exclamations
- References the narrative and stakes of the match

Example style: "And here comes the storm! Number 7 with lightning in his boots, 
cutting through the defense like a hot knife through butter!"
""",
    
    "tactical": """You are an elite tactical analyst commentator. Your commentary focuses on:
- Spatial organization and team shape
- Pressing triggers and defensive compactness
- Passing lane availability and progressive actions
- Positional rotations and off-ball movement
- Decision-making quality

Example style: "Watch the defensive line here - excellent compactness, 
but number 12's third-man run exploits the space between midfield and defense."
""",
    
    "coach": """You are a developmental youth academy coach providing constructive, 
educational commentary. Your focus is on:
- Teaching moments and learning opportunities
- Praising good decision-making
- Explaining why certain choices work or don't work
- Encouraging attitude and work rate
- Building confidence while identifying areas for improvement

Example style: "Great anticipation from number 3 to track that run! 
That's exactly the awareness we work on in training."
""",
}


MULTI_LANGUAGE_PROMPTS = {
    "spanish": "Provide commentary in passionate Spanish broadcasting style.",
    "arabic": "Provide commentary in dramatic Arabic broadcasting style (famous for extended 'GOOOOOL' calls).",
    "hindi": "Provide commentary in enthusiastic Hindi/English cricket-style commentary.",
}


def generate_dynamic_commentary(
    events: list[dict],
    clip_duration_seconds: float,
    persona: Literal["broadcast", "tactical", "coach"] = "broadcast",
    player_names: Optional[dict[int, str]] = None,
    team_names: Optional[dict[int, str]] = None,
    match_context: Optional[dict] = None,
    language: str = "english",
    model: str = "qwen/qwen3.8-27b",
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Generate dynamic, persona-driven commentary with identity enrichment.
    """
    
    # Build system prompt
    persona_instruction = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["broadcast"])
    
    if language != "english" and language in MULTI_LANGUAGE_PROMPTS:
        persona_instruction += "\n\n" + MULTI_LANGUAGE_PROMPTS[language]
    
    system_prompt = f"""{persona_instruction}

You will receive match events with timestamps from computer vision tracking.

IDENTITY CONTEXT:
{f"Player names: {json.dumps(player_names)}" if player_names else "Use player numbers (e.g., 'number 7')"}
{f"Team names: {json.dumps(team_names)}" if team_names else "Refer to teams by Team 1 / Team 2"}
{f"Match context: {json.dumps(match_context)}" if match_context else ""}

OUTPUT FORMAT:
Return ONLY a JSON array (no markdown) with this structure:
[
  {{
    "time": <float seconds>,
    "text": "<commentary line>",
    "excitement_level": "<low|medium|high|explosive>",
    "target_player_id": <int or null>
  }}
]

EXCITEMENT CALIBRATION:
- low: Routine play, ball circulation (calm voice)
- medium: Progressive actions, sprints, pressure (moderate energy)
- high: Box entries, shots, dangerous moments (elevated intensity)
- explosive: Goals, brilliant skills, dramatic turnarounds (peak emotion)
- The excitement_level value must be exactly one of: low, medium, high, explosive.

RULES:
- Keep lines short (2-4 seconds of speech, 8-20 words)
- Don't narrate every event - combine nearby actions into natural sentences
- Leave gaps where nothing significant happens
- Cover distinct important sequences throughout the clip; for a 30-second clip, aim for 5-10 lines when the events support it
- Never replace available match events with a generic opening or filler line
- Describe only actions supported by the supplied events; do not infer goals, outcomes, or player identities
- Use player names when available, numbers when not
- Match excitement_level to the action's importance
- For 'tactical' persona: Explain the 'why' behind actions
- For 'coach' persona: Frame as teaching moments
"""

    # Build user content
    if not events:
        return []

    user_content = {
        "clip_duration_seconds": round(clip_duration_seconds, 2),
        "events": _fit_commentary_events(events, clip_duration_seconds),
    }

    try:
        client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        "Generate commentary for these match events. Sprint entries "
                        "with count greater than one summarize multiple sprints in "
                        "the same short period; do not attribute the group to one player.\n\n"
                        f"{json.dumps(user_content, separators=(',', ':'), ensure_ascii=False)}"
                    ),
                },
            ],
            temperature=0.8 if persona == "broadcast" else 0.6,
            max_tokens=2000,
        )

        raw_text = response.choices[0].message.content
        if not raw_text:
            raise ValueError("Groq returned an empty commentary response")
        raw_text = raw_text.strip()

        # Try to extract JSON if wrapped in markdown
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.rsplit("```")[0].strip()

        lines = json.loads(raw_text)
        if isinstance(lines, dict) and isinstance(lines.get("commentary"), list):
            lines = lines["commentary"]
        if not isinstance(lines, list):
            raise ValueError("Groq commentary response must be a JSON array")

        for index, line in enumerate(lines, start=1):
            if not isinstance(line, dict):
                raise ValueError("Groq commentary items must be JSON objects")
            if not isinstance(line.get("time"), (int, float)):
                raise ValueError("Groq commentary items must include a numeric time")
            if not isinstance(line.get("text"), str) or not line["text"].strip():
                raise ValueError("Groq commentary items must include non-empty text")
            line["excitement_level"] = _normalize_excitement_level(
                line.get("excitement_level"), index
            )

        lines.sort(key=lambda x: x.get("time", 0))

        return lines
    except Exception as e:
        raise RuntimeError(f"Groq commentary generation failed: {e}") from e


if __name__ == "__main__":
    import sys

    events_path = sys.argv[1] if len(sys.argv) > 1 else "stats/events.json"
    persona = sys.argv[2] if len(sys.argv) > 2 else "broadcast"
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0

    with open(events_path) as f:
        events = json.load(f)

    # Example player names
    player_names = {
        1: "De Bruyne",
        7: "Sterling",
        12: "Foden",
        16: "Haaland",
    }

    team_names = {
        1: "City",
        2: "United",
    }

    match_context = {
        "score": "1-1",
        "match_time": "78th minute",
        "stakes": "Manchester Derby",
    }

    print(f"\n=== Generating {persona.upper()} Commentary ===\n")

    lines = generate_dynamic_commentary(
        events=events,
        clip_duration_seconds=duration,
        persona=persona,
        player_names=player_names,
        team_names=team_names,
        match_context=match_context,
    )

    for line in lines:
        print(f"[{line['time']:.2f}s] ({line['excitement_level']}) {line['text']}")
        if line.get('target_player_id'):
            print(f"  └─ Focus: Player {line['target_player_id']}")
