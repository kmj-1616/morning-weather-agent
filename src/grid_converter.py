import math

# 기상청 Lambert Conformal Conic 투영 고정 파라미터
_RE = 6371.00877
_GRID = 5.0
_SLAT1 = 30.0
_SLAT2 = 60.0
_OLON = 126.0
_OLAT = 38.0
_XO = 43.0
_YO = 136.0


def latlon_to_grid(lat: float, lng: float) -> tuple[int, int]:
    """위경도(WGS84) → 기상청 단기예보 격자 좌표(nx, ny)"""
    re = _RE / _GRID
    slat1 = math.radians(_SLAT1)
    slat2 = math.radians(_SLAT2)
    olon = math.radians(_OLON)
    olat = math.radians(_OLAT)

    sn = math.log(math.cos(slat1) / math.cos(slat2))
    sn /= math.log(
        math.tan(math.pi / 4.0 + slat2 / 2.0) / math.tan(math.pi / 4.0 + slat1 / 2.0)
    )
    sf = math.tan(math.pi / 4.0 + slat1 / 2.0) ** sn * math.cos(slat1) / sn
    ro = re * sf / math.tan(math.pi / 4.0 + olat / 2.0) ** sn

    ra = re * sf / math.tan(math.pi / 4.0 + math.radians(lat) / 2.0) ** sn
    theta = math.radians(lng) - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = int(ra * math.sin(theta) + _XO + 1.5)
    ny = int(ro - ra * math.cos(theta) + _YO + 1.5)
    return nx, ny
