from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.personal_state import PersonalStateImport
from app.services.personal_state import empire_state, import_snapshot, preview
from app.services.profile_context import get_profile_context

router=APIRouter(prefix="/micro",tags=["micro"])
@router.get("/empire")
def get_empire(db:Session=Depends(get_db)): return empire_state(db,get_profile_context(db))
@router.post("/import/preview")
def import_preview(payload:PersonalStateImport,db:Session=Depends(get_db)): return preview(db,get_profile_context(db),payload)
@router.post("/import")
def import_personal_state(payload:PersonalStateImport,db:Session=Depends(get_db)):
    try:return import_snapshot(db,get_profile_context(db),payload)
    except ValueError as error:raise HTTPException(422,str(error)) from error
@router.get("/recommendations")
def micro_recommendations(db:Session=Depends(get_db)):
    state=empire_state(db,get_profile_context(db))
    if not state["available"]:return {"available":False,"reason":"personal_state_required","items":[]}
    items=[]
    for city in state["cities"]:
        pop=city["population"]; free=pop.get("free") if pop else None; resources=city["resources"]
        if free is not None and free<50:items.append({"city_id":city["city_id"],"priority":"high","title":"Augmenter la capacité de population","message":"Population libre faible : la ferme doit précéder le recrutement.","evidence":["population_free < 50"]})
        if resources and resources.get("wood") is not None and resources.get("storage_capacity") and resources["wood"]>resources["storage_capacity"]*.9:items.append({"city_id":city["city_id"],"priority":"medium","title":"Éviter le plafond de bois","message":"Le stock de bois approche la capacité de stockage.","evidence":["wood/storage_capacity > 90%"]})
    return {"available":True,"items":items[:20]}
