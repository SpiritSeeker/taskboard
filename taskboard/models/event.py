from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    id: int
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = None

    source: str = "manual"  # "manual", "google", "outlook", etc.
    external_id: Optional[str] = None  # ID from external calendar if applicable
