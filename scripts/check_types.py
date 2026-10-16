import json
from pathlib import Path

DATA_DIR = Path("statsbomb-rag-data/data")
EVENTS_DIR = DATA_DIR / "events"

event_files = list(EVENTS_DIR.glob("*.json"))
if not event_files:
    print("No event files found.")
else:
    sample_file = event_files[0]
    print(f"Reading file: {sample_file.name}\n")
    
    with open(sample_file, "r", encoding="utf-8") as f:
        events = json.load(f)
    
    event_types = set()
    for event in events:
        t = event.get("type", {}).get("name")
        if t:
            event_types.add(t)
            
    print("Found the following event types in this match:")
    for et in sorted(event_types):
        print(f"- {et}")