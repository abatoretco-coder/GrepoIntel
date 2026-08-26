from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import City, SpyReport
from app.schemas.manual_intelligence import AttackSimulationRequest, SpyReportCreate
from app.services.manual_intelligence import save_spy_report, simulate_attack
from app.services.profile_context import get_profile_context

router = APIRouter(prefix="/manual-intelligence", tags=["manual intelligence"])

@router.get("/reports")
def reports(db: Session = Depends(get_db)):
    ctx = get_profile_context(db)
    return [{"id":r.id,"title":r.title,"city_id":r.city_id,"observed_at":r.observed_at,"units":r.units} for r in db.query(SpyReport).filter(SpyReport.world_id == ctx.world.id).order_by(SpyReport.observed_at.desc()).all()]

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
