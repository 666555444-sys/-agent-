# -*- coding: utf-8 -*-
"""LLM 客户端与 Agent 循环。"""
import json
import logging
import os

from openai import OpenAI

from tools import TOOLS_MAP, TOOLS_SCHEMA

logger = logging.getLogger(__name__)

MODEL = os.environ.get("WEATHER_AGENT_MODEL", "qwen3.8-flash")
BASE_URL = os.environ.get(
    "WEATHER_AGENT_BASE_URL",
    "https://cn-beijing.maas.qianwenaiapi.com/compatible-mode/v1",
)


def build_client() -> OpenAI:
    """创建 LLM 客户端，密钥从环境变量读取。"""
    key = os.environ.get("QWEN_API_KEY") or os.environ.get("OPENAI")
    if not key:
        raise SystemExit("请先设置环境变量 QWEN_API_KEY（或 OPENAI）")
    return OpenAI(api_key=key, base_url=BASE_URL)


def run_agent(client: OpenAI, messages: list, max_steps: int = 5) -> str:
    """Agent 循环：模型要求调工具就执行，直到模型给出最终回答。

    max_steps 防止工具调用死循环。
    """
    for step in range(1, max_steps + 1):
        logger.debug("第 %d 轮", step)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            messages.append(msg)
            return msg.content or ""

        messages.append(msg)
        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            logger.info("调用工具 %s，参数 %s", name, args)

            try:
                result = TOOLS_MAP[name](**args)
            except KeyError:
                result = f"错误：没有名为 {name} 的工具"
            except Exception as e:
                logger.exception("工具执行失败")
                result = f"工具执行失败：{type(e).__name__}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                }
            )

    logger.warning("达到最大步数 %d，停止", max_steps)
    return "执行步数过多，已停止"
