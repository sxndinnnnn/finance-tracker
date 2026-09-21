import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.recurrence import Frequency


class RecurrenceRuleCreate(BaseModel):
    frequency: Frequency
    interval: int = 1
    by_weekday: str | None = None
    by_monthday: int | None = None
    rrule_string: str | None = None
    start_date: date
    end_date: date | None = None


class RecurrenceRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    frequency: Frequency
    interval: int
    by_weekday: str | None
    by_monthday: int | None
    rrule_string: str | None
    start_date: date
    end_date: date | None
