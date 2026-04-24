import logging
import logging.handlers
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# 모든 경로를 __file__ 기준으로 계산 (Task Scheduler 실행 시 작업 디렉토리 문제 방지)
sys.path.insert(0, str(ROOT))

from src import (
    air_quality_fetcher,
    config_loader,
    geocoder,
    grid_converter,
    kakao_sender,
    message_generator,
    token_manager,
    weather_fetcher,
)


def setup_logging(config: dict) -> None:
    log_cfg = config.get("logging", {})
    log_path = ROOT / log_cfg.get("log_file", "logs/briefing.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=log_cfg.get("max_bytes", 1_048_576),
        backupCount=log_cfg.get("backup_count", 5),
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    logging.basicConfig(level=logging.INFO, handlers=[handler, stream_handler])


def main() -> None:
    config = config_loader.load_config(str(ROOT / "config.yaml"))
    setup_logging(config)
    logger = logging.getLogger(__name__)
    logger.info("=== 아침 날씨 브리핑 시작 ===")

    try:
        access_token = token_manager.ensure_valid_token(config)

        all_weather = []
        all_air = []

        for loc in config["locations"]:
            if "address" in loc and ("lat" not in loc or "lng" not in loc):
                loc["lat"], loc["lng"] = geocoder.address_to_latlon(
                    loc["address"], config["kakao"]["client_id"]
                )
            if "air_station" not in loc:
                tm_x, tm_y = geocoder.wgs84_to_tm(loc["lat"], loc["lng"])
                loc["air_station"] = air_quality_fetcher.find_nearest_station(
                    tm_x, tm_y, config["api_keys"]["airkorea_service_key"]
                )
            nx, ny = grid_converter.latlon_to_grid(loc["lat"], loc["lng"])
            weather = weather_fetcher.fetch(config, nx, ny, loc["name"])
            air = air_quality_fetcher.fetch(config, loc["air_station"], loc["name"])
            all_weather.append(weather)
            all_air.append(air)

        message = message_generator.generate_message(all_weather, all_air)
        kakao_sender.send_to_me(access_token, message)
        logger.info("=== 브리핑 전송 완료 ===")

    except Exception as e:
        logger.exception(f"브리핑 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
