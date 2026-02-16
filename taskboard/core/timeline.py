from dataclasses import dataclass
from datetime import datetime

from taskboard.models.task import Task


@dataclass
class ScheduledBlock:
    task: Task
    title: str
    start_time: datetime
    end_time: datetime
