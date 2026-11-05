# -*- coding: utf-8 -*-
"""天气 Agent —— 入口。

用法：
    python main.py
"""
import logging
import sys

from llm import build_client, run_agent


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("agent.log", encoding="utf-8")],
    )

    client = build_client()
    messages = [
        {"role": "system", "content": "你是一个天气助手，用简洁中文回答，可以给穿衣建议。"}
    ]

    print("天气 Agent 已启动，输入 q 退出")
    while True:
        try:
            q = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见")
            break

        if q in ("q", "exit", "quit"):
            print("再见")
            break
        if not q:
            continue

        messages.append({"role": "user", "content": q})
        try:
            print("AI：", run_agent(client, messages))
        except Exception as e:
            logging.exception("请求失败")
            print("出错了：", e)
            messages.pop()  # 撤回这句，避免历史里留下没回答的坑


if __name__ == "__main__":
    sys.exit(main())
