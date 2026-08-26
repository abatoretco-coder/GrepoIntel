"""Idempotent local FR183 demonstration data. Run with: python -m app.seed"""
from datetime import UTC, datetime, timedelta
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.all_models import Alliance, AllianceSnapshot, City, CitySnapshot, ConquestEvent, Player, PlayerSnapshot, UserProfile, World

def seed() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        world = db.scalar(select(World).where(World.code == "FR183"))
        if world:
            print("Seed already present for FR183."); return
        world = World(code="FR183", name="Echidnara", language="fr", game_speed=2, unit_speed=2, trade_speed=2, conquest_type="revolt", revolt_preparation_hours=12, revolt_active_hours=12, night_bonus_start="00:00", night_bonus_end="08:00", morale_enabled=True, luck_enabled=True, alliance_limit=40, endgame_type="world_wonders", endgame_speed="slow", resource_bonus=15)
        db.add(world); db.flush()
        alliances = [Alliance(world_id=world.id, external_id=f"a{i}", name=name, points=pts, rank=i, members_count=members, cities_count=members*7) for i, (name, pts, members) in enumerate([("Aegis", 8400000, 38), ("Ligue Boréale", 6800000, 31), ("Hydre", 5300000, 26), ("Indépendants", 1200000, 12)], 1)]
        db.add_all(alliances); db.flush()
        me = Player(world_id=world.id, external_id="p-me", name="Strategos", alliance_id=alliances[0].id, points=182430, rank=183, cities_count=5, attack_points=28400, defense_points=15700, battle_points=44100)
        neighbors = [Player(world_id=world.id, external_id=f"p-{i}", name=f"Voisin {i:02d}", alliance_id=alliances[(i % 4)].id if i % 5 else None, points=30000+i*9700, rank=400-i*9, cities_count=1+i%5, attack_points=i*1200, defense_points=i*800, battle_points=i*2000) for i in range(1, 21)]
        db.add_all([me, *neighbors]); db.flush(); db.add(UserProfile(nickname="Commandant", world_id=world.id, player_id=me.id))
        cities = [City(world_id=world.id, external_id=f"my-{i}", name=f"Bastion {i}", player_id=me.id, x=438+i*3, y=512+(i%2)*4, is_ghost=False, points=12000+i*1100, island_x=43, island_y=51) for i in range(1, 6)]
        for i, player in enumerate(neighbors, 1): cities.append(City(world_id=world.id, external_id=f"city-{i}", name=f"Polis {i:02d}", player_id=player.id, x=430+(i*7)%35, y=500+(i*11)%31, is_ghost=i in (7, 16), points=3500+i*850, island_x=43+(i%4), island_y=50+(i%4)))
        db.add_all(cities); db.flush()
        for player in [me, *neighbors]:
            for hours, delta in ((168, -5200), (24, -950), (0, 0)):
                db.add(PlayerSnapshot(player_id=player.id, timestamp=now-timedelta(hours=hours), points=max(0, player.points+delta), rank=player.rank+max(0, hours//24), cities_count=max(1, player.cities_count-(1 if hours == 168 and player.id % 3 == 0 else 0)), attack_points=max(0, player.attack_points+delta//4), defense_points=max(0, player.defense_points+delta//6), battle_points=max(0, player.battle_points+delta//3), alliance_id=player.alliance_id))
        for city in cities: db.add(CitySnapshot(city_id=city.id, timestamp=now, player_id=city.player_id, points=city.points, is_ghost=city.is_ghost))
        for alliance in alliances: db.add(AllianceSnapshot(alliance_id=alliance.id, timestamp=now, points=alliance.points, rank=alliance.rank, members_count=alliance.members_count, cities_count=alliance.cities_count))
        db.add(ConquestEvent(world_id=world.id, city_id=cities[8].id, timestamp=now-timedelta(hours=32), old_player_id=neighbors[7].id, new_player_id=neighbors[6].id, old_alliance_id=neighbors[7].alliance_id, new_alliance_id=neighbors[6].alliance_id))
        db.commit(); print("Seeded Echidnara (FR183): 1 profile, 25 cities, 20 neighbours, 4 alliances.")

if __name__ == "__main__": seed()
