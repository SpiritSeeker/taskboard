from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional, Tuple


@dataclass
class Task:
    id: int
    title: str
    duration_minutes: int
    priority: int  # 1 (highest) to 3 (lowest)
    earliest_start_time: Optional[time]
    latest_end_time: Optional[time]
    flexible: bool
    is_completed: bool = False
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    energy_level: int = 2  # 1 (low) to 3 (high)
    work_sessions: List[Tuple[datetime, datetime]] = field(default_factory=list)
    active_session_start: Optional[datetime] = None
