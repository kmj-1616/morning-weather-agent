# 아침 날씨 브리핑 에이전트
> AI-powered Morning Weather Briefing Automation

주소만 입력하면 기상청·에어코리아 API로 날씨와 대기질을 수집하고, Claude AI가 자연스러운 한국어 브리핑을 작성해 카카오톡으로 자동 전송하는 **AI 기반 자동화 에이전트**입니다.

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
- **자동 실행**: macOS launchd + pmset / Windows Task Scheduler로 매일 아침 자동 실행 — 잠자기 상태에서 자동 깨우기 및 전송 후 자동 재잠자기 지원

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

### macOS — launchd + pmset (권장)

cron은 Mac이 잠자기 상태일 때 예약을 건너뛰므로 사용하지 않습니다.  
**launchd**로 스케줄을 관리하고, **pmset**으로 실행 전 Mac을 자동으로 깨웁니다.  
브리핑 전송이 완료되면 Mac이 자동으로 다시 잠자기 상태로 돌아갑니다.

**실행 흐름**

```
원하는시간-5분  pmset → Mac 자동 깨우기
원하는시간      launchd → run_briefing.sh 실행
                  └─ 날씨·대기질 수집 → AI 브리핑 생성 → 카카오톡 전송
완료+30초        osascript → Mac 자동 잠자기
```

> 시간 변경 시 `com.weather-briefing.plist`의 `Hour` / `Minute` 값과 `pmset` 명령의 시각을 함께 수정하세요.

#### 1단계 — 실행 권한 부여 및 plist 설치

`com.weather-briefing.plist`의 경로는 현재 사용자명으로 교체해야 합니다.

```bash
chmod +x ~/weather_briefing/scripts/run_briefing.sh

# plist 내 경로를 현재 사용자명으로 치환 후 설치
sed "s|YOUR_USERNAME|$(whoami)|g" \
  ~/weather_briefing/com.weather-briefing.plist \
  > ~/Library/LaunchAgents/com.weather-briefing.plist

launchctl load ~/Library/LaunchAgents/com.weather-briefing.plist
```

#### 2단계 — 매일 6:25 자동 깨우기 설정

```bash
sudo pmset repeat wake MTWRFSU 06:25:00
```

설정 확인: `pmset -g sched`

#### 3단계 — 즉시 테스트

```bash
launchctl start com.weather-briefing
```

로그 확인: `logs/launchd.log` / `logs/launchd_err.log`

#### 주의사항

- **pyenv 미사용 시**: `scripts/run_briefing.sh`의 `eval "$(pyenv init -)"` 줄은 무시됩니다 (오류 없이 넘어감).
- **배터리 전원 시 깨우기**: 시스템 설정 → 배터리 → "네트워크 접근 시 깨우기" 또는 "전원 어댑터" 탭에서 깨우기 관련 옵션을 활성화해야 pmset wake가 동작합니다.
- **잠자기 타이밍**: `main.py` 종료 후 30초 뒤 잠자기가 실행됩니다. 스크립트 실패 시에도 잠자기는 동작합니다.
- **launchd catch-up**: Mac이 06:30에 깨어 있지 않아도, 이후 깨어날 때 당일 미실행 작업을 즉시 실행합니다.

### Windows — Task Scheduler

macOS의 pmset에 해당하는 별도 도구 없이, 작업 스케줄러 자체에서 절전 해제를 처리합니다.

작업 스케줄러에서 새 작업을 만들고 아래와 같이 설정합니다.

| 탭       | 항목              | 값                                      |
| -------- | ----------------- | --------------------------------------- |
| 일반     | 보안 옵션         | 사용자 로그온 여부에 관계없이 실행      |
| 트리거   | 시작              | 매일 오전 6:30 (원하는 시간으로 변경 가능) |
| 동작     | 프로그램/스크립트 | `C:\Python3x\python.exe`                |
| 동작     | 인수              | `C:\Users\...\weather_briefing\main.py` |
| 동작     | 시작 위치         | `C:\Users\...\weather_briefing`         |
| **조건** | **절전**          | **"이 작업을 실행하기 위해 컴퓨터 절전 모드 해제" 체크** |

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
├── main.py                      # 엔트리포인트
├── config.yaml                  # 실제 설정 (git 제외)
├── config.example.yaml          # 설정 예제 템플릿
├── requirements.txt
├── com.weather-briefing.plist   # macOS launchd 스케줄 설정
├── scripts/
│   ├── kakao_auth.py            # 최초 1회 OAuth 인증
│   └── run_briefing.sh          # macOS launchd 실행 래퍼 (pyenv 경로 처리 + 잠자기)
├── src/
│   ├── config_loader.py
│   ├── geocoder.py
│   ├── grid_converter.py
│   ├── weather_fetcher.py
│   ├── air_quality_fetcher.py
│   ├── token_manager.py
│   ├── kakao_sender.py
│   └── message_generator.py
└── logs/                        # 런타임 로그 (git 제외)
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

## 고도화 계획

현재는 고정된 파이프라인(수집 → 생성 → 전송)으로 동작하는 **AI 기반 자동화** 구조입니다. 향후 진정한 **AI Agent** 구조로 발전시키는 것을 목표로 합니다.

- **자율적 도구 선택**: Claude가 날씨 상황에 따라 추가 정보(강수 예보 상세, 대기질 예보 등)를 스스로 조회할지 판단
- **예외 대응**: API 응답 이상·데이터 누락 시 Claude가 상황을 판단해 대체 행동 수행
- **피드백 루프**: 사용자 반응(메시지 읽음 여부 등)을 학습해 브리핑 스타일 자동 조정
- **멀티 채널**: 카카오톡 외 슬랙·이메일 등 채널을 AI가 상황에 맞게 선택
