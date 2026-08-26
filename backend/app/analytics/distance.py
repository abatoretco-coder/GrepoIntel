from math import hypot

def calculate_distance(city_a: tuple[int, int], city_b: tuple[int, int]) -> float:
    return round(hypot(city_a[0] - city_b[0], city_a[1] - city_b[1]), 2)

def estimated_travel_time(distance: float, unit_speed: float, world_speed: float) -> int:
    if unit_speed <= 0 or world_speed <= 0: raise ValueError("Speeds must be positive")
    return round(distance * 3600 / (unit_speed * world_speed))
