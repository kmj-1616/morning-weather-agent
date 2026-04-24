import logging
from datetime import datetime, timedelta, timezone

import requests

from .config_loader import save_config

logger = logging.getLogger(__name__)

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
# 리프레시 토큰 만료 D-7 이하면 경고
REFRESH_WARN_DAYS = 7


def ensure_valid_token(config: dict) -> str:
    expires_at_str = config.get("kakao", {}).get("token_expires_at", "")
    if not expires_at_str:
        raise RuntimeError("카카오 access_token이 없습니다. scripts/kakao_auth.py를 먼저 실행하세요.")

    expires_at = datetime.fromisoformat(expires_at_str)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if now >= expires_at - timedelta(minutes=30):
        logger.info("카카오 access_token 갱신 중...")
        _refresh_and_save(config)

    _warn_if_refresh_token_expiring(config, now)
    return config["kakao"]["access_token"]


def _refresh_and_save(config: dict) -> None:
    refresh_token = config["kakao"].get("refresh_token", "")
    if not refresh_token:
        raise RuntimeError("refresh_token이 없습니다. scripts/kakao_auth.py를 다시 실행하세요.")

    token_data = {
        "grant_type": "refresh_token",
        "client_id": config["kakao"]["client_id"],
        "refresh_token": refresh_token,
    }
    client_secret = config["kakao"].get("client_secret", "")
    if client_secret:
        token_data["client_secret"] = client_secret

    resp = requests.post(TOKEN_URL, data=token_data, timeout=10)
    resp.raise_for_status()
    result = resp.json()

    now = datetime.now(timezone.utc)
    config["kakao"]["access_token"] = result["access_token"]
    config["kakao"]["token_expires_at"] = (
        now + timedelta(seconds=result.get("expires_in", 21600))
    ).isoformat()

    if "refresh_token" in result:
        config["kakao"]["refresh_token"] = result["refresh_token"]
        config["kakao"]["refresh_token_expires_at"] = (
            now + timedelta(seconds=result.get("refresh_token_expires_in", 5184000))
        ).isoformat()
        logger.info("카카오 refresh_token도 갱신되었습니다.")

    save_config(config)
    logger.info("카카오 access_token 갱신 완료.")


def _warn_if_refresh_token_expiring(config: dict, now: datetime) -> None:
    rt_expires_str = config.get("kakao", {}).get("refresh_token_expires_at", "")
    if not rt_expires_str:
        return
    rt_expires = datetime.fromisoformat(rt_expires_str)
    if rt_expires.tzinfo is None:
        rt_expires = rt_expires.replace(tzinfo=timezone.utc)
    days_left = (rt_expires - now).days
    if days_left <= REFRESH_WARN_DAYS:
        logger.warning(
            f"카카오 refresh_token 만료까지 {days_left}일 남았습니다. "
            "scripts/kakao_auth.py를 실행해 토큰을 갱신하세요."
        )
