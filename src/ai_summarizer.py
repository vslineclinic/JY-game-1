from __future__ import annotations

import json
from typing import Any

from google import genai

from src.config import get_gemini_api_key, get_gemini_model
from src.schemas import StrategyNote, UserInput, VideoResult, strategy_note_json_schema

MAX_MANUAL_NOTES_CHARS = 12000
MAX_VIDEO_DESCRIPTION_CHARS = 600

RISK_KEYWORDS = [
    "현질",
    "과금",
    "뽑기",
    "확률",
    "도박",
    "카지노",
    "계정거래",
    "대리랭",
    "핵",
    "치트",
    "버그판",
    "무료 다이아",
    "무료 로벅스",
    "개인정보",
    "비밀번호",
]

SYSTEM_PROMPT = """
너는 초등학교 4~5학년 아이에게 게임 공략을 쉽게 설명해주는 친절한 코치다.

목표:
- 어려운 게임 용어를 쉬운 말로 바꾼다.
- 아이가 바로 따라 할 수 있는 순서로 정리한다.
- 폭력적이거나 자극적인 표현은 줄이고, 연습/전략/판단 중심으로 설명한다.
- 과금, 현질, 뽑기, 도박성 요소를 부추기지 않는다.
- 과도한 게임 시간을 권장하지 않는다.
- 욕설, 혐오, 선정적 표현을 제거한다.
- 개인정보 입력, 계정 공유, 외부 사이트 접속을 유도하지 않는다.
- 원본 영상 내용을 그대로 길게 복사하지 않고, 사용자가 제공한 정보에서 핵심만 새롭게 재구성한다.
- 영상 제목/설명만 있는 경우에는 "영상 내용을 직접 확인했다"고 말하지 않는다.
- 초등학교 4~5학년이 읽을 수 있도록 짧은 문장으로 쓴다.
- 너무 유치하게 쓰지 말고, 똑똑한 초등학생에게 설명하듯 작성한다.
- 결과는 반드시 지정된 JSON Schema에 맞춰 작성한다.
""".strip()


def _trim_text(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.65)]
    tail = text[-int(max_chars * 0.25) :]
    return f"{head}\n\n...[중간 내용 일부 생략: 너무 긴 입력을 비용 절감을 위해 줄였습니다]...\n\n{tail}"


def detect_risk_keywords(text: str) -> list[str]:
    lower = (text or "").lower()
    return [kw for kw in RISK_KEYWORDS if kw.lower() in lower]


def format_video_metadata(videos: list[VideoResult]) -> str:
    if not videos:
        return "선택된 유튜브 영상 없음. 사용자가 입력한 메모를 중심으로 작성한다."

    lines: list[str] = []
    for idx, video in enumerate(videos[:5], start=1):
        desc = _trim_text(video.description, MAX_VIDEO_DESCRIPTION_CHARS)
        lines.append(
            f"""
[{idx}]
제목: {video.title}
채널: {video.channel_title}
업로드일: {video.published_at}
링크: {video.youtube_url}
설명 일부: {desc}
""".strip()
        )
    return "\n\n".join(lines)


def build_user_prompt(user_input: UserInput) -> str:
    manual_notes = _trim_text(user_input.manual_notes, MAX_MANUAL_NOTES_CHARS)
    selected_video_metadata = format_video_metadata(user_input.selected_videos)
    risks = detect_risk_keywords("\n".join([manual_notes, selected_video_metadata]))
    risk_instruction = ""
    if risks:
        risk_instruction = (
            "\n[주의: 입력 내용에 다음 위험/주의 키워드가 포함됨]\n"
            + ", ".join(sorted(set(risks)))
            + "\n위 내용은 권장하지 말고, 안전한 게임 습관과 연습 중심 표현으로 바꿔 설명한다."
        )

    return f"""
아래 정보를 바탕으로 초등학교 4~5학년 아이가 이해할 수 있는 게임 공략노트를 만들어줘.

[게임 이름]
{user_input.game_name}

[공략 주제]
{user_input.topic}

[아이의 실력]
{user_input.skill_level}

[요약 난이도]
{user_input.grade_level}

[아이의 질문]
{user_input.child_question or "없음"}

[오늘 연습 목표]
{user_input.practice_goal or "없음"}

[선택한 유튜브 영상 정보]
{selected_video_metadata}

[사용자가 직접 입력한 자막/메모]
{manual_notes or "사용자 메모 없음. 영상 제목/설명과 입력 정보만 바탕으로 제한적으로 작성한다."}
{risk_instruction}

작성 기준:
1. 어려운 단어는 쉬운 말로 설명한다.
2. 아이가 바로 따라 할 수 있는 순서로 정리한다.
3. 핵심 공략은 최대 5개로 제한한다.
4. 초보자가 자주 하는 실수와 고치는 방법을 넣는다.
5. 마지막에는 오늘 바로 해볼 수 있는 연습 미션 3개를 제시한다.
6. 복습 퀴즈 3개를 만든다.
7. 원본 영상 내용을 그대로 복사하지 말고, 짧고 이해하기 쉽게 재구성한다.
8. 과금 유도, 도박성 뽑기, 과몰입을 부추기는 내용은 제외한다.
9. 입력이 부족하면 확실하지 않은 내용을 단정하지 말고, '제공된 정보 기준'으로 정리한다.
10. JSON 외의 설명문, 마크다운 코드블록, ``` 표시는 절대 쓰지 않는다.
""".strip()


def _strip_code_fence(content: str) -> str:
    content = (content or "").strip()
    if content.startswith("```"):
        lines = content.splitlines()
        # remove first fence line such as ```json and last fence line ```
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return content


def _parse_strategy_note(content: str) -> StrategyNote:
    content = _strip_code_fence(content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI 응답을 JSON으로 해석하지 못했습니다: {exc}") from exc
    return StrategyNote.from_dict(data)


def _gemini_config(use_schema: bool = True) -> dict[str, Any]:
    config: dict[str, Any] = {
        "temperature": 0.35,
        "max_output_tokens": 4096,
        "response_mime_type": "application/json",
    }
    if use_schema:
        config["response_json_schema"] = strategy_note_json_schema()
    return config


def _generate_once(client: genai.Client, model: str, user_input: UserInput, use_schema: bool = True) -> StrategyNote:
    prompt = f"{SYSTEM_PROMPT}\n\n{build_user_prompt(user_input)}"
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=_gemini_config(use_schema=use_schema),
    )
    content = response.text or "{}"
    return _parse_strategy_note(content)


def generate_strategy_note(user_input: UserInput) -> StrategyNote:
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 없습니다. .streamlit/secrets.toml 또는 환경변수에 설정하세요.")

    client = genai.Client(api_key=api_key)
    model = get_gemini_model()

    # First attempt: Gemini structured output with JSON Schema.
    try:
        return _generate_once(client, model, user_input, use_schema=True)
    except Exception:
        # Second attempt: JSON MIME type without schema, with an additional strict instruction.
        retry_input = UserInput.from_dict(user_input.to_dict())
        retry_input.manual_notes = (
            user_input.manual_notes
            + "\n\n[재시도 지시] 반드시 유효한 JSON 객체 하나만 출력해. 마크다운 코드블록은 쓰지 마."
        )
        return _generate_once(client, model, retry_input, use_schema=False)
