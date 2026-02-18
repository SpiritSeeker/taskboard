from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScheduledBlock:
    id: int
    title: str
    start_time: datetime
    end_time: datetime
