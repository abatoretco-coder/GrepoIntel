"""Read-only attack advice based on a synchronised army and dated intelligence."""
from datetime import UTC, datetime
from math import ceil

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.distance import calculate_distance, estimated_travel_time
from app.game_data.grepolis import UNITS, canonical_unit_id
from app.models.all_models import City, PersonalCityState, PersonalEmpireSnapshot, SpyReport
from app.services.combat_engine import LAND_DOMAINS, simulate
from app.services.profile_context import ProfileContext


def _home(state: PersonalCityState) -> dict[str, int]:
    raw = (state.units or {}).get("home", {})
    return {canonical_unit_id(key): value for key, value in raw.items()}


def _speed(units: dict[str, int], fallback: int) -> int:
    # A mixed land army travels at the slowest included unit's speed.
    speeds = [UNITS[key].speed for key, value in units.items()
              if value and key in UNITS and UNITS[key].domain in LAND_DOMAINS and UNITS[key].speed]
    return int(min(speeds)) if speeds else fallback


def _recommended_composition(units: dict[str, int], land_ratio: float) -> tuple[dict[str, int], str]:
    """Scale the actual available stack toward the explicit 1.25× safety margin.

    It is a transparent proportional proposal, not a claim to solve combat
    losses or unknown bonuses. When the available stack is insufficient, it
    returns the full known stack and says so.
    """
    if not units:
        return {}, "Aucune composition synchronisée"
    if land_ratio <= 0:
        return units, "Défense connue sans puissance terrestre exploitable"
    factor = min(1.0, 1.25 / land_ratio)
    composition = {key: min(amount, max(1, ceil(amount * factor))) for key, amount in units.items() if amount > 0}
    return composition, "Composition disponible insuffisante pour la marge 1.25×" if factor == 1 else "Composition proportionnelle pour la marge 1.25×"


def _playbook(result: dict, report_age_hours: float, can_conquer: bool, revolt_hours: int) -> list[dict]:
    stages: list[dict] = []
    if report_age_hours > 6 or result["unknown_units"]["defender"]:
        stages.append({"stage": "RECON", "status": "recommended", "reason": "Le renseignement est ancien ou incomplet : une nouvelle reconnaissance réduit le risque."})
    if result["naval"]["defense"]:
        stages.append({"stage": "NAVAL_CLEAR", "status": "evaluate", "reason": "Une défense navale connue doit être traitée avant le transport inter-île."})
    stages.append({"stage": "LAND_CLEAR", "status": "ready" if result["land"]["ratio"] >= 1.25 else "insufficient", "reason": "Comparaison contre la défense terrestre connue, par type d’arme dominant."})
    stages.append({"stage": "RE_CLEAN", "status": "evaluate", "reason": "Prévoir une seconde vague si des recrues ou soutiens peuvent arriver après le clear."})
    if can_conquer:
        stages.append({"stage": "REVOLT", "status": "evaluate", "reason": f"Conquête par révolte : vérifier les fenêtres du monde (préparation {revolt_hours} h)."})
    return stages


def advice(db: Session, ctx: ProfileContext, target_city_id: int) -> dict:
    target = db.get(City, target_city_id)
    if not target or target.world_id != ctx.world.id:
        raise ValueError("Target city not found in active world")
    report = db.scalar(select(SpyReport).where(SpyReport.world_id == ctx.world.id, SpyReport.city_id == target.id).order_by(SpyReport.observed_at.desc()))
    if not report:
        return {"recommendation": "SCOUT_FIRST", "target": {"name": target.name, "city_id": target.id}, "confidence": 0, "reasons": ["Aucun espionnage lié à cette cible."], "plans": [], "playbook": [{"stage": "RECON", "status": "required", "reason": "Aucun renseignement militaire n’est disponible."}], "informational_only": True}
    snapshot = db.scalar(select(PersonalEmpireSnapshot).where(PersonalEmpireSnapshot.profile_id == ctx.profile.id).order_by(PersonalEmpireSnapshot.captured_at.desc()))
    if not snapshot:
        return {"recommendation": "SCOUT_FIRST", "target": {"name": target.name, "city_id": target.id}, "confidence": 0, "reasons": ["Armées personnelles non synchronisées."], "plans": [], "informational_only": True}
    age = (datetime.now(UTC) - (report.observed_at or datetime.now(UTC))).total_seconds() / 3600
    states = {state.city_id: state for state in db.scalars(select(PersonalCityState).where(PersonalCityState.snapshot_id == snapshot.id))}
    wall = (report.buildings or {}).get("wall")
    plans = []
    for city in ctx.cities:
        state = states.get(city.id)
        if not state:
            continue
        units = _home(state)
        result = simulate(units, report.units or {}, wall_level=wall)
        composition, composition_note = _recommended_composition(result["known_units"]["attacker"], result["land"]["ratio"])
        distance = calculate_distance((city.x, city.y), (target.x, target.y))
        plans.append({
            "origin": {"name": city.name, "city_id": city.id},
            "available_units": result["known_units"]["attacker"],
            "unknown_units": result["unknown_units"]["attacker"],
            "distance": distance,
            "travel_seconds": estimated_travel_time(distance, _speed(units, ctx.world.unit_speed), ctx.world.game_speed),
            "unit_speed": _speed(composition, ctx.world.unit_speed),
            "recommended_composition": composition,
            "composition_note": composition_note,
            "simulation": result,
            "minimum_margin": "1.05× base-force comparison",
            "recommended_margin": "1.25× base-force comparison",
        })
    plans.sort(key=lambda plan: plan["simulation"]["land"]["ratio"], reverse=True)
    best = plans[0] if plans else None
    stale = age > 6
    result = best["simulation"] if best else simulate({}, report.units or {}, wall_level=wall)
    has_colonist = any(plan["available_units"].get("colonize_ship", 0) for plan in plans)
    if stale or result["unknown_units"]["defender"]:
        recommendation = "SCOUT_FIRST"
    elif result["land"]["ratio"] >= 1.25:
        recommendation = "EVALUATE_ATTACK"
    else:
        recommendation = "REINFORCE_OR_AVOID"
    return {
        "recommendation": recommendation,
        "target": {"name": target.name, "city_id": target.id, "known_defense": report.units, "last_spy_hours": round(age, 1), "provenance": "SPY_REPORT", "observed_at": report.observed_at},
        "confidence": result["confidence"],
        "assumptions": ["Les ratios ne sont pas une probabilité de victoire.", "Moral, chance, mur, recherches, héros et dieux restent inconnus lorsqu’ils ne sont pas observés.", "Aucun ordre Grepolis n’est envoyé."],
        "reasons": ["Renseignement à renouveler avant toute décision." if stale else "Plans comparés avec les armées personnelles du dernier snapshot et la défense observée."],
        "plans": plans[:3],
        "playbook": _playbook(result, age, has_colonist, ctx.world.revolt_preparation_hours),
        "informational_only": True,
    }
