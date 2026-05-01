import concurrent.futures
import logging
from datetime import datetime, timedelta

import pytz
import requests

logger = logging.getLogger(__name__)

KST = pytz.timezone("Asia/Seoul")
BASE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
_TOTAL_TIMEOUT = 30
_RETRIES = 2


def _get(url: str, params: dict) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(_RETRIES):
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(requests.get, url, params=params, timeout=10)
        try:
            return future.result(timeout=_TOTAL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            last_exc = requests.exceptions.Timeout(f"API 총 요청 시간 초과 ({_TOTAL_TIMEOUT}초): {url}")
        except requests.exceptions.RequestException as e:
            last_exc = e
        finally:
            executor.shutdown(wait=False)
        if attempt < _RETRIES - 1:
            logger.warning(f"날씨 API 요청 실패, 재시도 중... ({url})")
    raise last_exc
BASE_HOURS = [2, 5, 8, 11, 14, 17, 20, 23]

SKY_MAP = {"1": "맑음", "3": "구름많음", "4": "흐림"}
PTY_MAP = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}


def _get_base_datetime() -> tuple[str, str]:
    now = datetime.now(KST) - timedelta(minutes=10)
    available = [h for h in BASE_HOURS if h <= now.hour]
    if available:
        base_hour = max(available)
        base_date = now.strftime("%Y%m%d")
    else:
        base_hour = 23
        base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
    return base_date, f"{base_hour:02d}00"


def fetch(config: dict, nx: int, ny: int, location_name: str) -> dict:
    base_date, base_time = _get_base_datetime()
    params = {
        "serviceKey": config["api_keys"]["kma_service_key"],
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    resp = _get(BASE_URL, params)
    resp.raise_for_status()
    data = resp.json()

    items = data["response"]["body"]["items"]["item"]
    hourly = {}
    for item in items:
        t = item["fcstTime"]
        if t not in hourly:
            hourly[t] = {"time": t}
        cat = item["fcstCategory"] if "fcstCategory" in item else item.get("category", "")
        val = item["fcstValue"] if "fcstValue" in item else item.get("obsrValue", "")
        if cat == "TMP":
            hourly[t]["tmp"] = int(val)
        elif cat == "POP":
            hourly[t]["pop"] = int(val)
        elif cat == "PTY":
            hourly[t]["pty"] = PTY_MAP.get(str(val), str(val))
        elif cat == "SKY":
            hourly[t]["sky"] = SKY_MAP.get(str(val), str(val))
        elif cat == "REH":
            hourly[t]["reh"] = int(val)
        elif cat == "WSD":
            hourly[t]["wsd"] = float(val)

    today_slots = sorted(
        [h for h in hourly.values() if "tmp" in h],
        key=lambda x: x["time"],
    )
    temps = [h["tmp"] for h in today_slots if "tmp" in h]
    pops = [h.get("pop", 0) for h in today_slots]

    logger.info(f"[{location_name}] 날씨 데이터 수신: base={base_date} {base_time}, {len(today_slots)}개 시간대")
    return {
        "location_name": location_name,
        "base_datetime": f"{base_date} {base_time}",
        "hourly": today_slots,
        "daily_max_tmp": max(temps) if temps else None,
        "daily_min_tmp": min(temps) if temps else None,
        "daily_max_pop": max(pops) if pops else 0,
    }
