from datetime import datetime, timedelta
from app.analytics.cluster import cluster_analysis
from app.analytics.distance import calculate_distance, estimated_travel_time
from app.analytics.scoring import target_score, threat_score
from app.analytics.world_rules.fr183 import calculate_revolt_window


def test_distance_and_travel_are_centralised():
    assert calculate_distance((0, 0), (3, 4)) == 5
    assert estimated_travel_time(5, 1, 2) > 0


def test_scores_are_bounded_and_explainable():
    threat = threat_score(5, 200000, 10, 60000, 2_000_000, 1000)
    target = target_score(4, True, 100, False)
    assert threat["score"] == 100 and threat["reasons"]
    assert target["score"] >= 80 and target["reasons"]


def test_cluster_and_revolt_window():
    cluster = cluster_analysis([(438, 512), (440, 513), (439, 511)])
    assert cluster["cohesion_score"] > 90
    activation = datetime(2026, 1, 1, 12)
    window = calculate_revolt_window(activation)
    assert window["preparation_start"] == activation - timedelta(hours=12)
    assert window["active_end"] == activation + timedelta(hours=12)
