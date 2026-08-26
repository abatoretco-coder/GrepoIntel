from datetime import datetime
from pydantic import BaseModel, Field

class SpyReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    city_id: int | None = Field(default=None, gt=0)
    observed_at: datetime | None = None
    raw_text: str = Field(min_length=1, max_length=20_000)

class AttackSimulationRequest(BaseModel):
    report_id: int = Field(gt=0)
    attacker_units: dict[str, int] = Field(min_length=1)
    wall_level: int = Field(default=0, ge=0, le=25)

class CombatAdviceRequest(BaseModel):
    target_city_id: int = Field(gt=0)
