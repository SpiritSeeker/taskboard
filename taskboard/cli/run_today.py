import argparse
from datetime import datetime, time

from taskboard.core.scheduler import generate_schedule
from taskboard.core.timeline import ScheduledBlock
from taskboard.storage.events_repository import load_events
from taskboard.storage.tasks_repository import load_tasks


def parse_time_string(time_str: str) -> time:
    try:
        return time.fromisoformat(time_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid time format: '{time_str}'. Expected HH:MM."
        )


def main():
    parser = argparse.ArgumentParser(description="Generate today's TaskBoard schedule.")
    parser.add_argument(
        "--start",
        type=parse_time_string,
        default=datetime.now().time(),
        help="Start time for scheduling (default: current time)",
    )
    parser.add_argument(
        "--end",
        type=parse_time_string,
        default="23:59",
        help="End time for scheduling (default: 23:59)",
    )
    parser.add_argument(
        "--buffer",
        type=int,
        default=0,
        help="Buffer time in minutes between tasks (default: 0)",
    )
    args = parser.parse_args()

    today = datetime.now().date()

    if isinstance(args.start, str):
        args.start = time.fromisoformat(args.start)
    if isinstance(args.end, str):
        args.end = time.fromisoformat(args.end)

    day_start = datetime.combine(today, args.start)
    day_end = datetime.combine(today, args.end)

    if day_end <= day_start:
        print("Error: End time must be after start time.")
        return

    tasks = load_tasks()
    events = load_events()
    events = [e for e in events if e.start.date() == today]
    events = [e for e in events if e.end > datetime.now()]  # Filter out past events
    event_blocks = []
    now = datetime.now()
    for e in events:
        title = f"[EVENT] {e.title}"

        if e.start <= now <= e.end:
            title = f"[EVENT - ONGOING] {e.title}"

        event_blocks.append(
            ScheduledBlock(
                id=e.id,
                title=title,
                start_time=e.start,
                end_time=e.end,
            )
        )

    # Delegate active task handling to scheduler
    schedule, unscheduled = generate_schedule(
        tasks, events, day_start, day_end, buffer_minutes=args.buffer
    )
    all_blocks = schedule + event_blocks
    all_blocks.sort(key=lambda block: block.start_time)

    print("\n=== Today's Schedule ===\n")

    total_minutes = 0
    for block in all_blocks:
        duration = (block.end_time - block.start_time).total_seconds() / 60
        total_minutes += duration

        print(
            f"{block.start_time.strftime('%H:%M')} - {block.end_time.strftime('%H:%M')}: "
            f"{block.title} ({int(duration)} mins)"
        )

    print(f"\nTotal scheduled time: {int(total_minutes)} minutes")

    if unscheduled:
        print("\n=== Unscheduled Tasks ===\n")
        for task in unscheduled:
            print(f"- {task.title} ({task.duration_minutes} mins)")


if __name__ == "__main__":
    main()
