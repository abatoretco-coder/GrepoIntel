import re
from datetime import UTC, datetime
from sqlalchemy.orm import Session
from app.models.all_models import SpyReport

UNIT_ALIASES = {"épéiste":"sword","epeiste":"sword","hoplite":"hoplite","frondeur":"slinger","archer":"archer","cavalier":"rider","bireme":"bireme","trirème":"trireme","trireme":"trireme","colon":"colonist"}
UNIT_POWER = {"sword":12,"hoplite":16,"slinger":8,"archer":10,"rider":18,"bireme":12,"trireme":16,"colonist":0}

def parse_report_units(raw_text: str) -> dict[str, int]:
    units: dict[str, int] = {}
    for line in raw_text.lower().splitlines():
        match = re.search(r"([a-zàâçéèêëîïôûùüÿñæœ]+)\s*[:x-]?\s*([0-9][0-9 .]*)", line)
        if not match:
            continue
        key = UNIT_ALIASES.get(match.group(1))
        if key:
            units[key] = units.get(key, 0) + int(re.sub(r"[ .]", "", match.group(2)))
    return units

def save_spy_report(db: Session, world_id: int, title: str, raw_text: str, city_id: int | None = None, observed_at: datetime | None = None) -> SpyReport:
    report = SpyReport(world_id=world_id, city_id=city_id, title=title, raw_text=raw_text, observed_at=observed_at or datetime.now(UTC), units=parse_report_units(raw_text))
    db.add(report); db.commit(); db.refresh(report)
    return report

def simulate_attack(report: SpyReport, attacker_units: dict[str, int], wall_level: int) -> dict:
    attackers = {key: max(0, int(value)) for key, value in attacker_units.items() if key in UNIT_POWER}
    attack_power = sum(UNIT_POWER[key] * value for key, value in attackers.items())
    defense_power = sum(UNIT_POWER.get(key, 10) * value for key, value in report.units.items()) * (1 + wall_level * .03)
    ratio = attack_power / defense_power if defense_power else float("inf")
    chance = 100 if defense_power == 0 and attack_power else max(0, min(99, round(ratio / (1 + ratio) * 100)))
    return {"report_id": report.id, "attacker_units": attackers, "defender_units": report.units, "attack_power": round(attack_power), "estimated_defense_power": round(defense_power), "power_ratio": round(ratio, 2) if ratio != float("inf") else None, "estimated_success_chance": chance, "disclaimer":"Estimation locale indicative : elle ne remplace pas le simulateur officiel et n’envoie aucun ordre au jeu."}
