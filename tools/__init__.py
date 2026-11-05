# -*- coding: utf-8 -*-
"""工具注册表：名字 → 实现。agent 循环按名字取函数执行。"""
from tools.weather import get_air_quality, get_weather, suggest_clothes

# 名字必须和 schema 里 function.name 完全一致
TOOLS_MAP = {
    "get_weather": get_weather,
    "get_air_quality": get_air_quality,
    "suggest_clothes": suggest_clothes,
}


# 给模型看的工具说明书（官方 Function Calling 格式）
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气（温度、湿度、风速）。用户问天气、气温、下雨、风力时调用。不用于查询空气质量。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如：济南、北京"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_air_quality",
            "description": "查询指定城市的空气质量（PM2.5、PM10）。用户问空气、雾霾、污染时调用。不用于查询天气预报。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如：济南、北京"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_clothes",
            "description": "根据气温和天气给穿衣建议。必须使用已查询到的真实气温和天气描述，不能凭空猜测。",
            "parameters": {
                "type": "object",
                "properties": {
                    "temperature": {"type": "number", "description": "摄氏温度，如 25"},
                    "weather": {"type": "string", "description": "天气描述，如：晴、雨、多云"},
                },
                "required": ["temperature", "weather"],
            },
        },
    },
]
