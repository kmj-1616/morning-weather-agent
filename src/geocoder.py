import logging
import math

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://dapi.kakao.com/v2/local/search/address.json"


def address_to_latlon(address: str, kakao_rest_api_key: str) -> tuple[float, float]:
    headers = {"Authorization": f"KakaoAK {kakao_rest_api_key}"}
    resp = requests.get(BASE_URL, headers=headers, params={"query": address}, timeout=10)
    resp.raise_for_status()
    documents = resp.json().get("documents", [])
    if not documents:
        raise ValueError(f"주소를 찾을 수 없습니다: {address}")
    doc = documents[0]
    lat, lng = float(doc["y"]), float(doc["x"])
    logger.info(f"주소 변환: {address} → lat={lat}, lng={lng}")
    return lat, lng


def wgs84_to_tm(lat: float, lng: float) -> tuple[float, float]:
    """WGS84 위경도 → 한국 중부원점 TM 좌표 변환 (에어코리아 API 요구 형식)."""
    a = 6378137.0
    f = 1 / 298.257222101
    e2 = 2 * f - f ** 2
    ep2 = e2 / (1 - e2)

    lat0 = math.radians(38.0)
    lng0 = math.radians(127.0)
    E0, N0, k0 = 200000.0, 500000.0, 1.0

    phi = math.radians(lat)
    lam = math.radians(lng)

    def meridian_arc(phi_r):
        return a * (
            (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * phi_r
            - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * phi_r)
            + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * phi_r)
            - (35 * e2**3 / 3072) * math.sin(6 * phi_r)
        )

    N = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    T = math.tan(phi) ** 2
    C = ep2 * math.cos(phi) ** 2
    A = math.cos(phi) * (lam - lng0)
    M = meridian_arc(phi)
    M0 = meridian_arc(lat0)

    x = k0 * N * (A + (1 - T + C) * A**3 / 6 + (5 - 18*T + T**2 + 72*C - 58*ep2) * A**5 / 120)
    y = k0 * (M - M0 + N * math.tan(phi) * (
        A**2 / 2
        + (5 - T + 9*C + 4*C**2) * A**4 / 24
        + (61 - 58*T + T**2 + 600*C - 330*ep2) * A**6 / 720
    ))

    return E0 + x, N0 + y
