from __future__ import annotations

from datetime import UTC, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.distance import calculate_distance
from app.analytics.scoring import target_score, threat_score
from app.models.all_models import Alliance, City, CitySnapshot, Player, PlayerSnapshot, UserProfile


def latest_snapshot_delta(db: Session, player_id: int, since: timedelta) -> dict[str, int]:
    now = datetime.now(UTC)
    current = db.scalar(select(PlayerSnapshot).where(PlayerSnapshot.player_id == player_id).order_by(PlayerSnapshot.timestamp.desc()))
    older = db.scalar(select(PlayerSnapshot).where(PlayerSnapshot.player_id == player_id, PlayerSnapshot.timestamp <= now - since).order_by(PlayerSnapshot.timestamp.desc()))
    if not current or not older:
        return {"points": 0, "rank": 0, "cities": 0, "battle_points": 0}
    return {"points": current.points - older.points, "rank": older.rank - current.rank, "cities": current.cities_count - older.cities_count, "battle_points": current.battle_points - older.battle_points}


def activity_estimate(delta_7d: dict[str, int]) -> dict[str, object]:
    score = min(100, max(0, delta_7d["points"] // 500 + max(delta_7d["cities"], 0) * 20 + max(delta_7d["battle_points"], 0) // 250))
    label = "élevée" if score >= 65 else "modérée" if score >= 25 else "faible"
    return {"score": score, "label": label, "disclaimer": "Estimation fondée sur les évolutions publiques, pas sur une connexion au jeu."}


def player_report(db: Session, player: Player, profile: UserProfile | None = None) -> dict[str, object]:
    delta_24h, delta_7d = latest_snapshot_delta(db, player.id, timedelta(hours=24)), latest_snapshot_delta(db, player.id, timedelta(days=7))
    alliance = db.get(Alliance, player.alliance_id) if player.alliance_id else None
    report: dict[str, object] = {"id": player.id, "world_id": player.world_id, "name": player.name, "points": player.points, "rank": player.rank, "cities_count": player.cities_count, "attack_points": player.attack_points, "defense_points": player.defense_points, "battle_points": player.battle_points, "alliance": {"id": alliance.id, "name": alliance.name} if alliance else None, "growth_24h": delta_24h, "growth_7d": delta_7d, "activity": activity_estimate(delta_7d)}
    report["history"] = [{"timestamp": snapshot.timestamp.isoformat(), "points": snapshot.points, "rank": snapshot.rank} for snapshot in db.scalars(select(PlayerSnapshot).where(PlayerSnapshot.player_id == player.id).order_by(PlayerSnapshot.timestamp.asc()).limit(60))]
    if profile and profile.player_id != player.id:
        mine = list(db.scalars(select(City).where(City.player_id == profile.player_id)))
        city = db.scalar(select(City).where(City.player_id == player.id).limit(1))
        if mine and city:
            distance = min(calculate_distance((city.x, city.y), (own.x, own.y)) for own in mine)
            report["threat"] = threat_score(distance, player.points, player.cities_count, player.attack_points, alliance.points if alliance else 0, delta_7d["points"])
    return report


def dashboard_data(db: Session, profile: UserProfile) -> dict[str, object]:
    player = db.get(Player, profile.player_id)
    assert player
    mine = list(db.scalars(select(City).where(City.player_id == player.id)))
    alerts: list[dict[str, object]] = []
    for other in db.scalars(select(Player).where(Player.world_id == profile.world_id, Player.id != player.id).limit(300)):
        report = player_report(db, other, profile)
        threat = report.get("threat")
        if isinstance(threat, dict) and threat.get("score", 0) >= 60:
            alerts.append({"severity": "warning", "title": f"{other.name} est une menace à surveiller", "detail": "; ".join(threat["reasons"][:2]), "player_id": other.id})
    return {"profile": {"nickname": profile.nickname, "player": player_report(db, player, profile)}, "cities": [{"id": city.id, "name": city.name, "x": city.x, "y": city.y, "points": city.points} for city in mine], "alerts": alerts[:6]}
