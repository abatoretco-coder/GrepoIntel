from statistics import mean
from app.analytics.distance import calculate_distance

def cluster_analysis(cities: list[tuple[int, int]]) -> dict:
    if not cities: return {"cohesion_score": 0, "centroid": None, "average_distance": 0, "isolated_cities": []}
    centroid = (round(mean(x for x, _ in cities), 1), round(mean(y for _, y in cities), 1))
    distances = [calculate_distance(city, centroid) for city in cities]
    average = round(mean(distances), 2)
    return {"cohesion_score": max(0, min(100, round(100 - average * 4))), "centroid": {"x": centroid[0], "y": centroid[1]}, "average_distance": average, "isolated_cities": [index for index, value in enumerate(distances) if value > average * 1.5]}
