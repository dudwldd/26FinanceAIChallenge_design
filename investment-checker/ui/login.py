"""Login gate used by the Streamlit prototype."""

import re

import streamlit as st


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def render_login() -> bool:
    """Render the Figma-inspired demo login and return its login state."""
    if st.session_state.get("authenticated", False):
        return True

    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    intro_column, form_column = st.columns([1.08, 0.92], gap="large")

    with intro_column:
        st.markdown(
            """
            <section class="login-intro">
                <span class="login-eyebrow">투자 논리 점검 도구</span>
                <h1>투자 판단의 답보다,<br>근거를 먼저 점검합니다.</h1>
                <p class="login-lead">
                    포트폴리오 추천 없이 내가 세운 투자 논리와<br>
                    판단 근거를 점검해보세요.
                </p>
                <div class="login-feature-list">
                    <div><span>▥</span> 포트폴리오 비중 및 구성 논리 입력</div>
                    <div><span>⌕</span> 5가지 판단 근거 점검 질문</div>
                    <div><span>✦</span> AI 기반 행동편향 및 논리 정합성 분석</div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with form_column:
        st.markdown('<div class="login-form-heading">', unsafe_allow_html=True)
        st.subheader("로그인")
        st.caption("계정에 로그인하여 계속하세요.")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.form("demo_login_form"):
            email = st.text_input(
                "이메일",
                placeholder="name@example.com",
                autocomplete="email",
            )
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="••••••••",
                autocomplete="current-password",
            )
            option_column, link_column = st.columns([1.25, 0.75])
            with option_column:
                st.checkbox("로그인 상태 유지", key="remember_login")
            with link_column:
                st.markdown(
                    '<div class="login-help">비밀번호 찾기</div>',
                    unsafe_allow_html=True,
                )

            submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            if not EMAIL_PATTERN.match(email.strip()):
                st.error("올바른 이메일 주소를 입력해주세요.")
            elif not password:
                st.error("비밀번호를 입력해주세요.")
            else:
                st.session_state["authenticated"] = True
                st.session_state["login_email"] = email.strip()
                st.rerun()

        st.markdown('<div class="login-divider"><span>또는</span></div>', unsafe_allow_html=True)
        if st.button("G  Google로 로그인", use_container_width=True):
            st.info("Google 로그인은 실제 인증 연동 단계에서 활성화됩니다.")
        st.markdown(
            '<p class="login-signup">아직 계정이 없으신가요? '
            '<span>회원가입</span></p>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("현재 로그인 화면은 UI 검토를 위한 시연용이며 실제 계정 인증을 수행하지 않습니다.")
    return False
