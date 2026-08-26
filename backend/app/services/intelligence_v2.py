from collections import Counter, defaultdict
from math import atan2, degrees
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.distance import calculate_distance
from app.models.all_models import Alliance, AllianceRelation, City, Player, PlayerSnapshot
from app.services.profile_context import ProfileContext

def _level(score: int) -> str:
    return "critique" if score >= 85 else "très élevée" if score >= 70 else "élevée" if score >= 50 else "modérée" if score >= 25 else "faible"

def _relation_map(db: Session, world_id: int) -> dict[int, str]:
    return {row.alliance_id: row.relation for row in db.scalars(select(AllianceRelation).where(AllianceRelation.world_id == world_id))}

def _distance(city: City, mine: list[City]) -> float:
    return min((calculate_distance((city.x, city.y), (own.x, own.y)) for own in mine), default=999.0)

def threat_rows(db: Session, ctx: ProfileContext, radius: float = 80, min_score: int = 0) -> list[dict]:
    cities_by_player: dict[int, list[City]] = defaultdict(list)
    for city in db.scalars(select(City).where(City.world_id == ctx.world.id, City.player_id.is_not(None), City.player_id != ctx.player.id)):
        cities_by_player[city.player_id].append(city)
    players = {p.id:p for p in db.scalars(select(Player).where(Player.world_id == ctx.world.id, Player.id != ctx.player.id))}
    alliances = {a.id:a for a in db.scalars(select(Alliance).where(Alliance.world_id == ctx.world.id))}; relations = _relation_map(db, ctx.world.id)
    rows=[]
    for player_id, cities in cities_by_player.items():
        player=players.get(player_id)
        if not player: continue
        distances=[_distance(city,ctx.cities) for city in cities]; nearest=min(distances); nearby=sum(d<=radius for d in distances)
        alliance=alliances.get(player.alliance_id); ratio=player.points/max(ctx.player.points,1)
        score=min(100, round((35 if nearest<=20 else 20 if nearest<=40 else 5) + min(20,nearby*5) + min(15,ratio*8) + min(15,player.attack_points/25_000) + (10 if alliance and alliance.points>ctx.player.points*5 else 0)))
        if alliance and alliance.id == ctx.player.alliance_id: score=max(0,score-60)
        if relations.get(player.alliance_id)=="FRIENDLY": score=max(0,score-40)
        reasons=[]
        if nearby: reasons.append({"factor":"nearby_presence","impact":min(20,nearby*5),"message":f"{nearby} ville(s) dans le rayon {radius:g}"})
        if ratio>=1: reasons.append({"factor":"relative_size","impact":min(15,round(ratio*8)),"message":"Puissance supérieure ou comparable à votre empire"})
        if alliance and alliance.points>ctx.player.points*5: reasons.append({"factor":"strong_alliance","impact":10,"message":f"Alliance {alliance.name} fortement capitalisée"})
        if player.attack_points>=25_000: reasons.append({"factor":"offensive_activity","impact":min(15,round(player.attack_points/25_000)),"message":"Points offensifs publics significatifs"})
        row={"player_id":player.id,"name":player.name,"alliance":{"id":alliance.id,"name":alliance.name} if alliance else None,"score":score,"level":_level(score),"nearest_distance":nearest,"nearby_city_count":nearby,"points":player.points,"cities_count":player.cities_count,"attack_points":player.attack_points,"battle_points":player.battle_points,"reasons":reasons}
        if score>=min_score: rows.append(row)
    return sorted(rows,key=lambda row:row["score"],reverse=True)

def target_rows(db: Session, ctx: ProfileContext, radius: float=80, min_score:int=0, ghost_only:bool=False, unallied_only:bool=False) -> list[dict]:
    players={p.id:p for p in db.scalars(select(Player).where(Player.world_id==ctx.world.id))}; alliances={a.id:a for a in db.scalars(select(Alliance).where(Alliance.world_id==ctx.world.id))}
    rows=[]
    for city in db.scalars(select(City).where(City.world_id==ctx.world.id, City.player_id != ctx.player.id)):
        owner=players.get(city.player_id); alliance=alliances.get(owner.alliance_id) if owner and owner.alliance_id else None
        if ghost_only and not city.is_ghost: continue
        if unallied_only and (not owner or owner.alliance_id): continue
        distance=_distance(city,ctx.cities)
        if distance>radius: continue
        territorial=max(0,min(100,round(65-distance + (20 if distance<15 else 0) + (15 if city.island_x in {own.island_x for own in ctx.cities} and city.island_y in {own.island_y for own in ctx.cities} else 0))))
        risk=(25 if alliance else 5)+(15 if owner and owner.points>ctx.player.points else 0)
        score=max(0,min(100,round((35 if distance<=20 else 20 if distance<=40 else 5)+(30 if city.is_ghost else 0)+(15 if not alliance else 0)+territorial*.25-risk*.35)))
        if score<min_score: continue
        reasons=[]
        if city.is_ghost: reasons.append({"factor":"ghost","impact":30,"message":"Ville fantôme"})
        if not alliance: reasons.append({"factor":"unallied","impact":15,"message":"Absence d’alliance connue"})
        reasons.append({"factor":"territorial_value","impact":round(territorial*.25),"message":f"Valeur territoriale {territorial}/100"})
        rows.append({"city_id":city.id,"name":city.name,"x":city.x,"y":city.y,"distance":distance,"points":city.points,"owner":{"id":owner.id,"name":owner.name} if owner else None,"alliance":{"id":alliance.id,"name":alliance.name} if alliance else None,"target_score":score,"territorial_value":territorial,"risk":risk,"level":_level(score),"reasons":reasons})
    return sorted(rows,key=lambda row:(row["target_score"],row["territorial_value"]),reverse=True)

