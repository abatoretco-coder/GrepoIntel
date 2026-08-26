from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from sqlalchemy import select
from app.models.all_models import City, PersonalCityState, PersonalEmpireSnapshot, SpyReport
from app.schemas.manual_intelligence import AttackSimulationRequest, SpyReportCreate, CombatAdviceRequest
from app.services.combat_advisor import advice
from app.services.manual_intelligence import save_spy_report, simulate_attack
from app.services.profile_context import get_profile_context

router = APIRouter(prefix="/manual-intelligence", tags=["manual intelligence"])

@router.get("/reports")
def reports(db: Session = Depends(get_db)):
    ctx = get_profile_context(db)
    city_names = {city.id: city.name for city in db.scalars(select(City).where(City.world_id == ctx.world.id))}
    return [{"id":r.id,"title":r.title,"city_id":r.city_id,"city_name":city_names.get(r.city_id),"observed_at":r.observed_at,"units":r.units,"provenance":"MANUAL_SPY_REPORT"} for r in db.query(SpyReport).filter(SpyReport.world_id == ctx.world.id).order_by(SpyReport.observed_at.desc()).all()]

@router.get("/simulator/context")
def simulator_context(db: Session = Depends(get_db)):
    """Only human-facing labels and the last passively captured home armies."""
    ctx = get_profile_context(db)
    snapshot = db.scalar(select(PersonalEmpireSnapshot).where(PersonalEmpireSnapshot.profile_id == ctx.profile.id).order_by(PersonalEmpireSnapshot.captured_at.desc()))
    states = {state.city_id: state for state in db.scalars(select(PersonalCityState).where(PersonalCityState.snapshot_id == snapshot.id))} if snapshot else {}
    return {"snapshot_at": snapshot.captured_at if snapshot else None, "origins": [{"city_id": city.id, "name": city.name, "coordinates": f"{city.x}|{city.y}", "units": (states[city.id].units or {}).get("home", {}) if city.id in states else {}, "available": city.id in states} for city in ctx.cities]}

@router.post("/reports")
def create_report(payload: SpyReportCreate, db: Session = Depends(get_db)):
    ctx = get_profile_context(db)
    if payload.city_id:
        city = db.get(City, payload.city_id)
        if not city or city.world_id != ctx.world.id: raise HTTPException(404,"City not found in current world")
    report=save_spy_report(db,ctx.world.id,payload.title,payload.raw_text,payload.city_id,payload.observed_at)
    return {"id":report.id,"title":report.title,"units":report.units,"observed_at":report.observed_at}

@router.post("/simulator/attack")
def attack_simulator(payload: AttackSimulationRequest, db: Session = Depends(get_db)):
    ctx=get_profile_context(db); report=db.get(SpyReport,payload.report_id)
    if not report or report.world_id != ctx.world.id: raise HTTPException(404,"Report not found")
    return simulate_attack(report,payload.attacker_units,payload.wall_level)

@router.post("/combat/advice")
def combat_advice(payload:CombatAdviceRequest,db:Session=Depends(get_db)):
    try:return advice(db,get_profile_context(db),payload.target_city_id)
    except ValueError as error:raise HTTPException(404,str(error)) from error
