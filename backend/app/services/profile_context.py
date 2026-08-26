from dataclasses import dataclass
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.all_models import City, Player, UserProfile, World

@dataclass(frozen=True)
class ProfileContext:
    profile: UserProfile
    world: World
    player: Player
    cities: list[City]

def get_profile_context(db: Session) -> ProfileContext:
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile:
        raise HTTPException(404, "Configure your pseudonym first")
    world, player = db.get(World, profile.world_id), db.get(Player, profile.player_id)
    if not world or not player:
        raise HTTPException(409, "Configured profile is inconsistent")
    return ProfileContext(profile=profile, world=world, player=player, cities=list(db.scalars(select(City).where(City.player_id == player.id))))
