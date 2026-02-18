from datetime import datetime

from taskboard.storage.tasks_repository import load_tasks, save_tasks


def main():
    tasks = load_tasks()

    active_tasks = [t for t in tasks if t.active_session_start is not None]

    if active_tasks:
        print(
            f"You are already working on '{active_tasks[0].title}'. Please complete it before starting a new task."
        )
        return

    available_tasks = [t for t in tasks if not t.is_completed]

    if not available_tasks:
        print("No incomplete tasks available to start.")
        return

    print("\nSelect a task to start:\n")
    for i, task in enumerate(available_tasks, start=1):
        date_str = f"({task.scheduled_date.isoformat()})" if task.scheduled_date else ""
        print(f"{i}. {task.title} {date_str}")

    choice = input("\nEnter the number of the task to start: ")

    try:
        selected_task = available_tasks[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    override = input(
        "Enter start time (YYYY-MM-DD HH:MM) or leave blank to start now: "
    )

    if override:
        try:
            start_time = datetime.fromisoformat(override)
        except ValueError:
            print("Invalid datetime format.")
            return
    else:
        start_time = datetime.now()

    selected_task.active_session_start = start_time
    save_tasks(tasks)

    print(f"\nStarted '{selected_task.title}' at {start_time.strftime('%H:%M')}.")


if __name__ == "__main__":
    main()
