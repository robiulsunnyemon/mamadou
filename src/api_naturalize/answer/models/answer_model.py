from beanie import Document, before_event, Replace, Save
from datetime import datetime, timezone
from pydantic import Field
import uuid


class AnswerModel(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str = ""
    course_id: str = ""
    lesson_id: str = ""
    question_id: str = ""
    submit_answer: str = ""
    right_answer: str = ""
    score: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Auto-update "updated_at" on update
    @before_event([Save, Replace])
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "answers"
