"""Streamlit entry point for the Investment Thesis Checker POC."""

import pandas as pd
import streamlit as st

from data.financial_data import FinancialDataError, get_financial_data
from logic.portfolio import (
    PortfolioValidationError,
    calculate_concentration,
    validate_portfolio,
)


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


st.set_page_config(page_title="Portfolio Thesis Checker")
st.title("Portfolio Thesis Checker")
st.caption("포트폴리오를 추천하지 않고, 입력한 구성과 투자 논리를 점검합니다.")

with st.form("thesis_form"):
    st.subheader("포트폴리오 입력")
    portfolio_input = st.data_editor(
        pd.DataFrame(
            [
                {"ticker": "AAPL", "weight": 40.0},
                {"ticker": "MSFT", "weight": 30.0},
                {"ticker": "NVDA", "weight": 30.0},
            ]
        ),
        column_config={
            "ticker": st.column_config.TextColumn(
                "Ticker", help="미국 상장주식 ticker를 입력하세요."
            ),
            "weight": st.column_config.NumberColumn(
                "비중 (%)", min_value=0.01, max_value=100.0, format="%.2f"
            ),
        },
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
    )
    st.caption("최대 10개 종목까지 입력할 수 있으며 비중 합계는 100%여야 합니다.")

    thesis = st.text_area(
        "포트폴리오 구성 논리",
        placeholder="예: AI 성장주를 여러 기업에 나누어 투자해 위험을 분산했다고 생각한다.",
        help="이 종목들과 비중을 선택한 이유를 자유롭게 적어주세요.",
    )

    st.subheader("판단 근거 점검")
    thesis_factors = st.multiselect(
        "1. 이 판단에서 중요하게 본 근거는 무엇인가요? (복수 선택 가능)",
        THESIS_FACTORS,
    )
    decision_trigger = st.radio(
        "2. 이 포트폴리오를 구성하게 된 가장 큰 계기는 무엇인가요?",
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
        "5. 포트폴리오 가치가 30% 하락한다면 어떻게 대응할 가능성이 가장 높은가요?",
        LOSS_RESPONSES,
        index=None,
    )

    submitted = st.form_submit_button("Check my thesis")

if submitted:
    if not thesis.strip():
        st.error("포트폴리오 구성 논리를 입력해주세요.")
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
        try:
            holdings = validate_portfolio(portfolio_input.to_dict("records"))
        except PortfolioValidationError as exc:
            st.error(str(exc))
        else:
            financial_rows = []
            data_error = None

            try:
                with st.spinner("종목별 금융 데이터를 불러오는 중입니다..."):
                    for holding in holdings:
                        financial_data = get_financial_data(str(holding["ticker"]))
                        financial_rows.append(
                            {
                                "Ticker": financial_data["ticker"],
                                "회사명": financial_data["company_name"],
                                "비중 (%)": holding["weight"],
                                "현재 주가": financial_data["market_data"]["current_price"],
                                "시가총액": financial_data["market_data"]["market_cap"],
                                "P/E": financial_data["valuation"]["pe_ratio"],
                                "P/B": financial_data["valuation"]["pb_ratio"],
                                "매출 성장률": financial_data["growth"]["revenue_growth"],
                                "이익률": financial_data["profitability"]["profit_margin"],
                                "부채비율": financial_data["financial_health"][
                                    "debt_to_equity"
                                ],
                            }
                        )
            except FinancialDataError as exc:
                data_error = str(exc)

            if data_error:
                st.error(data_error)
            else:
                concentration = calculate_concentration(holdings)

                st.subheader("포트폴리오 구성")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("종목 수", f"{len(holdings)}개")
                metric_col2.metric(
                    "최대 비중 종목",
                    str(concentration["largest_ticker"]),
                    f'{concentration["largest_weight"]:.2f}%',
                )
                metric_col3.metric(
                    "상위 2개 종목 비중",
                    f'{concentration["top_two_weight"]:.2f}%',
                )

                st.dataframe(
                    pd.DataFrame(financial_rows),
                    hide_index=True,
                    width="stretch",
                )

                with st.expander("입력한 투자 논리와 응답 보기"):
                    st.write(f"포트폴리오 구성 논리: {thesis.strip()}")
                    st.write("핵심 근거: " + ", ".join(thesis_factors))
                    st.write(f"판단 계기: {decision_trigger}")
                    st.write(f"자료 확인 수준: {evidence_level}")
                    st.write(f"예상 투자 기간: {investment_horizon}")
                    st.write(f"30% 하락 시 예상 대응: {loss_response}")

                st.info(
                    "현재 단계에서는 구성과 금융 데이터만 보여주며, "
                    "포트폴리오 추천이나 최적 비중 계산은 하지 않습니다."
                )
