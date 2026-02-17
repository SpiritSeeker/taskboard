from datetime import datetime

from taskboard.storage.repository import load_tasks, save_tasks


def main():
    tasks = load_tasks()

    active_tasks = [t for t in tasks if t.active_session_start is not None]

    if not active_tasks:
        print("No active task to stop.")
        return

    task = active_tasks[0]

    print(f"\nCurrently working on '{task.title}'.")
    assert task.active_session_start is not None  # For type checker
    print(f"Started at: {task.active_session_start.strftime('%Y-%m-%d %H:%M')}")

    override = input("Enter stop time (YYYY-MM-DD HH:MM) or leave blank to stop now: ")

    if override:
        try:
            stop_time = datetime.fromisoformat(override)
        except ValueError:
            print("Invalid datetime format.")
            return
    else:
        stop_time = datetime.now()

    # Append work session
    task.work_sessions.append((task.active_session_start, stop_time))
    task.active_session_start = None

    duration_minutes = int((stop_time - task.work_sessions[-1][0]).total_seconds() / 60)
    print(f"\nSession duration: {duration_minutes} minutes.")

    mark_complete = input("Mark task as completed? (y/n): ").lower() == "y"
    if mark_complete:
        task.is_completed = True
        print(f"Task '{task.title}' marked as completed.")

    save_tasks(tasks)

    print("Session stopped and saved successfully.")


if __name__ == "__main__":
    main()
