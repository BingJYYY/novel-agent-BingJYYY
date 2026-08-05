"""
Web 仪表盘 —— Flask 实时查看数据库 + 在线提交章节
"""

import json
import os
import sys
import webbrowser
import threading
from pathlib import Path

from flask import Flask, render_template, jsonify, request

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 延迟导入重型模块，按需加载（启动速度重大优化）
_init_db = None
_models_cache = None
_repo_cache = None
_parser_cache = None
_applier_cache = None


def _lazy_models():
    global _models_cache
    if _models_cache is None:
        from db import models as _m
        _models_cache = _m
    return _models_cache


def _lazy_init_db(db_path="novel.db"):
    from db.models import init_db
    return init_db(db_path)


def _lazy_repo():
    global _repo_cache
    if _repo_cache is None:
        from db import repository as _r
        _repo_cache = _r
    return _repo_cache


def _lazy_parser():
    global _parser_cache
    if _parser_cache is None:
        from extractor import parser as _p
        _parser_cache = _p
    return _parser_cache


def _lazy_applier():
    global _applier_cache
    if _applier_cache is None:
        from extractor import applier as _a
        _applier_cache = _a
    return _applier_cache

app = Flask(__name__, template_folder="templates", static_folder="static")

DB_PATH = "novel.db"
CONFIG_PATH = "config.yaml"
NOVELS_FILE = "novels.json"
_current_novel = None  # 当前小说名，None 表示默认


def _check_first_run():
    """检查是否首次运行，输出提示"""
    import os as _os
    if not _os.path.exists(CONFIG_PATH):
        return
    yaml = None
    try:
        import yaml as _yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            yaml = _yaml.safe_load(f) or {}
    except Exception:
        return
    llm = yaml.get("llm", {})
    provider = llm.get("provider", "deepseek")
    _cfg_key = "openai" if provider in ("deepseek", "openai") else provider
    key = (llm.get(_cfg_key, {}) or {}).get("api_key", "")
    if not key or key == "your-api-key-here":
        print("\n  [提示] 未检测到 API Key，打开后在弹窗中填写即可。\n")