def islands(db: Session, ctx: ProfileContext) -> list[dict]:
    all_cities=list(db.scalars(select(City).where(City.world_id==ctx.world.id))); players={p.id:p for p in db.scalars(select(Player).where(Player.world_id==ctx.world.id))}
    grouped:dict[tuple[int,int],list[City]]=defaultdict(list)
    for city in all_cities: grouped[(city.island_x,city.island_y)].append(city)
    result=[]
    for (x,y), cities in grouped.items():
        mine=[c for c in cities if c.player_id==ctx.player.id]; allied=[c for c in cities if players.get(c.player_id) and players[c.player_id].alliance_id==ctx.player.alliance_id]; ghosts=[c for c in cities if c.is_ghost]
        if not mine and min((_distance(c,ctx.cities) for c in cities),default=999)>40: continue
        total=len(cities); alliance_pct=round(len(allied)/total*100,1) if total else 0; opportunity=min(100,round(alliance_pct*.6+len(ghosts)*18+len(mine)*8))
        result.append({"island_x":x,"island_y":y,"total_cities":total,"self_cities":len(mine),"alliance_cities":len(allied),"ghost_cities":len(ghosts),"self_control_pct":round(len(mine)/total*100,1) if total else 0,"alliance_control_pct":alliance_pct,"island_opportunity_score":opportunity,"purpose":"intérêt territorial / préparation long terme"})
    return sorted(result,key=lambda row:row["island_opportunity_score"],reverse=True)

def frontiers(db: Session, ctx: ProfileContext) -> list[dict]:
    centroid=(sum(c.x for c in ctx.cities)/len(ctx.cities),sum(c.y for c in ctx.cities)/len(ctx.cities)) if ctx.cities else (0,0); names=["E","NE","N","NW","W","SW","S","SE"]; sectors={name:[] for name in names}
    for city in db.scalars(select(City).where(City.world_id==ctx.world.id, City.player_id != ctx.player.id)):
        dx,dy=city.x-centroid[0],city.y-centroid[1]; index=round((degrees(atan2(dy,dx))%360)/45)%8; sectors[names[index]].append(city)
    return [{"direction":name,"non_allied_cities":len(cities),"pressure":min(100,len(cities)*3),"level":_level(min(100,len(cities)*3)),"reason":f"{len(cities)} villes non personnelles dans ce secteur"} for name,cities in sectors.items()]

def overview(db: Session, ctx: ProfileContext) -> dict:
    threats=threat_rows(db,ctx)[:5]; targets=target_rows(db,ctx)[:5]; island_rows=islands(db,ctx)[:5]; frontier_rows=frontiers(db,ctx)
    recommendations=[]
    if threats: recommendations.append({"priority":"high" if threats[0]["score"]>=70 else "medium","category":"menace","title":f"Surveiller {threats[0]['name']}","message":"; ".join(reason["message"] for reason in threats[0]["reasons"][:2]),"evidence":threats[0]["reasons"],"related_entities":[{"type":"player","id":threats[0]["player_id"]}]})
    if targets: recommendations.append({"priority":"high" if targets[0]["target_score"]>=70 else "medium","category":"expansion","title":f"Évaluer {targets[0]['name']}","message":f"Score cible {targets[0]['target_score']}/100, valeur territoriale {targets[0]['territorial_value']}/100.","evidence":targets[0]["reasons"],"related_entities":[{"type":"city","id":targets[0]["city_id"]}]})
    player={"name":ctx.player.name,"points":ctx.player.points,"rank":ctx.player.rank,"cities_count":ctx.player.cities_count,"alliance_id":ctx.player.alliance_id,"battle_points":ctx.player.battle_points,"attack_points":ctx.player.attack_points,"defense_points":ctx.player.defense_points}
    snapshots=list(db.scalars(select(PlayerSnapshot).where(PlayerSnapshot.player_id==ctx.player.id).order_by(PlayerSnapshot.timestamp.asc())))
    latest=snapshots[-1].timestamp if snapshots else None; history_hours=round((latest-snapshots[0].timestamp).total_seconds()/3600,1) if len(snapshots)>1 and latest else 0
    confidence=min(1,history_hours/(24*7))
    return {"player":player,"profile":{"nickname":ctx.profile.nickname,"player":player},"cities":[{"id":c.id,"name":c.name,"x":c.x,"y":c.y,"points":c.points} for c in ctx.cities],"empire":{"cities_count":len(ctx.cities),"cluster_cohesion_score":max(0,100-round(sum(_distance(c,[other for other in ctx.cities if other.id!=c.id] or [c]) for c in ctx.cities)/max(len(ctx.cities),1)*4)),"centroid":{"x":round(sum(c.x for c in ctx.cities)/len(ctx.cities),1),"y":round(sum(c.y for c in ctx.cities)/len(ctx.cities),1)} if ctx.cities else None},"environment":{"nearby_threat_count":sum(row["score"]>=50 for row in threats),"island_opportunities":len(island_rows)},"threats":threats,"opportunities":targets,"territorial_signals":frontier_rows,"recommendations":recommendations,"data_freshness":{"latest_snapshot_at":latest,"history_span_hours":history_hours,"snapshot_count":len(snapshots),"confidence":round(confidence,2),"available":history_hours>=24,"reason":None if history_hours>=24 else "insufficient_history"}}
