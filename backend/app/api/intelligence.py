from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.intelligence_v2 import frontiers, islands, overview, target_rows, threat_rows
from app.services.profile_context import get_profile_context
from app.services.analytics_cache import cache_key, get_cached, set_cached

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get("/overview")
def intelligence_overview(db: Session = Depends(get_db)):
    ctx=get_profile_context(db); key=cache_key(ctx.world.code,ctx.player.id,"overview"); cached=get_cached(key)
    if cached: return {**cached,"cache":"hit"}
    result=overview(db,ctx); set_cached(key,result); return {**result,"cache":"miss"}

@router.get("/threats")
def intelligence_threats(radius: float = Query(80, ge=1, le=200), min_score: int = Query(0, ge=0, le=100), limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    ctx=get_profile_context(db); key=cache_key(ctx.world.code,ctx.player.id,"threats",f":{radius}:{min_score}:{limit}"); cached=get_cached(key)
    if cached: return {"items":cached,"cache":"hit"}
    result=threat_rows(db,ctx,radius,min_score)[:limit]; set_cached(key,result); return {"items":result,"cache":"miss"}

@router.get("/targets")
def intelligence_targets(radius: float = Query(80, ge=1, le=200), min_score: int = Query(0, ge=0, le=100), ghost_only: bool = False, unallied_only: bool = False, limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    ctx=get_profile_context(db); key=cache_key(ctx.world.code,ctx.player.id,"targets",f":{radius}:{min_score}:{ghost_only}:{unallied_only}:{limit}"); cached=get_cached(key)
    if cached: return {"items":cached,"cache":"hit"}
    result=target_rows(db,ctx,radius,min_score,ghost_only,unallied_only)[:limit]; set_cached(key,result); return {"items":result,"cache":"miss"}

@router.get("/islands")
def intelligence_islands(db: Session = Depends(get_db)):
    ctx=get_profile_context(db); key=cache_key(ctx.world.code,ctx.player.id,"islands"); cached=get_cached(key)
    if cached: return {"items":cached,"cache":"hit"}
    result=islands(db,ctx); set_cached(key,result); return {"items":result,"cache":"miss"}

@router.get("/frontiers")
def intelligence_frontiers(db: Session = Depends(get_db)):
    ctx=get_profile_context(db); key=cache_key(ctx.world.code,ctx.player.id,"frontiers"); cached=get_cached(key)
    if cached: return {"items":cached,"cache":"hit"}
    result=frontiers(db,ctx); set_cached(key,result); return {"items":result,"cache":"miss"}
