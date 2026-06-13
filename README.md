# 🎮 공략노트 AI — Gemini 2.5 Flash 버전

유튜브 게임 공략 영상 정보나 사용자가 직접 입력한 자막/메모를 바탕으로, 초등학교 4~5학년 아이가 이해하기 쉬운 공략노트·연습 미션·복습 퀴즈를 만들어주는 Streamlit 웹앱입니다.

이 버전은 **OpenAI API 대신 Google Gemini API**를 사용하며, 기본 모델은 **`gemini-2.5-flash`** 입니다.

## 1. 핵심 기능

- 게임 이름, 공략 주제, 아이 질문, 연습 목표 입력
- 사용자가 직접 정리한 자막/메모 입력
- Gemini 2.5 Flash로 초4~5 눈높이 공략노트 생성
- 핵심 공략 5개, 따라 하는 순서, 초보 실수, 용어 설명, 미션, 퀴즈 생성
- 결과를 JSON 파일에 저장하고 다시 보기
- 선택 기능: YouTube Data API로 영상 검색 결과 표시
- 같은 검색어는 24시간 캐싱해 API 사용량 절약

## 2. 중요한 정책/안전 기준

이 앱은 다음 기능을 하지 않습니다.

- 유튜브 영상 다운로드
- 유튜브 음성 추출
- 비공식 자막 스크래핑
- 원본 영상을 봤다고 허위 표현
- 과금/현질/뽑기/도박성 요소 권장
- 과도한 게임 시간 권장

요약은 사용자가 직접 입력한 메모, 자막, 영상 제목/설명 등 접근 가능한 정보만 바탕으로 생성됩니다.

## 3. 기술 스택

- Python 3.11+
- Streamlit
- Google GenAI Python SDK (`google-genai`)
- Gemini API 기본 모델: `gemini-2.5-flash`
- YouTube Data API 검색 endpoint
- JSON 파일 저장

## 4. 파일 구조

```text
strategy_note_ai_mvp/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ .streamlit/
│  ├─ config.toml
│  └─ secrets.toml.example
├─ data/
│  └─ .gitkeep
└─ src/
   ├─ __init__.py
   ├─ config.py
   ├─ schemas.py
   ├─ ai_summarizer.py
   ├─ youtube_client.py
   ├─ storage.py
   └─ ui_components.py
```

## 5. 로컬 실행 방법

### Windows PowerShell 기준

```powershell
cd strategy_note_ai_mvp
python -m venv .venv
.\.venv\Scriptsctivate
pip install -r requirements.txt
streamlit run app.py
```

### macOS/Linux 기준

```bash
cd strategy_note_ai_mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 6. Gemini API 키 설정

`.streamlit/secrets.toml.example` 파일을 복사해서 `.streamlit/secrets.toml`로 만드세요.

```toml
GEMINI_API_KEY = "AIza..."
GEMINI_MODEL = "gemini-2.5-flash"
YOUTUBE_API_KEY = "AIza..."
```

- `GEMINI_API_KEY`: 공략노트 생성에 필요합니다.
- `GEMINI_MODEL`: 사용할 Gemini 모델명입니다. 기본값은 `gemini-2.5-flash`입니다.
- `YOUTUBE_API_KEY`: YouTube 검색 기능을 사용할 때만 필요합니다.

`secrets.toml`은 절대 GitHub에 올리면 안 됩니다. `.gitignore`에 이미 제외되어 있습니다.

## 7. Google AI Studio에서 Gemini API 키 받기

1. Google AI Studio에 접속합니다.
2. API key 메뉴에서 새 키를 만듭니다.
3. 발급받은 키를 `.streamlit/secrets.toml`에 넣습니다.
4. Streamlit Cloud 배포 시에는 파일로 올리지 말고, 앱의 Secrets 설정에 넣습니다.

## 8. 사용 방법

1. 앱을 실행합니다.
2. `새 공략노트 만들기` 메뉴에서 게임명과 공략 주제를 입력합니다.
3. 영상 자막 또는 직접 정리한 공략 메모를 붙여넣습니다.
4. `공략노트 만들기` 버튼을 누릅니다.
5. 결과가 마음에 들면 `저장하기`를 누릅니다.
6. `저장된 공략 보기` 메뉴에서 이전 결과를 다시 확인합니다.

## 9. YouTube 검색 사용 방법

YouTube 검색은 선택 기능입니다.

1. `.streamlit/secrets.toml`에 `YOUTUBE_API_KEY`를 입력합니다.
2. `YouTube 영상 검색` expander를 엽니다.
3. 검색어를 입력하고 검색합니다.
4. 참고할 영상 1~5개를 선택합니다.
5. 선택된 영상의 제목/설명/링크만 AI 입력에 포함됩니다.

## 10. Streamlit Community Cloud 배포

1. GitHub에 이 프로젝트를 올립니다.
2. 단, `.streamlit/secrets.toml`은 올리지 않습니다.
3. Streamlit Community Cloud에서 새 앱을 생성합니다.
4. Advanced settings 또는 Secrets 설정에 아래 내용을 붙여넣습니다.

```toml
GEMINI_API_KEY = "AIza..."
GEMINI_MODEL = "gemini-2.5-flash"
YOUTUBE_API_KEY = "AIza..."
```

5. `app.py`를 entry point로 배포합니다.

## 11. 향후 확장 계획

- Supabase 로그인/DB 저장
- 가족별 공략노트 기록장
- 아이가 직접 쓰는 “오늘 배운 점” 기능
- A4 인쇄용 공략 카드
- 게임별 템플릿
- 부모용 학습 피드백 리포트
- 모바일 화면 최적화

## 12. 문제 해결

### GEMINI_API_KEY가 없다고 나와요

`.streamlit/secrets.toml` 파일이 있는지, 키 이름이 정확히 `GEMINI_API_KEY`인지 확인하세요.

### Gemini 응답을 JSON으로 해석하지 못했다고 나와요

같은 입력으로 한 번 더 실행해보세요. 앱은 1회 재시도 로직을 포함합니다. 계속 실패하면 메모 길이를 줄이거나, 공략 주제를 더 구체적으로 입력하세요.

### YouTube 검색이 안 돼요

`YOUTUBE_API_KEY`가 없으면 검색 기능은 작동하지 않습니다. 메모 입력형 요약은 YouTube 키 없이도 가능합니다.

### 저장이 안 돼요

`data/` 폴더에 쓰기 권한이 있는지 확인하세요. 저장 파일은 `data/strategy_notes.json`에 생성됩니다.
