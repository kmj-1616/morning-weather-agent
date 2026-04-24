import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
NEARBY_STATION_URL = "https://apis.data.go.kr/B552584/MsrstnInfoInqireSvc/getNearbyMsrstnList"


def find_nearest_station(tm_x: float, tm_y: float, airkorea_key: str) -> str:
    params = {
        "serviceKey": airkorea_key,
        "returnType": "json",
        "tmX": tm_x,
        "tmY": tm_y,
        "ver": "1.1",
    }
    resp = requests.get(NEARBY_STATION_URL, params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json()["response"]["body"]["items"]
    if not items:
        raise ValueError("근처 측정소를 찾을 수 없습니다.")
    station = items[0]["stationName"]
    logger.info(f"가장 가까운 측정소: {station}")
    return station
GRADE_MAP = {"1": "좋음", "2": "보통", "3": "나쁨", "4": "매우나쁨"}


def _safe_int(val) -> int | None:
    if val is None or str(val).strip() in ("-", ""):
        return None
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return None


def fetch(config: dict, station_name: str, location_name: str) -> dict:
    params = {
        "serviceKey": config["api_keys"]["airkorea_service_key"],
        "returnType": "json",
        "numOfRows": 1,
        "pageNo": 1,
        "stationName": station_name,
        "dataTerm": "DAILY",
        "ver": "1.0",
    }
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data["response"]["body"]["items"]
    if not items:
        logger.warning(f"[{location_name}] 에어코리아 데이터 없음: station={station_name}")
        return {"location_name": location_name, "station": station_name, "pm10": None, "pm25": None,
                "pm10_grade": None, "pm25_grade": None, "measured_at": None}

    item = items[0]
    pm10 = _safe_int(item.get("pm10Value"))
    pm25 = _safe_int(item.get("pm25Value"))
    pm10_grade = GRADE_MAP.get(str(item.get("pm10Grade", "")), None)
    pm25_grade = GRADE_MAP.get(str(item.get("pm25Grade", "")), None)

    logger.info(f"[{location_name}] 미세먼지: PM10={pm10}({pm10_grade}), PM2.5={pm25}({pm25_grade})")
    return {
        "location_name": location_name,
        "station": station_name,
        "pm10": pm10,
        "pm25": pm25,
        "pm10_grade": pm10_grade,
        "pm25_grade": pm25_grade,
        "measured_at": item.get("dataTime"),
    }
