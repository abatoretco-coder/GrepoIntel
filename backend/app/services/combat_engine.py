"""Transparent combat comparison, intentionally not an order executor."""
from typing import Mapping

from app.game_data.grepolis import UNITS, canonical_unit_id

LAND_DOMAINS = {"land", "mythic_land"}
NAVAL_DOMAINS = {"naval", "mythic_naval"}


def _normalise(stack: Mapping[str, int] | None) -> tuple[dict[str, int], dict[str, int]]:
    known: dict[str, int] = {}
    unknown: dict[str, int] = {}
    for raw_key, raw_value in (stack or {}).items():
        try:
            amount = max(0, int(raw_value))
        except (TypeError, ValueError):
            continue
        key = canonical_unit_id(str(raw_key))
        if not amount:
            continue
        (known if key in UNITS else unknown)[key] = amount
    return known, unknown


def _score(stack: Mapping[str, int], domains: set[str], field: str) -> int:
    return sum((getattr(UNITS[key], field) or 0) * amount
               for key, amount in stack.items() if UNITS[key].domain in domains)


def _attack_type(stack: Mapping[str, int]) -> str:
    values = {kind: 0 for kind in ("hack", "pierce", "distance")}
    for key, amount in stack.items():
        unit = UNITS[key]
        if unit.domain in LAND_DOMAINS and unit.attack_kind in values:
            values[unit.attack_kind] += (unit.attack or 0) * amount
    return max(values, key=values.get)


def simulate(attacker: Mapping[str, int], defender: Mapping[str, int], *,
             attack_type: str | None = None, wall_level: int | None = None,
             modifiers: dict | None = None) -> dict:
    """Compare known base forces and list every input that remains unknown.

    The ratio is a base-force comparison, never a claimed probability. A
    modifier is applied only when the caller explicitly supplies it.
    """
    modifiers = modifiers or {}
    attack, attack_unknown = _normalise(attacker)
    defense, defense_unknown = _normalise(defender)
    attack_type = attack_type if attack_type in {"hack", "pierce", "distance"} else _attack_type(attack)
    land_attack = _score(attack, LAND_DOMAINS, "attack")
    land_defense = _score(defense, LAND_DOMAINS, f"defense_{attack_type}")
    naval_attack = _score(attack, NAVAL_DOMAINS, "attack")
    naval_defense = _score(defense, NAVAL_DOMAINS, "naval_defense")
    unknown: list[str] = []
    if wall_level is None:
        unknown.append("Niveau de mur inconnu")
        wall_multiplier = 1.0
    else:
        # This base approximation is visible in the response, never concealed.
        wall_multiplier = 1 + max(0, wall_level) * 0.03
    for name, label in (("moral", "Moral"), ("luck", "Chance"), ("night_bonus", "Bonus de nuit"),
                        ("research", "Recherches"), ("hero", "Bonus héros"), ("god", "Bonus dieu"),
                        ("fr183", "Paramètres FR183")):
        if not modifiers.get(f"{name}_known"):
            unknown.append(f"{label} inconnu")
    for key, label in (("attack_multiplier", "Bonus d’attaque"), ("defense_multiplier", "Bonus de défense")):
        value = modifiers.get(key)
        if value is not None and isinstance(value, (int, float)):
            if key == "attack_multiplier":
                land_attack *= value
                naval_attack *= value
            else:
                land_defense *= value
                naval_defense *= value
    adjusted_land_defense = land_defense * wall_multiplier
    land_ratio = land_attack / max(adjusted_land_defense, 1)
    naval_ratio = naval_attack / max(naval_defense, 1)
    confidence = max(0, 100 - len(unknown) * 11 - (10 if attack_unknown or defense_unknown else 0))
    return {
        "land": {"attack": round(land_attack), "defense": round(adjusted_land_defense), "ratio": round(land_ratio, 2), "attack_type": attack_type, "wall": {"level": wall_level, "base_multiplier": round(wall_multiplier, 2) if wall_level is not None else None}},
        "naval": {"attack": round(naval_attack), "defense": round(naval_defense), "ratio": round(naval_ratio, 2)},
        "known_units": {"attacker": attack, "defender": defense},
        "unknown_units": {"attacker": attack_unknown, "defender": defense_unknown},
        "unknown_modifiers": unknown,
        "confidence": confidence,
        "outlook": "favorable" if land_ratio >= 1.25 else "incertain" if land_ratio >= .9 else "insuffisant",
        "informational_only": True,
    }
