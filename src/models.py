## pydantic Program 모델

from pydantic import BaseModel, Field
from datetime import date
from typing import Literal, Optional

class Program(BaseModel):
    model_config = {"from_attributes": True}  # SQLAlchemy 객체 -> pydantic 자동 변환 허용

    source: Literal["bizinfo", "mss"]
    source_id: str
    title: str
    target: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: str
    jurisdiction_org: str
    executing_org: str
    category: str
    source_url: str

