import argparse
from datetime import datetime, time

from taskboard.core.scheduler import generate_schedule
from taskboard.storage.repository import load_tasks


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
        default="09:00",
        help="Start time for scheduling (default: 09:00)",
    )
    parser.add_argument(
        "--end",
        type=parse_time_string,
        default="17:00",
        help="End time for scheduling (default: 22:00)",
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

    schedule, unscheduled = generate_schedule(
        tasks, day_start, day_end, buffer_minutes=args.buffer
    )

    print("\n=== Today's Schedule ===\n")

    total_minutes = 0
    for block in schedule:
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
