"""Versioned, application-wide Grepolis unit catalogue.

The values below are the *base* unit values. World rules, researches, heroes,
divine powers and timed events are deliberately not baked into them: callers
must pass a known modifier or report it as unknown.
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Unit:
    id: str
    label: str
    domain: str  # land | naval | mythic_land | mythic_naval
    role: str
    population: int | None
    speed: float | None
    attack: int | None
    attack_kind: str | None = None  # hack | pierce | distance
    defense_hack: int | None = None
    defense_pierce: int | None = None
    defense_distance: int | None = None
    naval_defense: int | None = None
    transport: int = 0
    god: str | None = None
    requires: tuple[str, ...] = ()


def unit(id: str, label: str, domain: str, role: str, population: int | None,
         speed: float | None, attack: int | None, attack_kind: str | None = None,
         defense_hack: int | None = None, defense_pierce: int | None = None,
         defense_distance: int | None = None, naval_defense: int | None = None,
         transport: int = 0, god: str | None = None,
         requires: tuple[str, ...] = ()) -> Unit:
    return Unit(id, label, domain, role, population, speed, attack, attack_kind,
                defense_hack, defense_pierce, defense_distance, naval_defense,
                transport, god, requires)


# Base roster. Mythical entries include every currently supported Olympian
# creature. A runtime-only or event unit is not guessed: it is returned to the
# UI as an unknown unit instead of being silently discarded.
UNITS = {item.id: item for item in [
    unit("sword", "Épéiste", "land", "DEF_LAND", 1, 8, 5, "hack", 14, 8, 30, requires=("barracks", "sword")),
    unit("slinger", "Frondeur", "land", "OFF_LAND", 1, 6, 23, "distance", 7, 8, 2, requires=("barracks", "slinger")),
    unit("archer", "Archer", "land", "DEF_LAND", 1, 8, 8, "distance", 7, 25, 13, requires=("barracks", "archer")),
    unit("hoplite", "Hoplite", "land", "OFF_LAND", 1, 7, 16, "pierce", 18, 12, 7, requires=("barracks", "hoplite")),
    unit("rider", "Cavalier", "land", "OFF_LAND", 3, 3, 55, "hack", 3, 1, 18, requires=("barracks", "rider")),
    unit("chariot", "Char", "land", "DEF_LAND", 4, 4, 56, "pierce", 76, 16, 56, requires=("barracks", "chariot")),
    unit("catapult", "Catapulte", "land", "SIEGE", 15, 30, 100, "distance", 100, 10, 50, requires=("barracks", "catapult")),
    unit("small_transporter", "Petit transport", "naval", "TRANSPORT", 8, 10, 0, naval_defense=8, transport=26, requires=("harbor", "small_transporter")),
    unit("big_transporter", "Grand transport", "naval", "TRANSPORT", 10, 16, 0, naval_defense=10, transport=30, requires=("harbor", "big_transporter")),
    unit("bireme", "Birème", "naval", "NAV_DEF", 8, 8, 8, naval_defense=60, requires=("harbor", "bireme")),
    unit("attack_ship", "Navire léger", "naval", "NAV_OFF", 8, 10, 16, naval_defense=8, requires=("harbor", "attack_ship")),
    unit("trireme", "Trière", "naval", "NAV_DEF", 16, 8, 30, naval_defense=40, requires=("harbor", "trireme")),
    unit("demolition_ship", "Brûlot", "naval", "SIEGE_NAV", 8, 10, 8, naval_defense=8, requires=("harbor", "demolition_ship")),
    unit("colonize_ship", "Navire colonisateur", "naval", "CONQUEST", 170, 26, 0, naval_defense=0, requires=("harbor", "colonize_ship")),
    unit("minotaur", "Minotaure", "mythic_land", "MYTHIC_DEF", 30, 10, 650, "hack", 750, 330, 640, god="Zeus", requires=("temple",)),
    unit("manticore", "Manticore", "mythic_land", "MYTHIC_OFF", 45, 22, 1010, "pierce", 170, 225, 505, god="Zeus", requires=("temple",)),
    unit("cyclops", "Cyclope", "mythic_land", "MYTHIC_SIEGE", 40, 8, 1035, "distance", 1050, 10, 1450, god="Poséidon", requires=("temple",)),
    unit("hydra", "Hydre", "mythic_naval", "MYTHIC_NAV_OFF", 50, 8, 1310, naval_defense=1400, god="Poséidon", requires=("temple",)),
    unit("medusa", "Méduse", "mythic_land", "MYTHIC_OFF", 18, 6, 425, "pierce", 480, 345, 290, god="Héra", requires=("temple",)),
    unit("harpy", "Harpie", "mythic_land", "MYTHIC_OFF", 14, 28, 295, "hack", 105, 70, 1, god="Héra", requires=("temple",)),
    unit("centaur", "Centaure", "mythic_land", "MYTHIC_OFF", 12, 18, 134, "distance", 195, 585, 80, god="Athéna", requires=("temple",)),
    unit("pegasus", "Pégase", "mythic_land", "MYTHIC_DEF", 20, 35, 100, "pierce", 750, 275, 275, god="Athéna", requires=("temple",)),
    unit("cerberus", "Cerbère", "mythic_land", "MYTHIC_DEF", 30, 4, 210, "hack", 825, 300, 1575, god="Hadès", requires=("temple",)),
    unit("erinys", "Érinye", "mythic_land", "MYTHIC_OFF", 55, 10, 1700, "distance", 460, 460, 595, god="Hadès", requires=("temple",)),
    unit("calydonian_boar", "Sanglier de Calydon", "mythic_land", "MYTHIC_DEF", 20, 16, 180, "pierce", 700, 700, 100, god="Artémis", requires=("temple",)),
    unit("griffin", "Griffon", "mythic_land", "MYTHIC_OFF", 35, 18, 900, "hack", 320, 330, 100, god="Artémis", requires=("temple",)),
    unit("spartoi", "Spartoï", "mythic_land", "MYTHIC_OFF", 10, 16, 205, "hack", 100, 100, 150, god="Arès", requires=("temple",)),
    unit("ladon", "Ladon", "mythic_land", "MYTHIC_OFF", 180, 100, 2530, "distance", 2390, 1950, 2100, god="Arès", requires=("temple",)),
    unit("satyr", "Satyre", "mythic_land", "MYTHIC_OFF", 16, 136, 385, "pierce", 55, 105, 170, god="Aphrodite", requires=("temple",)),
    unit("siren", "Sirène", "mythic_naval", "MYTHIC_NAV_OFF", 16, 22, 180, naval_defense=170, god="Aphrodite", requires=("temple",)),
    unit("godsent", "Messager divin", "mythic_land", "SUPPORT", 3, 16, 45, "hack", 40, 40, 40, god="Universel", requires=("temple",)),
]}

UNIT_ALIASES = {"colonist": "colonize_ship", "colon": "colonize_ship", "demolition": "demolition_ship"}


def canonical_unit_id(unit_id: str) -> str:
    return UNIT_ALIASES.get(unit_id, unit_id)


def catalogue() -> list[dict]:
    return [asdict(item) for item in UNITS.values()]
