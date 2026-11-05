#!/usr/bin/env python3
"""
Test script for AI Coach functionality

Usage:
    python3 test_ai_coach.py [player_id]

Example:
    python3 test_ai_coach.py 1
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from coaching.ai_coach import generate_player_coach_report


def main():
    # Configuration
    stats_path = Path("stats/match_stats.json")
    events_path = Path("stats/events.json")
    player_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    # Check if files exist
    if not stats_path.exists():
        print(f"❌ Error: {stats_path} not found")
        return

    if not events_path.exists():
        print(f"❌ Error: {events_path} not found")
        return

    # Load data
    with open(stats_path) as f:
        match_stats = json.load(f)

    with open(events_path) as f:
        events = json.load(f)

    # Find player info
    player_data = next(
        (p for p in match_stats["players"] if p["player_id"] == player_id),
        None,
    )

    if not player_data:
        print(f"❌ Error: Player {player_id} not found")
        print(f"\nAvailable players:")
        for p in match_stats["players"][:10]:
            print(f"  - Player {p['player_id']} (Team {p['team']})")
        return

    print("\n" + "=" * 70)
    print(f"🏃 FALCON PERCH AI COACH - Player {player_id} Performance Report")
    print("=" * 70)

    # Generate report
    print("\n⏳ Analyzing performance data with AI coach...\n")

    try:
        report = generate_player_coach_report(
            match_stats=match_stats,
            player_id=player_id,
            events=events,
            player_name=f"Player {player_id}",
        )

        # Display report
        print("📊 OVERALL PERFORMANCE")
        print(f"   Score: {report['overall_score']}/100")
        print(f"   Accuracy: {report['accuracy_percent']}%")
        print(f"\n📝 SUMMARY")
        print(f"   {report['summary']}")

        print(f"\n💪 STRENGTHS ({len(report['strengths'])})")
        for strength in report['strengths']:
            print(f"   ✓ {strength}")

        print(f"\n⚠️  AREAS FOR IMPROVEMENT ({len(report['weaknesses'])})")
        for weakness in report['weaknesses']:
            print(f"   • {weakness}")

        print(f"\n🎯 KEY MOMENTS ({len(report['key_moments'])})")
        for moment in report['key_moments']:
            mins = int(moment['timestamp_seconds'] // 60)
            secs = int(moment['timestamp_seconds'] % 60)
            emoji = {
                'Brilliant': '🌟',
                'Great': '⭐',
                'Good': '✅',
                'Inaccuracy': '⚡',
                'Mistake': '⚠️',
                'Blunder': '❌',
            }.get(moment['classification'], '📍')
            print(f"   {emoji} [{mins:02d}:{secs:02d}] {moment['classification']}: {moment['comment']}")

        print(f"\n🏋️  RECOMMENDED DRILLS ({len(report['drills'])})")
        for i, drill in enumerate(report['drills'], 1):
            print(f"   {i}. {drill}")

        # Phase scores
        print(f"\n📈 PHASE BREAKDOWN")
        for phase in report['phases']:
            bar_length = int(phase['score'] / 5)
            bar = '█' * bar_length + '░' * (20 - bar_length)
            print(f"   {phase['name'].capitalize():15} [{bar}] {phase['score']}%")

        # Raw metrics
        print(f"\n📊 RAW METRICS")
        print(f"   Distance: {player_data['distance_m']:.1f}m")
        print(f"   Max Speed: {player_data['max_speed_kmh']:.1f} km/h")
        print(f"   Sprints: {player_data['sprints']}")
        print(f"   Touches: {player_data['touches']}")
        print(f"   Passes: {player_data['passes']} (Progressive: {player_data['progressive_passes']})")
        print(f"   Box Entries: {player_data['box_entries']}")
        print(f"   Shots: {player_data['shots']}")

        print("\n" + "=" * 70)
        print("✅ Report generated successfully!")
        print("=" * 70 + "\n")

        # Save report
        output_path = Path(f"stats/player_{player_id}_coach_report.json")
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"💾 Report saved to: {output_path}")

    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
