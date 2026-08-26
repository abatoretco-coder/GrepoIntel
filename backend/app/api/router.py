from datetime import timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import Alliance, AllianceChangeEvent, City, CitySnapshot, ConquestEvent, Player, PlayerSnapshot, UserProfile, World
from app.schemas.common import Page
from app.schemas.profile import ProfileUpdate
from app.schemas.planner import RevoltRequest, TravelRequest
from app.services.import_service import ImportAlreadyRunning, import_public_world
from app.core.config import settings
from app.services.intelligence_service import dashboard_data, latest_snapshot_delta, player_report
from app.analytics.cluster import cluster_analysis
from app.analytics.distance import calculate_distance, estimated_travel_time
from app.analytics.scoring import target_score, threat_score
from app.analytics.world_rules.fr183 import calculate_revolt_window
from app.api.intelligence import router as intelligence_router
from app.api.manual_intelligence import router as manual_intelligence_router
from app.api.map import router as map_router

router = APIRouter(prefix="/api")
router.include_router(intelligence_router)
router.include_router(manual_intelligence_router)
router.include_router(map_router)

def world_or_404(db: Session, world_id: int) -> World:
    world = db.get(World, world_id)
    if not world: raise HTTPException(404, "World not found")
    return world

@router.get("/worlds")
def worlds(db: Session = Depends(get_db)):
    return [{"id": w.id, "code": w.code, "name": w.name, "language": w.language, "game_speed": w.game_speed, "unit_speed": w.unit_speed, "conquest_type": w.conquest_type} for w in db.scalars(select(World).order_by(World.name))]

@router.get("/worlds/{world_id}")
def world(world_id: int, db: Session = Depends(get_db)):
    w = world_or_404(db, world_id)
    return {key: getattr(w, key) for key in ("id", "code", "name", "language", "game_speed", "unit_speed", "trade_speed", "conquest_type", "revolt_preparation_hours", "revolt_active_hours", "night_bonus_start", "night_bonus_end", "morale_enabled", "luck_enabled", "alliance_limit", "endgame_type", "endgame_speed", "resource_bonus")}

@router.post("/worlds/{world_id}/import")
async def import_world(world_id: int, db: Session = Depends(get_db)):
    try:
        return await import_public_world(db, world_or_404(db, world_id))
    except ImportAlreadyRunning as error:
        raise HTTPException(409, str(error)) from error

@router.get("/players")
def players(world_id: int, page: Page = Depends(), db: Session = Depends(get_db)):
    query = select(Player).where(Player.world_id == world_id).order_by(Player.rank).offset(page.offset).limit(page.limit)
    total = db.scalar(select(func.count()).select_from(Player).where(Player.world_id == world_id))
    return {"total": total, "items": [{"id": p.id, "name": p.name, "points": p.points, "rank": p.rank, "cities_count": p.cities_count, "alliance_id": p.alliance_id, "attack_points": p.attack_points, "defense_points": p.defense_points} for p in db.scalars(query)]}

@router.get("/players/{player_id}")
def player(player_id: int, db: Session = Depends(get_db)):
    p = db.get(Player, player_id)
    if not p: raise HTTPException(404, "Player not found")
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    report = player_report(db, p, profile)
    report["cities"] = [{"id": c.id, "name": c.name, "x": c.x, "y": c.y, "points": c.points} for c in db.scalars(select(City).where(City.player_id == p.id))]
    report["history"] = [{"timestamp": row.timestamp, "points": row.points, "rank": row.rank, "cities_count": row.cities_count, "battle_points": row.battle_points} for row in db.scalars(select(PlayerSnapshot).where(PlayerSnapshot.player_id == p.id).order_by(PlayerSnapshot.timestamp.asc()).limit(60))]
    return report

@router.get("/cities")
def cities(world_id: int, page: Page = Depends(), db: Session = Depends(get_db)):
    query = select(City).where(City.world_id == world_id).order_by(City.id).offset(page.offset).limit(page.limit)
    total = db.scalar(select(func.count()).select_from(City).where(City.world_id == world_id))
    return {"total": total, "items": [{"id": c.id, "name": c.name, "player_id": c.player_id, "x": c.x, "y": c.y, "points": c.points, "is_ghost": c.is_ghost} for c in db.scalars(query)]}

