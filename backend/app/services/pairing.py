import hashlib, secrets
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.all_models import PersonalStatePairing
from app.services.profile_context import ProfileContext

def _digest(token:str)->str: return hashlib.sha256(token.encode()).hexdigest()
def create_pairing(db:Session,ctx:ProfileContext)->str:
    token=secrets.token_urlsafe(32); row=db.scalar(select(PersonalStatePairing).where(PersonalStatePairing.profile_id==ctx.profile.id))
    if row: row.token_hash=_digest(token)
    else: db.add(PersonalStatePairing(profile_id=ctx.profile.id,token_hash=_digest(token)))
    db.commit(); return token
def valid_pairing(db:Session,ctx:ProfileContext,token:str|None)->bool:
    if not token:return False
    row=db.scalar(select(PersonalStatePairing).where(PersonalStatePairing.profile_id==ctx.profile.id))
    return bool(row and secrets.compare_digest(row.token_hash,_digest(token)))
