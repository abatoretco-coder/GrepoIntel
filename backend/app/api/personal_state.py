from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import PersonalEmpireSnapshot, PersonalCityState, PersonalStatePairing
from app.schemas.personal_state import PersonalStateImport
from app.services.pairing import create_pairing, valid_pairing
from app.services.personal_state import import_snapshot
from app.services.profile_context import get_profile_context

router=APIRouter(prefix="/personal-state",tags=["personal-state"])
@router.post("/pairing")
def create_local_pairing(db:Session=Depends(get_db)):
    ctx=get_profile_context(db); return {"token":create_pairing(db,ctx),"world":ctx.world.code,"player":ctx.player.name,"warning":"Store this GrepoIntel token only in the local companion; it is not a Grepolis credential."}
@router.get("/status")
def personal_state_status(db:Session=Depends(get_db)):
    ctx=get_profile_context(db); latest=db.scalar(select(PersonalEmpireSnapshot).where(PersonalEmpireSnapshot.profile_id==ctx.profile.id).order_by(PersonalEmpireSnapshot.captured_at.desc()))
    paired=db.scalar(select(PersonalStatePairing.id).where(PersonalStatePairing.profile_id==ctx.profile.id).limit(1)) is not None
    cities=len(list(db.scalars(select(PersonalCityState).where(PersonalCityState.snapshot_id==latest.id)))) if latest else 0
    diagnostics=(latest.global_state or {}).get("diagnostics",{}) if latest else {}
    return {"connected":latest is not None,"paired":paired,"player":ctx.player.name,"world":ctx.world.code,"last_snapshot_at":latest.captured_at if latest else None,"cities":cities,"diagnostics":diagnostics}
@router.post("/import")
def companion_import(payload:PersonalStateImport,x_grepointel_pairing: str | None=Header(default=None),db:Session=Depends(get_db)):
    ctx=get_profile_context(db)
    if not valid_pairing(db,ctx,x_grepointel_pairing): raise HTTPException(401,"Valid local pairing token required")
    try: return import_snapshot(db,ctx,payload,source_type="COMPANION")
    except ValueError as error: raise HTTPException(422,str(error)) from error
