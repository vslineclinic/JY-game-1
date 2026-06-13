from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _limit_list(items: list[Any] | None, max_items: int) -> list[Any]:
    if not items:
        return []
    return list(items)[:max_items]


@dataclass
class VideoResult:
    video_id: str
    title: str
    channel_title: str
    published_at: str
    description: str
    thumbnail_url: str
    youtube_url: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoResult":
        return cls(
            video_id=_clean_text(data.get("video_id")),
            title=_clean_text(data.get("title")),
            channel_title=_clean_text(data.get("channel_title")),
            published_at=_clean_text(data.get("published_at")),
            description=_clean_text(data.get("description")),
            thumbnail_url=_clean_text(data.get("thumbnail_url")),
            youtube_url=_clean_text(data.get("youtube_url")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserInput:
    game_name: str
    topic: str
    skill_level: str
    grade_level: str
    selected_videos: list[VideoResult] = field(default_factory=list)
    manual_notes: str = ""
    child_question: str = ""
    practice_goal: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserInput":
        videos = [VideoResult.from_dict(v) for v in data.get("selected_videos", [])]
        return cls(
            game_name=_clean_text(data.get("game_name")),
            topic=_clean_text(data.get("topic")),
            skill_level=_clean_text(data.get("skill_level"), "완전 초보"),
            grade_level=_clean_text(data.get("grade_level"), "초4-5"),
            selected_videos=videos,
            manual_notes=_clean_text(data.get("manual_notes")),
            child_question=_clean_text(data.get("child_question")),
            practice_goal=_clean_text(data.get("practice_goal")),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["selected_videos"] = [v.to_dict() for v in self.selected_videos]
        return data


@dataclass
class CoreTip:
    tip: str
    why_it_matters: str
    kid_friendly_example: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoreTip":
        return cls(
            tip=_clean_text(data.get("tip")),
            why_it_matters=_clean_text(data.get("why_it_matters")),
            kid_friendly_example=_clean_text(data.get("kid_friendly_example")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommonMistake:
    mistake: str
    fix: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommonMistake":
        return cls(
            mistake=_clean_text(data.get("mistake")),
            fix=_clean_text(data.get("fix")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GameTerm:
    term: str
    easy_meaning: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameTerm":
        return cls(
            term=_clean_text(data.get("term")),
            easy_meaning=_clean_text(data.get("easy_meaning")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QuizItem:
    question: str
    answer: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuizItem":
        return cls(
            question=_clean_text(data.get("question")),
            answer=_clean_text(data.get("answer")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyNote:
    title: str
    one_line_summary: str
    today_goal: str
    quick_summary: str
    core_tips: list[CoreTip] = field(default_factory=list)
    step_by_step: list[str] = field(default_factory=list)
    common_mistakes: list[CommonMistake] = field(default_factory=list)
    terms: list[GameTerm] = field(default_factory=list)
    practice_missions: list[str] = field(default_factory=list)
    quiz: list[QuizItem] = field(default_factory=list)
    parent_comment: str = ""
    safety_note: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrategyNote":
        return cls(
            title=_clean_text(data.get("title"), "공략노트"),
            one_line_summary=_clean_text(data.get("one_line_summary")),
            today_goal=_clean_text(data.get("today_goal")),
            quick_summary=_clean_text(data.get("quick_summary")),
            core_tips=[CoreTip.from_dict(x) for x in _limit_list(data.get("core_tips"), 5)],
            step_by_step=[_clean_text(x) for x in _limit_list(data.get("step_by_step"), 8) if _clean_text(x)],
            common_mistakes=[CommonMistake.from_dict(x) for x in _limit_list(data.get("common_mistakes"), 5)],
            terms=[GameTerm.from_dict(x) for x in _limit_list(data.get("terms"), 6)],
            practice_missions=[_clean_text(x) for x in _limit_list(data.get("practice_missions"), 3) if _clean_text(x)],
            quiz=[QuizItem.from_dict(x) for x in _limit_list(data.get("quiz"), 3)],
            parent_comment=_clean_text(data.get("parent_comment")),
            safety_note=_clean_text(data.get("safety_note"), "짧게 연습하고 중간중간 쉬는 시간을 가지세요."),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "one_line_summary": self.one_line_summary,
            "today_goal": self.today_goal,
            "quick_summary": self.quick_summary,
            "core_tips": [x.to_dict() for x in self.core_tips],
            "step_by_step": self.step_by_step,
            "common_mistakes": [x.to_dict() for x in self.common_mistakes],
            "terms": [x.to_dict() for x in self.terms],
            "practice_missions": self.practice_missions,
            "quiz": [x.to_dict() for x in self.quiz],
            "parent_comment": self.parent_comment,
            "safety_note": self.safety_note,
        }


def strategy_note_json_schema() -> dict[str, Any]:
    """JSON Schema used for Gemini Structured Outputs."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "title",
            "one_line_summary",
            "today_goal",
            "quick_summary",
            "core_tips",
            "step_by_step",
            "common_mistakes",
            "terms",
            "practice_missions",
            "quiz",
            "parent_comment",
            "safety_note",
        ],
        "properties": {
            "title": {"type": "string"},
            "one_line_summary": {"type": "string"},
            "today_goal": {"type": "string"},
            "quick_summary": {"type": "string"},
            "core_tips": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["tip", "why_it_matters", "kid_friendly_example"],
                    "properties": {
                        "tip": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                        "kid_friendly_example": {"type": "string"},
                    },
                },
            },
            "step_by_step": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
            "common_mistakes": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["mistake", "fix"],
                    "properties": {
                        "mistake": {"type": "string"},
                        "fix": {"type": "string"},
                    },
                },
            },
            "terms": {
                "type": "array",
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["term", "easy_meaning"],
                    "properties": {
                        "term": {"type": "string"},
                        "easy_meaning": {"type": "string"},
                    },
                },
            },
            "practice_missions": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
            "quiz": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["question", "answer"],
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                    },
                },
            },
            "parent_comment": {"type": "string"},
            "safety_note": {"type": "string"},
        },
    }
