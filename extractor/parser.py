"""
LLM 梗概提取器 —— 核心解析逻辑
"""

import json
import re
import yaml
from typing import Optional, Tuple
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .prompt import SYSTEM_PROMPT
from db.repository import build_context_summary


def load_config(config_path: str = "config.yaml") -> dict:
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def create_llm(config: dict) -> ChatOpenAI:
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "deepseek")
    timeout = llm_config.get("request_timeout", 120)

    if provider == "openai" or provider == "deepseek":
        openai_cfg = llm_config.get("openai", {})
        return ChatOpenAI(
            api_key=openai_cfg.get("api_key", ""),
            base_url=openai_cfg.get("base_url", "https://api.deepseek.com/v1"),
            model=openai_cfg.get("model", "deepseek-chat"),
            temperature=openai_cfg.get("temperature", 0.3),
            max_tokens=openai_cfg.get("max_tokens", 16000),
            request_timeout=timeout,
            max_retries=llm_config.get("max_retries", 3),
        )
    elif provider == "tongyi":
        tongyi_cfg = llm_config.get("tongyi", {})
        return ChatOpenAI(
            api_key=tongyi_cfg.get("api_key", ""),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=tongyi_cfg.get("model", "qwen-plus"),
            temperature=tongyi_cfg.get("temperature", 0.3),
            max_tokens=tongyi_cfg.get("max_tokens", 16000),
            request_timeout=timeout,
            max_retries=llm_config.get("max_retries", 3),
        )
    elif provider == "zhipu":
        zhipu_cfg = llm_config.get("zhipu", {})
        return ChatOpenAI(
            api_key=zhipu_cfg.get("api_key", ""),
            base_url="https://open.bigmodel.cn/api/paas/v4",
            model=zhipu_cfg.get("model", "glm-4"),
            temperature=zhipu_cfg.get("temperature", 0.3),
            max_tokens=zhipu_cfg.get("max_tokens", 16000),
            request_timeout=timeout,
            max_retries=llm_config.get("max_retries", 3),
        )
    else:
        raise ValueError(f"不支持的 LLM provider: {provider}")


def parse_llm_response(response_text: str) -> Tuple[str, Optional[dict]]:
    json_pattern = r'```json\s*\n(.*?)\n```'
    matches = list(re.finditer(json_pattern, response_text, re.DOTALL))

    db_ops = None
    human_output = response_text

    if matches:
        last_match = matches[-1]
        try:
            json_str = last_match.group(1)
            db_ops = json.loads(json_str)
            human_output = response_text[:last_match.start()].strip()
        except json.JSONDecodeError:
            pass
    else:
        brace_pattern = r'\{[^{}]*"db_operations"[^{}]*\}'
        brace_matches = list(re.finditer(brace_pattern, response_text, re.DOTALL))
        if brace_matches:
            last = brace_matches[-1]
            start = last.start()
            depth = 0
            end = start
            for i, ch in enumerate(response_text[start:], start):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > start:
                try:
                    json_str = response_text[start:end]
                    db_ops = json.loads(json_str)
                    human_output = response_text[:start].strip()
                except json.JSONDecodeError:
                    pass

    return human_output, db_ops


def process_chapters(
    db_session,
    chapter_texts: list[Tuple[int, str]],
    chapter_range: str,
    author_notes: str = "",
    config_path: str = "config.yaml",
) -> Tuple[str, Optional[dict]]:
    config = load_config(config_path)
    llm = create_llm(config)
    protagonist_name = config.get("novel", {}).get("protagonist", "")

    context = build_context_summary(db_session)

    chapter_content = "\n\n".join(
        f"=== 第{ch_num}章 ===\n{text}" if not text.startswith("===") else text
        for ch_num, text in chapter_texts
    )

    user_message_parts = [
        f"## 已有数据库状态\n{context}",
        f"## 本次提交章节范围\n{chapter_range}",
        f"## 本次正文\n{chapter_content}",
    ]
    if protagonist_name:
        user_message_parts.insert(2, f"## 主角\n主角名：{protagonist_name}")
    if author_notes:
        user_message_parts.append(f"## 作者说明\n{author_notes}")

    user_message = "\n\n---\n\n".join(user_message_parts)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    response_text = response.content if hasattr(response, 'content') else str(response)

    human_output, db_ops = parse_llm_response(response_text)

    return human_output, db_ops


def process_chapters_quick(
    db_session,
    chapter_texts: list[Tuple[int, str]],
    chapter_range: str,
    config_path: str = "config.yaml",
) -> str:
    config = load_config(config_path)
    llm = create_llm(config)

    context = build_context_summary(db_session)

    chapter_content = "\n\n".join(
        f"=== 第{ch_num}章 ===\n{text}"
        for ch_num, text in chapter_texts
    )

    quick_prompt = SYSTEM_PROMPT + """

你现在处于【快速阅读模式】。
作者不是要求维护数据库，而是要求快速总结。请优先输出精简版：

第X-X章「事件名称」
事件状态：
叙事类型：
故事内容
关键结果
新增设定
重要角色
状态变化
伏笔
角色关系图

此模式仍然必须遵守：禁止脑补、当前状态与历史状态分离、信息可信性质、事件段划分、历史锁定。
不要输出数据库操作 JSON。
"""

    user_message = f"""## 已有数据库状态
{context}

## 本次章节范围
{chapter_range}

## 本次正文
{chapter_content}"""

    messages = [
        SystemMessage(content=quick_prompt),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    return response.content if hasattr(response, 'content') else str(response)
