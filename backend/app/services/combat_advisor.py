from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.distance import calculate_distance, estimated_travel_time
from app.models.all_models import City, PersonalCityState, PersonalEmpireSnapshot, SpyReport
from app.services.manual_intelligence import UNIT_POWER
from app.services.profile_context import ProfileContext

def advice(db:Session,ctx:ProfileContext,target_city_id:int)->dict:
    target=db.get(City,target_city_id)
    if not target or target.world_id!=ctx.world.id: raise ValueError("Target city not found in active world")
    report=db.scalar(select(SpyReport).where(SpyReport.world_id==ctx.world.id,SpyReport.city_id==target.id).order_by(SpyReport.observed_at.desc()))
    if not report:return {"recommendation":"SCOUT_FIRST","target":{"name":target.name,"city_id":target.id},"confidence":0,"reasons":["Aucun espionnage lié à cette cible."],"plans":[],"informational_only":True}
    age=(datetime.now(UTC)-(report.observed_at or datetime.now(UTC))).total_seconds()/3600; defense=sum(UNIT_POWER.get(k,10)*v for k,v in report.units.items())
    snapshot=db.scalar(select(PersonalEmpireSnapshot).where(PersonalEmpireSnapshot.profile_id==ctx.profile.id).order_by(PersonalEmpireSnapshot.captured_at.desc()))
    if not snapshot:return {"recommendation":"SCOUT_FIRST","target":{"name":target.name,"city_id":target.id},"confidence":0,"reasons":["Armées personnelles non synchronisées."],"plans":[],"informational_only":True}
    states={s.city_id:s for s in db.scalars(select(PersonalCityState).where(PersonalCityState.snapshot_id==snapshot.id))}; plans=[]
    for city in ctx.cities:
        state=states.get(city.id); units=(state.units or {}).get("home",{}) if state else {}; power=sum(UNIT_POWER.get(k,0)*v for k,v in units.items()); ratio=power/max(defense,1); distance=calculate_distance((city.x,city.y),(target.x,target.y)); plans.append({"origin":{"name":city.name,"city_id":city.id},"available_units":units,"distance":distance,"travel_seconds":estimated_travel_time(distance,1,ctx.world.game_speed),"power_ratio":round(ratio,2),"minimum_power":round(defense*1.05),"recommended_power":round(defense*1.25),"outlook":"favorable" if ratio>=1.25 else "incertain" if ratio>=.9 else "insuffisant"})
    plans.sort(key=lambda p:p["power_ratio"],reverse=True); best=plans[0] if plans else None; stale=age>6; recommendation="SCOUT_FIRST" if stale else "ATTACK" if best and best["power_ratio"]>=1.25 else "AVOID"
    return {"recommendation":recommendation,"target":{"name":target.name,"city_id":target.id,"known_defense":report.units,"last_spy_hours":round(age,1)},"confidence":max(15,round(85-min(age*8,60))),"assumptions":["Simulation indicative : moral, chance, mur et bonus inconnus peuvent modifier le résultat.","Aucun ordre Grepolis n’est envoyé."],"reasons":["Espionnage trop ancien : renouveler le renseignement." if stale else "Plan classé à partir des armées synchronisées et de la dernière défense observée."],"plans":plans[:3],"informational_only":True}
