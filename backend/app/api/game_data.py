from fastapi import APIRouter
from app.game_data.grepolis import catalogue
router=APIRouter(prefix="/game-data",tags=["game-data"])
@router.get("/units")
def units(): return {"items":catalogue(),"version":"standard-grepolis-v1"}
