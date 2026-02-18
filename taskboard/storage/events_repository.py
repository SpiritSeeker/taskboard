import json
from datetime import datetime
from pathlib import Path
from typing import List

from taskboard.models.event import Event

DATA_PATH = Path(__file__).parent / "events.json"


def _serialize_event(event: Event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "description": event.description,
        "source": event.source,
        "external_id": event.external_id,
    }


def _deserialize_event(data: dict) -> Event:
    return Event(
        id=data["id"],
        title=data["title"],
        start=datetime.fromisoformat(data["start"]),
        end=datetime.fromisoformat(data["end"]),
        description=data.get("description"),
        source=data["source"],
        external_id=data.get("external_id"),
    )


def load_events() -> List[Event]:
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    return [_deserialize_event(item) for item in data]


def save_events(events: List[Event]):
    # Sort events by start time, then by title
    events.sort(key=lambda e: (e.start, e.title))
    with open(DATA_PATH, "w") as f:
        json.dump([_serialize_event(event) for event in events], f, indent=2)
