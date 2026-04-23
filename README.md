# 아침 날씨 브리핑 에이전트

기상청·에어코리아 API로 날씨와 대기질을 수집하고, Claude AI가 자연스러운 한국어 브리핑을 작성해 카카오톡으로 전송하는 Python 자동화 에이전트입니다.

## 주요 기능

- **날씨 수집**: 기상청 단기예보 API — 시간별 기온, 강수확률, 하늘상태, 습도, 풍속
- **대기질 수집**: 에어코리아 API — PM10, PM2.5 농도 및 등급
- **다중 위치 지원**: 집, 회사 등 여러 위치를 한 번에 처리
- **AI 브리핑 생성**: Claude AI(claude-sonnet-4-6)가 300자 이내 카카오톡 최적화 브리핑 작성
  - 기온에 따른 옷차림 추천 (8단계)
  - 강수확률 50% 이상 시 우산 권고
  - PM2.5 "나쁨" 이상 시 마스크 권고
- **카카오톡 전송**: 나에게 보내기 기능으로 자동 전송
- **OAuth2 토큰 자동 갱신**: 만료 30분 전 자동 갱신, 7일 전 경고
- **Windows Task Scheduler 연동**: 매일 아침 자동 실행 가능
- **Retrobot**: 커밋마다 Claude AI가 KPT 회고를 자동 생성해 `retros/`에 저장

## 사전 요구사항

- Python 3.9 이상
- 아래 API 키 4종:

| API | 발급처 |
|-----|--------|
| 기상청 단기예보 API 키 | [data.go.kr](https://www.data.go.kr) |
| 에어코리아 API 키 | [data.go.kr](https://www.data.go.kr) |
| 카카오 REST API 키 | [developers.kakao.com](https://developers.kakao.com) |

- **Claude Pro/Max 구독** 및 `claude login` 완료 상태 필요 (API 키 불필요)

## 설치

```bash
git clone https://github.com/kwonmijeong/weather-briefing.git
cd weather-briefing
pip install -r requirements.txt
npm install -g @anthropic-ai/claude-code
claude login
```

## 설정

### 1. 설정 파일 생성

```bash
cp config.example.yaml config.yaml
```

### 2. config.yaml 편집

```yaml
api_keys:
  kma_service_key: "기상청_API_키"
  airkorea_service_key: "에어코리아_API_키"

locations:
  - name: "집"
    lat: 37.5172        # 위도 (WGS84)
    lng: 127.0473       # 경도 (WGS84)
    air_station: "강남구"  # 에어코리아 측정소명

kakao:
  client_id: "카카오_REST_API_키"
  redirect_uri: "http://localhost:5000/callback"

logging:
  log_file: "logs/briefing.log"
  max_bytes: 1048576
  backup_count: 5
```

### 3. 카카오 OAuth 최초 인증 (1회)

```bash
python scripts/kakao_auth.py
```

브라우저가 열리면 카카오 계정으로 로그인 후 동의합니다. 완료되면 토큰이 config.yaml에 자동 저장됩니다.

### 4. Git hooks 활성화

```bash
git config core.hooksPath .githooks
```

커밋마다 Retrobot이 자동으로 회고를 생성합니다. **clone 후 1회 실행 필요.**

## 실행

```bash
python main.py
```

## 자동 실행 설정

### Windows — Task Scheduler

작업 스케줄러에서 새 작업을 만들고 아래와 같이 설정합니다.

| 항목 | 값 |
|------|-----|
| 트리거 | 매일 오전 6:30 (원하는 시간) |
| 프로그램/스크립트 | `C:\Python3x\python.exe` |
| 인수 | `C:\Users\...\weather_briefing\main.py` |
| 시작 위치 | `C:\Users\...\weather_briefing` |

### macOS — cron

```bash
crontab -e
```

아래 줄을 추가합니다 (매일 오전 6:30 실행):

```
30 6 * * * /usr/bin/python3 /Users/사용자명/weather_briefing/main.py
```

python3 경로가 다를 경우 `which python3`으로 확인하세요.

## 아키텍처

```
main.py
  │
  ├─ config_loader      config.yaml 로드·검증
  ├─ token_manager      카카오 OAuth 토큰 자동 갱신
  │
  ├─ [위치별 반복]
  │    ├─ grid_converter    위경도 → 기상청 격자 좌표
  │    ├─ weather_fetcher   기상청 단기예보 API
  │    └─ air_quality_fetcher  에어코리아 API
  │
  ├─ message_generator  Claude AI로 한국어 브리핑 생성
  └─ kakao_sender       카카오톡 나에게 보내기 전송
```

## 디렉토리 구조

```
weather_briefing/
├── main.py                  # 엔트리포인트
├── config.yaml              # 실제 설정 (git 제외)
├── config.example.yaml      # 설정 예제 템플릿
├── requirements.txt
├── .githooks/
│   └── post-commit          # Retrobot hook
├── retrobot/
│   └── SKILL.md             # Retrobot AI 지침
├── retros/                  # 자동 생성 회고 파일
├── scripts/
│   └── kakao_auth.py        # 최초 1회 OAuth 인증
├── src/
│   ├── config_loader.py
│   ├── grid_converter.py
│   ├── weather_fetcher.py
│   ├── air_quality_fetcher.py
│   ├── token_manager.py
│   ├── kakao_sender.py
│   └── message_generator.py
└── logs/                    # 런타임 로그 (git 제외)
```

## 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| requests | ≥2.31.0 | HTTP API 호출 |
| anthropic | ≥0.25.0 | Claude API 클라이언트 |
| pyyaml | ≥6.0.1 | 설정 파일 파싱 |
| pytz | ≥2024.1 | 한국 시간대(KST) 처리 |

## 보안

- `config.yaml`은 `.gitignore`에 포함되어 있습니다. API 키·토큰을 절대 커밋하지 마세요.
- 카카오 access_token은 6시간마다 자동 갱신됩니다.
