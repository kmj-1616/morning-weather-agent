# CLAUDE.md

아침 날씨 브리핑을 카카오톡으로 보내는 Python AI 기반 자동화 에이전트입니다.

## 실행 흐름

```
config 로드 → 카카오 토큰 갱신 확인
→ [위치별] 주소 → 위경도 변환 → 가까운 측정소 탐색 → 격자 변환 + 날씨/대기질 수집
→ Claude AI 브리핑 생성 → 카카오톡 전송
```

## 모듈 구조

| 파일 | 역할 |
|------|------|
| `main.py` | 전체 파이프라인 오케스트레이션, 로깅 설정 |
| `src/config_loader.py` | config.yaml 로드·검증·저장 (`ConfigError` 예외 포함) |
| `src/geocoder.py` | 주소 → 위경도 (카카오 로컬 API), WGS84 → TM 좌표 변환 |
| `src/grid_converter.py` | WGS84 위경도 → 기상청 격자 좌표 변환 (`latlon_to_grid`) |
| `src/weather_fetcher.py` | 기상청 단기예보 API 호출, 시간별 날씨 수집 |
| `src/air_quality_fetcher.py` | 에어코리아 API 호출, PM10/PM2.5 수집 및 가까운 측정소 탐색 |
| `src/token_manager.py` | 카카오 OAuth2 토큰 자동 갱신 (30분 전 갱신, 7일 전 경고) |
| `src/kakao_sender.py` | 카카오톡 "나에게 보내기" 전송 |
| `src/message_generator.py` | Claude CLI 호출로 한국어 브리핑 생성 |
| `scripts/kakao_auth.py` | 최초 1회 OAuth 인증 (access/refresh token 발급) |
| `scripts/run_briefing.sh` | macOS launchd 실행 래퍼 — pyenv·homebrew 경로 설정, 전송 후 claude 프로세스 정리 및 자동 잠자기 |
| `com.weather-briefing.plist` | macOS launchd 스케줄 설정 (매일 원하는 시각 실행) |

## 설정 파일 (config.yaml)

`config.example.yaml`을 복사해 사용합니다. 필수 키:

```yaml
api_keys:
  kma_service_key:        # 기상청 API
  airkorea_service_key:   # 에어코리아 API

locations:
  - name: "집"
    address: "서울시 강남구 테헤란로 1"  # 주소 입력 시 lat/lng 자동 변환
    # lat/lng 직접 입력 시 address 대신 사용
    # air_station 생략 시 위치 기반 자동 탐색

kakao:
  client_id:              # 카카오 REST API 키
  client_secret:          # 클라이언트 시크릿 (활성화한 경우에만)
  redirect_uri:           # OAuth 콜백 주소 (기본: http://localhost:8080/callback)
  access_token:           # kakao_auth.py 실행 후 자동 저장
  refresh_token:
  token_expires_at:
  refresh_token_expires_at:

logging:
  log_file: "logs/briefing.log"
  max_bytes: 1048576
  backup_count: 5
```

## 외부 API

| API | 엔드포인트 | 인증 |
|-----|-----------|------|
| 기상청 단기예보 | `apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst` | serviceKey |
| 에어코리아 대기오염정보 | `apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty` | serviceKey |
| 에어코리아 측정소정보 | `apis.data.go.kr/B552584/MsrstnInfoInqireSvc/getNearbyMsrstnList` | serviceKey |
| 카카오 로컬 | `dapi.kakao.com/v2/local/search/address.json` | KakaoAK REST API 키 |
| 카카오 OAuth | `kauth.kakao.com/oauth/token` | client_id + refresh_token |
| 카카오 메시지 | `kapi.kakao.com/v2/api/talk/memo/default/send` | Bearer token |
| Claude CLI | `claude -p "..."` subprocess | Claude Pro/Max 구독 인증 |

## 초기 설정 및 실행

```bash
# 최초 1회: 카카오 OAuth 인증
python scripts/kakao_auth.py

# 실행
python main.py
```

macOS 자동 실행(launchd + pmset)은 README의 "자동 실행 설정" 참고.

## 규칙 및 주의사항

- **`config.yaml`은 절대 커밋 금지** — API 키·토큰 포함, `.gitignore`에 등록됨
- **토큰 갱신 로직**은 `src/token_manager.py`에만 둔다
- **격자 변환**은 `src/grid_converter.py`의 `latlon_to_grid()`만 사용한다
- **주소 → 위경도 변환**은 `src/geocoder.py`의 `address_to_latlon()`만 사용한다
- **TM 좌표 변환**은 `src/geocoder.py`의 `wgs84_to_tm()`만 사용한다
- **Claude 호출**은 `src/message_generator.py`에만 위치, `claude -p` subprocess 방식을 사용한다 (anthropic SDK 아님)
- **로그 경로**는 config.yaml의 `logging.log_file` 값을 따른다 (하드코딩 금지)
- config 저장은 반드시 `.tmp` 임시 파일 경유 후 원자적 교체 방식을 유지한다 (`src/config_loader.py` 참고)
- 프롬프트 설계 배경은 `PROMPT_DESIGN.md` 참고
