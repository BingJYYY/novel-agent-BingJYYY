"""
数据库操作应用器 —— 将 LLM 输出的 JSON 操作应用到数据库
"""

import json
from typing import Optional
from sqlalchemy.orm import Session

from db.repository import (
    upsert_character, add_character_alias, add_status_change,
    upsert_setting, mark_setting_overridden,
    upsert_relationship, add_relationship_change,
    create_event, update_event, lock_event,
    upsert_foreshadowing, add_timeline_entry, add_conflict,
    get_character, get_or_create_tag, tag_entity,
    archive_character, get_relationship,
)


def _ensure_list(v):
    if isinstance(v, str):
        return [v]
    if v is None:
        return []
    return v


def _ensure_str(v):
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def apply_db_operations(db: Session, db_ops: dict) -> dict:
    import traceback

    stats = {"added": 0, "updated": 0, "archived": 0, "locked": 0, "conflicts": 0, "errors": []}

    ops = db_ops.get("db_operations", db_ops)
    if not ops or not isinstance(ops, dict):
        return stats

    # ---- ADD ----
    add = ops.get("add") or {}

    for char_data in _ensure_list(add.get("characters")):
        try:
            aliases = _ensure_list(char_data.pop("aliases", []))
            name = char_data.pop("name", "未知角色")
            # 将 list/dict 类型字段转为 JSON 字符串，避免 SQLite 绑定错误
            for k, v in list(char_data.items()):
                if isinstance(v, (list, dict)):
                    char_data[k] = json.dumps(v, ensure_ascii=False)
            char = upsert_character(db, name, **char_data)
            for alias in aliases:
                add_character_alias(db, char.id, _ensure_str(alias))
            stats["added"] += 1
        except Exception as e:
            print(f"[WARN] 添加角色失败: {e}")
            stats["errors"].append(f"添加角色失败: {e}")
            traceback.print_exc()

    for event_data in _ensure_list(add.get("events")):
        try:
            key_results = _ensure_list(event_data.pop("key_results", []))
            create_event(db, key_results=json.dumps(key_results, ensure_ascii=False), **event_data)
            stats["added"] += 1
        except Exception as e:
            print(f"[WARN] 添加事件失败: {e}")
            stats["errors"].append(f"添加事件失败: {e}")
            traceback.print_exc()

    for ws_data in _ensure_list(add.get("world_settings")):
        try:
            upsert_setting(db, **ws_data)
            stats["added"] += 1
        except Exception as e:
            print(f"[WARN] 添加设定失败: {e}")
            stats["errors"].append(f"添加设定失败: {e}")
            traceback.print_exc()

    for fs_data in _ensure_list(add.get("foreshadowings")):
        try:
            for k, v in list(fs_data.items()):
                if isinstance(v, (list, dict)):
                    fs_data[k] = json.dumps(v, ensure_ascii=False)
            upsert_foreshadowing(db, **fs_data)
            stats["added"] += 1
        except Exception as e:
            print(f"[WARN] 添加伏笔失败: {e}")
            stats["errors"].append(f"添加伏笔失败: {e}")
            traceback.print_exc()

    for tl_data in _ensure_list(add.get("timeline")):
        try:
            add_timeline_entry(db, **tl_data)
            stats["added"] += 1
        except Exception as e:
            print(f"[WARN] 添加时间线失败: {e}")
            stats["errors"].append(f"添加时间线失败: {e}")
            traceback.print_exc()

    for cf_data in _ensure_list(add.get("conflicts")):
        try:
            add_conflict(db, **cf_data)
            stats["conflicts"] += 1
        except Exception as e:
            print(f"[WARN] 添加冲突记录失败: {e}")
            stats["errors"].append(f"添加冲突记录失败: {e}")
            traceback.print_exc()

    # ---- UPDATE ----
    update = ops.get("update") or {}

    for char_upd in _ensure_list(update.get("characters")):
        try:
            name = char_upd["name"]
            field = char_upd["field"]
            old_val = char_upd.get("old_value", "")
            new_val = char_upd["new_value"]
            char = get_character(db, name)
            if char:
                old_actual = str(getattr(char, field, "")) if hasattr(char, field) else ""
                setattr(char, field, _ensure_str(new_val))
                add_status_change(db, char.id, _map_field_to_change_type(field),
                                  field, str(old_val or old_actual), _ensure_str(new_val))
                stats["updated"] += 1
        except Exception as e:
            print(f"[WARN] 更新角色失败: {e}")
            stats["errors"].append(f"更新角色失败: {e}")
            traceback.print_exc()

    for rel_upd in _ensure_list(update.get("relationships")):
        try:
            char_a = get_character(db, rel_upd["char_a"])
            char_b = get_character(db, rel_upd["char_b"])
            if char_a and char_b:
                field = rel_upd["field"]
                old_val = rel_upd.get("old_value", "")
                new_val = rel_upd["new_value"]
                rel = get_relationship(db, char_a.id, char_b.id)
                if rel:
                    old_actual = getattr(rel, field, "")
                    add_relationship_change(db, rel.id, str(old_val or old_actual), _ensure_str(new_val),
                                            change_reason=rel_upd.get("reason", ""))
                    upsert_relationship(db, char_a.id, char_b.id, current_relationship=_ensure_str(new_val),
                                        relationship_nature=rel_upd.get("nature", ""))
                else:
                    upsert_relationship(db, char_a.id, char_b.id,
                                        current_relationship=_ensure_str(new_val),
                                        relationship_nature=rel_upd.get("nature", ""))
                stats["updated"] += 1
        except Exception as e:
            print(f"[WARN] 更新关系失败: {e}")
            stats["errors"].append(f"更新关系失败: {e}")
            traceback.print_exc()

    for ws_upd in _ensure_list(update.get("settings")):
        try:
            name = ws_upd["name"]
            field = ws_upd["field"]
            new_val = ws_upd["new_value"]
            from db.models import WorldSetting
            ws = db.query(WorldSetting).filter(WorldSetting.name == name).first()
            if ws:
                old_val = ws_upd.get("old_value", "")
                if old_val == "(被推翻)":
                    mark_setting_overridden(ws.id)
                elif hasattr(ws, field):
                    setattr(ws, field, _ensure_str(new_val))
                stats["updated"] += 1
        except Exception as e:
            print(f"[WARN] 更新设定失败: {e}")
            stats["errors"].append(f"更新设定失败: {e}")
            traceback.print_exc()

    for fs_upd in _ensure_list(update.get("foreshadowings")):
        try:
            name = fs_upd["name"]
            field = fs_upd["field"]
            new_val = fs_upd["new_value"]
            fs = upsert_foreshadowing(db, name)
            if hasattr(fs, field):
                setattr(fs, field, _ensure_str(new_val))
            stats["updated"] += 1
        except Exception as e:
            print(f"[WARN] 更新伏笔失败: {e}")
            stats["errors"].append(f"更新伏笔失败: {e}")
            traceback.print_exc()

    for evt_upd in _ensure_list(update.get("events")):
        try:
            chapter_start = evt_upd["chapter_start"]
            field = evt_upd["field"]
            new_val = evt_upd["new_value"]
            from db.models import Event
            event = db.query(Event).filter(Event.chapter_start == chapter_start).first()
            if event and hasattr(event, field):
                setattr(event, field, _ensure_str(new_val))
                stats["updated"] += 1
        except Exception as e:
            print(f"[WARN] 更新事件失败: {e}")
            stats["errors"].append(f"更新事件失败: {e}")
            traceback.print_exc()

    # ---- ARCHIVE ----
    archive = ops.get("archive") or {}
    for char_name in _ensure_list(archive.get("characters")):
        try:
            char = get_character(db, _ensure_str(char_name))
            if char:
                archive_character(db, char.id)
                stats["archived"] += 1
        except Exception as e:
            print(f"[WARN] 归档角色失败: {e}")
            stats["errors"].append(f"归档角色失败: {e}")
            traceback.print_exc()
    for fs_name in _ensure_list(archive.get("foreshadowings")):
        try:
            fs = upsert_foreshadowing(db, _ensure_str(fs_name))
            if fs:
                fs.current_status = "已回收"
                stats["archived"] += 1
        except Exception as e:
            print(f"[WARN] 归档伏笔失败: {e}")
            stats["errors"].append(f"归档伏笔失败: {e}")
            traceback.print_exc()

    # ---- LOCK ----
    for lock_data in _ensure_list(ops.get("lock")):
        try:
            from db.models import Event
            event = db.query(Event).filter(
                Event.chapter_start == lock_data["chapter_start"]
            ).first()
            if event:
                lock_event(db, event.id, lock_data["chapter_end"])
            stats["locked"] += 1
        except Exception as e:
            print(f"[WARN] 锁定事件失败: {e}")
            stats["errors"].append(f"锁定事件失败: {e}")
            traceback.print_exc()

    # ---- CONFLICTS ----
    for cf_data in _ensure_list(ops.get("conflicts")):
        try:
            add_conflict(db, **cf_data)
            stats["conflicts"] += 1
        except Exception as e:
            print(f"[WARN] 添加冲突失败: {e}")
            stats["errors"].append(f"添加冲突失败: {e}")
            traceback.print_exc()

    return stats


def _map_field_to_change_type(field: str) -> str:
    mapping = {
        "current_rank": "等级", "abilities": "能力", "equipment": "装备",
        "special_resources": "资源", "faction": "阵营", "current_position": "身份",
        "current_location": "位置", "life_death_status": "生死身体",
        "physical_status": "身体状态", "relationship_with_protagonist": "关系",
        "core_goal": "目标",
    }
    return mapping.get(field, "其他")
