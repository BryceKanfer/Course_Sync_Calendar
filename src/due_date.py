from datetime import datetime

class DueDate:
    title: str
    due_date: datetime
    course: str
    type: str
    description: str
    source: str

    def __init__(self, title: str, due_date: datetime, course: str, type: str, description: str, source: str):
        self.title = title
        self.due_date = due_date
        self.course = course
        self.type = type
        self.description = description
        self.source = source