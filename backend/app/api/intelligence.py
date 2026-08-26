from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.intelligence_v2 import frontiers, islands, overview, target_rows, threat_rows
from app.services.profile_context import get_profile_context

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get("/overview")
def intelligence_overview(db: Session = Depends(get_db)):
    return overview(db, get_profile_context(db))

@router.get("/threats")
def intelligence_threats(radius: float = Query(80, ge=1, le=200), min_score: int = Query(0, ge=0, le=100), limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    return threat_rows(db, get_profile_context(db), radius, min_score)[:limit]

@router.get("/targets")
def intelligence_targets(radius: float = Query(80, ge=1, le=200), min_score: int = Query(0, ge=0, le=100), ghost_only: bool = False, unallied_only: bool = False, limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    return target_rows(db, get_profile_context(db), radius, min_score, ghost_only, unallied_only)[:limit]

@router.get("/islands")
def intelligence_islands(db: Session = Depends(get_db)):
    return islands(db, get_profile_context(db))

@router.get("/frontiers")
def intelligence_frontiers(db: Session = Depends(get_db)):
    return frontiers(db, get_profile_context(db))
