"""
数据库操作层 —— 提供所有 CRUD 操作
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import (
    Character, CharacterAlias, CharacterStatusChange,
    WorldSetting, Relationship, RelationshipChange,
    Event, EventCharacter, EventSetting,
    Foreshadowing, TimelineEntry, SettingConflict,
    Tag, EntityTag, SessionRecord,
)


# ============================================================
# 角色操作
# ============================================================

def get_character(db: Session, name: str) -> Optional[Character]:
    char = db.query(Character).filter(Character.name == name).first()
    if char:
        return char
    alias = db.query(CharacterAlias).filter(CharacterAlias.alias == name).first()
    if alias:
        return alias.character
    return None


def get_character_by_id(db: Session, char_id: int) -> Optional[Character]:
    return db.query(Character).filter(Character.id == char_id).first()


def get_all_characters(db: Session, activity_status: Optional[str] = None) -> List[Character]:
    q = db.query(Character)
    if activity_status:
        q = q.filter(Character.activity_status == activity_status)
    return q.order_by(Character.name).all()


def get_protagonist(db: Session) -> Optional[Character]:
    return db.query(Character).filter(Character.is_protagonist == True).first()


def upsert_character(db: Session, name: str, **fields) -> Character:
    """插入或更新角色"""
    char = get_character(db, name)
    if char:
        for k, v in fields.items():
            if v is not None and hasattr(char, k):
                setattr(char, k, v)
        char.updated_at = datetime.now()
    else:
        char = Character(name=name, **fields)
        db.add(char)
    db.flush()
    return char


def add_character_alias(db: Session, character_id: int, alias: str):
    existing = db.query(CharacterAlias).filter(
        and_(CharacterAlias.character_id == character_id,
             CharacterAlias.alias == alias)
    ).first()
    if not existing:
        db.add(CharacterAlias(character_id=character_id, alias=alias))


def add_status_change(db: Session, character_id: int, change_type: str,
                      field_name: str, old_value: str, new_value: str,
                      chapter_range: str = "", detail: str = ""):
    db.add(CharacterStatusChange(
        character_id=character_id, change_type=change_type,
        field_name=field_name, old_value=old_value, new_value=new_value,
        chapter_range=chapter_range, detail=detail,
    ))


def archive_character(db: Session, char_id: int, reason: str = ""):
    char = db.query(Character).filter(Character.id == char_id).first()
    if char:
        if "死亡" in reason or char.life_death_status == "死亡":
            char.activity_status = "休眠角色｜已死亡"
        else:
            char.activity_status = "历史角色"


# ============================================================
# 世界观设定操作
# ============================================================

def get_setting(db: Session, category: str, name: str) -> Optional[WorldSetting]:
    return db.query(WorldSetting).filter(
        and_(WorldSetting.category == category, WorldSetting.name == name)
    ).first()


def get_all_settings(db: Session, category: Optional[str] = None) -> List[WorldSetting]:
    q = db.query(WorldSetting)
    if category:
        q = q.filter(WorldSetting.category == category)
    return q.order_by(WorldSetting.category, WorldSetting.name).all()


def upsert_setting(db: Session, category: str, name: str, content: str,
                   first_appearance: str = "", credibility: str = "客观事实",
                   notes: str = "") -> WorldSetting:
    setting = get_setting(db, category, name)
    if setting:
        setting.content = content
        setting.last_confirmed = first_appearance or setting.last_confirmed
        if credibility != "客观事实" or setting.credibility == "":
            setting.credibility = credibility
        setting.notes = notes or setting.notes
        setting.updated_at = datetime.now()
    else:
        setting = WorldSetting(
            category=category, name=name, content=content,
            first_appearance=first_appearance, last_confirmed=first_appearance,
            credibility=credibility, notes=notes,
        )
        db.add(setting)
    db.flush()
    return setting


def mark_setting_overridden(db: Session, setting_id: int):
    s = db.query(WorldSetting).filter(WorldSetting.id == setting_id).first()
    if s:
        s.notes = (s.notes or "") + "\n【旧设定已被新版正文覆盖】"


# ============================================================
# 关系操作
# ============================================================

def get_relationship(db: Session, char_a_id: int, char_b_id: int) -> Optional[Relationship]:
    return db.query(Relationship).filter(
        ((Relationship.character_a_id == char_a_id) & (Relationship.character_b_id == char_b_id)) |
        ((Relationship.character_a_id == char_b_id) & (Relationship.character_b_id == char_a_id))
    ).first()


def upsert_relationship(db: Session, char_a_id: int, char_b_id: int,
                        current_relationship: str, relationship_nature: str = "",
                        formation_reason: str = "", first_established: str = "",
                        trust_level: str = "", has_unresolved_conflict: bool = False,
                        notes: str = "") -> Relationship:
    rel = get_relationship(db, char_a_id, char_b_id)
    if rel:
        rel.current_relationship = current_relationship
        rel.relationship_nature = relationship_nature or rel.relationship_nature
        rel.trust_level = trust_level or rel.trust_level
        rel.has_unresolved_conflict = has_unresolved_conflict
        rel.notes = notes or rel.notes
        rel.updated_at = datetime.now()
        if first_established:
            rel.last_change = first_established
    else:
        rel = Relationship(
            character_a_id=char_a_id, character_b_id=char_b_id,
            current_relationship=current_relationship,
            relationship_nature=relationship_nature,
            formation_reason=formation_reason,
            first_established=first_established,
            last_change=first_established,
            trust_level=trust_level,
            has_unresolved_conflict=has_unresolved_conflict,
            notes=notes,
        )
        db.add(rel)
    db.flush()
    return rel


def add_relationship_change(db: Session, relationship_id: int,
                            old_relationship: str, new_relationship: str,
                            change_reason: str, chapter_range: str = ""):
    db.add(RelationshipChange(
        relationship_id=relationship_id,
        old_relationship=old_relationship, new_relationship=new_relationship,
        change_reason=change_reason, chapter_range=chapter_range,
    ))


# ============================================================
# 事件操作
# ============================================================

def get_ongoing_event(db: Session) -> Optional[Event]:
    return db.query(Event).filter(Event.status == "进行中").first()


def get_all_events(db: Session) -> List[Event]:
    return db.query(Event).order_by(Event.sort_order, Event.chapter_start).all()


def get_event_by_chapter(db: Session, chapter: int) -> Optional[Event]:
    return db.query(Event).filter(
        and_(Event.chapter_start <= chapter,
             (Event.chapter_end == None) | (Event.chapter_end >= chapter))
    ).first()


def create_event(db: Session, name: str, chapter_start: int,
                 chapter_end: Optional[int] = None, status: str = "进行中",
                 narrative_type: str = "", narrative_subtype: str = "",
                 story_content: str = "", key_results: str = "[]") -> Event:
    event = Event(
        name=name, chapter_start=chapter_start, chapter_end=chapter_end,
        status=status, narrative_type=narrative_type,
        narrative_subtype=narrative_subtype,
        story_content=story_content, key_results=key_results,
        sort_order=chapter_start,
    )
    db.add(event)
    db.flush()
    return event


def update_event(db: Session, event_id: int, **fields) -> Optional[Event]:
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        for k, v in fields.items():
            if v is not None and hasattr(event, k):
                setattr(event, k, v)
        event.updated_at = datetime.now()
    return event


def lock_event(db: Session, event_id: int, chapter_end: int):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        event.status = "已完成"
        event.is_locked = True
        if not event.chapter_end:
            event.chapter_end = chapter_end
        event.updated_at = datetime.now()


def add_event_character(db: Session, event_id: int, character_id: int, **fields):
    db.add(EventCharacter(event_id=event_id, character_id=character_id, **fields))


def add_event_setting(db: Session, event_id: int, content: str, setting_type: str = "新增"):
    db.add(EventSetting(event_id=event_id, content=content, setting_type=setting_type))


# ============================================================
# 伏笔操作
# ============================================================

def get_foreshadowing(db: Session, name: str) -> Optional[Foreshadowing]:
    return db.query(Foreshadowing).filter(Foreshadowing.name == name).first()


def get_all_foreshadowings(db: Session, status: Optional[str] = None) -> List[Foreshadowing]:
    q = db.query(Foreshadowing)
    if status:
        q = q.filter(Foreshadowing.current_status == status)
    return q.order_by(Foreshadowing.first_appearance).all()


def upsert_foreshadowing(db: Session, name: str, **fields) -> Foreshadowing:
    fs = get_foreshadowing(db, name)
    if fs:
        for k, v in fields.items():
            if v is not None and hasattr(fs, k):
                setattr(fs, k, v)
        fs.updated_at = datetime.now()
    else:
        fs = Foreshadowing(name=name, **fields)
        db.add(fs)
    db.flush()
    return fs


# ============================================================
# 时间线操作
# ============================================================

def add_timeline_entry(db: Session, chapter_range: str, time_precision: str,
                       time_value: str, event_description: str,
                       sort_order: float = 0) -> TimelineEntry:
    entry = TimelineEntry(
        chapter_range=chapter_range, time_precision=time_precision,
        time_value=time_value, event_description=event_description,
        sort_order=sort_order,
    )
    db.add(entry)
    db.flush()
    return entry


def get_timeline(db: Session) -> List[TimelineEntry]:
    return db.query(TimelineEntry).order_by(TimelineEntry.sort_order).all()


# ============================================================
# 设定冲突操作
# ============================================================

def add_conflict(db: Session, conflict_content: str, old_info: str = "",
                 new_info: str = "", conflict_type: str = "",
                 possible_reason: str = "",
                 needs_author_confirmation: bool = False,
                 involved_chapters: str = "[]") -> SettingConflict:
    conflict = SettingConflict(
        conflict_content=conflict_content, old_info=old_info,
        new_info=new_info, conflict_type=conflict_type,
        possible_reason=possible_reason,
        needs_author_confirmation=needs_author_confirmation,
        involved_chapters=involved_chapters,
    )
    db.add(conflict)
    db.flush()
    return conflict


def get_unresolved_conflicts(db: Session) -> List[SettingConflict]:
    return db.query(SettingConflict).filter(SettingConflict.is_resolved == False).all()


# ============================================================
# 标签操作
# ============================================================

def get_or_create_tag(db: Session, name: str, is_author: bool = False,
                      is_suggested: bool = False) -> Tag:
    tag = db.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name, is_author_tag=is_author, is_suggested=is_suggested)
        db.add(tag)
        db.flush()
    return tag


def tag_entity(db: Session, tag_id: int, entity_type: str, entity_id: int):
    existing = db.query(EntityTag).filter(
        and_(EntityTag.tag_id == tag_id,
             EntityTag.entity_type == entity_type,
             EntityTag.entity_id == entity_id)
    ).first()
    if not existing:
        db.add(EntityTag(tag_id=tag_id, entity_type=entity_type, entity_id=entity_id))


# ============================================================
# 会话记录
# ============================================================

def create_session_record(db: Session, chapter_range: str,
                          raw_output: str, db_operations: str) -> SessionRecord:
    record = SessionRecord(
        chapter_range=chapter_range, raw_output=raw_output, db_operations=db_operations,
    )
    db.add(record)
    db.flush()
    return record


# ============================================================
# 数据库状态摘要
# ============================================================

def build_context_summary(db: Session) -> str:
    parts = []

    ongoing = get_ongoing_event(db)
    if ongoing:
        parts.append(f"【当前进行中的事件】\n第{ongoing.chapter_start}-{ongoing.chapter_end or '?'}章「{ongoing.name}」\n状态：{ongoing.status}")

    protagonist = get_protagonist(db)
    if protagonist:
        parts.append(f"【主角】\n角色名：{protagonist.name}\n当前等级：{protagonist.current_rank or '未知'}\n当前位置：{protagonist.current_location or '未知'}\n所属势力：{protagonist.faction or '未知'}\n身体状态：{protagonist.physical_status or '未知'}\n当前目标：{protagonist.core_goal or '未知'}")

    active_chars = get_all_characters(db, activity_status="活跃")
    if active_chars:
        char_lines = [f"- {c.name}：{c.identity or '未知身份'}，{c.current_rank or '?'}级，{c.faction or '无阵营'}，与主角关系：{c.relationship_with_protagonist or '未知'}"
                      for c in active_chars if not c.is_protagonist]
        if char_lines:
            parts.append(f"【活跃角色】（共{len(char_lines)}人）\n" + "\n".join(char_lines))

    dormant = get_all_characters(db, activity_status="休眠")
    if dormant:
        parts.append(f"【休眠角色】{len(dormant)}人：{', '.join(c.name for c in dormant[:10])}{'...' if len(dormant) > 10 else ''}")

    settings = get_all_settings(db)
    setting_cats = {}
    for s in settings:
        setting_cats.setdefault(s.category, []).append(s.name)
    if setting_cats:
        slines = [f"  {cat}：{', '.join(names[:5])}{'...' if len(names) > 5 else ''}" for cat, names in setting_cats.items()]
        parts.append(f"【世界观设定】（共{len(settings)}条）\n" + "\n".join(slines))

    pending_fs = [f for f in get_all_foreshadowings(db) if f.current_status != "已回收"]
    if pending_fs:
        parts.append(f"【未解决伏笔】（共{len(pending_fs)}条）\n" + "\n".join(f"- {f.name}（首次：第{f.first_appearance}章，状态：{f.current_status}）" for f in pending_fs[:10]))

    events = get_all_events(db)
    if events:
        parts.append(f"【已有事件】（共{len(events)}条）\n" + "\n".join(f"- 第{e.chapter_start}-{e.chapter_end or '?'}章「{e.name}」[{e.status}]" for e in events[-5:]))

    timeline = get_timeline(db)
    if timeline:
        parts.append(f"【最近时间线】\n" + "\n".join(f"- [{t.time_precision}] {t.time_value}——{t.event_description}" for t in timeline[-5:]))

    conflicts = get_unresolved_conflicts(db)
    if conflicts:
        parts.append(f"【未解决设定冲突】（共{len(conflicts)}条）\n" + "\n".join(f"- {c.conflict_content[:80]}" for c in conflicts))

    return "\n\n".join(parts) if parts else "（空数据库，这是首次提交章节）"
