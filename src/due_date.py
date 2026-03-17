from dataclasses import dataclass
from datetime import datetime

@dataclass
class DueDate:
    title: str
    due_date: datetime
    course: str
    event_type: str
    description: str
    source: str