def _load_novels():
    """加载小说列表"""
    try:
        with open(NOVELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_novels(data):
    with open(NOVELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_db():
    global _current_novel
    if _current_novel:
        return _lazy_init_db(f"novel-{_current_novel}.db")
    return _lazy_init_db(DB_PATH)


# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    _check_first_run()
    return render_template("dashboard.html")


# ============================================================
# 配置 API（在页面内直接设置 API Key）
# ============================================================

@app.route("/api/config")
def api_config():
    """获取当前配置（API Key 脱敏后返回）"""
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return jsonify({"ok": True, "config": {"provider": "deepseek", "model": "deepseek-chat", "api_key": "", "has_key": False}})

    llm = config.get("llm", {})
    provider = llm.get("provider", "deepseek")
    _cfg_key = "openai" if provider in ("deepseek", "openai") else provider
    provider_cfg = llm.get(_cfg_key, {})
    api_key = provider_cfg.get("api_key", "")

    return jsonify({
        "ok": True,
        "config": {
            "provider": provider,
            "model": provider_cfg.get("model", ""),
            "api_key": _mask_key(api_key),
            "has_key": bool(api_key and api_key != "your-api-key-here"),
        }
    })


@app.route("/api/config", methods=["POST"])
def api_config_save():
    """保存配置（API Key 等）"""
    import yaml
    data = request.get_json() or {}
    api_key = (data.get("api_key") or "").strip()
    provider = (data.get("provider") or "deepseek").strip()
    model = (data.get("model") or "deepseek-chat").strip()

    if not api_key:
        return jsonify({"ok": False, "error": "API Key 不能为空"})

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        # 首次保存：从模板复制完整结构
        config = {}
        example_path = "config.example.yaml"
        if os.path.exists(example_path):
            with open(example_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

    config.setdefault("llm", {})["provider"] = provider
    _cfg_key = "openai" if provider in ("deepseek", "openai") else provider
    config["llm"].setdefault(_cfg_key, {})
    config["llm"][_cfg_key]["api_key"] = api_key
    if model:
        config["llm"][_cfg_key]["model"] = model
    if provider == "deepseek":
        config["llm"][_cfg_key].setdefault("base_url", "https://api.deepseek.com/v1")
        config["llm"][_cfg_key].setdefault("temperature", 0.3)
        config["llm"][_cfg_key].setdefault("max_tokens", 16000)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return jsonify({"ok": True, "message": "配置已保存"})


def _mask_key(key: str) -> str:
    if not key or len(key) <= 8:
        return key
    return key[:5] + "****" + key[-3:]


# ============================================================
# 数据查询 API
# ============================================================

@app.route("/api/status")
def api_status():
    db = get_db()
    try:
        summary = _lazy_repo().build_context_summary(db)
        return jsonify({"ok": True, "summary": summary})
    finally:
        db.close()


@app.route("/api/characters")
def api_characters():
    db = get_db()
    try:
        models = _lazy_models()
        chars = db.query(models.Character).order_by(models.Character.is_protagonist.desc(), models.Character.name).all()
        result = []
        for c in chars:
            aliases = [a.alias for a in c.aliases]
            status_changes = [
                {"type": sc.change_type, "field": sc.field_name,
                 "old": sc.old_value, "new": sc.new_value,
                 "chapter": sc.chapter_range}
                for sc in c.status_changes
            ]
            result.append({
                "id": c.id, "name": c.name, "is_protagonist": c.is_protagonist,
                "activity_status": c.activity_status, "identity": c.identity or "",
                "gender": c.gender or "", "age": c.age or "",
                "current_rank": c.current_rank or "", "faction": c.faction or "",
                "current_position": c.current_position or "",
                "current_location": c.current_location or "",
                "life_death_status": c.life_death_status or "",
                "physical_status": c.physical_status or "",
                "personality": c.personality or "",
                "core_goal": c.core_goal or "",
                "relationship_with_protagonist": c.relationship_with_protagonist or "",
                "info_source": c.info_source or "",
                "first_appearance": c.first_appearance or "",
                "aliases": aliases,
                "contract_binding_status": c.contract_binding_status or "",
                "status_changes": status_changes,
            })
        return jsonify({"ok": True, "characters": result})
    finally:
        db.close()


@app.route("/api/events")
def api_events():
    db = get_db()
    try:
        models = _lazy_models()
        events = db.query(models.Event).order_by(models.Event.sort_order).all()
        result = []
        for e in events:
            result.append({
                "id": e.id, "name": e.name,
                "chapter_start": e.chapter_start, "chapter_end": e.chapter_end,
                "status": e.status, "is_locked": e.is_locked,
                "narrative_type": e.narrative_type or "",
                "narrative_subtype": e.narrative_subtype or "",
                "story_content": e.story_content or "",
                "key_results": e.key_results or "[]",
            })
        return jsonify({"ok": True, "events": result})
    finally:
        db.close()


@app.route("/api/settings")
def api_settings():
    db = get_db()
    try:
        models = _lazy_models()
        settings = db.query(models.WorldSetting).order_by(models.WorldSetting.category, models.WorldSetting.name).all()
        result = []
        for s in settings:
            result.append({
                "id": s.id, "category": s.category, "name": s.name,
                "content": s.content, "first_appearance": s.first_appearance or "",
                "last_confirmed": s.last_confirmed or "",
                "credibility": s.credibility or "",
                "notes": s.notes or "",
            })
        return jsonify({"ok": True, "settings": result})
    finally:
        db.close()


@app.route("/api/foreshadowings")
def api_foreshadowings():
    db = get_db()
    try:
        models = _lazy_models()
        fs_list = db.query(models.Foreshadowing).order_by(models.Foreshadowing.first_appearance).all()
        result = []
        for f in fs_list:
            result.append({
                "id": f.id, "name": f.name,
                "fs_type": f.fs_type, "first_appearance": f.first_appearance or "",
                "last_advanced": f.last_advanced or "",
                "current_status": f.current_status,
                "known_info": f.known_info or "",
                "unresolved_part": f.unresolved_part or "",
                "credibility": f.credibility or "",
            })
        return jsonify({"ok": True, "foreshadowings": result})
    finally:
        db.close()


@app.route("/api/timeline")
def api_timeline():
    db = get_db()
    try:
        models = _lazy_models()
        entries = db.query(models.TimelineEntry).order_by(models.TimelineEntry.sort_order).all()
        result = []
        for t in entries:
            result.append({
                "id": t.id, "chapter_range": t.chapter_range,
                "time_precision": t.time_precision, "time_value": t.time_value or "",
                "event_description": t.event_description,
                "sort_order": t.sort_order,
            })
        return jsonify({"ok": True, "timeline": result})
    finally:
        db.close()


@app.route("/api/conflicts")
def api_conflicts():
    db = get_db()
    try:
        models = _lazy_models()
        conflicts = db.query(models.SettingConflict).order_by(models.SettingConflict.created_at.desc()).all()
        result = []
        for c in conflicts:
            result.append({
                "id": c.id, "conflict_content": c.conflict_content,
                "old_info": c.old_info or "", "new_info": c.new_info or "",
                "conflict_type": c.conflict_type or "",
                "possible_reason": c.possible_reason or "",
                "needs_author_confirmation": c.needs_author_confirmation,
                "is_resolved": c.is_resolved,
            })
        return jsonify({"ok": True, "conflicts": result})
    finally:
        db.close()


# ============================================================
# 章节提交 API
# ============================================================

@app.route("/api/submit", methods=["POST"])
def api_submit():
    """提交章节进行分析"""
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"ok": False, "error": "请提供章节正文"}), 400

    content = data["content"]
    chapter_range = data.get("chapter_range", "")
    notes = data.get("notes", "")
    mode = data.get("mode", "full")  # full 或 quick

    if not chapter_range:
        chapter_range = "新章节"

    db = get_db()
    try:
        if mode == "quick":
            chapter_texts = _parse_chapters(content)
            result_text = _lazy_parser().process_chapters_quick(db, chapter_texts, chapter_range, CONFIG_PATH)
            db_ops = None
        else:
            chapter_texts = _parse_chapters(content)
            result_text, db_ops = _lazy_parser().process_chapters(
                db, chapter_texts, chapter_range, notes, CONFIG_PATH
            )

        # 应用数据库操作
        stats = {}
        if db_ops:
            stats = _lazy_applier().apply_db_operations(db, db_ops)

        # 保存会话记录
        _lazy_repo().create_session_record(db, chapter_range, result_text,
                              json.dumps(db_ops, ensure_ascii=False) if db_ops else "{}")
        db.commit()

        return jsonify({
            "ok": True,
            "result": result_text,
            "stats": stats,
        })
    except Exception as e:
        import traceback
        db.rollback()
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e),
                         "traceback": traceback.format_exc()}), 500
    finally:
        db.close()