@router.get("/cities/{city_id}")
def city(city_id: int, db: Session = Depends(get_db)):
    c = db.get(City, city_id)
    if not c: raise HTTPException(404, "City not found")
    owner = db.get(Player, c.player_id) if c.player_id else None
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    mine = list(db.scalars(select(City).where(City.player_id == profile.player_id))) if profile else []
    nearest_distance = min((calculate_distance((c.x, c.y), (own.x, own.y)) for own in mine), default=None)
    nearby = list(db.scalars(select(City).where(City.world_id == c.world_id, City.id != c.id).limit(100)))
    nearby.sort(key=lambda row: calculate_distance((c.x, c.y), (row.x, row.y)))
    return {"id": c.id, "world_id": c.world_id, "name": c.name, "player_id": c.player_id, "owner": {"id": owner.id, "name": owner.name, "alliance_id": owner.alliance_id} if owner else None, "x": c.x, "y": c.y, "points": c.points, "island_x": c.island_x, "island_y": c.island_y, "is_ghost": c.is_ghost, "distance_to_me": nearest_distance, "nearby_cities": [{"id": row.id, "name": row.name, "x": row.x, "y": row.y, "points": row.points, "distance": calculate_distance((c.x, c.y), (row.x, row.y))} for row in nearby[:8]], "history": [{"timestamp": row.timestamp, "player_id": row.player_id, "points": row.points, "is_ghost": row.is_ghost} for row in db.scalars(select(CitySnapshot).where(CitySnapshot.city_id == c.id).order_by(CitySnapshot.timestamp.desc()).limit(60))]}

@router.get("/alliances")
def alliances(world_id: int, page: Page = Depends(), db: Session = Depends(get_db)):
    query = select(Alliance).where(Alliance.world_id == world_id).order_by(Alliance.rank).offset(page.offset).limit(page.limit)
    total = db.scalar(select(func.count()).select_from(Alliance).where(Alliance.world_id == world_id))
    return {"total": total, "items": [{"id": a.id, "name": a.name, "points": a.points, "rank": a.rank, "members_count": a.members_count, "cities_count": a.cities_count} for a in db.scalars(query)]}

@router.get("/alliances/{alliance_id}")
def alliance(alliance_id: int, db: Session = Depends(get_db)):
    a = db.get(Alliance, alliance_id)
    if not a: raise HTTPException(404, "Alliance not found")
    members = list(db.scalars(select(Player).where(Player.alliance_id == a.id).order_by(Player.points.desc()).limit(20)))
    return {"id": a.id, "world_id": a.world_id, "name": a.name, "points": a.points, "rank": a.rank, "members_count": a.members_count, "cities_count": a.cities_count, "top_players": [{"id": p.id, "name": p.name, "points": p.points, "cities_count": p.cities_count, "growth_7d": latest_snapshot_delta(db, p.id, timedelta(days=7))} for p in members]}

