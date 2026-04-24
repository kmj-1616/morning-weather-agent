# 아침 날씨 브리핑 에이전트

기상청·에어코리아 API로 날씨와 대기질을 수집하고, Claude AI가 자연스러운 한국어 브리핑을 작성해 카카오톡으로 전송하는 Python 자동화 에이전트입니다.

## 주요 기능

- **날씨 수집**: 기상청 단기예보 API — 시간별 기온, 강수확률, 하늘상태, 습도, 풍속
- **대기질 수집**: 에어코리아 API — PM10, PM2.5 농도 및 등급
- **다중 위치 지원**: 집, 회사 등 여러 위치를 한 번에 처리
- **주소 자동 변환**: 주소 입력 시 카카오 로컬 API로 위경도 자동 변환, 가장 가까운 에어코리아 측정소 자동 탐색
- **AI 브리핑 생성**: Claude AI가 400자 이내 카카오톡 최적화 브리핑 작성
  - 집(아침/저녁) · 회사(9~18시) 스케줄 기반 날씨 분석
  - 출퇴근 시간대(7~9시, 18~20시) 강수확률 기반 우산 권고
  - 아침 최저기온 + 낮 최고기온을 고려한 옷차림 추천 (8단계)
  - PM2.5 "나쁨" 이상 시 마스크 권고
- **카카오톡 전송**: 나에게 보내기 기능으로 자동 전송
- **OAuth2 토큰 자동 갱신**: 만료 30분 전 자동 갱신, 7일 전 경고
- **자동 실행**: macOS cron / Windows Task Scheduler로 매일 아침 자동 실행 가능

## 브리핑 예시

```
🌤️ 4월 24일 날씨 브리핑

오늘 맑고 쾌청한 하루예요!
최저 11°C → 최고 21°C로 일교차가 꽤 크니 주의하세요.

☂️ 우산: 출퇴근 강수확률 모두 30% 이하 → 오늘은 안 챙겨도 돼요!

😷 마스크: PM2.5 보통 → 평소대로 외출하세요.

👗 옷차림: 아침 11°C엔 트렌치코트나 야상이 딱 맞아요.
낮엔 21°C까지 오르니 안에는 긴소매 얇게 입고
겉옷은 벗을 수 있도록 레이어드 추천!

오늘도 활기찬 하루 되세요 😊
```

## 사전 요구사항

- Python 3.9 이상
- 아래 API 키 4종:

