import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 친절한 아침 날씨 브리핑 도우미입니다.
주어진 날씨와 미세먼지 데이터를 바탕으로, 사용자에게 오늘 하루 준비에 필요한 정보를
자연스럽고 따뜻한 한국어로 전달해주세요.

브리핑에 반드시 포함할 내용:
1. 전체적인 날씨 요약 (최고/최저 기온, 하늘 상태)
2. 우산 필요 여부 — 강수확률 50% 이상이면 "우산 챙기세요"
3. 마스크/외출 주의 여부 — PM2.5 등급이 "나쁨" 이상이면 마스크 권고
4. 기온별 옷차림 추천
   - 최고기온 28°C 이상: 민소매·반팔·반바지
   - 23~27°C: 반팔·얇은 긴팔
   - 20~22°C: 얇은 가디건·긴팔
   - 17~19°C: 얇은 니트·맨투맨
   - 12~16°C: 자켓·가디건
   - 9~11°C: 트렌치코트·니트
   - 5~8°C: 울코트·히트텍
   - 4°C 이하: 패딩·두꺼운 코트
5. 짧은 응원 한마디

형식 규칙:
- 카카오톡 메시지에 어울리는 짧고 읽기 쉬운 형태
- 적절한 이모지 사용
- 위치가 여러 곳이면 각 위치별로 간략히 구분
- 전체 길이는 300자 이내로 간결하게"""


def _format_data(weather_list: list[dict], air_list: list[dict]) -> str:
    lines = ["=== 오늘의 날씨 데이터 ==="]
    air_by_location = {a["location_name"]: a for a in air_list}

    for w in weather_list:
        name = w["location_name"]
        lines.append(f"\n[{name}]")
        lines.append(f"- 최고기온: {w['daily_max_tmp']}°C, 최저기온: {w['daily_min_tmp']}°C")
        lines.append(f"- 최대 강수확률: {w['daily_max_pop']}%")

        if w.get("hourly"):
            morning = [h for h in w["hourly"] if "0700" <= h["time"] <= "1200"]
            if morning:
                sky_vals = [h["sky"] for h in morning if h.get("sky")]
                sky = sky_vals[0] if sky_vals else "알 수 없음"
                lines.append(f"- 오전 하늘: {sky}")

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
