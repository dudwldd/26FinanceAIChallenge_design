"""Workflow navigation and transition screens."""

import time

import streamlit as st
import streamlit.components.v1 as components


STEPS = [
    ("portfolio", "포트폴리오 입력"),
    ("criteria", "투자 기준"),
    ("followup", "추가 질문"),
    ("result", "진단 결과"),
]


def scroll_to_top_on_screen_change(screen: str) -> None:
    """Reset the main viewport only when the workflow advances to another screen."""
    previous_screen = st.session_state.get("_last_workflow_screen")
    if previous_screen == screen:
        return
    st.session_state["_last_workflow_screen"] = screen
    components.html(
        """
        <script>
        const scrollMainToTop = () => {
            const doc = window.parent.document;
            const main = doc.querySelector('[data-testid="stMain"]');
            const view = doc.querySelector('[data-testid="stAppViewContainer"]');
            if (main) main.scrollTo({ top: 0, left: 0, behavior: 'instant' });
            if (view) view.scrollTo({ top: 0, left: 0, behavior: 'instant' });
            window.parent.scrollTo({ top: 0, left: 0, behavior: 'instant' });
        };
        scrollMainToTop();
        window.setTimeout(scrollMainToTop, 80);
        window.setTimeout(scrollMainToTop, 250);
        window.setTimeout(scrollMainToTop, 500);

        const shield = window.parent.document.getElementById('workflow-transition-shield');
        if (shield && %REMOVE_SHIELD%) {
            window.setTimeout(() => shield.remove(), 300);
        }
        </script>
        """.replace("%REMOVE_SHIELD%", "true" if screen != "loading" else "false"),
        height=0,
        width=0,
    )


def _keep_loading_background_covered() -> None:
    """Keep a white layer mounted across the loading-to-content rerun."""
    components.html(
        """
        <script>
        const doc = window.parent.document;
        if (!doc.getElementById('workflow-transition-shield')) {
            const shield = doc.createElement('div');
            shield.id = 'workflow-transition-shield';
            Object.assign(shield.style, {
                position: 'fixed',
                zIndex: '90',
                top: '70px',
                right: '0',
                bottom: '0',
                left: '0',
                background: '#ffffff'
            });
            doc.body.appendChild(shield);
        }
        </script>
        """,
        height=0,
        width=0,
    )


def render_step_navigation(active_step: str) -> None:
    """Render the compact four-step navigation used after login."""
    active_index = next(
        (index for index, step in enumerate(STEPS) if step[0] == active_step),
        0,
    )
    items = []
    for index, (_, label) in enumerate(STEPS):
        state = "is-active" if index == active_index else ""
        if index < active_index:
            state = "is-complete"
        items.append(
            f'<div class="workflow-step {state}"><span></span>{label}</div>'
        )
    st.markdown(
        '<nav class="workflow-nav"><b>Portfolio Thesis Checker</b>'
        f'<div class="workflow-steps">{"".join(items)}</div></nav>',
        unsafe_allow_html=True,
    )


def _loading_markup(active_index: int) -> str:
    stages = [
        ("포트폴리오 구성 파악", "입력한 종목, 비중, 투자 논리를 읽어들입니다"),
        ("데이터 대조", "재무 지표·상관관계와 투자 논리를 비교합니다"),
        ("추가 질문 생성", "논리에서 확인이 필요한 부분을 질문으로 만듭니다"),
    ]
    rows = []
    for index, (title, description) in enumerate(stages):
        if index < active_index:
            state, symbol = "complete", "✓"
        elif index == active_index:
            state, symbol = "active", "↻"
        else:
            state, symbol = "pending", "•"
        rows.append(
            f'<div class="loading-stage {state}">'
            f'<div class="loading-node">{symbol}</div>'
            f'<div><strong>{title}</strong><p>{description}</p></div>'
            '</div>'
        )
    return (
        '<section class="analysis-loading">'
        '<div class="loading-spinner"></div>'
        '<h1>추가 질문 생성 중</h1>'
        '<p class="loading-lead">입력하신 포트폴리오와 투자 논리를 바탕으로<br>'
        '확인이 필요한 부분을 분석하고 있습니다.</p>'
        f'<div class="loading-card">{"".join(rows)}</div>'
        '</section>'
    )


def render_question_loading() -> None:
    """Show a short staged transition, then advance to analysis."""
    _keep_loading_background_covered()
    placeholder = st.empty()
    for active_index in range(3):
        placeholder.markdown(
            _loading_markup(active_index),
            unsafe_allow_html=True,
        )
        time.sleep(0.9)
    placeholder.markdown(_loading_markup(3), unsafe_allow_html=True)
    time.sleep(0.55)
    st.session_state["workflow_screen"] = "analysis"
    st.session_state["analysis_processed"] = False
    st.rerun()
