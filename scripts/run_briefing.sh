#!/bin/bash
# launchd는 shell 환경변수를 로드하지 않으므로 pyenv 경로를 명시적으로 설정
export PATH="$HOME/.pyenv/shims:$HOME/.pyenv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
eval "$(pyenv init -)" 2>/dev/null || true

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

python main.py

# claude CLI 백그라운드 프로세스 정리
pkill -f "claude-code" 2>/dev/null || true

# 카톡 전송 완료 후 30초 대기 뒤 잠자기 (sudo 불필요)
sleep 30
osascript -e 'tell application "System Events" to sleep'
