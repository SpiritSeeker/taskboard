import uuid
from datetime import date, time

from taskboard.models.task import Task
from taskboard.storage.repository import load_tasks, save_tasks


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
    )

    tasks.append(task)
    save_tasks(tasks)

    print(f"Task '{title}' added successfully!")


if __name__ == "__main__":
    main()
