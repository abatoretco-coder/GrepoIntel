import hashlib, json
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.all_models import City, PersonalCityState, PersonalEmpireSnapshot
from app.schemas.personal_state import PersonalStateImport
from app.services.profile_context import ProfileContext

def _home(state: PersonalCityState) -> dict: return (state.units or {}).get("home", {})
def _role(state: PersonalCityState) -> tuple[str,str,int]:
    units=_home(state); buildings=state.buildings or {}; naval=sum(units.get(x,0) for x in ("bireme","trireme","attack_ship","demolition_ship","colonize_ship")); land=sum(units.get(x,0) for x in ("sword","slinger","archer","hoplite","rider","chariot","catapult")); port=buildings.get("harbor",0)
    current="NAVAL_DEFENSE" if units.get("bireme",0)>=100 else "LAND_OFFENSE" if units.get("slinger",0)+units.get("hoplite",0)>=150 else "ECONOMY" if land+naval<100 else "MIXED"
    recommended="NAVAL_DEFENSE" if port>=20 and (naval<250 or units.get("bireme",0)>0) else "LAND_OFFENSE" if land>=naval else "ECONOMY"
    focused=max(naval,land)/max(naval+land,1); return current,recommended,round(35+focused*65)
def _actions(state: PersonalCityState, recommended:str) -> list[dict]:
    actions=[]; pop=state.population or {}; buildings=state.buildings or {}; resources=state.resources or {}; units=_home(state)
    if pop.get("free") is not None and pop["free"]<50: actions.append({"priority":"high","action":"Monter la ferme","reason":"Population libre sous 50."})
    if resources.get("wood") and resources.get("storage_capacity") and resources["wood"]>resources["storage_capacity"]*.9: actions.append({"priority":"medium","action":"Dépenser ou transférer le bois","reason":"Stockage bois supérieur à 90 %."})
    if recommended=="NAVAL_DEFENSE" and buildings.get("harbor",0)<25: actions.append({"priority":"medium","action":"Monter le port","reason":"Le rôle NAV-DEF nécessite une capacité navale."})
    if recommended=="NAVAL_DEFENSE" and units.get("bireme",0)<250: actions.append({"priority":"high","action":"Recruter des birèmes","reason":"Défense navale insuffisante pour le rôle proposé."})
    if recommended=="LAND_OFFENSE" and buildings.get("barracks",0)<25: actions.append({"priority":"medium","action":"Monter la caserne","reason":"La ville offensive doit soutenir son recrutement."})
    return actions[:5]
def hero_plan(cities:list[dict], heroes:list[dict]) -> list[dict]:
    result=[]
    for hero in heroes:
        name=str(hero.get("name") or hero.get("hero_name") or "Héros inconnu"); current=hero.get("assigned_city") or hero.get("town_id")
        target=next((city for city in cities if city["recommended_role"]=="NAVAL_DEFENSE"),cities[0] if cities else None)
        result.append({"hero":name,"level":hero.get("level") or hero.get("hero_level"),"current_city":current,"recommended_city":target["city_id"] if target else None,"reason":"Priorité aux villes NAV-DEF disponibles ; à confirmer selon le bonus réel du héros."})
    return result

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

def import_snapshot(db:Session,ctx:ProfileContext,payload:PersonalStateImport,source_type:str="PERSONAL_EXPORT")->dict:
    if payload.world.upper()!=ctx.world.code.upper() or payload.player.casefold()!=ctx.player.name.casefold(): raise ValueError("Snapshot world/player does not match active profile")
    state_hash=_hash(payload); existing=db.scalar(select(PersonalEmpireSnapshot).where(PersonalEmpireSnapshot.profile_id==ctx.profile.id,PersonalEmpireSnapshot.state_hash==state_hash))
    if existing:return {"created":False,"snapshot_id":existing.id,"reason":"duplicate_snapshot"}
    matched,missing=match_cities(db,ctx,payload)
    if missing: raise ValueError(f"Unmatched cities: {', '.join(map(str,missing))}")
    snapshot=PersonalEmpireSnapshot(profile_id=ctx.profile.id,world_id=ctx.world.id,captured_at=payload.captured_at,source_type=source_type,source_version=payload.version,state_hash=state_hash,global_state={"heroes":payload.heroes,"account":payload.account,"diagnostics":payload.diagnostics,"client_version":payload.client_version}); db.add(snapshot);db.flush()
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
        role,recommended,specialization=_role(state); units=_home(state); hero_name=str((state.hero or {}).get("name", "")); hero_score=80 if hero_name and ((recommended.startswith("NAVAL") and "nav" in hero_name.lower()) or (recommended.startswith("LAND") and any(x in hero_name.lower() for x in ("hop","sling","sword")))) else 45 if hero_name else None; god_score=70 if state.god else None
        cities.append({"city_id":city.id,"name":city.name,"role":role,"recommended_role":recommended,"resources":state.resources,"population":state.population,"buildings":state.buildings,"researches":state.researches,"units":state.units,"god":state.god,"hero":state.hero,"freshness":{"status":freshness,"age_minutes":round(age,1)},"provenance":{"resources":"PERSONAL_EXPORT","population":"PERSONAL_EXPORT","buildings":"PERSONAL_EXPORT","researches":"PERSONAL_EXPORT","units":"PERSONAL_EXPORT","god":"PERSONAL_EXPORT","hero":"PERSONAL_EXPORT"},"specialization_score":specialization,"army_specialization_score":specialization,"hero_synergy_score":hero_score,"god_synergy_score":god_score,"next_best_actions":_actions(state,recommended)})
    heroes=snapshot.global_state.get("heroes",[])
    return {"available":True,"captured_at":snapshot.captured_at,"source":snapshot.source_type,"heroes":heroes,"hero_assignment_plan":hero_plan(cities,heroes),"account":snapshot.global_state.get("account",{}),"diagnostics":snapshot.global_state.get("diagnostics",{}),"cities":cities}
