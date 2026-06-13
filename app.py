from __future__ import annotations

import streamlit as st

from src.ai_summarizer import generate_strategy_note
from src.config import APP_NAME
from src.schemas import StrategyNote, UserInput
from src.storage import JsonStorage, make_input_hash
from src.ui_components import (
    format_datetime,
    inject_css,
    note_to_markdown,
    render_policy_notice,
    render_strategy_note,
    render_video_results,
)
from src.youtube_client import YouTubeSearchError, search_youtube_videos

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="expanded",
)

inject_css()
storage = JsonStorage()


def init_session_state() -> None:
    st.session_state.setdefault("youtube_results", [])
    st.session_state.setdefault("current_note", None)
    st.session_state.setdefault("current_user_input", None)


def render_sidebar() -> str:
    st.sidebar.title("🎮 공략노트 AI")
    st.sidebar.caption("게임 공략을 초등학생 눈높이로 바꾸는 가족용 웹앱")
    menu = st.sidebar.radio(
        "메뉴",
        ["새 공략노트 만들기", "저장된 공략 보기", "설정/사용법"],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **사용 순서**
        1. 게임명과 공략 주제를 입력합니다.
        2. 영상 메모나 자막을 붙여넣습니다.
        3. AI가 초4~5 눈높이 공략노트를 만듭니다.
        4. 좋은 결과는 저장합니다.
        """
    )
    st.sidebar.info("YouTube 검색은 선택 기능입니다. 메모만 입력해도 공략노트를 만들 수 있습니다.")
    return menu


def build_user_input(selected_videos) -> UserInput:
    return UserInput(
        game_name=st.session_state.get("game_name", "").strip(),
        topic=st.session_state.get("topic", "").strip(),
        skill_level=st.session_state.get("skill_level", "완전 초보"),
        grade_level=st.session_state.get("grade_level", "초4-5"),
        selected_videos=selected_videos,
        manual_notes=st.session_state.get("manual_notes", "").strip(),
        child_question=st.session_state.get("child_question", "").strip(),
        practice_goal=st.session_state.get("practice_goal", "").strip(),
    )


def render_create_page() -> None:
    st.title("🎮 공략노트 AI")
    st.write("유튜브 공략 영상 정보나 직접 적은 메모를 초등학교 4~5학년 아이가 이해하기 쉬운 공략노트로 바꿔줍니다.")

    with st.container(border=True):
        st.subheader("1단계. 공략 주제 입력")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("게임 이름", placeholder="예: 브롤스타즈", key="game_name")
            st.selectbox("아이의 실력", ["완전 초보", "조금 해봄", "꽤 잘함"], key="skill_level")
        with col2:
            st.text_input("공략 주제", placeholder="예: 모티스 잘하는 법", key="topic")
            st.selectbox("요약 난이도", ["초4", "초5", "초4-5"], index=2, key="grade_level")

        st.text_input("아이가 궁금해하는 점", placeholder="예: 왜 자꾸 들어가자마자 죽는지 궁금해요", key="child_question")
        st.text_input("오늘 연습 목표", placeholder="예: 무리해서 들어가지 않고 궁극기 아껴쓰기", key="practice_goal")

    with st.expander("선택 기능: YouTube 영상 검색", expanded=False):
        st.caption("공식 YouTube Data API 검색만 사용합니다. 영상 다운로드, 음성 추출, 비공식 자막 수집은 하지 않습니다.")
        default_query = " ".join([st.session_state.get("game_name", ""), st.session_state.get("topic", ""), "공략"]).strip()
        query = st.text_input("검색어", value=default_query, placeholder="예: 브롤스타즈 모티스 공략")
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            max_results = st.number_input("검색 개수", min_value=1, max_value=10, value=5)
        with col_b:
            search_button = st.button("검색", type="secondary")
        if search_button:
            try:
                with st.spinner("YouTube 검색 중..."):
                    st.session_state.youtube_results = search_youtube_videos(query=query, max_results=int(max_results))
                st.success(f"검색 결과 {len(st.session_state.youtube_results)}개를 가져왔습니다.")
            except YouTubeSearchError as exc:
                st.error(str(exc))

        selected_videos = render_video_results(st.session_state.youtube_results)
    
    st.subheader("2단계. 자막/메모 입력")
    st.text_area(
        "영상 자막 또는 직접 정리한 공략 메모를 붙여넣으세요",
        placeholder="예: 모티스는 무작정 들어가면 안 되고, 적 스킬이 빠진 다음 벽을 이용해서 들어가야 한다...",
        height=260,
        key="manual_notes",
    )

    st.caption("메모가 많을수록 더 정확합니다. 메모가 없으면 영상 제목/설명과 입력 정보 기준으로 제한적 요약만 생성합니다.")

    col_make, col_reset = st.columns([2, 1])
    with col_make:
        make_button = st.button("🚀 공략노트 만들기", type="primary", use_container_width=True)
    with col_reset:
        if st.button("초기화", use_container_width=True):
            st.session_state.current_note = None
            st.session_state.current_user_input = None
            st.session_state.youtube_results = []
            st.rerun()

    if make_button:
        selected_videos = selected_videos or []
        user_input = build_user_input(selected_videos)
        if not user_input.game_name or not user_input.topic:
            st.warning("게임 이름과 공략 주제는 반드시 입력해주세요.")
            return

        input_hash = make_input_hash(user_input)
        cached_note = storage.find_by_input_hash(input_hash)
        if cached_note:
            st.info("같은 입력으로 만든 공략노트가 있어 저장된 결과를 불러왔습니다.")
            note = StrategyNote.from_dict(cached_note.strategy_note)
            st.session_state.current_note = note
            st.session_state.current_user_input = user_input
        else:
            try:
                with st.spinner("AI가 아이 눈높이 공략노트를 만드는 중..."):
                    note = generate_strategy_note(user_input)
                st.session_state.current_note = note
                st.session_state.current_user_input = user_input
            except Exception as exc:
                st.error(str(exc))
                st.info("GEMINI_API_KEY를 .streamlit/secrets.toml에 넣었는지 확인해주세요. 키 없이도 화면 구성과 저장 목록은 볼 수 있습니다.")
                return

    current_note = st.session_state.get("current_note")
    current_user_input = st.session_state.get("current_user_input")
    if current_note:
        st.markdown("---")
        render_strategy_note(current_note)
        md = note_to_markdown(current_note)
        st.download_button(
            "📄 마크다운 파일로 내려받기",
            data=md.encode("utf-8"),
            file_name="strategy_note.md",
            mime="text/markdown",
        )
        with st.expander("복사용 텍스트 보기"):
            st.code(md, language="markdown")

        if current_user_input and st.button("💾 이 공략노트 저장하기", type="secondary"):
            saved = storage.save_note(current_user_input, current_note)
            st.success(f"저장했습니다. ID: {saved.note_id[:8]}")

    st.markdown("---")
    render_policy_notice()


def render_saved_page() -> None:
    st.title("📚 저장된 공략노트")
    notes = storage.list_notes()
    if not notes:
        st.info("아직 저장된 공략노트가 없습니다.")
        return

    labels = [f"{n.game_name} · {n.topic} · {format_datetime(n.created_at)}" for n in notes]
    selected_idx = st.selectbox("불러올 공략노트", range(len(labels)), format_func=lambda i: labels[i])
    selected = notes[selected_idx]
    note = StrategyNote.from_dict(selected.strategy_note)

    render_strategy_note(note)
    md = note_to_markdown(note)
    st.download_button(
        "📄 마크다운 파일로 내려받기",
        data=md.encode("utf-8"),
        file_name=f"{selected.game_name}_{selected.topic}_strategy_note.md".replace("/", "_"),
        mime="text/markdown",
    )

    with st.expander("저장된 입력 정보 보기"):
        st.json(selected.user_input)

    if st.button("🗑️ 이 공략노트 삭제", type="secondary"):
        storage.delete_note(selected.note_id)
        st.success("삭제했습니다.")
        st.rerun()


def render_settings_page() -> None:
    st.title("⚙️ 설정/사용법")
    st.markdown(
        """
        ## 로컬 실행 순서

        ```bash
        python -m venv .venv
        .venv\\Scripts\\activate  # Windows
        pip install -r requirements.txt
        streamlit run app.py
        ```

        ## API 키 설정

        `.streamlit/secrets.toml.example` 파일을 복사해서 `.streamlit/secrets.toml`로 만든 뒤 아래처럼 입력합니다.

        ```toml
        GEMINI_API_KEY = "AIza..."
        GEMINI_MODEL = "gemini-2.5-flash"
        YOUTUBE_API_KEY = "AIza..."
        ```

        - `GEMINI_API_KEY`: 공략노트 생성에 필요합니다.
        - `GEMINI_MODEL`: 기본값은 `gemini-2.5-flash`입니다.
        - `YOUTUBE_API_KEY`: YouTube 검색 기능에만 필요합니다.
        - YouTube 검색을 쓰지 않고 메모만 넣는 MVP는 `YOUTUBE_API_KEY` 없이도 가능합니다.

        ## 하지 않는 것

        - 유튜브 영상 다운로드 안 함
        - 음성 추출 안 함
        - 비공식 자막 스크래핑 안 함
        - 남의 영상 내용을 봤다고 허위 표시 안 함
        """
    )
    render_policy_notice()


def main() -> None:
    init_session_state()
    menu = render_sidebar()
    if menu == "새 공략노트 만들기":
        render_create_page()
    elif menu == "저장된 공략 보기":
        render_saved_page()
    else:
        render_settings_page()


if __name__ == "__main__":
    main()
