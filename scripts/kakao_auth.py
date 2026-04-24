"""
카카오 OAuth 최초 인증 스크립트 — 한 번만 실행하면 됩니다.
실행 방법: python scripts/kakao_auth.py
"""
import sys
import urllib.parse
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.yaml"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"

_auth_code = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write("<html><body><h2>인증 완료! 이 창을 닫아도 됩니다.</h2></body></html>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"code parameter not found")

    def log_message(self, format, *args):
        pass  # suppress server logs


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    client_id = config["kakao"]["client_id"]
    redirect_uri = config["kakao"]["redirect_uri"]

    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri, safe='')}"
        f"&scope=talk_message"
    )

    print("\n=== 카카오 OAuth 인증 ===")
    print("브라우저에서 카카오 계정으로 로그인 후 '동의하고 계속하기'를 눌러주세요.\n")
    print(f"자동으로 브라우저가 열리지 않으면 아래 URL을 직접 복사해 접속하세요:\n{auth_url}\n")
    webbrowser.open(auth_url)

    parsed = urllib.parse.urlparse(redirect_uri)
    port = parsed.port or 5000
    server = HTTPServer(("localhost", port), _CallbackHandler)
    print(f"localhost:{port} 에서 콜백 대기 중...")
    server.handle_request()

    if not _auth_code:
        print("인증 코드를 받지 못했습니다. 다시 시도해주세요.")
        sys.exit(1)

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code": _auth_code,
        },
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()

    now = datetime.now(timezone.utc)
    config["kakao"]["access_token"] = result["access_token"]
    config["kakao"]["refresh_token"] = result.get("refresh_token", "")
    config["kakao"]["token_expires_at"] = (
        now + timedelta(seconds=result.get("expires_in", 21600))
    ).isoformat()
    config["kakao"]["refresh_token_expires_at"] = (
        now + timedelta(seconds=result.get("refresh_token_expires_in", 5184000))
    ).isoformat()

    tmp_path = str(CONFIG_PATH) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    import os
    os.replace(tmp_path, CONFIG_PATH)

    print("\n✅ 인증 완료! config.yaml에 토큰이 저장되었습니다.")
    print("이제 python main.py 를 실행해 테스트해보세요.")


if __name__ == "__main__":
    main()
