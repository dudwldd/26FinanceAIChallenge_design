"""Streamlit entry point for the Investment Thesis Checker POC."""

import streamlit as st

from data.financial_data import FinancialDataError, get_financial_data


THESIS_FACTORS = [
    "밸류에이션이 매력적이라고 판단했다",
    "매출·이익 등 성장성이 높다고 판단했다",
    "수익성이 좋다고 판단했다",
    "부채·현금흐름 등 재무 상태가 안정적이라고 판단했다",
    "최근 주가 흐름이 긍정적이라고 판단했다",
    "산업·제품의 미래 전망이 좋다고 판단했다",
    "위험 대비 기대수익이 적절하다고 판단했다",
    "기타",
]

DECISION_TRIGGERS = [
    "최근 실적 또는 공시를 확인했다",
    "과거부터 지켜보며 장기적인 변화를 확인했다",
    "동종 기업이나 시장 평균과 비교했다",
    "산업 전망이나 관련 뉴스를 접했다",
    "최근 주가 상승 또는 하락을 보고 관심이 생겼다",
    "제품·서비스를 직접 경험했다",
    "아직 뚜렷한 계기는 없다",
]

EVIDENCE_LEVELS = [
    "아직 별도의 자료를 확인하지 않았다",
    "뉴스·영상·커뮤니티 자료를 주로 확인했다",
    "회사의 실적 발표나 재무지표를 확인했다",
    "경쟁사·과거 수치와 함께 비교했다",
    "여러 출처를 비교하고 반대 근거도 확인했다",
]

INVESTMENT_HORIZONS = [
    "6개월 미만",
    "6개월 이상 1년 미만",
    "1년 이상 3년 미만",
    "3년 이상",
    "아직 정하지 않았다",
]

LOSS_RESPONSES = [
    "손실을 줄이기 위해 매도할 가능성이 높다",
    "투자 논리와 최신 데이터를 다시 검토한 뒤 결정한다",
    "처음의 투자 논리가 유효하다면 보유한다",
    "투자 논리가 유효하다면 추가 매수를 검토한다",
    "아직 생각해보지 않았다",
]


st.set_page_config(page_title="Investment Thesis Checker")
st.title("Investment Thesis Checker")
st.caption("투자 결정을 대신하지 않고, 입력한 투자 논리와 근거를 점검합니다.")

with st.form("thesis_form"):
    ticker = st.text_input("미국 상장주식 티커", placeholder="예: AAPL")
    thesis = st.text_area(
        "현재 투자 판단",
        placeholder="예: 애플은 다른 빅테크보다 PER이 낮고 매출도 성장하고 있어 투자하고 싶다.",
        help="매수·관망·매도 등 현재 생각과 그 이유를 자유롭게 적어주세요.",
    )

    st.subheader("판단 근거 점검")
    thesis_factors = st.multiselect(
        "1. 이 판단에서 중요하게 본 근거는 무엇인가요? (복수 선택 가능)",
        THESIS_FACTORS,
    )
    decision_trigger = st.radio(
        "2. 이 종목에 대한 판단을 하게 된 가장 큰 계기는 무엇인가요?",
        DECISION_TRIGGERS,
        index=None,
    )
    evidence_level = st.radio(
        "3. 판단하기 전에 어느 정도까지 자료를 확인했나요?",
        EVIDENCE_LEVELS,
        index=None,
    )
    investment_horizon = st.radio(
        "4. 예상하는 투자 기간은 어느 정도인가요?",
        INVESTMENT_HORIZONS,
        index=None,
        horizontal=True,
    )
    loss_response = st.radio(
        "5. 매수 후 주가가 30% 하락한다면 어떻게 대응할 가능성이 가장 높은가요?",
        LOSS_RESPONSES,
        index=None,
    )

    submitted = st.form_submit_button("Check my thesis")

if submitted:
    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker:
        st.error("Please enter a ticker.")
    elif not thesis.strip():
        st.error("Please enter your investment thesis.")
    elif not all(
        [
            thesis_factors,
            decision_trigger,
            evidence_level,
            investment_horizon,
            loss_response,
        ]
    ):
        st.error("판단 근거 점검 문항에 모두 응답해주세요.")
    else:
        st.subheader("입력 내용")
        st.write(f"Ticker: {normalized_ticker}")
        st.write(f"투자 판단: {thesis.strip()}")
        st.write("핵심 근거: " + ", ".join(thesis_factors))
        st.write(f"판단 계기: {decision_trigger}")
        st.write(f"자료 확인 수준: {evidence_level}")
        st.write(f"예상 투자 기간: {investment_horizon}")
        st.write(f"30% 하락 시 예상 대응: {loss_response}")

        try:
            with st.spinner("Loading financial data..."):
                financial_data = get_financial_data(normalized_ticker)
        except FinancialDataError as exc:
            st.error(str(exc))
        else:
            st.subheader("Financial data")
            st.json(financial_data)
