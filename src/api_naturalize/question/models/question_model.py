from beanie import Document, before_event, Replace, Save
from datetime import datetime, timezone
from pydantic import Field
from typing import List
import uuid


class QuestionModel(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str = ""
    lesson_id: str = ""
    difficulty: str = ""
    image_url: str = ""
    course_id: str = ""
    options: List[str] = []
    correct_answer: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Auto-update "updated_at" on update
    @before_event([Save, Replace])
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "questions"


#  *** _ ***