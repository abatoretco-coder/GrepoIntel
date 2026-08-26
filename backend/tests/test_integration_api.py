"""Integration checks run against the Compose PostgreSQL/Redis services."""
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import app
from app.db.session import SessionLocal
from app.models.all_models import City, Player, World
from app.seed import seed_database


client = TestClient(app)


def test_health_and_core_collections():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["database"] == "ok"
    assert health.json()["redis"] == "ok"
    worlds = client.get("/api/worlds")
    assert worlds.status_code == 200 and worlds.json()
    assert client.get("/api/worlds/999999").status_code == 404
    for endpoint in ("/api/me", "/api/me/cities", "/api/dashboard", "/api/analytics/cluster", "/api/analytics/threats", "/api/analytics/targets", "/api/events", "/api/intelligence/overview", "/api/intelligence/threats", "/api/intelligence/targets", "/api/intelligence/islands", "/api/intelligence/frontiers"):
        assert client.get(endpoint).status_code == 200


def test_pagination_details_and_planner_validation():
    players = client.get("/api/players?world_id=1&limit=2&offset=0")
    assert players.status_code == 200 and len(players.json()["items"]) == 2
    assert client.get("/api/players?world_id=1&limit=-1").status_code == 422
    player_id = players.json()["items"][0]["id"]
    cities = client.get("/api/cities?world_id=1&limit=2")
    assert cities.status_code == 200 and len(cities.json()["items"]) == 2
    city_id = cities.json()["items"][0]["id"]
    assert client.get(f"/api/players/{player_id}").status_code == 200
    assert client.get(f"/api/cities/{city_id}").status_code == 200
    assert client.get("/api/players/999999").status_code == 404
    assert client.get("/api/cities/999999").status_code == 404
    alliance = client.get("/api/alliances?world_id=1&limit=1").json()["items"][0]
    assert client.get(f"/api/alliances/{alliance['id']}").status_code == 200
    assert client.post("/api/planner/travel", json={"origin_city_id": city_id, "target_city_id": city_id, "unit_speed": 0}).status_code == 422
    assert client.post("/api/planner/revolt", json={"activation_time": "not-a-date"}).status_code == 422


def test_database_external_ids_and_seed_are_idempotent():
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(World)) >= 1
        assert db.scalar(select(func.count()).select_from(Player)) > 0
        assert db.scalar(select(func.count()).select_from(City)) > 0
        before = db.scalar(select(func.count()).select_from(Player))
        assert seed_database(db) is False
        after = db.scalar(select(func.count()).select_from(Player))
        assert before == after
