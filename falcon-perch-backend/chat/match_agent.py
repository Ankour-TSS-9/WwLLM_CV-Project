"""
match_agent.py - Conversational Match Analytics (RAG on Match Telemetry)

Enables natural language Q&A over match tracking data using LLM with function calling.
Players and coaches can ask questions like:
- "How many sprints did player 7 make above 33 km/h?"
- "Which player covered the most distance in the final third?"
- "Show me all box entries by our team"

Requires:
    pip install groq
"""

import json
import os
from typing import Optional
from groq import Groq


# Define tools for function calling
TOOLS = {
    "get_player_stats": {
        "description": "Retrieve detailed statistics for a specific player by their ID",
        "parameters": {
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "integer",
                    "description": "The player's tracking ID",
                },
            },
            "required": ["player_id"],
        },
    },
    "find_events": {
        "description": "Search for events matching specific criteria (type, player, speed threshold, zone)",
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Type of event (sprint, pass, shot, carry, box_entry, possession_start)",
                },
                "player_id": {
                    "type": "integer",
                    "description": "Filter by player ID (optional)",
                },
                "team": {
                    "type": "integer",
                    "description": "Filter by team (1 or 2, optional)",
                },
                "min_speed_kmh": {
                    "type": "number",
                    "description": "Minimum speed threshold for sprints (optional)",
                },
                "zone": {
                    "type": "string",
                    "description": "Zone filter: own_third, middle_third, final_third (optional)",
                },
            },
            "required": ["event_type"],
        },
    },
    "compare_players": {
        "description": "Compare statistics between two players",
        "parameters": {
            "type": "object",
            "properties": {
                "player_id_1": {"type": "integer"},
                "player_id_2": {"type": "integer"},
            },
            "required": ["player_id_1", "player_id_2"],
        },
    },
    "get_team_summary": {
        "description": "Get overall team statistics and performance summary",
        "parameters": {
            "type": "object",
            "properties": {
                "team": {
                    "type": "integer",
                    "description": "Team number (1 or 2)",
                },
            },
            "required": ["team"],
        },
    },
}


class MatchAgent:
    """
    Conversational agent for match analytics using LLM function calling.
    """

    def __init__(
        self,
        match_stats: dict,
        events: list[dict],
        player_names: Optional[dict[int, str]] = None,
        model: str = "qwen/qwen3.8-27b",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the match agent.

        Args:
            match_stats: Match statistics JSON
            events: Match events list
            player_names: Optional mapping of player_id -> name
            model: Groq model to use
            api_key: Groq API key
        """
        self.match_stats = match_stats
        self.events = events
        self.player_names = player_names or {}
        self.model = model
        self.client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))

    def _get_player_stats(self, player_id: int) -> dict:
        """Tool: Get player statistics."""
        player = next(
            (p for p in self.match_stats["players"] if p["player_id"] == player_id),
            None,
        )
        if not player:
            return {"error": f"Player {player_id} not found"}
        
        player_name = self.player_names.get(player_id, f"Player {player_id}")
        return {
            "player_id": player_id,
            "name": player_name,
            "stats": player,
        }

    def _find_events(
        self,
        event_type: str,
        player_id: Optional[int] = None,
        team: Optional[int] = None,
        min_speed_kmh: Optional[float] = None,
        zone: Optional[str] = None,
    ) -> list[dict]:
        """Tool: Find events matching criteria."""
        filtered = [e for e in self.events if e.get("type") == event_type]

        if player_id is not None:
            filtered = [e for e in filtered if e.get("player_id") == player_id]

        if team is not None:
            filtered = [e for e in filtered if e.get("team") == team]

        if min_speed_kmh is not None:
            filtered = [
                e for e in filtered
                if e.get("speed_kmh", 0) >= min_speed_kmh
            ]

        if zone is not None:
            filtered = [e for e in filtered if e.get("zone") == zone]

        return filtered

    def _compare_players(self, player_id_1: int, player_id_2: int) -> dict:
        """Tool: Compare two players."""
        p1_stats = self._get_player_stats(player_id_1)
        p2_stats = self._get_player_stats(player_id_2)

        if "error" in p1_stats or "error" in p2_stats:
            return {"error": "One or both players not found"}

        return {
            "player_1": p1_stats,
            "player_2": p2_stats,
            "comparison": {
                "distance_diff_m": round(
                    p1_stats["stats"]["distance_m"] - p2_stats["stats"]["distance_m"], 2
                ),
                "speed_diff_kmh": round(
                    p1_stats["stats"]["max_speed_kmh"] - p2_stats["stats"]["max_speed_kmh"], 2
                ),
                "sprint_diff": p1_stats["stats"]["sprints"] - p2_stats["stats"]["sprints"],
            },
        }

    def _get_team_summary(self, team: int) -> dict:
        """Tool: Get team summary."""
        team_data = self.match_stats["teams"].get(str(team), {})
        team_players = [
            p for p in self.match_stats["players"] if p["team"] == team
        ]

        return {
            "team": team,
            "team_stats": team_data,
            "player_count": len(team_players),
            "top_performers": {
                "fastest": max(team_players, key=lambda x: x["max_speed_kmh"]),
                "most_distance": max(team_players, key=lambda x: x["distance_m"]),
                "most_sprints": max(team_players, key=lambda x: x["sprints"]),
            },
        }

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a tool function."""
        tool_map = {
            "get_player_stats": self._get_player_stats,
            "find_events": self._find_events,
            "compare_players": self._compare_players,
            "get_team_summary": self._get_team_summary,
        }

        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return tool_map[tool_name](**args)
        except Exception as e:
            return {"error": str(e)}

    def chat(self, user_question: str) -> str:
        """
        Answer a user question about the match using function calling.

        Args:
            user_question: Natural language question

        Returns:
            Natural language answer with video timestamps where relevant
        """
        system_prompt = f"""You are an expert football analytics assistant. You have access to 
detailed tracking data from a match analysis system. Answer user questions conversationally 
but precisely, citing specific statistics and timestamps.

Available data:
- Match duration: {self.match_stats['meta']['duration_s']}s
- Teams: {list(self.match_stats['teams'].keys())}
- Total players tracked: {len(self.match_stats['players'])}
- Total events: {len(self.events)}

When referencing specific moments, include the timestamp in format "at MM:SS".
If you find relevant events, mention when they occurred.

Be helpful and insightful. Provide specific statistics and context from the data.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"


if __name__ == "__main__":
    # Test the agent
    stats_path = "stats/match_stats.json"
    events_path = "stats/events.json"

    with open(stats_path) as f:
        match_stats = json.load(f)

    with open(events_path) as f:
        events = json.load(f)

    agent = MatchAgent(
        match_stats=match_stats,
        events=events,
        player_names={1: "Player A", 7: "Player B", 12: "Player C"},
    )

    print("=== Falcon Perch Match Chat Agent ===\n")
    print("Example questions:")
    print("- How many sprints did player 1 make?")
    print("- Who was the fastest player?")
    print("- Show me all shots on goal")
    print("- Compare player 1 and player 12\n")

    # Interactive mode
    while True:
        question = input("\n🏃 Ask a question (or 'quit'): ").strip()
        if question.lower() in ["quit", "exit", "q"]:
            break

        answer = agent.chat(question)
        print(f"\n🤖 {answer}")
