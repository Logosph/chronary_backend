from typing import Optional
from datetime import datetime
from pydantic import BaseModel, validator
from app.db.models import Tag, Subtag

class ActivityBase(BaseModel):
    name: str
    description: str
    tag_id: int
    subtag_id: Optional[int] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tag_id: Optional[int] = None
    subtag_id: Optional[int] = None

class ActivityInDB(ActivityBase):
    id: int
    user_id: int
    start: datetime
    end: Optional[datetime] = None

    class Config:
        from_attributes = True

class ActivityResponse(ActivityInDB):
    pass

class TimeRange(BaseModel):
    start: datetime
    end: datetime

    @validator('end')
    def end_must_be_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('end time must be after start time')
        return v

class TagStats(BaseModel):
    tag_id: int
    tag_name: str
    average_duration_minutes: float

class SubtagStats(BaseModel):
    subtag_id: int
    subtag_name: str
    tag_id: int
    average_duration_minutes: float

class TagTypeStats(BaseModel):
    tag_type_id: int
    tag_type_name: str
    average_duration_minutes: float

class DailyStats(BaseModel):
    by_tags: list[TagStats]
    by_subtags: list[SubtagStats]
    by_tag_types: list[TagTypeStats]

class WeeklyStats(BaseModel):
    by_tags: list[TagStats]
    by_subtags: list[SubtagStats]
    by_tag_types: list[TagTypeStats]

class ActivityStats(BaseModel):
    daily: DailyStats
    weekly: WeeklyStats 