import json
from datetime import date, datetime, time
from pathlib import Path
from typing import List

from taskboard.models.task import Task

DATA_PATH = Path(__file__).parent / "tasks.json"


def _serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
        "earliest_start_time": task.earliest_start_time.isoformat()
        if task.earliest_start_time
        else None,
        "latest_end_time": task.latest_end_time.isoformat()
        if task.latest_end_time
        else None,
        "flexible": task.flexible,
        "is_completed": task.is_completed,
        "description": task.description,
        "scheduled_date": task.scheduled_date.isoformat()
        if task.scheduled_date
        else date.today().isoformat(),
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "energy_level": task.energy_level,
        "work_sessions": [
            (start.isoformat(), end.isoformat()) for start, end in task.work_sessions
        ],
        "active_session_start": (
            task.active_session_start.isoformat() if task.active_session_start else None
        ),
    }


def _deserialize_task(data: dict) -> Task:
    return Task(
        id=data["id"],
        title=data["title"],
        duration_minutes=data["duration_minutes"],
        priority=data["priority"],
        earliest_start_time=time.fromisoformat(data["earliest_start_time"])
        if data["earliest_start_time"]
        else None,
        latest_end_time=time.fromisoformat(data["latest_end_time"])
        if data["latest_end_time"]
        else None,
        flexible=data["flexible"],
        is_completed=data.get("is_completed", False),
        description=data.get("description"),
        scheduled_date=date.fromisoformat(data["scheduled_date"])
        if data.get("scheduled_date")
        else date.today(),
        deadline=datetime.fromisoformat(data["deadline"]) if data["deadline"] else None,
        energy_level=data.get("energy_level", 2),
        work_sessions=[
            (datetime.fromisoformat(start), datetime.fromisoformat(end))
            for start, end in data.get("work_sessions", [])
        ],
        active_session_start=(
            datetime.fromisoformat(data["active_session_start"])
            if data.get("active_session_start")
            else None
        ),
    )


def load_tasks() -> List[Task]:
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    return [_deserialize_task(item) for item in data]


def save_tasks(tasks: List[Task]):
    # Sort tasks by scheduled date and priority before saving
    tasks.sort(key=lambda t: (t.scheduled_date or date.today(), t.priority))
    with open(DATA_PATH, "w") as f:
        json.dump([_serialize_task(task) for task in tasks], f, indent=2)
