from datetime import datetime
from pydantic import BaseModel, Field, PositiveFloat


class TravelRequest(BaseModel):
    origin_city_id: int = Field(gt=0)
    target_city_id: int = Field(gt=0)
    unit_speed: PositiveFloat = 1
    desired_arrival: datetime | None = None
    order_type: str = Field(default="attack", max_length=32)


class RevoltRequest(BaseModel):
    activation_time: datetime
