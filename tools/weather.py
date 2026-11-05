# -*- coding: utf-8 -*-
"""工具集合：天气、空气质量、穿衣建议。

每个工具是一个普通函数，返回字符串（字符串内容会作为工具结果回传给模型）。
"""
import json
import logging

import httpx

logger = logging.getLogger(__name__)


def _value(field):
    """兼容 wttr.in 返回：字段可能是字符串，也可能是 [{"value": "..."}]。"""
    if isinstance(field, list):
        return field[0]["value"]
    return field


def _geocode_ok(city: str) -> tuple[bool, str]:
    """用地理编码验证城市，返回 (是否通过, 原因)。

    注意：地理编码会匹配任何字符串（"火星"会匹配到广东/湖南的同名小村庄），
    但真实城市/城镇在结果里带 population 字段，同名小村庄没有。
    所以要求"名字完全相同 且 有 population 数据"才算有效城市。
    """
    try:
        r = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 5, "language": "zh"},
            timeout=10,
        )
        r.raise_for_status()
        results = r.json().get("results") or []
        for item in results:
            if item.get("name") == city and item.get("population"):
                return True, ""
        return False, f"未找到城市「{city}」，请确认城市名称是否正确（需要是真实城市/县城）"
    except Exception:
        logger.warning("地理编码校验失败，跳过校验")
        return True, ""


def get_weather(city: str) -> str:
    """查询指定城市的实时天气。"""
    ok, reason = _geocode_ok(city)
    if not ok:
        return reason

    try:
        r = httpx.get(
            f"https://wttr.in/{city}",
            params={"format": "j1", "lang": "zh"},
            timeout=15,
        )
        r.raise_for_status()
        data = json.loads(r.text)

        # 城市有效性校验：wttr.in 对中文城市名会返回英文地名（如"济南"→"Hongjialou"），
        # 不能靠名字匹配。改为校验经纬度是否在合理范围 + 温度是否异常。
        area = data.get("nearest_area", [{}])[0]
        try:
            lat = float(_value(area.get("latitude", 0)))
            lon = float(_value(area.get("longitude", 0)))
        except (TypeError, ValueError):
            return f"未找到城市「{city}」"

        if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
            return f"未找到城市「{city}」，请确认城市名称是否正确"

        current = data["current_condition"][0]
        try:
            temp = float(current["temp_C"])
        except (TypeError, ValueError):
            return f"城市「{city}」天气数据异常，请稍后再试"
        if not (-60 <= temp <= 60):
            return f"「{city}」温度数据异常（{temp}°C），可能不是有效城市"

        desc = (
            current["lang_zh"][0]["value"]
            if "lang_zh" in current
            else current["weatherDesc"][0]["value"]
        )
        return json.dumps(
            {
                "城市": city,
                "天气": desc,
                "温度": f"{current['temp_C']}°C",
                "体感温度": f"{current['FeelsLikeC']}°C",
                "湿度": f"{current['humidity']}%",
                "风速": f"{current['windspeedKmph']} km/h",
            },
            ensure_ascii=False,
        )
    except httpx.TimeoutException:
        return "查询超时，请稍后再试"
    except Exception as e:
        logger.exception("天气查询失败")
        return f"天气查询失败：{type(e).__name__}"


def get_air_quality(city: str) -> str:
    """查询指定城市的空气质量（PM2.5、PM10）。"""
    try:
        geo = httpx.get(
            f"https://wttr.in/{city}",
            params={"format": "j1"},
            timeout=15,
        ).json()
        area = geo["nearest_area"][0]

        lat = area["latitude"]    # 实际返回是字符串
        lon = area["longitude"]

        r = httpx.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={"latitude": lat, "longitude": lon, "current": "pm2_5,pm10"},
            timeout=15,
        )
        r.raise_for_status()
        cur = r.json()["current"]
        return json.dumps(
            {
                "城市": city,
                "PM2.5": f"{cur['pm2_5']} μg/m³",
                "PM10": f"{cur['pm10']} μg/m³",
            },
            ensure_ascii=False,
        )
    except httpx.TimeoutException:
        return "空气质量查询超时，请稍后再试"
    except Exception as e:
        logger.exception("空气质量查询失败")
        return f"空气质量查询失败：{type(e).__name__}"


def suggest_clothes(temperature: float, weather: str) -> str:
    """根据温度和天气给出穿衣建议。"""
    try:
        temperature = float(str(temperature).replace("°C", "").strip())
    except (TypeError, ValueError):
        return "温度参数格式错误，应为数字"

    weather = (weather or "").lower()
    if "雨" in weather or "rain" in weather:
        base = "带伞"
    elif "雪" in weather or "snow" in weather:
        base = "防滑雪地靴、厚外套"
    elif "晴" in weather or "sun" in weather:
        base = "注意防晒"
    else:
        base = ""

    if temperature >= 28:
        return f"{base} 短袖短裤，注意补水"
    elif temperature >= 20:
        return f"{base} 短袖或薄长袖，舒适"
    elif temperature >= 12:
        return f"{base} 薄外套或长袖"
    elif temperature >= 5:
        return f"{base} 厚外套，围巾"
    else:
        return f"{base} 羽绒服，注意保暖"
