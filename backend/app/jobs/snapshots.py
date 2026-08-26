"""Periodic, read-only public-world snapshot collection."""
import logging
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.all_models import World
from app.services.import_service import import_public_world

logger = logging.getLogger("grepointel.jobs")


async def collect_all_worlds() -> None:
    """Collect each configured world once; failures are isolated per world."""
    with SessionLocal() as db:
        worlds = list(db.scalars(select(World)))
        for world in worlds:
            try:
                logger.info("collector.start", extra={"world": world.code})
                result = await import_public_world(db, world)
                logger.info("collector.success", extra={"world": world.code, "counts": result})
            except Exception:
                db.rollback()
                logger.exception("collector.failure", extra={"world": world.code})
