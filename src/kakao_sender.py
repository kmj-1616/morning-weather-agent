import concurrent.futures
import json
import logging

import requests

logger = logging.getLogger(__name__)

SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
_TOTAL_TIMEOUT = 30
_RETRIES = 2


def _post(url: str, headers: dict, data: dict) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(_RETRIES):
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(requests.post, url, headers=headers, data=data, timeout=10)
        try:
            return future.result(timeout=_TOTAL_TIMEOUT)
        except concurrent.futures.TimeoutError:
            last_exc = requests.exceptions.Timeout(f"카카오 API 총 요청 시간 초과 ({_TOTAL_TIMEOUT}초)")
        except requests.exceptions.RequestException as e:
            last_exc = e
        finally:
            executor.shutdown(wait=False)
        if attempt < _RETRIES - 1:
            logger.warning("카카오 API 요청 실패, 재시도 중...")
    raise last_exc


def send_to_me(access_token: str, message_text: str) -> None:
    template = {
        "object_type": "text",
        "text": message_text,
        "link": {"web_url": "", "mobile_web_url": ""},
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"template_object": json.dumps(template, ensure_ascii=False)}
    resp = _post(SEND_URL, headers=headers, data=data)
    resp.raise_for_status()
    result = resp.json()
    if result.get("result_code") != 0:
        raise RuntimeError(f"카카오 전송 실패: {result}")
    logger.info("카카오톡 메시지 전송 완료.")
