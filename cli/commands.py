"""
CLI 命令 —— 基于 Click 的命令行交互界面
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from sqlalchemy.orm import Session

from db.models import init_db
from db.repository import (
    get_all_characters, get_all_events, get_all_settings,
    get_all_foreshadowings, get_timeline, get_unresolved_conflicts,
    get_protagonist, build_context_summary, create_session_record,
    upsert_character,
)
from extractor.parser import process_chapters, process_chapters_quick
from extractor.applier import apply_db_operations


def get_db_path(config_path: str = "config.yaml") -> str:
    cfg = load_config(config_path)
    return cfg.get("database", {}).get("path", "novel.db")


def load_config(path: str = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        _init_config_from_example(p)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def _init_config_from_example(config_path: Path):
    example = Path("config.example.yaml")
    if example.exists():
        import shutil
        shutil.copy(example, config_path)
        print(f"[提示] 已自动生成 {config_path}，请打开该文件填入你的 API Key 后重新运行。")
        return True
    return False


def save_config(config: dict, path: str = "config.yaml"):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


@click.group()
@click.pass_context
def cli(ctx):
    """小说动态大纲与快速阅读智能体"""
    ctx.ensure_object(dict)


@cli.command()
@click.option("-f", "--file", "file_path", type=click.Path(exists=True),
              help="从文件读取章节正文")
@click.option("-c", "--chapters", "chapter_range", default="",
              help="章节范围，如 '第5-7章'")
@click.option("-n", "--notes", "author_notes", default="",
              help="作者额外说明")
@click.option("--protagonist", default="",
              help="设置/更新主角名")
def submit(file_path, chapter_range, author_notes, protagonist):
    """提交新章节进行分析"""
    config_path = "config.yaml"
    db_path = get_db_path(config_path)
    db = init_db(db_path)

    if protagonist:
        config = load_config(config_path)
        config.setdefault("novel", {})["protagonist"] = protagonist
        save_config(config)
        upsert_character(db, protagonist, is_protagonist=True)
        db.commit()
        click.echo(f"已设置主角：{protagonist}")

    chapter_texts = []
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        chapter_texts = _parse_chapters(content)
    else:
        click.echo("请粘贴章节正文（输入 END 结束）：")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        content = "\n".join(lines)
        chapter_texts = _parse_chapters(content)

    if not chapter_texts:
        click.echo("错误：未检测到有效章节内容。", err=True)
        db.close()
        return

    if not chapter_range:
        ch_nums = [str(c[0]) for c in chapter_texts]
        chapter_range = f"第{ch_nums[0]}章" if len(ch_nums) == 1 else f"第{ch_nums[0]}-{ch_nums[-1]}章"

    click.echo(f"\n正在分析 {chapter_range}（{len(chapter_texts)} 个章节）...\n")

    try:
        human_output, db_ops = process_chapters(
            db, chapter_texts, chapter_range, author_notes, config_path
        )
        click.echo("=" * 60)
        click.echo(human_output)
        click.echo("=" * 60)

        if db_ops:
            stats = apply_db_operations(db, db_ops)
            click.echo(f"\n数据库已更新：新增 {stats['added']}，更新 {stats['updated']}，"
                       f"归档 {stats['archived']}，锁定事件 {stats['locked']}，"
                       f"冲突 {stats['conflicts']}")
            if stats.get("errors"):
                click.echo(f"\n⚠ 以下操作失败：")
                for err in stats["errors"]:
                    click.echo(f"  - {err}")
        else:
            click.echo("\n未检测到数据库操作 JSON，已保存原始输出。")

        create_session_record(db, chapter_range, human_output,
                              json.dumps(db_ops, ensure_ascii=False) if db_ops else "{}")
        db.commit()
    except Exception as e:
        click.echo(f"处理出错：{e}", err=True)
        db.rollback()
    finally:
        db.close()


@cli.command()
@click.option("-f", "--file", "file_path", type=click.Path(exists=True),
              help="从文件读取章节正文")
def quick(file_path):
    """快速阅读模式 —— 快速总结章节，不维护数据库"""
    config_path = "config.yaml"
    db_path = get_db_path(config_path)
    db = init_db(db_path)

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        chapter_texts = _parse_chapters(content)
    else:
        click.echo("请粘贴章节正文（输入 END 结束）：")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        content = "\n".join(lines)
        chapter_texts = _parse_chapters(content)

    if not chapter_texts:
        click.echo("错误：未检测到有效章节内容。", err=True)
        return

    ch_nums = [str(c[0]) for c in chapter_texts]
    chapter_range = f"第{ch_nums[0]}-{ch_nums[-1]}章" if len(ch_nums) > 1 else f"第{ch_nums[0]}章"
    click.echo(f"\n快速阅读 {chapter_range}...\n")

    try:
        result = process_chapters_quick(db, chapter_texts, chapter_range, config_path)
        click.echo(result)
    except Exception as e:
        click.echo(f"处理出错：{e}", err=True)
    finally:
        db.close()


@cli.command()
@click.argument("query_type", type=click.Choice(
    ["characters", "events", "settings", "foreshadowings", "timeline",
     "conflicts", "status", "full"]
))
@click.option("--category", "-c", default="", help="设定分类筛选")
@click.option("--status-filter", "-s", default="", help="状态筛选")
def query(query_type, category, status_filter):
    """查询数据库"""
    config_path = "config.yaml"
    db_path = get_db_path(config_path)
    db = init_db(db_path)

    try:
        if query_type == "characters":
            _print_characters(get_all_characters(db))
        elif query_type == "events":
            _print_events(get_all_events(db))
        elif query_type == "settings":
            _print_settings(get_all_settings(db, category or None))
        elif query_type == "foreshadowings":
            _print_foreshadowings(get_all_foreshadowings(db, status_filter or None))
        elif query_type == "timeline":
            _print_timeline(get_timeline(db))
        elif query_type == "conflicts":
            _print_conflicts(get_unresolved_conflicts(db))
        elif query_type == "status":
            click.echo(build_context_summary(db))
        elif query_type == "full":
            _print_full_outline(db)
    finally:
        db.close()


@cli.command()
@click.option("--provider", type=click.Choice(["deepseek", "tongyi", "zhipu"]), help="设置 LLM provider")
@click.option("--api-key", help="设置 API Key")
@click.option("--model", help="设置模型名称")
@click.option("--show", is_flag=True, help="显示当前配置")
def config(provider, api_key, model, show):
    """配置 LLM 参数"""
    config_path = "config.yaml"
    cfg = load_config(config_path)
    if show:
        click.echo(yaml.dump(cfg, allow_unicode=True, default_flow_style=False))
        return
    if provider:
        cfg.setdefault("llm", {})["provider"] = provider
    if api_key:
        provider_name = cfg.get("llm", {}).get("provider", "openai")
        cfg.setdefault("llm", {}).setdefault(provider_name, {})["api_key"] = api_key
    if model:
        provider_name = cfg.get("llm", {}).get("provider", "openai")
        cfg.setdefault("llm", {}).setdefault(provider_name, {})["model"] = model
    save_config(cfg, config_path)
    click.echo("配置已更新。")


# ============================================================
# 辅助函数
# ============================================================

def _parse_chapters(content: str) -> list:
    import re
    chapter_pattern = re.compile(
        r'(?:^|\n)(?:===?\s*)?第(\d+)(?:[-–—](\d+))?章\s*(?:===?)?\s*?\n',
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


def _print_characters(chars):
    click.echo(f"\n{'='*60}")
    click.echo(f"角色数据库（共 {len(chars)} 人）")
    click.echo(f"{'='*60}\n")
    for c in chars:
        status_mark = ("★" if c.is_protagonist else "") + c.activity_status
        click.echo(f"[{status_mark}] {c.name}")
        click.echo(f"  身份：{c.identity or '未知'}")
        click.echo(f"  等级：{c.current_rank or '未知'}")
        click.echo(f"  阵营：{c.faction or '无'}")
        click.echo(f"  位置：{c.current_location or '未知'}")
        click.echo(f"  状态：{c.life_death_status} | {c.physical_status or '正常'}")
        click.echo(f"  首次登场：{c.first_appearance or '未知'}")
        if c.aliases:
            click.echo(f"  别名：{', '.join(a.alias for a in c.aliases)}")
        click.echo()


def _print_events(events):
    click.echo(f"\n{'='*60}")
    click.echo(f"事件大纲（共 {len(events)} 个）")
    click.echo(f"{'='*60}\n")
    for e in events:
        lock_mark = "🔒" if e.is_locked else ""
        click.echo(f"{lock_mark} 第{e.chapter_start}-{e.chapter_end or '?'}章「{e.name}」[{e.status}]")
        if e.narrative_type:
            click.echo(f"  类型：{e.narrative_type}" + (f" - {e.narrative_subtype}" if e.narrative_subtype else ""))
        if e.story_content:
            click.echo(f"  内容：{e.story_content[:120]}...")
        click.echo()


def _print_settings(settings):
    click.echo(f"\n{'='*60}")
    click.echo(f"世界观设定库（共 {len(settings)} 条）")
    click.echo(f"{'='*60}\n")
    current_cat = ""
    for s in settings:
        if s.category != current_cat:
            current_cat = s.category
            click.echo(f"\n【{current_cat}】")
        click.echo(f"  [{s.credibility}] {s.name}")
        click.echo(f"    {s.content[:100]}...")
        click.echo(f"    首次：{s.first_appearance or '?'} | 最近确认：{s.last_confirmed or '?'}")


def _print_foreshadowings(fs_list):
    click.echo(f"\n{'='*60}")
    click.echo(f"伏笔数据库（共 {len(fs_list)} 条）")
    click.echo(f"{'='*60}\n")
    for f in fs_list:
        status_icon = {"未解决": "❓", "推进": "🔍", "已回收": "✅"}.get(f.current_status, "❓")
        click.echo(f"{status_icon} [{f.fs_type}] {f.name}")
        click.echo(f"  状态：{f.current_status}")
        click.echo(f"  首次出现：第{f.first_appearance}章")
        if f.last_advanced:
            click.echo(f"  最近推进：第{f.last_advanced}章")
        if f.known_info:
            click.echo(f"  已知信息：{f.known_info[:100]}...")
        click.echo()


def _print_timeline(entries):
    click.echo(f"\n{'='*60}")
    click.echo(f"时间线（共 {len(entries)} 条）")
    click.echo(f"{'='*60}\n")
    for e in entries:
        click.echo(f"[{e.time_precision}] {e.time_value}——{e.event_description}")


def _print_conflicts(conflicts):
    if not conflicts:
        click.echo("没有未解决的设定冲突。")
        return
    click.echo(f"\n{'='*60}")
    click.echo(f"未解决设定冲突（共 {len(conflicts)} 条）")
    click.echo(f"{'='*60}\n")
    for c in conflicts:
        click.echo(f"⚠️  [{c.conflict_type}] {c.conflict_content}")
        if c.old_info:
            click.echo(f"  旧信息：{c.old_info}")
        if c.new_info:
            click.echo(f"  新信息：{c.new_info}")
        if c.needs_author_confirmation:
            click.echo(f"  ⚡ 需要作者确认")
        click.echo()


def _print_full_outline(db: Session):
    click.echo("\n" + "=" * 60)
    click.echo("完整动态大纲")
    click.echo("=" * 60)
    protagonist = get_protagonist(db)
    if protagonist:
        click.echo(f"\n## 当前剧情快照\n")
        click.echo(f"主角：{protagonist.name}")
        click.echo(f"  等级：{protagonist.current_rank or '未知'}")
        click.echo(f"  职业：{protagonist.identity or '未知'}")
        click.echo(f"  阵营：{protagonist.faction or '无'}")
        click.echo(f"  位置：{protagonist.current_location or '未知'}")
        click.echo(f"  身体状态：{protagonist.physical_status or '正常'}")
        click.echo(f"  当前目标：{protagonist.core_goal or '未知'}")
    click.echo("\n## 全部事件大纲\n")
    _print_events(get_all_events(db))
    click.echo("\n## 角色数据库\n")
    _print_characters(get_all_characters(db))
    click.echo("\n## 世界观设定库\n")
    _print_settings(get_all_settings(db))
    click.echo("\n## 伏笔数据库\n")
    _print_foreshadowings(get_all_foreshadowings(db))
    click.echo("\n## 时间线\n")
    _print_timeline(get_timeline(db))
    click.echo("\n## 未解决设定冲突\n")
    _print_conflicts(get_unresolved_conflicts(db))


@cli.command()
@click.option("-p", "--port", default=5000, help="Web 服务端口（默认: 5000）")
def serve(port):
    """启动 Web 仪表盘，浏览器实时查看数据库"""
    from web.server import run_server
    run_server(port=port)


if __name__ == "__main__":
    cli()
