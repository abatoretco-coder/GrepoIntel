from app.models.all_models import SpyReport
from app.services.manual_intelligence import parse_report_units, simulate_attack

def test_manual_report_parser_and_local_simulator():
    units = parse_report_units("Hoplite: 120\nArcher: 80\nÉpéiste: 50")
    assert units == {"hoplite": 120, "archer": 80, "sword": 50}
    report = SpyReport(id=42, world_id=1, title="test", raw_text="", units=units, buildings={})
    simulation = simulate_attack(report, {"hoplite": 180, "archer": 100, "invalid": 99}, wall_level=5)
    assert simulation["land"]["ratio"] > 0
    assert "invalid" not in simulation["attacker_units"]
    assert simulation["unknown_units"]["attacker"] == {"invalid": 99}
