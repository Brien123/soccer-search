import json
import os
from pathlib import Path

DATA_DIR = Path("statsbomb-rag-data/data")
EVENTS_DIR = DATA_DIR / "events"


def format_event_to_narrative(event):
    """Converts a StatsBomb event JSON dict into a natural language sentence."""
    player = event.get("player", {}).get("name", "Unknown Player")
    team = event.get("team", {}).get("name", "Unknown Team")
    event_type = event.get("type", {}).get("name", "Unknown")
    minute = event.get("minute", 0)
    second = event.get("second", 0)
    period = event.get("period", 1)

    if event_type == "Pass":
        recipient = event.get("pass", {}).get("recipient", {}).get("name", "a teammate")
        outcome = event.get("pass", {}).get("outcome", {}).get("name", "complete")
        return f"At {minute}:{second} in period {period}, {player} for {team} attempted a pass to {recipient}, which was {outcome.lower()}."

    elif event_type == "Shot":
        stats = event.get("shot", {})
        xg = stats.get("statsbomb_xg", 0.0)
        outcome = stats.get("outcome", {}).get("name", "missed")
        return f"At {minute}:{second} in period {period}, {player} for {team} took a shot with an xG of {xg:.2f}, resulting in a {outcome.lower()}."

    return f"At {minute}:{second} in period {period}, {player} for {team} performed a {event_type} action."


def process_sample_match():
    # Find the first available JSON file in the events folder
    event_files = list(EVENTS_DIR.glob("*.json"))
    if not event_files:
        print("No event files found. Check your directory path.")
        return

    sample_file = event_files[0]
    print(f"Reading sample match events from: {sample_file.name}\n")

    with open(sample_file, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Print the first 10 generated narratives as a test
    for event in events[:10]:
        narrative = format_event_to_narrative(event)
        print(f"- {narrative}")


if __name__ == "__main__":
    process_sample_match()