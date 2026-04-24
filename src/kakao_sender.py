import json
import logging

import requests

logger = logging.getLogger(__name__)

SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


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
    resp = requests.post(SEND_URL, headers=headers, data=data, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    if result.get("result_code") != 0:
        raise RuntimeError(f"카카오 전송 실패: {result}")
    logger.info("카카오톡 메시지 전송 완료.")
