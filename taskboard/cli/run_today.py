import argparse
from datetime import datetime, time, timedelta

from taskboard.core.scheduler import generate_schedule
from taskboard.core.timeline import ScheduledBlock
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

    active_tasks = [task for task in tasks if task.active_session_start is not None]
    active_block = None
    if active_tasks:
        active_task = active_tasks[0]
        assert active_task.active_session_start is not None
        active_task_end_estimated = active_task.active_session_start + timedelta(
            minutes=active_task.duration_minutes
        )
        # If the active task end time is in the past, the active task end time is now
        if active_task_end_estimated < datetime.now():
            active_task_end_estimated = datetime.now()

        # Bump the active_task_end_estimated to next multiple of buffer_minutes if buffer is set
        if args.buffer > 0:
            buffer_td = timedelta(minutes=args.buffer)
            active_task_end_estimated += (
                buffer_td - (active_task_end_estimated - datetime.min) % buffer_td
            ) % buffer_td
            day_start = max(day_start, active_task_end_estimated + buffer_td)
        else:
            day_start = max(day_start, active_task_end_estimated)

        active_block = ScheduledBlock(
            task=active_task,
            title=active_task.title + " (IN PROGRESS)",
            start_time=active_task.active_session_start,
            end_time=active_task_end_estimated,
        )

        # Remove active task from scheduling pool
        tasks = [t for t in tasks if t.id != active_task.id]

    schedule, unscheduled = generate_schedule(
        tasks, day_start, day_end, buffer_minutes=args.buffer
    )
    if active_block is not None:
        schedule.insert(0, active_block)
    schedule.sort(key=lambda block: block.start_time)

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
