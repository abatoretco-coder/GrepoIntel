from pydantic import BaseModel, Field

class ProfileUpdate(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    player_name: str = Field(min_length=1, max_length=100, description="Pseudo Grepolis exact")
