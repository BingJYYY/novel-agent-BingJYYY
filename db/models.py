"""
数据库模型 —— 网文动态大纲管理系统
基于 SQLAlchemy ORM，SQLite 存储
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, create_engine, event
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session


class Base(DeclarativeBase):
    pass


# ============================================================
# 角色数据库
# ============================================================

class Character(Base):
    """角色数据库 —— 所有人物信息的唯一主数据源"""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    is_protagonist = Column(Boolean, default=False)

    first_appearance = Column(String(50))
    activity_status = Column(String(20), default="活跃")

    identity = Column(Text)
    gender = Column(String(10))
    age = Column(String(20))

    current_rank = Column(String(50))
    abilities = Column(Text, default="[]")
    equipment = Column(Text, default="[]")
    special_resources = Column(Text, default="{}")

    faction = Column(String(100))
    current_position = Column(String(100))
    current_location = Column(String(200))

    life_death_status = Column(String(20), default="存活")
    physical_status = Column(String(200))

    personality = Column(Text)
    core_goal = Column(Text)
    relationship_with_protagonist = Column(Text)
    important_experiences = Column(Text, default="[]")
    possessed_items = Column(Text, default="[]")
    contract_binding_status = Column(Text)
    identity_publicity = Column(Text)

    other_info = Column(Text)
    info_source = Column(String(50), default="客观事实")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    aliases = relationship("CharacterAlias", back_populates="character", cascade="all, delete-orphan")
    status_changes = relationship("CharacterStatusChange", back_populates="character", cascade="all, delete-orphan")


class CharacterAlias(Base):
    __tablename__ = "character_aliases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    alias = Column(String(100), nullable=False)
    character = relationship("Character", back_populates="aliases")


class CharacterStatusChange(Base):
    __tablename__ = "character_status_changes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    change_type = Column(String(30), nullable=False)
    field_name = Column(String(50))
    old_value = Column(Text)
    new_value = Column(Text)
    chapter_range = Column(String(50))
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    character = relationship("Character", back_populates="status_changes")


# ============================================================
# 世界观设定库
# ============================================================

class WorldSetting(Base):
    __tablename__ = "world_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    first_appearance = Column(String(50))
    last_confirmed = Column(String(50))
    credibility = Column(String(20), default="客观事实")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============================================================
# 关系数据库
# ============================================================

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True, autoincrement=True)
    character_a_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    character_b_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    current_relationship = Column(Text, nullable=False)
    relationship_nature = Column(String(50))
    formation_reason = Column(Text)
    first_established = Column(String(50))
    last_change = Column(String(50))
    trust_level = Column(String(30))
    has_unresolved_conflict = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    character_a = relationship("Character", foreign_keys=[character_a_id])
    character_b = relationship("Character", foreign_keys=[character_b_id])
    changes = relationship("RelationshipChange", back_populates="relationship", cascade="all, delete-orphan")


class RelationshipChange(Base):
    __tablename__ = "relationship_changes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    relationship_id = Column(Integer, ForeignKey("relationships.id"), nullable=False)
    old_relationship = Column(Text)
    new_relationship = Column(Text)
    change_reason = Column(Text)
    chapter_range = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    relationship = relationship("Relationship", back_populates="changes")


# ============================================================
# 事件大纲
# ============================================================

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    chapter_start = Column(Integer, nullable=False)
    chapter_end = Column(Integer)
    status = Column(String(20), default="进行中")
    is_locked = Column(Boolean, default=False)
    narrative_type = Column(String(30))
    narrative_subtype = Column(String(50))
    story_content = Column(Text)
    key_results = Column(Text, default="[]")
    sort_order = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    characters = relationship("EventCharacter", back_populates="event", cascade="all, delete-orphan")
    settings = relationship("EventSetting", back_populates="event", cascade="all, delete-orphan")


class EventCharacter(Base):
    __tablename__ = "event_characters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    identity_in_event = Column(Text)
    faction_in_event = Column(String(100))
    initial_status = Column(Text)
    end_status = Column(Text)
    goal = Column(Text)
    key_actions = Column(Text)
    plot_role = Column(Text)
    relationship_changes = Column(Text)
    event = relationship("Event", back_populates="characters")
    character = relationship("Character")


class EventSetting(Base):
    __tablename__ = "event_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    content = Column(Text, nullable=False)
    setting_type = Column(String(20), default="新增")
    event = relationship("Event", back_populates="settings")


# ============================================================
# 伏笔与悬念数据库
# ============================================================

class Foreshadowing(Base):
    __tablename__ = "foreshadowings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    fs_type = Column(String(20), default="已确认伏笔")
    first_appearance = Column(String(50))
    last_advanced = Column(String(50))
    current_status = Column(String(20), default="未解决")
    related_characters = Column(Text, default="[]")
    known_info = Column(Text)
    unresolved_part = Column(Text)
    credibility = Column(String(20), default="客观事实")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============================================================
# 时间线
# ============================================================

class TimelineEntry(Base):
    __tablename__ = "timeline_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_range = Column(String(50))
    time_precision = Column(String(20), nullable=False)
    time_value = Column(String(200))
    event_description = Column(Text, nullable=False)
    sort_order = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)


# ============================================================
# 设定冲突记录
# ============================================================

class SettingConflict(Base):
    __tablename__ = "setting_conflicts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conflict_content = Column(Text, nullable=False)
    involved_chapters = Column(Text, default="[]")
    old_info = Column(Text)
    new_info = Column(Text)
    conflict_type = Column(String(50))
    possible_reason = Column(Text)
    needs_author_confirmation = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolution_note = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ============================================================
# 标签系统
# ============================================================

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    is_author_tag = Column(Boolean, default=False)
    is_suggested = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class EntityTag(Base):
    __tablename__ = "entity_tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


# ============================================================
# 会话记录
# ============================================================

class SessionRecord(Base):
    __tablename__ = "session_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_range = Column(String(50))
    raw_output = Column(Text)
    db_operations = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.now)


# ============================================================
# 数据库初始化
# ============================================================

def init_db(db_path: str = "novel.db") -> Session:
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    Base.metadata.create_all(engine)
    return Session(engine)
