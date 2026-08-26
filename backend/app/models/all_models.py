from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class World(Timestamped, Base):
    __tablename__ = "worlds"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100)); language: Mapped[str] = mapped_column(String(8))
    game_speed: Mapped[int] = mapped_column(Integer); unit_speed: Mapped[int] = mapped_column(Integer); trade_speed: Mapped[int] = mapped_column(Integer)
    conquest_type: Mapped[str] = mapped_column(String(32)); revolt_preparation_hours: Mapped[int] = mapped_column(Integer); revolt_active_hours: Mapped[int] = mapped_column(Integer)
    night_bonus_start: Mapped[str] = mapped_column(String(5)); night_bonus_end: Mapped[str] = mapped_column(String(5))
    morale_enabled: Mapped[bool] = mapped_column(Boolean); luck_enabled: Mapped[bool] = mapped_column(Boolean); alliance_limit: Mapped[int] = mapped_column(Integer)
    endgame_type: Mapped[str] = mapped_column(String(64)); endgame_speed: Mapped[str] = mapped_column(String(32)); resource_bonus: Mapped[int] = mapped_column(Integer)

class Alliance(Timestamped, Base):
    __tablename__ = "alliances"; __table_args__ = (UniqueConstraint("world_id", "external_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), index=True); external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(100), index=True); points: Mapped[int] = mapped_column(Integer, default=0); rank: Mapped[int] = mapped_column(Integer, default=0)
    members_count: Mapped[int] = mapped_column(Integer, default=0); cities_count: Mapped[int] = mapped_column(Integer, default=0)

class Player(Timestamped, Base):
    __tablename__ = "players"; __table_args__ = (UniqueConstraint("world_id", "external_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), index=True); external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(100), index=True); alliance_id: Mapped[int | None] = mapped_column(ForeignKey("alliances.id"), nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0); rank: Mapped[int] = mapped_column(Integer, default=0); cities_count: Mapped[int] = mapped_column(Integer, default=0)
    attack_points: Mapped[int] = mapped_column(Integer, default=0); defense_points: Mapped[int] = mapped_column(Integer, default=0); battle_points: Mapped[int] = mapped_column(Integer, default=0)

class City(Timestamped, Base):
    __tablename__ = "cities"; __table_args__ = (UniqueConstraint("world_id", "external_id"), Index("ix_city_coordinates", "world_id", "x", "y"))
    id: Mapped[int] = mapped_column(primary_key=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), index=True); external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(100)); player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)
    x: Mapped[int] = mapped_column(Integer); y: Mapped[int] = mapped_column(Integer); is_ghost: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    points: Mapped[int] = mapped_column(Integer, default=0); island_x: Mapped[int] = mapped_column(Integer); island_y: Mapped[int] = mapped_column(Integer)

class PlayerSnapshot(Base):
    __tablename__ = "player_snapshots"; __table_args__ = (Index("ix_player_snapshot_time", "player_id", "timestamp"),)
    id: Mapped[int] = mapped_column(primary_key=True); player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True); timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    points: Mapped[int] = mapped_column(Integer); rank: Mapped[int] = mapped_column(Integer); cities_count: Mapped[int] = mapped_column(Integer); attack_points: Mapped[int] = mapped_column(Integer); defense_points: Mapped[int] = mapped_column(Integer); battle_points: Mapped[int] = mapped_column(Integer); alliance_id: Mapped[int | None] = mapped_column(ForeignKey("alliances.id"), nullable=True)

class CitySnapshot(Base):
    __tablename__ = "city_snapshots"; __table_args__ = (Index("ix_city_snapshot_time", "city_id", "timestamp"),)
    id: Mapped[int] = mapped_column(primary_key=True); city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True); timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True); player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True); points: Mapped[int] = mapped_column(Integer); is_ghost: Mapped[bool] = mapped_column(Boolean)

class AllianceSnapshot(Base):
    __tablename__ = "alliance_snapshots"; __table_args__ = (Index("ix_alliance_snapshot_time", "alliance_id", "timestamp"),)
    id: Mapped[int] = mapped_column(primary_key=True); alliance_id: Mapped[int] = mapped_column(ForeignKey("alliances.id"), index=True); timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True); points: Mapped[int] = mapped_column(Integer); rank: Mapped[int] = mapped_column(Integer); members_count: Mapped[int] = mapped_column(Integer); cities_count: Mapped[int] = mapped_column(Integer)

class ConquestEvent(Base):
    __tablename__ = "conquest_events"
    id: Mapped[int] = mapped_column(primary_key=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), index=True); city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True); timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    old_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True); new_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True); old_alliance_id: Mapped[int | None] = mapped_column(ForeignKey("alliances.id"), nullable=True); new_alliance_id: Mapped[int | None] = mapped_column(ForeignKey("alliances.id"), nullable=True)

class AllianceChangeEvent(Base):
    __tablename__ = "alliance_change_events"
    id: Mapped[int] = mapped_column(primary_key=True); player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True); timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True); old_alliance_id: Mapped[int | None] = mapped_column(ForeignKey("alliances.id"), nullable=True); new_alliance_id: Mapped[int | None] = mapped_column(ForeignKey("alliances.id"), nullable=True)

class UserProfile(Timestamped, Base):
    __tablename__ = "user_profiles"
    id: Mapped[int] = mapped_column(primary_key=True); nickname: Mapped[str] = mapped_column(String(100), unique=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id")); player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))

class AllianceRelation(Timestamped, Base):
    __tablename__ = "alliance_relations"; __table_args__ = (UniqueConstraint("world_id", "alliance_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), index=True); alliance_id: Mapped[int] = mapped_column(ForeignKey("alliances.id"), index=True)
    relation: Mapped[str] = mapped_column(String(16), default="NEUTRAL"); note: Mapped[str | None] = mapped_column(String(500), nullable=True)

class SpyReport(Timestamped, Base):
    __tablename__ = "spy_reports"
    id: Mapped[int] = mapped_column(primary_key=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), index=True); city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(160)); observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True); raw_text: Mapped[str] = mapped_column(Text)
    units: Mapped[dict] = mapped_column(JSON, default=dict); buildings: Mapped[dict] = mapped_column(JSON, default=dict)

class PersonalEmpireSnapshot(Base):
    __tablename__ = "personal_empire_snapshots"; __table_args__ = (UniqueConstraint("profile_id", "state_hash"),)
    id: Mapped[int] = mapped_column(primary_key=True); profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True); world_id: Mapped[int] = mapped_column(ForeignKey("worlds.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True); source_type: Mapped[str] = mapped_column(String(32)); source_version: Mapped[int] = mapped_column(Integer); state_hash: Mapped[str] = mapped_column(String(64))

class PersonalCityState(Base):
    __tablename__ = "personal_city_states"; __table_args__ = (UniqueConstraint("snapshot_id", "city_id"),)
    id: Mapped[int] = mapped_column(primary_key=True); snapshot_id: Mapped[int] = mapped_column(ForeignKey("personal_empire_snapshots.id"), index=True); city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    resources: Mapped[dict] = mapped_column(JSON, default=dict); population: Mapped[dict] = mapped_column(JSON, default=dict); buildings: Mapped[dict] = mapped_column(JSON, default=dict); researches: Mapped[dict] = mapped_column(JSON, default=dict); units: Mapped[dict] = mapped_column(JSON, default=dict); queues: Mapped[dict] = mapped_column(JSON, default=dict); god: Mapped[str | None] = mapped_column(String(64), nullable=True); hero: Mapped[dict] = mapped_column(JSON, default=dict)
