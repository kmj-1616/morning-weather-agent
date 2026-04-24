import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 친절한 아침 날씨 브리핑 도우미입니다.
주어진 날씨와 미세먼지 데이터를 바탕으로, 사용자에게 오늘 하루 준비에 필요한 정보를
자연스럽고 따뜻한 한국어로 전달해주세요.

사용자 일정:
- 첫 번째 위치(집): 아침 출근 전 및 저녁 퇴근 후 기준
- 두 번째 위치(회사): 오전 9시 ~ 오후 6시 기준
- 데이터에 위치가 하나뿐이면 하루 전체 기준으로 판단하세요

브리핑에 반드시 포함할 내용:
1. 전체적인 날씨 요약 (최고/최저 기온, 하늘 상태)
2. 우산 필요 여부 — 출근(7~9시) 또는 퇴근(18~20시) 강수확률이 50% 이상이면 "우산 챙기세요"
3. 마스크/외출 주의 여부 — PM2.5 등급이 "나쁨" 이상이면 마스크 권고
4. 기온별 옷차림 추천 — 집의 아침 최저기온과 회사의 낮 최고기온을 모두 고려해 결정
   - 최고기온 28°C 이상: 민소매·반소매·반바지·치마·린넨
   - 23~27°C: 반소매·얇은 셔츠·반바지·면바지
   - 20~22°C: 블라우스·긴소매·면바지·슬랙스
   - 17~19°C: 얇은 가디건이나 니트·스웨트셔츠·후드·긴바지
   - 12~16°C: 자켓·가디건·니트·스타킹·청바지
   - 9~11°C: 트렌치코트·야상 점퍼·스타킹·기모바지
   - 5~8°C: 울코트·히트텍·가죽 옷·기모
   - 4°C 이하: 패딩·두꺼운 코트·누빔 옷·기모·목도리
5. 짧은 응원 한마디

형식 규칙:
- 카카오톡 메시지에 어울리는 짧고 읽기 쉬운 형태
- 적절한 이모지 사용
- 전체 길이는 400자 이내로 간결하게"""


def _commute_pop(hourly: list[dict], start: str, end: str) -> int:
    slots = [h for h in hourly if start <= h["time"] <= end]
    return max((h.get("pop", 0) for h in slots), default=0)


def _format_data(weather_list: list[dict], air_list: list[dict]) -> str:
    lines = ["=== 오늘의 날씨 데이터 ==="]
    air_by_location = {a["location_name"]: a for a in air_list}

    for i, w in enumerate(weather_list):
        name = w["location_name"]
        role = "집 — 아침·저녁 기준" if i == 0 else "회사 — 9~18시 기준"
        lines.append(f"\n[{name} / {role}]")

        hourly = w.get("hourly", [])

        if i == 0:
            morning_slots = [h for h in hourly if h["time"] <= "0900"]
            morning_min = min((h["tmp"] for h in morning_slots if "tmp" in h), default=None)
            if morning_min is not None:
                lines.append(f"- 아침 최저기온: {morning_min}°C")
        else:
            daytime = [h for h in hourly if "0900" <= h["time"] <= "1800"]
            daytime_max = max((h["tmp"] for h in daytime if "tmp" in h), default=None)
            if daytime_max is not None:
                lines.append(f"- 낮 최고기온 (9~18시): {daytime_max}°C")

        lines.append(f"- 일 최고: {w['daily_max_tmp']}°C / 최저: {w['daily_min_tmp']}°C")
        lines.append(f"- 출근 강수확률 (7~9시): {_commute_pop(hourly, '0700', '0900')}%")
        lines.append(f"- 퇴근 강수확률 (18~20시): {_commute_pop(hourly, '1800', '2000')}%")

        morning_sky = [h.get("sky") for h in hourly if "0700" <= h["time"] <= "1200" and h.get("sky")]
        if morning_sky:
            lines.append(f"- 오전 하늘: {morning_sky[0]}")

        air = air_by_location.get(name)
        if air:
            lines.append(f"- PM10: {air['pm10']}({air['pm10_grade']}), PM2.5: {air['pm25']}({air['pm25_grade']})")

    return "\n".join(lines)


def generate_message(weather_list: list[dict], air_list: list[dict]) -> str:
    data_summary = _format_data(weather_list, air_list)
    full_prompt = SYSTEM_PROMPT + "\n\n" + data_summary

    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            shell=(sys.platform == "win32"),
        )
    except FileNotFoundError:
        raise RuntimeError(
            "claude CLI를 찾을 수 없습니다. "
            "'npm install -g @anthropic-ai/claude-code' 후 'claude login'을 실행하세요."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("claude CLI 응답 시간 초과 (60초)")

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI 실행 실패: {result.stderr.strip()}")

    message = result.stdout.strip()
    logger.info("Claude 메시지 생성 완료.")
    return message