def _parse_chapters(content: str) -> list:
    """从文本中解析章节"""
    import re
    chapter_pattern = re.compile(
        r'(?:^|\n)(?:===?\s*)?第(\d+)(?:[-–—](\d+))?章[ \t]*(.*?)\s*\n',
        re.MULTILINE
    )
    matches = list(chapter_pattern.finditer(content))

    if not matches:
        return [(1, content.strip())]

    chapters = []
    for i, match in enumerate(matches):
        ch_start = int(match.group(1))
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        ch_text = content[start_pos:end_pos].strip()
        chapters.append((ch_start, ch_text))

    return chapters


# ============================================================
# 批量导入 API
# ============================================================

@app.route("/api/import", methods=["POST"])
def api_import():
    """整本导入 —— 自动分章，逐批分析，支持断点续传"""
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"ok": False, "error": "请提供小说正文"}), 400

    content = data["content"]
    batch_size = data.get("batch_size", 3)  # 每批几章
    notes = data.get("notes", "")

    # 解析所有章节
    all_chapters = _parse_chapters(content)

    if not all_chapters:
        return jsonify({"ok": False, "error": "未检测到章节内容"}), 400

    # 检测数据库中已有数据的最大章节号，实现断点续传
    db_check = get_db()
    models = _lazy_models()
    existing_events = db_check.query(models.Event).all()
    max_chapter = 0
    for evt in existing_events:
        end = evt.chapter_end or evt.chapter_start
        if end and end > max_chapter:
            max_chapter = end
    db_check.close()

    # 过滤已导入的章节
    if max_chapter > 0:
        all_chapters = [(ch, txt) for ch, txt in all_chapters if ch > max_chapter]
        if not all_chapters:
            return jsonify({"ok": True, "total_chapters": 0, "total_batches": 0,
                            "results": [], "total_stats": {"added": 0, "updated": 0, "archived": 0, "locked": 0, "conflicts": 0},
                            "skipped": f"数据库已覆盖到第{max_chapter}章，无需重复导入"})

    total_chapters = len(all_chapters)
    batches = []
    for i in range(0, total_chapters, batch_size):
        batch = all_chapters[i:i + batch_size]
        ch_nums = [str(c[0]) for c in batch]
        if len(ch_nums) == 1:
            ch_range = f"第{ch_nums[0]}章"
        else:
            ch_range = f"第{ch_nums[0]}-{ch_nums[-1]}章"
        batches.append((ch_range, batch))

    db = get_db()
    all_results = []
    total_stats = {"added": 0, "updated": 0, "archived": 0, "locked": 0, "conflicts": 0}

    try:
        for idx, (ch_range, batch) in enumerate(batches):
            success = False
            last_error = None
            for attempt in range(2):  # 最多重试1次
                try:
                    result_text, db_ops = _lazy_parser().process_chapters(
                        db, batch, ch_range, notes, CONFIG_PATH
                    )
                    stats = {}
                    if db_ops:
                        stats = _lazy_applier().apply_db_operations(db, db_ops)
                        for k in total_stats:
                            total_stats[k] += stats.get(k, 0)
                    _lazy_repo().create_session_record(db, ch_range, result_text,
                                          json.dumps(db_ops, ensure_ascii=False) if db_ops else "{}")
                    db.commit()
                    all_results.append({
                        "batch": idx + 1, "total_batches": len(batches),
                        "chapter_range": ch_range, "result": result_text, "stats": stats,
                    })
                    print(f"  第 {idx+1}/{len(batches)} 批完成：{ch_range}")
                    success = True
                    break
                except Exception as batch_err:
                    last_error = batch_err
                    db.rollback()
                    if attempt == 0:
                        print(f"  第 {idx+1}/{len(batches)} 批失败，重试中：{ch_range} - {batch_err}")
                        import time
                        time.sleep(3)
                    else:
                        import traceback
                        traceback.print_exc()
                        print(f"  第 {idx+1}/{len(batches)} 批重试仍失败，跳过：{ch_range}")
            if not success:
                all_results.append({
                    "batch": idx + 1, "total_batches": len(batches),
                    "chapter_range": ch_range, "result": "", "stats": {},
                    "error": str(last_error),
                })

        return jsonify({
            "ok": True,
            "total_chapters": total_chapters,
            "total_batches": len(batches),
            "results": all_results,
            "total_stats": total_stats,
            "skipped": max_chapter,
        })

    except Exception as e:
        import traceback
        db.rollback()
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e),
                         "traceback": traceback.format_exc()}), 500
    finally:
        db.close()


