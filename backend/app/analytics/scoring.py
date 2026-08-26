from app.analytics.config import TARGET_WEIGHTS, THREAT_WEIGHTS

def _level(score: int) -> str:
    return "high" if score >= 70 else "medium" if score >= 40 else "low"

def threat_score(distance: float, player_points: int, player_cities: int, attack_points: int, alliance_points: int, growth: int = 0) -> dict:
    reasons: list[str] = []
    score = 0
    if distance <= 20: score += THREAT_WEIGHTS["distance"]; reasons.append(f"À {distance:.1f} cases de votre empire")
    if player_points >= 100_000: score += THREAT_WEIGHTS["points"]; reasons.append("Puissance élevée")
    if player_cities >= 8: score += THREAT_WEIGHTS["cities"]; reasons.append("Empire étendu")
    if attack_points >= 50_000: score += THREAT_WEIGHTS["battle"]; reasons.append("Forte activité offensive")
    if alliance_points >= 1_000_000: score += THREAT_WEIGHTS["alliance"]; reasons.append("Alliance puissante")
    if growth > 0: score += THREAT_WEIGHTS["growth"]; reasons.append("Progression récente")
    return {"score": min(100, score), "level": _level(score), "reasons": reasons or ["Aucun facteur de risque majeur détecté"]}

def target_score(distance: float, is_ghost: bool, points: int, has_alliance: bool) -> dict:
    reasons: list[str] = []; score = 0
    if distance <= 20: score += TARGET_WEIGHTS["distance"]; reasons.append(f"À {distance:.1f} cases de votre ville la plus proche")
    if is_ghost: score += TARGET_WEIGHTS["ghost"]; reasons.append("Ville fantôme")
    if not has_alliance: score += TARGET_WEIGHTS["alliance"]; reasons.append("Sans alliance")
    if points <= 10_000: score += TARGET_WEIGHTS["points"]; reasons.append("Ville de taille limitée")
    return {"score": min(100, score), "level": _level(score), "reasons": reasons or ["Cible à analyser"]}