| API                            | 발급처                                                                                              |
| ------------------------------ | --------------------------------------------------------------------------------------------------- |
| 기상청 단기예보 조회 API 키    | [data.go.kr](https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15084084)       |
| 에어코리아 대기오염정보 API 키 | [data.go.kr](https://www.data.go.kr/data/15073861/openapi.do)                                       |
| 에어코리아 측정소정보 API 키   | [data.go.kr](https://www.data.go.kr/data/15073877/openapi.do) — 가장 가까운 측정소 자동 탐색에 필요 |
| 카카오 REST API 키             | [developers.kakao.com](https://developers.kakao.com)                                                |

- **Claude Pro/Max 구독** 및 `claude login` 완료 상태 필요 (API 키 불필요)

## API 키 발급

### 기상청 단기예보 API

1. [공공데이터포털](https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15084084) 접속 → 로그인
2. **활용신청** 버튼 클릭 → 활용 목적 입력 후 제출
3. 자동 승인 (수 분~1시간 소요)
4. **마이페이지 → 개발계정** → `Encoding` 키 복사
5. `config.yaml`의 `api_keys.kma_service_key`에 입력

### 에어코리아 대기오염정보 API

1. [공공데이터포털](https://www.data.go.kr/data/15073861/openapi.do) 접속 → 로그인
2. **"한국환경공단\_에어코리아\_대기오염정보"** 항목에서 **활용신청**
   - `측정소별 실시간 측정정보 조회(getMsrstnAcctoRltmMesureDnsty)` 오퍼레이션 포함
3. **마이페이지 → 개발계정** → `Encoding` 키 복사
4. `config.yaml`의 `api_keys.airkorea_service_key`에 입력

### 에어코리아 측정소정보 API

주소 기반으로 가장 가까운 측정소를 자동 탐색하는 데 사용합니다.

1. [공공데이터포털](https://www.data.go.kr/data/15073877/openapi.do) 접속 → 로그인
2. **"한국환경공단\_에어코리아\_측정소정보"** 항목에서 **활용신청**
   - `근접측정소 목록 조회(getNearbyMsrstnList)` 오퍼레이션 포함
3. 승인 후 기존 `airkorea_service_key`와 동일한 키로 자동 동작 (별도 입력 불필요)

### 카카오 REST API 키

1. [developers.kakao.com](https://developers.kakao.com) 접속 → 카카오 계정 로그인
2. **내 애플리케이션 → 애플리케이션 추가하기** → 앱 이름 입력 후 저장
3. 생성된 앱 클릭 → 앱 → 플랫폼 키 → **REST API 키** 복사 → `config.yaml`의 `kakao.client_id`에 입력
4. **카카오 로그인 리다이렉트 URI** 에 `http://localhost:8080/callback` 등록
   - **앱 → 플랫폼 키 → REST API 키 → 클라이언트 시크릿**이 활성화되어 있다면 시크릿 코드를 `config.yaml`의 `kakao.client_secret`에 추가
5. **제품 설정 → 카카오 로그인 → 일반** → 사용 설정 ON
6. **제품 설정 → 카카오맵** → 활성화 ON (주소 기반 위경도 변환에 필요)
7. **동의항목** → `카카오톡 메시지 전송` → 이용중동의 설정

## 설치

```bash
git clone https://github.com/kwonmijeong/weather-briefing.git
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
  kma_service_key: "기상청_단기예보조회서비스_API_키"
  airkorea_service_key: "한국환경공단_에어코리아_대기오염정보_API_키"

locations:
  - name: "집"
    address: "서울시 강남구 테헤란로 1" # 주소 입력 시 위경도 자동 변환
    # 위경도를 직접 입력하면 address 대신 사용됩니다
    # lat: 37.5172
    # lng: 127.0473
    # air_station 생략 시 위치 기반으로 가장 가까운 측정소 자동 선택
    # air_station: "강남구"
  - name: "회사"
    address: "서울시 종로구 세종대로 1"

kakao:
  client_id: "카카오_REST_API_키"
  client_secret: "클라이언트_시크릿_코드" # 활성화한 경우에만 입력
  redirect_uri: "http://localhost:8080/callback"

logging:
  log_file: "logs/briefing.log"
  max_bytes: 1048576
  backup_count: 5
```

> **locations 순서**: 첫 번째 항목을 집(아침/저녁 기준), 두 번째 항목을 회사(9~18시 기준)로 인식합니다.

### 3. 카카오 OAuth 최초 인증 (1회)

```bash
python scripts/kakao_auth.py
```

브라우저가 열리면 카카오 계정으로 로그인 후 동의합니다. 완료되면 토큰이 config.yaml에 자동 저장됩니다.

## 실행

```bash
python main.py
```

## 자동 실행 설정

### Windows — Task Scheduler

작업 스케줄러에서 새 작업을 만들고 아래와 같이 설정합니다.

| 항목              | 값                                      |
| ----------------- | --------------------------------------- |
| 트리거            | 매일 오전 6:30 (원하는 시간)            |
| 프로그램/스크립트 | `C:\Python3x\python.exe`                |
| 인수              | `C:\Users\...\weather_briefing\main.py` |
| 시작 위치         | `C:\Users\...\weather_briefing`         |

### macOS — cron

```bash
crontab -e
```

아래 줄을 추가합니다 (매일 오전 6:30 실행):

```
30 6 * * * /Users/사용자명/.pyenv/versions/3.x.x/bin/python3 /Users/사용자명/morning-weather-agent/main.py
```

> **pyenv 사용 시 주의**: cron은 셸 프로파일을 로드하지 않아 `which python3`으로 나오는 shim 경로(`~/.pyenv/shims/python3`)가 동작하지 않습니다. 실제 Python 경로를 사용해야 합니다.
> ```bash
> ls ~/.pyenv/versions/  # 설치된 버전 확인
> # 예: /Users/사용자명/.pyenv/versions/3.11.9/bin/python3
> ```

## 아키텍처

```
main.py
  │
  ├─ config_loader      config.yaml 로드·검증
  ├─ token_manager      카카오 OAuth 토큰 자동 갱신
  │
  ├─ [위치별 반복]
  │    ├─ geocoder          주소 → 위경도 (카카오 로컬 API)
  │    │                    위경도 → TM 좌표 → 가까운 측정소 탐색
  │    ├─ grid_converter    위경도 → 기상청 격자 좌표
  │    ├─ weather_fetcher   기상청 단기예보 API
  │    └─ air_quality_fetcher  에어코리아 API
  │
  ├─ message_generator  Claude AI로 한국어 브리핑 생성
  └─ kakao_sender       카카오톡 나에게 보내기 전송
```

## 디렉토리 구조

```
morning-weather-agent/
├── main.py                  # 엔트리포인트
├── config.yaml              # 실제 설정 (git 제외)
├── config.example.yaml      # 설정 예제 템플릿
├── requirements.txt
├── scripts/
│   └── kakao_auth.py        # 최초 1회 OAuth 인증
├── src/
│   ├── config_loader.py
│   ├── geocoder.py
│   ├── grid_converter.py
│   ├── weather_fetcher.py
│   ├── air_quality_fetcher.py
│   ├── token_manager.py
│   ├── kakao_sender.py
│   └── message_generator.py
└── logs/                    # 런타임 로그 (git 제외)
```

## 의존성

| 패키지   | 버전    | 용도                  |
| -------- | ------- | --------------------- |
| requests | ≥2.31.0 | HTTP API 호출         |
| pyyaml   | ≥6.0.1  | 설정 파일 파싱        |
| pytz     | ≥2024.1 | 한국 시간대(KST) 처리 |

## 보안

- `config.yaml`은 `.gitignore`에 포함되어 있습니다. API 키·토큰을 절대 커밋하지 마세요.
- 카카오 access_token은 6시간마다 자동 갱신됩니다.
