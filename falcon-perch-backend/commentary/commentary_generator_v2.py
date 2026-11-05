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
import os
from typing import Literal, Optional
from groq import Groq


# Persona definitions
PERSONA_PROMPTS = {
    "broadcast": """You are an iconic, poetic, highly enthusiastic football commentator 
in the style of Peter Drury or Ray Hudson. Your commentary is:
- Dramatic and emotionally charged
- Uses vivid metaphors and poetic language
- Builds tension during attacking plays
- Celebrates skill with passionate exclamations
- References the narrative and stakes of the match

Example style: "And here comes the storm! Number 7 with lightning in his boots, 
cutting through the defense like a hot knife through butter!"
""",
    
    "tactical": """You are an elite tactical analyst commentator in the style of 
Gary Neville or Pep Guardiola. Your commentary focuses on:
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

RULES:
- Keep lines short (2-4 seconds of speech, 8-20 words)
- Don't narrate every event - combine nearby actions into natural sentences
- Leave gaps where nothing significant happens
- Use player names when available, numbers when not
- Match excitement_level to the action's importance
- For 'tactical' persona: Explain the 'why' behind actions
- For 'coach' persona: Frame as teaching moments
"""

    # Build user content
    user_content = {
        "clip_duration_seconds": round(clip_duration_seconds, 2),
        "events": events,
    }

    # Call Groq with error handling
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
                    "content": f"Generate commentary for these match events:\n\n{json.dumps(user_content, indent=2)}",
                },
            ],
            temperature=0.8 if persona == "broadcast" else 0.6,
            max_tokens=2000,
        )

        raw_text = response.choices[0].message.content.strip()

        # Try to extract JSON if wrapped in markdown
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.rsplit("```")[0].strip()

        lines = json.loads(raw_text)
        if not isinstance(lines, list):
            lines = [lines]
        lines.sort(key=lambda x: x.get("time", 0))

        return lines
    except Exception as e:
        print(f"Error generating commentary: {e}")
        # Return fallback commentary
        return [
            {
                "time": 0.0,
                "text": "Watch the match unfold with precision and skill.",
                "excitement_level": "medium",
                "target_player_id": None
            }
        ]


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
