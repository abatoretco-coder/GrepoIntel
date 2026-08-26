from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import Alliance, City, Player
from app.services.profile_context import get_profile_context

router = APIRouter(prefix="/map", tags=["map"])

@router.get("/cities")
def map_cities(min_x:int|None=Query(None,ge=0,le=1000),max_x:int|None=Query(None,ge=0,le=1000),min_y:int|None=Query(None,ge=0,le=1000),max_y:int|None=Query(None,ge=0,le=1000),db:Session=Depends(get_db)):
    ctx=get_profile_context(db); query=select(City).where(City.world_id==ctx.world.id)
    if min_x is not None: query=query.where(City.x>=min_x)
    if max_x is not None: query=query.where(City.x<=max_x)
    if min_y is not None: query=query.where(City.y>=min_y)
    if max_y is not None: query=query.where(City.y<=max_y)
    players={p.id:p for p in db.scalars(select(Player).where(Player.world_id==ctx.world.id))}
    alliances={a.id:a.name for a in db.scalars(select(Alliance).where(Alliance.world_id==ctx.world.id))}
    features=[]
    for city in db.scalars(query):
        player=players.get(city.player_id); relation="SELF" if city.player_id==ctx.player.id else "ALLY" if player and player.alliance_id and player.alliance_id==ctx.player.alliance_id else "GHOST" if city.is_ghost else "UNKNOWN"
        features.append({"type":"Feature","geometry":{"type":"Point","coordinates":[city.x,city.y]},"properties":{"city_id":city.id,"name":city.name,"player_id":city.player_id,"player_name":player.name if player else None,"alliance_id":player.alliance_id if player else None,"alliance_name":alliances.get(player.alliance_id) if player and player.alliance_id else None,"points":city.points,"is_ghost":city.is_ghost,"relation":relation,"x":city.x,"y":city.y}})
    return {"type":"FeatureCollection","features":features}
