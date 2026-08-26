"""Public-world import: normalize by external IDs, snapshot atomically, derive events."""
from contextlib import contextmanager
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.collectors.providers.grepolis_public import GrepolisPublicProvider
from app.core.config import settings
from app.services.analytics_cache import invalidate_profile
from app.models.all_models import Alliance, AllianceChangeEvent, AllianceSnapshot, City, CitySnapshot, ConquestEvent, Player, PlayerSnapshot, UserProfile, World


def integer(value: str | None) -> int:
    try:
        return int(value or 0)
    except ValueError:
        return 0


class ImportAlreadyRunning(RuntimeError):
    pass


@contextmanager
def import_lock(world_code: str):
    client = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
    key, token = f"collector:{world_code.lower()}:lock", uuid4().hex
    try:
        if not client.set(key, token, nx=True, ex=900):
            raise ImportAlreadyRunning(f"An import is already running for {world_code}")
        yield
    finally:
        try:
            if client.get(key) == token:
                client.delete(key)
        finally:
            client.close()


async def import_public_world(db: Session, world: World) -> dict[str, int | float | str]:
    """Fetch a public export and commit one consistent state and its snapshots."""
    started = perf_counter()
    with import_lock(world.code):
        data = await GrepolisPublicProvider(world.code).fetch()
        now = datetime.now(UTC)
        try:
            alliances = {row.external_id: row for row in db.scalars(select(Alliance).where(Alliance.world_id == world.id))}
            for row in data.alliances:
                alliance = alliances.get(row["external_id"])
                if alliance is None:
                    alliance = Alliance(world_id=world.id, external_id=row["external_id"], name=row["name"])
                    db.add(alliance)
                    alliances[alliance.external_id] = alliance
                alliance.name, alliance.points, alliance.rank = row["name"], integer(row["points"]), integer(row["rank"])
                alliance.members_count, alliance.cities_count = integer(row["members_count"]), integer(row["cities_count"])
            db.flush()

            players = {row.external_id: row for row in db.scalars(select(Player).where(Player.world_id == world.id))}
            attack = {row["player_external_id"]: integer(row["points"]) for row in data.player_kills_attack}
            defense = {row["player_external_id"]: integer(row["points"]) for row in data.player_kills_defense}
            for row in data.players:
                player = players.get(row["external_id"])
                if player is None:
                    player = Player(world_id=world.id, external_id=row["external_id"], name=row["name"])
                    db.add(player)
                    players[player.external_id] = player
                old_alliance_id = player.alliance_id
                player.name = row["name"]
                player.alliance_id = alliances.get(row["alliance_external_id"]).id if row["alliance_external_id"] in alliances else None
                player.points, player.rank, player.cities_count = integer(row["points"]), integer(row["rank"]), integer(row["cities_count"])
                player.attack_points, player.defense_points = attack.get(player.external_id, 0), defense.get(player.external_id, 0)
                player.battle_points = player.attack_points + player.defense_points
                if player.id and old_alliance_id != player.alliance_id:
                    db.add(AllianceChangeEvent(player_id=player.id, timestamp=now, old_alliance_id=old_alliance_id, new_alliance_id=player.alliance_id))
            db.flush()

            cities = {row.external_id: row for row in db.scalars(select(City).where(City.world_id == world.id))}
            player_alliances = {player.id: player.alliance_id for player in players.values() if player.id}
            for row in data.towns:
                city = cities.get(row["external_id"])
                if city is None:
                    city = City(world_id=world.id, external_id=row["external_id"], name=row["name"], x=0, y=0, island_x=0, island_y=0)
                    db.add(city)
                    cities[city.external_id] = city
                old_player_id = city.player_id
                new_player_id = players.get(row["player_external_id"]).id if row["player_external_id"] in players else None
                city.name, city.player_id = row["name"], new_player_id
                city.island_x, city.island_y = integer(row["island_x"]), integer(row["island_y"])
                city.x, city.y, city.points = city.island_x, city.island_y, integer(row["points"])
                city.is_ghost = new_player_id is None
                if city.id and old_player_id != new_player_id:
                    db.add(ConquestEvent(world_id=world.id, city_id=city.id, timestamp=now, old_player_id=old_player_id, new_player_id=new_player_id, old_alliance_id=player_alliances.get(old_player_id), new_alliance_id=player_alliances.get(new_player_id)))
            db.flush()

            db.add_all([PlayerSnapshot(player_id=p.id, timestamp=now, points=p.points, rank=p.rank, cities_count=p.cities_count, attack_points=p.attack_points, defense_points=p.defense_points, battle_points=p.battle_points, alliance_id=p.alliance_id) for p in players.values()])
            db.add_all([AllianceSnapshot(alliance_id=a.id, timestamp=now, points=a.points, rank=a.rank, members_count=a.members_count, cities_count=a.cities_count) for a in alliances.values()])
            current_cities = list(db.scalars(select(City).where(City.world_id == world.id)))
            db.add_all([CitySnapshot(city_id=c.id, timestamp=now, player_id=c.player_id, points=c.points, is_ghost=c.is_ghost) for c in current_cities])
            db.commit()
            for profile in db.scalars(select(UserProfile).where(UserProfile.world_id == world.id)):
                invalidate_profile(world.code, profile.player_id)
            return {"players": len(data.players), "alliances": len(data.alliances), "cities": len(data.towns), "players_without_alliance": db.scalar(select(func.count()).select_from(Player).where(Player.world_id == world.id, Player.alliance_id.is_(None))) or 0, "ghost_cities": db.scalar(select(func.count()).select_from(City).where(City.world_id == world.id, City.is_ghost.is_(True))) or 0, "collected_at": now.isoformat(), "duration_seconds": round(perf_counter() - started, 2)}
        except Exception:
            db.rollback()
            raise
