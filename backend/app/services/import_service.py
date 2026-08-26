from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.collectors.providers.grepolis_public import GrepolisPublicProvider
from app.models.all_models import Alliance, AllianceChangeEvent, AllianceSnapshot, City, CitySnapshot, ConquestEvent, Player, PlayerSnapshot, World

def integer(value: str | None) -> int:
    try: return int(value or 0)
    except ValueError: return 0

async def import_public_world(db: Session, world: World) -> dict[str, int]:
    data = await GrepolisPublicProvider(world.code).fetch()
    now = datetime.now(UTC)
    alliances = {a.external_id: a for a in db.scalars(select(Alliance).where(Alliance.world_id == world.id))}
    for row in data.alliances:
        alliance = alliances.get(row["external_id"])
        if not alliance:
            alliance = Alliance(world_id=world.id, external_id=row["external_id"], name=row["name"]); db.add(alliance); alliances[alliance.external_id] = alliance
        alliance.name, alliance.points, alliance.rank = row["name"], integer(row["points"]), integer(row["rank"])
        alliance.members_count, alliance.cities_count = integer(row["members_count"]), integer(row["cities_count"])
    db.flush()
    players = {p.external_id: p for p in db.scalars(select(Player).where(Player.world_id == world.id))}
    attack = {r["player_external_id"]: integer(r["points"]) for r in data.player_kills_attack}; defense = {r["player_external_id"]: integer(r["points"]) for r in data.player_kills_defense}
    for row in data.players:
        player = players.get(row["external_id"])
        if not player:
            player = Player(world_id=world.id, external_id=row["external_id"], name=row["name"]); db.add(player); players[player.external_id] = player
        previous_alliance = player.alliance_id
        player.name, player.alliance_id = row["name"], (alliances.get(row["alliance_external_id"]).id if row["alliance_external_id"] in alliances else None)
        player.points, player.rank, player.cities_count = integer(row["points"]), integer(row["rank"]), integer(row["cities_count"])
        player.attack_points, player.defense_points = attack.get(player.external_id, 0), defense.get(player.external_id, 0)
        player.battle_points = player.attack_points + player.defense_points
        if previous_alliance != player.alliance_id and player.id:
            db.add(AllianceChangeEvent(player_id=player.id, timestamp=now, old_alliance_id=previous_alliance, new_alliance_id=player.alliance_id))
    db.flush()
    cities = {c.external_id: c for c in db.scalars(select(City).where(City.world_id == world.id))}
    for row in data.towns:
        city = cities.get(row["external_id"])
        if not city:
            city = City(world_id=world.id, external_id=row["external_id"], name=row["name"], x=0, y=0, island_x=0, island_y=0); db.add(city)
        previous_player = city.player_id
        new_player = players.get(row["player_external_id"]).id if row["player_external_id"] in players else None
        city.name, city.player_id, city.island_x, city.island_y = row["name"], new_player, integer(row["island_x"]), integer(row["island_y"])
        city.x, city.y, city.points, city.is_ghost = city.island_x, city.island_y, integer(row["points"]), not bool(city.player_id)
        if previous_player != new_player and city.id:
            old_player = db.get(Player, previous_player) if previous_player else None
            new_player_row = db.get(Player, new_player) if new_player else None
            db.add(ConquestEvent(world_id=world.id, city_id=city.id, timestamp=now, old_player_id=previous_player, new_player_id=new_player, old_alliance_id=old_player.alliance_id if old_player else None, new_alliance_id=new_player_row.alliance_id if new_player_row else None))
    db.flush()
    for player in players.values(): db.add(PlayerSnapshot(player_id=player.id, timestamp=now, points=player.points, rank=player.rank, cities_count=player.cities_count, attack_points=player.attack_points, defense_points=player.defense_points, battle_points=player.battle_points, alliance_id=player.alliance_id))
    for alliance in alliances.values(): db.add(AllianceSnapshot(alliance_id=alliance.id, timestamp=now, points=alliance.points, rank=alliance.rank, members_count=alliance.members_count, cities_count=alliance.cities_count))
    for city in db.scalars(select(City).where(City.world_id == world.id)):
        db.add(CitySnapshot(city_id=city.id, timestamp=now, player_id=city.player_id, points=city.points, is_ghost=city.is_ghost))
    db.commit()
    return {"players": len(data.players), "alliances": len(data.alliances), "cities": len(data.towns)}
