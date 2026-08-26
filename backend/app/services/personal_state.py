import hashlib, json
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.all_models import City, PersonalCityState, PersonalEmpireSnapshot
from app.schemas.personal_state import PersonalStateImport
from app.services.profile_context import ProfileContext

def _hash(payload: PersonalStateImport) -> str:
    return hashlib.sha256(json.dumps(payload.model_dump(mode="json"),sort_keys=True,separators=(",",":")).encode()).hexdigest()

def match_cities(db:Session, ctx:ProfileContext, payload:PersonalStateImport):
    matched=[]; missing=[]
    for item in payload.cities:
        city=db.scalar(select(City).where(City.world_id==ctx.world.id, City.external_id==item.external_city_id, City.player_id==ctx.player.id)) if item.external_city_id else db.scalar(select(City).where(City.world_id==ctx.world.id,City.x==item.x,City.y==item.y,City.player_id==ctx.player.id))
        (matched if city else missing).append(city.id if city else item.external_city_id or f"{item.x}/{item.y}")
    return matched,missing

def preview(db:Session,ctx:ProfileContext,payload:PersonalStateImport)->dict:
    matched,missing=match_cities(db,ctx,payload)
    return {"cities_detected":len(payload.cities),"cities_matched":len(matched),"missing":missing,"building_values":sum(len(c.buildings) for c in payload.cities),"research_values":sum(len(c.researches) for c in payload.cities),"unit_types":sum(sum(len(group) for group in c.units.values()) for c in payload.cities),"requires_confirmation":True}

def import_snapshot(db:Session,ctx:ProfileContext,payload:PersonalStateImport)->dict:
    if payload.world.upper()!=ctx.world.code.upper() or payload.player.casefold()!=ctx.player.name.casefold(): raise ValueError("Snapshot world/player does not match active profile")
    state_hash=_hash(payload); existing=db.scalar(select(PersonalEmpireSnapshot).where(PersonalEmpireSnapshot.profile_id==ctx.profile.id,PersonalEmpireSnapshot.state_hash==state_hash))
    if existing:return {"created":False,"snapshot_id":existing.id,"reason":"duplicate_snapshot"}
    matched,missing=match_cities(db,ctx,payload)
    if missing: raise ValueError(f"Unmatched cities: {', '.join(map(str,missing))}")
    snapshot=PersonalEmpireSnapshot(profile_id=ctx.profile.id,world_id=ctx.world.id,captured_at=payload.captured_at,source_type="PERSONAL_EXPORT",source_version=payload.version,state_hash=state_hash); db.add(snapshot);db.flush()
    for item in payload.cities:
        city=db.scalar(select(City).where(City.world_id==ctx.world.id,City.external_id==item.external_city_id,City.player_id==ctx.player.id)) if item.external_city_id else db.scalar(select(City).where(City.world_id==ctx.world.id,City.x==item.x,City.y==item.y,City.player_id==ctx.player.id))
        db.add(PersonalCityState(snapshot_id=snapshot.id,city_id=city.id,resources=item.resources,population=item.population,buildings=item.buildings,researches=item.researches,units=item.units,queues=item.queues,god=item.god,hero=item.hero))
    db.commit(); return {"created":True,"snapshot_id":snapshot.id,"captured_at":payload.captured_at,"cities":len(matched)}

def empire_state(db:Session,ctx:ProfileContext)->dict:
    snapshot=db.scalar(select(PersonalEmpireSnapshot).where(PersonalEmpireSnapshot.profile_id==ctx.profile.id).order_by(PersonalEmpireSnapshot.captured_at.desc()))
    if not snapshot:return {"available":False,"reason":"personal_state_required","cities":[]}
    states={state.city_id:state for state in db.scalars(select(PersonalCityState).where(PersonalCityState.snapshot_id==snapshot.id))}; now=datetime.now(UTC); age=max(0, (now-snapshot.captured_at).total_seconds()/60)
    freshness="FRESH" if age<15 else "RECENT" if age<60 else "STALE" if age<360 else "VERY_STALE"
    cities=[]
    for city in ctx.cities:
        state=states.get(city.id)
        if not state:continue
        units=state.units.get("home",{}) if state.units else {}; role="NAVAL_DEFENSE" if units.get("bireme",0)>100 else "LAND_OFFENSE" if units.get("hoplite",0)+units.get("sword",0)>100 else "UNDEFINED"
        cities.append({"city_id":city.id,"name":city.name,"role":role,"resources":state.resources,"population":state.population,"buildings":state.buildings,"researches":state.researches,"units":state.units,"god":state.god,"hero":state.hero,"freshness":{"status":freshness,"age_minutes":round(age,1)},"provenance":{"resources":"PERSONAL_EXPORT","population":"PERSONAL_EXPORT","buildings":"PERSONAL_EXPORT","researches":"PERSONAL_EXPORT","units":"PERSONAL_EXPORT","god":"PERSONAL_EXPORT","hero":"PERSONAL_EXPORT"},"specialization_score":70 if role!="UNDEFINED" else 20})
    return {"available":True,"captured_at":snapshot.captured_at,"source":"PERSONAL_EXPORT","cities":cities}
