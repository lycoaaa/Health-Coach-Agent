from typing import List, Optional
from pydantic import BaseModel, Field

class ActionItem(BaseModel):
    goal: str
    target: str
    by_date: Optional[str] = None
    period_weeks: Optional[int] = None
    motivation: Optional[str] = None

class WeeklyReport(BaseModel):
    summary: str = Field(max_length=200)
    action_items: List[ActionItem]

    @classmethod
    def __get_validators__(cls):
        yield cls.check_len

    @staticmethod
    def check_len(v):
        if len(v["action_items"]) != 3:
            raise ValueError("need exactly 3 action_items")
        return v
