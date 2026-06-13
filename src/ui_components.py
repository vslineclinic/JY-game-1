from __future__ import annotations

from datetime import datetime
from typing import Iterable

import streamlit as st

from src.schemas import StrategyNote, VideoResult


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container { padding-top: 2rem; max-width: 980px; }
        .gn-card {
            background: #ffffff;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 18px 20px;
            margin: 12px 0;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
        }
        .gn-muted { color: #6B7280; font-size: 0.92rem; }
        .gn-small { font-size: 0.86rem; }
        .gn-badge {
            display: inline-block;
            background: #EEF2FF;
            color: #3730A3;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.82rem;
            margin-right: 6px;
        }
        .gn-policy {
            background: #F8FAFC;
            border-left: 4px solid #4F8BF9;
            padding: 12px 14px;
            border-radius: 10px;
            color: #334155;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_policy_notice() -> None:
    st.markdown(
        """
        <div class="gn-policy">
        이 앱은 유튜브 영상을 다운로드하거나 음성을 추출하지 않습니다.<br>
        사용자가 직접 입력한 메모, 자막, 영상 제목/설명 등 접근 가능한 정보만 바탕으로 공략노트를 생성합니다.<br>
        AI 요약은 원본 영상의 대체물이 아니며, 정확한 내용은 원본 영상을 확인해주세요.<br><br>
        게임은 오래 하는 것보다 똑똑하게 연습하는 것이 더 중요해요. 오늘 미션을 짧게 해보고, 쉬는 시간도 꼭 가지세요.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_video_results(videos: list[VideoResult]) -> list[VideoResult]:
    if not videos:
        return []

    options = {}
    for idx, video in enumerate(videos, start=1):
        label = f"{idx}. {video.title} — {video.channel_title}"
        options[label] = video

    selected_labels = st.multiselect(
        "요약 참고용 영상 선택 — 최대 5개",
        options=list(options.keys()),
        max_selections=5,
        help="선택한 영상의 제목/설명/링크만 AI 입력에 포함됩니다. 영상 본문을 자동으로 읽지는 않습니다.",
    )

    st.markdown("#### 검색 결과")
    for label, video in options.items():
        with st.container(border=True):
            col_thumb, col_text = st.columns([1, 3])
            with col_thumb:
                if video.thumbnail_url:
                    st.image(video.thumbnail_url, use_container_width=True)
            with col_text:
                st.markdown(f"**{video.title}**")
                st.caption(f"채널: {video.channel_title} · 업로드: {video.published_at[:10]}")
                if video.description:
                    st.write(video.description[:180] + ("..." if len(video.description) > 180 else ""))
                st.link_button("YouTube에서 보기", video.youtube_url)

    return [options[label] for label in selected_labels]


def _bullet_list(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def render_strategy_note(note: StrategyNote) -> None:
    st.markdown(f"## {note.title}")
    st.markdown(f"<span class='gn-badge'>초4~5 눈높이</span><span class='gn-badge'>연습 중심</span>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### 🎯 오늘의 목표")
        st.write(note.today_goal)
        st.markdown("### ⚡ 한 줄 요약")
        st.write(note.one_line_summary)
        st.markdown("### ⏱️ 30초 요약")
        st.write(note.quick_summary)

    with st.container(border=True):
        st.markdown("### ✅ 핵심 공략")
        for idx, tip in enumerate(note.core_tips, start=1):
            st.markdown(f"**{idx}. {tip.tip}**")
            st.write(f"왜 중요해? {tip.why_it_matters}")
            st.caption(f"예시: {tip.kid_friendly_example}")

    with st.container(border=True):
        st.markdown("### 🪜 따라 하는 순서")
        for idx, step in enumerate(note.step_by_step, start=1):
            st.write(f"{idx}. {step}")

    with st.container(border=True):
        st.markdown("### ⚠️ 초보 실수와 고치는 법")
        for item in note.common_mistakes:
            st.markdown(f"- **실수:** {item.mistake}")
            st.markdown(f"  - **고치는 법:** {item.fix}")

    if note.terms:
        with st.container(border=True):
            st.markdown("### 📘 어려운 말 쉽게 설명")
            for term in note.terms:
                st.markdown(f"- **{term.term}**: {term.easy_meaning}")

    with st.container(border=True):
        st.markdown("### 🏆 오늘 연습 미션")
        for idx, mission in enumerate(note.practice_missions, start=1):
            st.write(f"{idx}. {mission}")

    with st.container(border=True):
        st.markdown("### ❓ 복습 퀴즈")
        for idx, quiz in enumerate(note.quiz, start=1):
            with st.expander(f"문제 {idx}. {quiz.question}"):
                st.write(f"정답: {quiz.answer}")

    with st.container(border=True):
        st.markdown("### 👨‍👦 부모 코멘트")
        st.write(note.parent_comment)
        st.markdown("### 🧭 안전한 게임 습관")
        st.write(note.safety_note)


def note_to_markdown(note: StrategyNote) -> str:
    lines = [
        f"# {note.title}",
        "",
        f"## 오늘의 목표\n{note.today_goal}",
        "",
        f"## 한 줄 요약\n{note.one_line_summary}",
        "",
        f"## 30초 요약\n{note.quick_summary}",
        "",
        "## 핵심 공략",
    ]
    for idx, tip in enumerate(note.core_tips, start=1):
        lines.append(f"{idx}. {tip.tip}\n   - 왜 중요해? {tip.why_it_matters}\n   - 예시: {tip.kid_friendly_example}")
    lines.extend(["", "## 따라 하는 순서", _bullet_list(note.step_by_step)])
    lines.extend(["", "## 초보 실수와 고치는 법"])
    for item in note.common_mistakes:
        lines.append(f"- 실수: {item.mistake}\n  - 고치는 법: {item.fix}")
    lines.extend(["", "## 어려운 말 쉽게 설명"])
    for term in note.terms:
        lines.append(f"- {term.term}: {term.easy_meaning}")
    lines.extend(["", "## 오늘 연습 미션", _bullet_list(note.practice_missions)])
    lines.extend(["", "## 복습 퀴즈"])
    for idx, quiz in enumerate(note.quiz, start=1):
        lines.append(f"{idx}. {quiz.question}\n   - 정답: {quiz.answer}")
    lines.extend(["", "## 부모 코멘트", note.parent_comment, "", "## 안전한 게임 습관", note.safety_note])
    return "\n".join(lines)


def format_datetime(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value
