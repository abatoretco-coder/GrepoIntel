from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class PersonalCityInput(BaseModel):
    external_city_id: str | None = None
    x: int | None = Field(default=None,ge=0,le=1000)
    y: int | None = Field(default=None,ge=0,le=1000)
    resources: dict[str,int|None] = {}
    population: dict[str,int|None] = {}
    buildings: dict[str,int|None] = {}
    researches: dict[str,bool|None] = {}
    units: dict[str,dict[str,int|None]] = {}
    queues: dict[str,list[dict]] = {}
    god: str | None = None
    hero: dict = {}

    @model_validator(mode="after")
    def require_stable_identity(self):
        if not self.external_city_id and (self.x is None or self.y is None):
            raise ValueError("A city requires external_city_id or both x and y coordinates")
        return self

class PersonalStateImport(BaseModel):
    schema_name: str = Field(alias="schema", pattern="^grepointel-personal-state$")
    version: int = Field(ge=1,le=1)
    world: str = Field(min_length=2,max_length=32)
    player: str = Field(min_length=1,max_length=100)
    captured_at: datetime
    cities: list[PersonalCityInput] = Field(min_length=1,max_length=500)
    model_config={"populate_by_name":True}
