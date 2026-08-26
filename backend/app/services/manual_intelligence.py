import re
from datetime import UTC, datetime
from sqlalchemy.orm import Session
from app.models.all_models import SpyReport
from app.game_data.grepolis import canonical_unit_id
from app.services.combat_engine import simulate

UNIT_ALIASES = {"épéiste":"sword","epeiste":"sword","hoplite":"hoplite","frondeur":"slinger","archer":"archer","cavalier":"rider","char":"chariot","catapulte":"catapult","birème":"bireme","bireme":"bireme","trirème":"trireme","trireme":"trireme","colon":"colonize_ship","navire colonisateur":"colonize_ship"}

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

def simulate_attack(report: SpyReport, attacker_units: dict[str, int], wall_level: int | None) -> dict:
    normalised = {canonical_unit_id(key): value for key, value in attacker_units.items()}
    result=simulate(normalised, report.units, wall_level=wall_level)
    return {"report_id":report.id,"attacker_units":result["known_units"]["attacker"],"defender_units":result["known_units"]["defender"],**result,"disclaimer":"Comparaison des forces connues : moral, chance et bonus absents ne sont jamais inventés. Aucun ordre Grepolis n’est envoyé."}