@router.get("/me")
def me(db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile: raise HTTPException(404, "Configure your pseudonym first")
    p = db.get(Player, profile.player_id)
    return {"id": profile.id, "nickname": profile.nickname, "world_id": profile.world_id, "player": {"id": p.id, "name": p.name, "points": p.points, "rank": p.rank, "cities_count": p.cities_count} if p else None}

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile: raise HTTPException(404, "Configure your pseudonym first")
    return dashboard_data(db, profile)

@router.put("/me")
def update_me(payload: ProfileUpdate, db: Session = Depends(get_db)):
    world = db.scalar(select(World).order_by(World.id))
    if not world: raise HTTPException(409, "Import or seed a world first")
    player = db.scalar(select(Player).where(Player.world_id == world.id, func.lower(Player.name) == payload.player_name.lower()))
    if not player: raise HTTPException(404, "Pseudonym not found in the imported world")
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile: profile = UserProfile(nickname=payload.nickname, world_id=world.id, player_id=player.id); db.add(profile)
    else: profile.nickname, profile.world_id, profile.player_id = payload.nickname, world.id, player.id
    db.commit(); return {"id": profile.id, "nickname": profile.nickname, "player_id": player.id, "player_name": player.name}

@router.get("/me/cities")
def my_cities(db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile: raise HTTPException(404, "Configure your pseudonym first")
    return [{"id": c.id, "name": c.name, "x": c.x, "y": c.y, "points": c.points} for c in db.scalars(select(City).where(City.player_id == profile.player_id))]

@router.get("/analytics/cluster")
def cluster(db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile: raise HTTPException(404, "Configure your pseudonym first")
    cities = list(db.scalars(select(City).where(City.player_id == profile.player_id)))
    return cluster_analysis([(city.x, city.y) for city in cities])

@router.get("/analytics/threats")
def threats(limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile: raise HTTPException(404, "Configure your pseudonym first")
    mine = list(db.scalars(select(City).where(City.player_id == profile.player_id)))
    if not mine: return []
    rows = []
    for player in db.scalars(select(Player).where(Player.world_id == profile.world_id, Player.id != profile.player_id).order_by(Player.points.desc()).limit(300)):
        city = db.scalar(select(City).where(City.player_id == player.id).limit(1))
        if not city: continue
        distance = min(calculate_distance((city.x, city.y), (own.x, own.y)) for own in mine)
        alliance = db.get(Alliance, player.alliance_id) if player.alliance_id else None
        score = threat_score(distance, player.points, player.cities_count, player.attack_points, alliance.points if alliance else 0)
        rows.append({"player_id": player.id, "name": player.name, "distance": distance, **score})
    return sorted(rows, key=lambda row: row["score"], reverse=True)[:min(limit, 100)]

@router.get("/analytics/targets")
def targets(limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db)):
    profile = db.scalar(select(UserProfile).order_by(UserProfile.id))
    if not profile: raise HTTPException(404, "Configure your pseudonym first")
    mine = list(db.scalars(select(City).where(City.player_id == profile.player_id)))
    rows = []
    for city in db.scalars(select(City).where(City.world_id == profile.world_id, City.player_id != profile.player_id).limit(1000)):
        distance = min(calculate_distance((city.x, city.y), (own.x, own.y)) for own in mine) if mine else 999
        owner = db.get(Player, city.player_id) if city.player_id else None
        score = target_score(distance, city.is_ghost, city.points, bool(owner and owner.alliance_id))
        rows.append({"city_id": city.id, "name": city.name, "distance": distance, "points": city.points, **score})
    return sorted(rows, key=lambda row: row["score"], reverse=True)[:min(limit, 100)]

@router.post("/planner/travel")
def travel(payload: TravelRequest, db: Session = Depends(get_db)):
    origin, target = db.get(City, payload.origin_city_id), db.get(City, payload.target_city_id)
    if not origin or not target: raise HTTPException(404, "City not found")
    if origin.world_id != target.world_id: raise HTTPException(422, "Cities must be in the same world")
    world = db.get(World, origin.world_id)
    distance = calculate_distance((origin.x, origin.y), (target.x, target.y))
    seconds = estimated_travel_time(distance, payload.unit_speed, world.game_speed)
    arrival = payload.desired_arrival
    if arrival and arrival.tzinfo is None:
        arrival = arrival.replace(tzinfo=ZoneInfo(settings.timezone))
    departure = arrival - timedelta(seconds=seconds) if arrival else None
    return {"origin_city_id": origin.id, "target_city_id": target.id, "order_type": payload.order_type, "distance": distance, "estimated_travel_seconds": seconds, "suggested_departure": departure, "desired_arrival": arrival, "timezone": settings.timezone, "informational_only": True}

@router.post("/planner/revolt")
def revolt(payload: RevoltRequest):
    activation = payload.activation_time
    if activation.tzinfo is None:
        activation = activation.replace(tzinfo=ZoneInfo(settings.timezone))
    return {**calculate_revolt_window(activation), "timezone": settings.timezone}

@router.get("/events")
def events(world_id: int = Query(default=1, gt=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    conquests = [{"type": "conquest", "timestamp": item.timestamp, "city_id": item.city_id, "old_player_id": item.old_player_id, "new_player_id": item.new_player_id} for item in db.scalars(select(ConquestEvent).where(ConquestEvent.world_id == world_id).order_by(ConquestEvent.timestamp.desc()).limit(limit))]
    changes = [{"type": "alliance_change", "timestamp": item.timestamp, "player_id": item.player_id, "old_alliance_id": item.old_alliance_id, "new_alliance_id": item.new_alliance_id} for item in db.scalars(select(AllianceChangeEvent).order_by(AllianceChangeEvent.timestamp.desc()).limit(limit))]
    return sorted([*conquests, *changes], key=lambda event: event["timestamp"], reverse=True)[:limit]
