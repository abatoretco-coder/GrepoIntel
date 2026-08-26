from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from redis import Redis
from app.api.router import router
from app.core.config import settings
from app.db.session import engine
from app.jobs.snapshots import collect_all_worlds

@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = AsyncIOScheduler(timezone="Europe/Paris")
    if settings.scheduler_enabled:
        scheduler.add_job(collect_all_worlds, "interval", hours=settings.snapshot_interval_hours, id="public-world-snapshot", replace_existing=True, max_instances=1, coalesce=True)
        scheduler.start()
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(title="GrepoIntel API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[value.strip() for value in settings.cors_origins.split(",")], allow_origin_regex=settings.companion_origin_regex, allow_credentials=False, allow_methods=["GET","POST","OPTIONS"], allow_headers=["Content-Type","X-GrepoIntel-Pairing"])

@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
    try:
        client.ping()
    finally:
        client.close()
    return {"status": "ok", "database": "ok", "redis": "ok", "service": "grepointel-api", "version": app.version}

app.include_router(router)
