"""Streamlit entry point for the Investment Thesis Checker POC."""

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from ai.portfolio_analyzer import AIAnalysisError, analyze_portfolio_thesis
from data.financial_data import (
    FinancialDataError,
    get_financial_data,
    get_historical_prices,
)
from data.pdf_evidence import PDFEvidenceError, extract_pdf_evidence
from logic.portfolio import (
    PortfolioValidationError,
    calculate_average_correlation,
    calculate_concentration,
    calculate_historical_portfolio_metrics,
    calculate_return_correlation,
    calculate_sector_concentration,
    build_comparison_weights,
    generate_portfolio_questions,
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


load_dotenv()


def get_openai_api_key() -> str | None:
    """Read the OpenAI API key from environment or Streamlit secrets."""
    environment_key = os.getenv("OPENAI_API_KEY")
    if environment_key:
        return environment_key
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except FileNotFoundError:
        return None


openai_api_key = get_openai_api_key()


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_financial_data(ticker: str) -> dict[str, object]:
    """Cache provider data briefly so reruns do not repeat the same request."""
    return get_financial_data(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_historical_prices(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Cache price history briefly for faster repeated thesis checks."""
    return get_historical_prices(list(tickers))


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

    evidence_pdf = st.file_uploader(
        "판단에 참고한 PDF (선택)",
        type=["pdf"],
        accept_multiple_files=False,
        help=(
            "10MB 이하의 PDF 1개를 첨부할 수 있습니다. "
            "파일은 DB에 저장하지 않으며, AI 분석을 선택한 경우에만 "
            "추출된 텍스트가 OpenAI API로 전송됩니다."
        ),
    )
    if evidence_pdf is not None:
        st.caption(f"첨부된 자료: {evidence_pdf.name}")

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

    use_ai_analysis = st.checkbox(
        "AI로 투자 논리와 데이터의 부합 여부를 추가 분석합니다.",
        value=False,
        disabled=not bool(openai_api_key),
        help=(
            "선택하면 입력한 투자 논리와 화면에 표시된 금융 데이터 요약이 "
            "OpenAI API로 전송됩니다. 매수·매도 추천은 생성하지 않습니다."
        ),
    )
    if not openai_api_key:
        st.caption("AI 분석을 사용하려면 OPENAI_API_KEY를 설정해주세요.")

    submitted = st.form_submit_button("Check my thesis")

pdf_evidence = None
pdf_error = None
if submitted and evidence_pdf is not None:
    try:
        pdf_evidence = extract_pdf_evidence(
            evidence_pdf.getvalue(), evidence_pdf.name
        )
    except PDFEvidenceError as exc:
        pdf_error = str(exc)

if submitted:
    if pdf_error:
        st.error(pdf_error)
    elif not thesis.strip():
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
            sectors = {}
            data_error = None

            try:
                with st.spinner("종목별 금융 데이터를 불러오는 중입니다..."):
                    for holding in holdings:
                        financial_data = get_cached_financial_data(
                            str(holding["ticker"])
                        )
                        sector = financial_data["company_profile"]["sector"]
                        sectors[str(holding["ticker"])] = sector
                        financial_rows.append(
                            {
                                "Ticker": financial_data["ticker"],
                                "회사명": financial_data["company_name"],
                                "산업": sector,
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
                if pdf_evidence is not None:
                    st.subheader("첨부 근거자료")
                    pdf_col1, pdf_col2 = st.columns(2)
                    pdf_col1.metric("파일", str(pdf_evidence["filename"]))
                    pdf_col2.metric("페이지", f'{pdf_evidence["page_count"]}쪽')
                    if pdf_evidence["was_truncated"]:
                        st.warning(
                            "문서가 길어 처음 30페이지와 최대 30,000자까지만 "
                            "분석에 사용합니다."
                        )
                    with st.expander("추출된 PDF 텍스트 미리보기"):
                        for page in pdf_evidence["pages"][:3]:
                            st.markdown(f'**{page["page"]}페이지**')
                            page_text = str(page["text"])
                            st.text(page_text[:2_000])
                        st.caption(
                            "미리보기는 최대 3페이지, 페이지당 2,000자만 표시합니다."
                        )

                concentration = calculate_concentration(holdings)
                sector_concentration = calculate_sector_concentration(
                    holdings, sectors
                )

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

                st.subheader("산업 집중도")
                sector_col1, sector_col2 = st.columns(2)
                sector_col1.metric(
                    "가장 큰 산업",
                    str(sector_concentration["dominant_sector"]),
                )
                sector_col2.metric(
                    "해당 산업 비중",
                    f'{sector_concentration["dominant_weight"]:.2f}%',
                )
                sector_table = pd.DataFrame(
                    {
                        "산업": sector_concentration["sector_weights"].keys(),
                        "비중 (%)": sector_concentration["sector_weights"].values(),
                    }
                )
                st.dataframe(sector_table, hide_index=True, width="stretch")

                st.subheader("최근 1년 수익률 상관관계")
                try:
                    prices = get_cached_historical_prices(
                        tuple(str(holding["ticker"]) for holding in holdings)
                    )
                    correlation = calculate_return_correlation(prices)
                    average_correlation = calculate_average_correlation(correlation)
                except (FinancialDataError, PortfolioValidationError) as exc:
                    st.warning(f"상관관계를 계산하지 못했습니다: {exc}")
                else:
                    if average_correlation is not None:
                        st.metric("종목 간 평균 상관계수", f"{average_correlation:.2f}")
                    st.dataframe(
                        correlation.round(2),
                        width="stretch",
                    )
                    st.caption(
                        "상관계수는 -1에서 1 사이의 값입니다. 1에 가까울수록 "
                        "같은 방향으로 움직인 경향이 강했다는 뜻이며, 미래 움직임을 "
                        "예측하거나 분산 효과를 단정하는 지표는 아닙니다."
                    )

                    st.subheader("비중 비교를 통한 논리 점검")
                    try:
                        comparison_weights = build_comparison_weights(
                            holdings, prices
                        )
                        historical_metrics = calculate_historical_portfolio_metrics(
                            prices, comparison_weights
                        )
                    except PortfolioValidationError as exc:
                        st.warning(f"비중 비교를 계산하지 못했습니다: {exc}")
                    else:
                        weight_table = (comparison_weights * 100).round(2)
                        st.dataframe(weight_table, width="stretch")
                        st.caption(
                            "동일 비중과 역변동성 비중은 사용자의 현재 구성을 "
                            "검토하기 위한 비교 기준이며, 추천하거나 따라야 할 목표 비중이 아닙니다."
                        )

                        display_metrics = historical_metrics.copy()
                        for column in display_metrics.columns:
                            display_metrics[column] = display_metrics[column].map(
                                lambda value: f"{value * 100:.2f}%"
                            )
                        st.dataframe(display_metrics, width="stretch")
                        st.caption(
                            "모든 성과 수치는 동일한 최근 1년 과거 가격으로 계산되며, "
                            "거래비용·세금·환율을 반영하지 않습니다. 과거 성과는 미래 성과를 보장하지 않습니다."
                        )

                        questions = generate_portfolio_questions(
                            holdings,
                            comparison_weights,
                            str(sector_concentration["dominant_sector"]),
                            float(sector_concentration["dominant_weight"]),
                            average_correlation,
                        )
                        st.markdown("#### 추가로 점검할 질문")
                        for question in questions:
                            st.write(f"- {question}")

                        if use_ai_analysis:
                            ai_context = {
                                "holdings": holdings,
                                "financial_data": financial_rows,
                                "sector_concentration": sector_concentration,
                                "average_correlation": average_correlation,
                                "comparison_weights_percent": weight_table.to_dict(),
                                "historical_metrics": historical_metrics.to_dict(),
                                "questionnaire": {
                                    "thesis_factors": thesis_factors,
                                    "decision_trigger": decision_trigger,
                                    "evidence_level": evidence_level,
                                    "investment_horizon": investment_horizon,
                                    "loss_response": loss_response,
                                },
                                "uploaded_evidence": pdf_evidence,
                            }
                            try:
                                with st.spinner("AI가 투자 논리를 검증하는 중입니다..."):
                                    ai_analysis = analyze_portfolio_thesis(
                                        thesis.strip(),
                                        ai_context,
                                        api_key=openai_api_key,
                                    )
                            except AIAnalysisError as exc:
                                st.warning(str(exc))
                            else:
                                st.subheader("AI 투자 논리 검증")
                                st.write(ai_analysis.summary)
                                st.write(
                                    "분류: " + ", ".join(ai_analysis.categories)
                                )

                                if pdf_evidence is not None:
                                    st.markdown("#### 첨부자료에서 확인한 내용")
                                    if ai_analysis.evidence_findings:
                                        for finding in ai_analysis.evidence_findings:
                                            st.write(f"- {finding}")
                                    else:
                                        st.write(
                                            "- 첨부자료에서 투자 논리와 직접 "
                                            "연결되는 근거를 확인하기 어렵습니다."
                                        )

                                st.markdown("#### 데이터와 부합하는 부분")
                                if ai_analysis.supported_points:
                                    for point in ai_analysis.supported_points:
                                        st.write(f"- {point}")
                                else:
                                    st.write("- 현재 데이터만으로 확인된 부분이 없습니다.")

                                st.markdown("#### 확인되지 않거나 보완이 필요한 부분")
                                if ai_analysis.uncertain_points:
                                    for point in ai_analysis.uncertain_points:
                                        st.write(f"- {point}")
                                else:
                                    st.write("- 별도로 식별된 항목이 없습니다.")

                                st.markdown("#### 편향 가능성")
                                if ai_analysis.possible_biases:
                                    for bias in ai_analysis.possible_biases:
                                        st.write(f"- {bias}")
                                else:
                                    st.write("- 현재 입력에서 뚜렷한 편향을 확인하기 어렵습니다.")

                                st.markdown("#### AI 반대심문 질문")
                                for question in ai_analysis.devils_advocate_questions:
                                    st.write(f"- {question}")

                                with st.expander("AI 분석의 데이터 한계"):
                                    for limitation in ai_analysis.data_limitations:
                                        st.write(f"- {limitation}")

                with st.expander("입력한 투자 논리와 응답 보기"):
                    st.write(f"포트폴리오 구성 논리: {thesis.strip()}")
                    st.write("핵심 근거: " + ", ".join(thesis_factors))
                    st.write(f"판단 계기: {decision_trigger}")
                    st.write(f"자료 확인 수준: {evidence_level}")
                    st.write(f"예상 투자 기간: {investment_horizon}")
                    st.write(f"30% 하락 시 예상 대응: {loss_response}")

                st.info(
                    "비교 비중은 사용자의 투자 논리를 점검하기 위한 참고 기준입니다. "
                    "이 서비스는 포트폴리오 추천이나 목표 비중을 제공하지 않습니다."
                )
