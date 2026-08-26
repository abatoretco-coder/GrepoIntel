from app.game_data.grepolis import UNITS
from app.services.combat_engine import simulate
from app.services.combat_advisor import _recommended_composition

def test_catalogue_has_domains_and_dependencies():
    assert {"land","naval","mythic_land","mythic_naval"}.issubset({unit.domain for unit in UNITS.values()})
    assert UNITS["hoplite"].population == 1
    assert "hoplite" in UNITS["hoplite"].requires

def test_combat_keeps_unknown_modifiers_explicit():
    result=simulate({"hoplite":100},{"sword":100},wall_level=None)
    assert result["land"]["attack"] > 0
    assert "Niveau de mur inconnu" in result["unknown_modifiers"]
    assert result["informational_only"] is True

def test_recommended_composition_is_quantified_and_never_exceeds_available():
    composition, note = _recommended_composition({"hoplite": 100, "slinger": 80}, 2.5)
    assert composition == {"hoplite": 50, "slinger": 40}
    assert "1.25" in note
