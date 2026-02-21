import argparse
from datetime import date, datetime

from taskboard.storage.events_repository import load_events


def parse_date_string(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."
        )


def main():
    parser = argparse.ArgumentParser(description="Display events")
    parser.add_argument(
        "--date",
        type=parse_date_string,
        default=date.today(),
        help="Date to display events for (default: today)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed event information",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all events regardless of date",
    )
    args = parser.parse_args()

    events = load_events()
    events = sorted(events, key=lambda e: e.start)
    if not args.all:
        events = [e for e in events if e.start.date() == args.date]

    if not events:
        print("No events found.")
        return

    for event in events:
        title = f"{event.title} (Event)"
        if event.start <= datetime.now() <= event.end:
            title = f"{event.title} (Event - Ongoing)"
        print(
            f"- {title}: {event.start.strftime('%Y-%m-%d %H:%M')} to {event.end.strftime('%Y-%m-%d %H:%M')}"
        )
        if args.verbose:
            print(f"  Description: {event.description}")


if __name__ == "__main__":
    main()