# ============================================================
# 小说管理 API
# ============================================================

@app.route("/api/novels")
def api_novels():
    """列出所有小说"""
    novels = _load_novels()
    return jsonify({
        "ok": True,
        "current": _current_novel or "默认小说",
        "novels": [{"name": k, "title": v.get("title", k), "protagonist": v.get("protagonist", "")} for k, v in novels.items()],
    })


@app.route("/api/novels/switch", methods=["POST"])
def api_switch_novel():
    """切换小说"""
    global _current_novel
    data = request.get_json()
    name = data.get("name", "")
    if name == "默认小说" or not name:
        _current_novel = None
    else:
        _current_novel = name
    return jsonify({"ok": True, "current": _current_novel or "默认小说"})


@app.route("/api/novels/create", methods=["POST"])
def api_create_novel():
    """创建新小说"""
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"ok": False, "error": "请输入小说名"}), 400

    novels = _load_novels()
    if name in novels:
        return jsonify({"ok": False, "error": "该小说已存在"}), 400

    novels[name] = {
        "title": data.get("title", name),
        "protagonist": data.get("protagonist", ""),
        "created_at": str(__import__("datetime").datetime.now()),
    }
    _save_novels(novels)

    global _current_novel
    _current_novel = name
    return jsonify({"ok": True, "current": name})


@app.route("/api/novels/delete", methods=["POST"])
def api_delete_novel():
    """删除小说"""
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"ok": False, "error": "请指定要删除的小说"}), 400
    if name == "默认小说":
        return jsonify({"ok": False, "error": "不能删除默认小说"}), 400

    novels = _load_novels()
    if name not in novels:
        return jsonify({"ok": False, "error": "小说不存在"}), 404

    # 如果删除的是当前使用的小说，先切回默认
    global _current_novel
    current_name = _current_novel or "默认小说"
    if name == current_name:
        _current_novel = None

    # 从列表移除 + 删除数据库
    del novels[name]
    _save_novels(novels)

    import os
    db_file = f"novel-{name}.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass

    return jsonify({"ok": True, "deleted": name, "current": _current_novel or "默认小说"})


# ============================================================
# 启动服务
# ============================================================

def run_server(port: int = 5000, db_path: str = "novel.db", open_browser: bool = True):
    global DB_PATH
    DB_PATH = db_path

    url = f"http://127.0.0.1:{port}"
    print(f"\n  网文数据库仪表盘已启动！")
    print(f"  浏览器访问: {url}")
    print(f"  按 Ctrl+C 停止服务\n")

    if open_browser:
        def _open():
            import time
            time.sleep(1.5)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    app.run(host="127.0.0.1", port=port, debug=False)
