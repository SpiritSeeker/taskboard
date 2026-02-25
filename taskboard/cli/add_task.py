import uuid
from datetime import date, time

from taskboard.models.task import Task
from taskboard.storage.tasks_repository import load_tasks, save_tasks


def main():
    tasks = load_tasks()

    title = input("Enter task title: ")
    duration_minutes = int(input("Enter duration in minutes: "))
    priority = int(input("Enter priority (1-3) (high-low): "))
    earliest_start_str = input("Enter earliest start time (HH:MM) or leave blank: ")
    latest_end_str = input("Enter latest end time (HH:MM) or leave blank: ")
    flexible_str = input("Is the task flexible? (y/n): ")
    description = input("Enter task description: ")
    scheduled_input = input("Enter scheduled date (YYYY-MM-DD) or leave blank: ")

    earliest_start_time = (
        time.fromisoformat(earliest_start_str) if earliest_start_str else None
    )
    latest_end_time = time.fromisoformat(latest_end_str) if latest_end_str else None
    flexible = flexible_str.lower() == "y"
    if scheduled_input:
        scheduled_date = date.fromisoformat(scheduled_input)
    else:
        scheduled_date = date.today()

    incomplete_tasks = [t for t in tasks if not t.is_completed]
    depends_on_ids = []
    if incomplete_tasks:
        choice = input("Does this task depend on another task? (y/n): ")
        if choice.lower() == "y":
            print(
                "\nSelect dependencies by number (comma separated), or blank to skip:\n"
            )

            for idx, task in enumerate(incomplete_tasks, 1):
                print(f"{idx}. {task.title}")

            selected = input("\nYour choice: ").strip()
            if selected:
                try:
                    selected_indices = [int(x.strip()) for x in selected.split(",")]
                    for idx in selected_indices:
                        if 1 <= idx <= len(incomplete_tasks):
                            depends_on_ids.append(incomplete_tasks[idx - 1].id)
                        else:
                            print(f"Invalid selection: {idx}. Skipping.")
                except (ValueError, IndexError):
                    print("Invalid selection. Skipping dependencies.")

    task = Task(
        id=int(uuid.uuid4()),
        title=title,
        duration_minutes=duration_minutes,
        priority=priority,
        earliest_start_time=earliest_start_time,
        latest_end_time=latest_end_time,
        flexible=flexible,
        description=description,
        scheduled_date=scheduled_date,
        depends_on=depends_on_ids,
    )

    tasks.append(task)
    save_tasks(tasks)

    print(f"Task '{title}' added successfully!")


if __name__ == "__main__":
    main()
