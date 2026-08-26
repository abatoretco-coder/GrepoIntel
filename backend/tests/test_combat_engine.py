from app.game_data.grepolis import UNITS
from app.services.combat_engine import simulate

def test_catalogue_has_domains_and_dependencies():
    assert {"land","naval","mythic_land","mythic_naval"}.issubset({unit.domain for unit in UNITS.values()})
    assert UNITS["hoplite"].population == 1
    assert "hoplite" in UNITS["hoplite"].requires

def test_combat_keeps_unknown_modifiers_explicit():
    result=simulate({"hoplite":100},{"sword":100},wall_level=None)
    assert result["land"]["attack"] > 0
    assert "Niveau de mur inconnu" in result["unknown_modifiers"]
    assert result["informational_only"] is True
