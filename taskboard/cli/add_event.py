import uuid
from datetime import datetime

from taskboard.models.event import Event
from taskboard.storage.events_repository import load_events, save_events


def main():
    events = load_events()

    title = input("Enter event title: ")
    start_str = input("Enter start time (YYYY-MM-DD HH:MM): ")
    end_str = input("Enter end time (YYYY-MM-DD HH:MM): ")
    description = input("Enter event description or leave blank: ")

    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
    except ValueError:
        print("Invalid datetime format.")
        return
    if end <= start:
        print("End time must be after start time.")
        return

    event = Event(
        id=int(uuid.uuid4()),
        title=title,
        start=start,
        end=end,
        description=description,
        source="manual",
    )

    events.append(event)
    save_events(events)

    print(f"Event '{title}' added successfully!")


if __name__ == "__main__":
    main()
