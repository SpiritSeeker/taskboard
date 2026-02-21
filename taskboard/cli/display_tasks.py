import argparse
from datetime import date

from taskboard.storage.tasks_repository import load_tasks


def parse_date_string(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."
        )


def main():
    parser = argparse.ArgumentParser(description="Display tasks")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all tasks regardless of date and completion status",
    )
    parser.add_argument(
        "--overdue",
        action="store_true",
        help="Show only overdue tasks",
    )
    parser.add_argument(
        "--date",
        type=parse_date_string,
        default=date.today(),
        help="Date to display tasks for (default: today)",
    )
    parser.add_argument(
        "--completed",
        action="store_true",
        help="Show only completed tasks",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed task information",
    )
    args = parser.parse_args()

    tasks = load_tasks()
    tasks.sort(
        key=lambda t: (
            not t.is_completed,
            t.scheduled_date or date.max,
            t.active_session_start is not None,
        )
    )

    if not args.all:
        if args.overdue:
            tasks = [
                t
                for t in tasks
                if t.scheduled_date is not None
                and t.scheduled_date < date.today()
                and not t.is_completed
                and t.active_session_start is None
            ]
        elif args.completed:
            tasks = [t for t in tasks if t.is_completed]
        else:
            tasks = [
                t for t in tasks if t.scheduled_date <= args.date and not t.is_completed
            ]

    if not tasks:
        print("No tasks to display.")
        return

    for task in tasks:
        post_title_str = ""
        if task.is_completed:
            status = "✓"
        elif task.active_session_start is not None:
            status = ">"
            post_title_str = f" (ACTIVE since {task.active_session_start.strftime('%Y-%m-%d %H:%M')})"
        elif task.scheduled_date is not None and task.scheduled_date < date.today():
            status = "!"
        else:
            status = " "
        print(f"[{status}] {task.title}{post_title_str}")
        if args.verbose:
            print(f"    Priority: {task.priority}")
            if task.is_completed:
                time_taken_minutes = int(
                    sum(
                        (end - start).total_seconds()
                        for start, end in task.work_sessions
                    )
                    / 60
                )
                print(f"    Time Taken: {time_taken_minutes} mins")
            else:
                print(f"    Estimated: {task.duration_minutes} mins")
            print(f"    Scheduled Date: {task.scheduled_date}")
            print(f"    Earliest Start: {task.earliest_start_time}")
            print(f"    Latest End: {task.latest_end_time}")
            print(f"    Flexible: {'Yes' if task.flexible else 'No'}")
            print(f"    Description: {task.description}\n")


if __name__ == "__main__":
    main()
