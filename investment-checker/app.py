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
from logic.cross_examination import (
    CrossExaminationError,
    select_cross_examination_questions,
    validate_cross_examination_answers,
)
from logic.thesis_standards import evaluate_thesis_standards
from ui.login import render_login
from ui.styles import apply_global_styles
from ui.workflow import (
    render_question_loading,
    render_step_navigation,
    scroll_to_top_on_screen_change,
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


st.set_page_config(
    page_title="Portfolio Thesis Checker",
    page_icon="⚖️",
    layout="centered",
)
apply_global_styles()

if not render_login():
    st.stop()

st.markdown(
    '<span class="app-shell-marker" aria-hidden="true">&nbsp;</span>',
    unsafe_allow_html=True,
)

if "workflow_screen" not in st.session_state:
    st.session_state["workflow_screen"] = "portfolio"

workflow_screen = st.session_state["workflow_screen"]
scroll_to_top_on_screen_change(workflow_screen)

if workflow_screen == "portfolio":
    render_step_navigation("portfolio")
    st.markdown(
        """
        <section class="page-hero">
            <h1>Portfolio Thesis Checker</h1>
            <p>포트폴리오를 추천하지 않고, 입력한 구성과 투자 논리를 점검합니다.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if "portfolio_rows" not in st.session_state:
        st.session_state["portfolio_rows"] = [
            {"id": 1, "ticker": "AAPL", "weight": 40.0},
            {"id": 2, "ticker": "MSFT", "weight": 30.0},
            {"id": 3, "ticker": "NVDA", "weight": 30.0},
        ]
        st.session_state["portfolio_row_sequence"] = 3

    rows = st.session_state["portfolio_rows"]
    with st.container(border=True):
        st.markdown('<h2 class="portfolio-card-title">포트폴리오 입력</h2>', unsafe_allow_html=True)
        ticker_header, weight_header, _ = st.columns([6, 1.55, 0.48], gap="small")
        ticker_header.markdown('<div class="portfolio-column-label">TICKER</div>', unsafe_allow_html=True)
        weight_header.markdown('<div class="portfolio-column-label right">비중 (%)</div>', unsafe_allow_html=True)
        st.markdown('<div class="portfolio-header-gap"></div>', unsafe_allow_html=True)

        remove_row_id = None
        for row in rows:
            ticker_column, weight_column, remove_column = st.columns(
                [6, 1.55, 0.48], gap="small"
            )
            row["ticker"] = ticker_column.text_input(
                "Ticker",
                value=str(row["ticker"]),
                key=f'portfolio_ticker_{row["id"]}',
                label_visibility="collapsed",
            ).upper()
            row["weight"] = weight_column.number_input(
                "비중",
                min_value=0.0,
                max_value=100.0,
                value=float(row["weight"]),
                step=1.0,
                key=f'portfolio_weight_{row["id"]}',
                label_visibility="collapsed",
            )
            if remove_column.button(
                "×",
                key=f'portfolio_remove_{row["id"]}',
                disabled=len(rows) == 1,
                use_container_width=True,
            ):
                remove_row_id = row["id"]

        if remove_row_id is not None:
            st.session_state["portfolio_rows"] = [
                row for row in rows if row["id"] != remove_row_id
            ]
            st.rerun()

        total_weight = sum(float(row["weight"]) for row in rows)
        add_column, total_column = st.columns([1, 1])
        with add_column:
            if st.button("＋ 종목 추가", disabled=len(rows) >= 10):
                st.session_state["portfolio_row_sequence"] += 1
                rows.append(
                    {
                        "id": st.session_state["portfolio_row_sequence"],
                        "ticker": "",
                        "weight": 0.0,
                    }
                )
                st.rerun()
        total_state = "valid" if abs(total_weight - 100.0) < 0.01 else "invalid"
        total_column.markdown(
            f'<div class="portfolio-total {total_state}">합계 '
            f'<strong>{total_weight:g}%</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="portfolio-rule"></div>', unsafe_allow_html=True)
        st.caption("최대 10개 종목까지 입력할 수 있으며 비중 합계는 100%여야 합니다.")

    with st.container(border=True):
        st.markdown('<h2 class="portfolio-card-title thesis">포트폴리오 구성 논리</h2>', unsafe_allow_html=True)
        st.markdown(
            '<p class="portfolio-card-copy">이 포트폴리오를 구성한 이유와 투자 판단의 근거를 자유롭게 작성해주세요.</p>',
            unsafe_allow_html=True,
        )
        thesis = st.text_area(
            "포트폴리오 구성 논리 작성",
            value=st.session_state.get("portfolio_thesis", ""),
            placeholder="예: AI 성장주를 여러 기업에 나누어 투자해 위험을 분산했다고 생각한다.",
            height=180,
            label_visibility="collapsed",
        )
    _, next_column = st.columns([2.4, 1])
    portfolio_submitted = next_column.button(
        "다음: 투자 기준 입력 →",
        type="primary",
        use_container_width=True,
    )
    if portfolio_submitted:
        portfolio_input = pd.DataFrame(
            [{"ticker": row["ticker"], "weight": row["weight"]} for row in rows]
        )
        try:
            validate_portfolio(portfolio_input.to_dict("records"))
        except PortfolioValidationError as exc:
            st.error(str(exc))
        else:
            if not thesis.strip():
                st.error("포트폴리오 구성 논리를 입력해주세요.")
            else:
                st.session_state["portfolio_input"] = portfolio_input
                st.session_state["portfolio_thesis"] = thesis.strip()
                st.session_state["workflow_screen"] = "criteria"
                st.rerun()
    st.stop()

if workflow_screen == "criteria":
    render_step_navigation("criteria")
    if st.button("← 포트폴리오 입력으로", key="criteria_back"):
        st.session_state["workflow_screen"] = "portfolio"
        st.rerun()
    st.markdown(
        """
        <section class="criteria-hero">
            <h1>투자 기준 입력</h1>
            <p>투자 판단의 근거와 기준을 입력하고, 관련 자료를 첨부하세요.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="criteria-question first"><span>1</span>'
        '<strong>이 판단에서 중요하게 본 근거는 무엇인가요? (복수 선택 가능)</strong></div>',
        unsafe_allow_html=True,
    )
    thesis_factors = st.pills(
        "중요하게 본 근거",
        THESIS_FACTORS[:-1],
        selection_mode="multi",
        default=None,
        key="criteria_thesis_factors",
        label_visibility="collapsed",
    )
    with st.container(border=True):
        st.markdown(
            """
            <div class="factor-detail-heading">
                <strong>선택한 근거를 조금 더 구체적으로 설명해주세요.</strong>
                <span>(선택)</span>
                <p>어떤 수치, 변화, 사건 또는 이유를 보고 그렇게 판단했는지 자유롭게 작성해주세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        factor_detail = st.text_area(
            "선택 근거 상세 설명",
            placeholder="최근 3년간 매출과 영업이익이 꾸준히 증가했고, AI 관련 수요 확대가 계속될 것으로 판단했습니다.",
            height=180,
            key="criteria_factor_detail",
            label_visibility="collapsed",
        )

    st.markdown(
        '<div class="criteria-question"><span>2</span>'
        '<strong>이 포트폴리오를 구성하게 된 가장 큰 계기는 무엇인가요?</strong></div>',
        unsafe_allow_html=True,
    )
    decision_trigger = st.radio(
        "포트폴리오 구성 계기",
        DECISION_TRIGGERS,
        index=None,
        key="criteria_decision_trigger",
        label_visibility="collapsed",
        width="stretch",
    )

    st.markdown(
        '<div class="criteria-question"><span>3</span>'
        '<strong>판단하기 전에 어느 정도까지 자료를 확인했나요?</strong></div>',
        unsafe_allow_html=True,
    )
    evidence_level = st.radio(
        "자료 확인 수준",
        EVIDENCE_LEVELS,
        index=None,
        key="criteria_evidence_level",
        label_visibility="collapsed",
        width="stretch",
    )

    with st.container(border=True):
        st.markdown(
            """
            <div class="evidence-panel-heading">
                <strong>참고한 자료 첨부</strong>
                <p>투자 판단에 참고한 자료가 있다면 첨부해주세요. 텍스트 기반 PDF 파일 1개를 업로드할 수 있습니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="upload-visual">
                <span class="upload-icon">▱</span>
                <strong>PDF 파일 업로드</strong>
                <p>최대 10MB · 텍스트 기반 PDF만 지원<br>
                스캔·암호화·이미지 전용 PDF는 지원하지 않습니다.</p>
                <small>업로드된 파일은 현재 분석에만 사용되며 저장되지 않습니다.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        evidence_pdf = st.file_uploader(
            "PDF 파일 업로드",
            type=["pdf"],
            accept_multiple_files=False,
            key="criteria_evidence_pdf",
            help=(
                "10MB 이하의 PDF 1개를 첨부할 수 있습니다. "
                "파일은 DB에 저장하지 않으며, AI 분석을 선택한 경우에만 "
                "추출된 텍스트가 OpenAI API로 전송됩니다."
            ),
            label_visibility="collapsed",
        )
        if evidence_pdf is not None:
            st.caption(f"첨부된 자료: {evidence_pdf.name}")
        url_column, url_button_column = st.columns([5, 1], gap="small")
        evidence_url = url_column.text_input(
            "참고 URL",
            placeholder="https://example.com/report",
            key="criteria_evidence_url",
            label_visibility="collapsed",
        )
        add_url = url_button_column.button(
            "URL 추가",
            key="criteria_add_url",
            use_container_width=True,
        )
        if add_url:
            if not evidence_url.startswith(("https://", "http://")):
                st.error("http:// 또는 https://로 시작하는 URL을 입력해주세요.")
            else:
                st.session_state["criteria_saved_url"] = evidence_url
                st.success("참고 URL이 추가되었습니다.")
        if st.session_state.get("criteria_saved_url"):
            st.caption("추가된 URL: " + st.session_state["criteria_saved_url"])

    st.markdown(
        '<div class="criteria-question"><span>4</span>'
        '<strong>예상하는 투자 기간은 어느 정도인가요?</strong></div>',
        unsafe_allow_html=True,
    )
    investment_horizon = st.radio(
        "예상 투자 기간",
        INVESTMENT_HORIZONS,
        index=None,
        key="criteria_investment_horizon",
        label_visibility="collapsed",
        width="stretch",
    )

    st.markdown(
        '<div class="criteria-question"><span>5</span>'
        '<strong>포트폴리오 가치가 30% 하락한다면 어떻게 대응할 가능성이 가장 높은가요?</strong></div>',
        unsafe_allow_html=True,
    )
    loss_response = st.radio(
        "손실 대응",
        LOSS_RESPONSES,
        index=None,
        key="criteria_loss_response",
        label_visibility="collapsed",
        width="stretch",
    )

    use_ai_analysis = st.checkbox(
        "반대심문 답변 후 AI로 최종 논리 일관성을 분석합니다.",
        value=True,
        disabled=False,
        key="criteria_use_ai",
        help=(
            "선택하면 최초 투자 논리, 금융 데이터 요약, 반대심문 답변이 "
            "최종 단계에서 OpenAI API로 전송됩니다. 매수·매도 추천은 생성하지 않습니다."
        ),
    )
    if not openai_api_key:
        st.caption("API 키가 없으면 AI 최종 분석 단계에서 안내 메시지가 표시됩니다.")

    _, criteria_button_column = st.columns([2.2, 1])
    criteria_submitted = criteria_button_column.button(
        "추가 질문 시작 →",
        type="primary",
        use_container_width=True,
        key="criteria_submit",
    )

    if criteria_submitted:
        if not all(
            [thesis_factors, decision_trigger, evidence_level, investment_horizon, loss_response]
        ):
            st.error("판단 근거 점검 문항에 모두 응답해주세요.")
        else:
            st.session_state["criteria_values"] = {
                "thesis_factors": thesis_factors,
                "decision_trigger": decision_trigger,
                "evidence_level": evidence_level,
                "investment_horizon": investment_horizon,
                "loss_response": loss_response,
                "use_ai_analysis": use_ai_analysis,
                "factor_detail": factor_detail,
                "evidence_url": st.session_state.get("criteria_saved_url", ""),
            }
            st.session_state["evidence_pdf"] = evidence_pdf
            st.session_state["workflow_screen"] = "loading"
            st.rerun()
    st.stop()

if workflow_screen == "loading":
    render_step_navigation("followup")
    render_question_loading()
    st.stop()

render_step_navigation("followup")
portfolio_input = st.session_state["portfolio_input"]
thesis = st.session_state["portfolio_thesis"]
evidence_pdf = st.session_state.get("evidence_pdf")
criteria_values = st.session_state["criteria_values"]
thesis_factors = criteria_values["thesis_factors"]
decision_trigger = criteria_values["decision_trigger"]
evidence_level = criteria_values["evidence_level"]
investment_horizon = criteria_values["investment_horizon"]
loss_response = criteria_values["loss_response"]
use_ai_analysis = criteria_values["use_ai_analysis"]
submitted = not st.session_state.get("analysis_processed", False)

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
                st.caption(
                    "디자인 작업 중이라면 실제 금융 데이터 없이 다음 화면을 확인할 수 있습니다."
                )
                if st.button(
                    "디자인 미리보기로 다음 화면 이동 →",
                    type="primary",
                    key="continue_design_preview",
                ):
                    preview_questions = [
                        "현재 포트폴리오에서 가장 확신하는 투자 근거는 무엇인가요?",
                        "처음의 투자 판단을 바꿀 수 있는 반대 근거는 무엇인가요?",
                        "시장 상황이 달라질 경우 어떤 기준으로 다시 판단하시겠어요?",
                    ]
                    st.session_state["cross_examination"] = {
                        "original_thesis": thesis.strip(),
                        "questions": preview_questions,
                        "analysis_context": {"design_preview": True},
                        "use_ai_analysis": False,
                        "has_pdf": pdf_evidence is not None,
                    }
                    st.session_state.pop("final_cross_examination", None)
                    for index in range(3):
                        st.session_state.pop(
                            f"cross_examination_answer_{index}", None
                        )
                    st.session_state["analysis_processed"] = True
                    st.session_state["workflow_screen"] = "followup"
                    st.rerun()
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

                    standard_findings = evaluate_thesis_standards(
                        holding_count=len(holdings),
                        dominant_sector_weight=float(
                            sector_concentration["dominant_weight"]
                        ),
                        average_correlation=average_correlation,
                        thesis_factors=thesis_factors,
                        investment_horizon=investment_horizon,
                        evidence_level=evidence_level,
                    )
                    st.subheader("팀 기준 진단")
                    if standard_findings:
                        for finding in standard_findings:
                            with st.expander(str(finding["rule"]), expanded=True):
                                st.write(str(finding["diagnosis"]))
                                st.caption("판정 근거: " + ", ".join(finding["evidence"]))
                                st.markdown(f'**후속 질문:** {finding["question"]}')
                    else:
                        st.success(
                            "현재 입력에서는 팀이 정한 3가지 규칙에 해당하는 "
                            "항목이 확인되지 않았습니다."
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
                        cross_examination_questions = (
                            select_cross_examination_questions(
                                standard_findings, questions
                            )
                        )
                        st.markdown("#### 1차 분석에서 확인된 쟁점")
                        st.write(
                            "아래 질문에 답하면 최초 투자 논리의 보완 여부와 "
                            "일관성을 최종 점검합니다."
                        )
                        for question in cross_examination_questions:
                            st.write(f"- {question}")

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
                            "team_standard_findings": standard_findings,
                        }
                        st.session_state["cross_examination"] = {
                            "original_thesis": thesis.strip(),
                            "questions": cross_examination_questions,
                            "analysis_context": ai_context,
                            "use_ai_analysis": use_ai_analysis,
                            "has_pdf": pdf_evidence is not None,
                        }
                        st.session_state.pop("final_cross_examination", None)
                        for index in range(3):
                            st.session_state.pop(
                                f"cross_examination_answer_{index}", None
                            )

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


if submitted:
    st.session_state["analysis_processed"] = True

cross_examination = st.session_state.get("cross_examination")
if cross_examination:
    st.divider()
    st.header("2단계: 반대심문 답변")
    st.write(
        "1차 분석에서 발견된 쟁점에 답해주세요. 답변은 새로운 추천을 받기 위한 "
        "것이 아니라, 최초 논리를 보완하거나 수정할 수 있는지 확인하는 데 사용됩니다."
    )

    with st.form("cross_examination_form"):
        follow_up_answers = [
            st.text_area(
                f"질문 {index + 1}. {question}",
                key=f"cross_examination_answer_{index}",
            )
            for index, question in enumerate(cross_examination["questions"])
        ]
        final_submitted = st.form_submit_button("최종 진단 보기")

    if final_submitted:
        try:
            answer_records = validate_cross_examination_answers(
                cross_examination["questions"], follow_up_answers
            )
        except CrossExaminationError as exc:
            st.error(str(exc))
        else:
            final_result: dict[str, object] = {"answers": answer_records}
            if cross_examination["use_ai_analysis"]:
                final_context = dict(cross_examination["analysis_context"])
                final_context["cross_examination_answers"] = answer_records
                combined_thesis = (
                    f'최초 투자 논리:\n{cross_examination["original_thesis"]}\n\n'
                    "반대심문 질문과 사용자 답변:\n"
                    + "\n".join(
                        f'Q: {record["question"]}\nA: {record["answer"]}'
                        for record in answer_records
                    )
                )
                try:
                    with st.spinner("AI가 최초 논리와 추가 답변을 함께 검증하는 중입니다..."):
                        final_result["ai_analysis"] = analyze_portfolio_thesis(
                            combined_thesis,
                            final_context,
                            api_key=openai_api_key,
                        )
                except AIAnalysisError as exc:
                    final_result["ai_error"] = str(exc)
            st.session_state["final_cross_examination"] = final_result

    final_cross_examination = st.session_state.get("final_cross_examination")
    if final_cross_examination:
        st.header("최종 진단")
        st.success("반대심문 답변이 모두 제출되었습니다.")

        st.markdown("#### 질문별 보완 답변")
        for record in final_cross_examination["answers"]:
            with st.expander(str(record["question"]), expanded=True):
                st.write(str(record["answer"]))

        ai_error = final_cross_examination.get("ai_error")
        ai_analysis = final_cross_examination.get("ai_analysis")
        if ai_error:
            st.warning(str(ai_error))
        elif ai_analysis:
            st.markdown("#### 최초 논리와 추가 답변의 종합 분석")
            st.write(ai_analysis.summary)
            st.write("분류: " + ", ".join(ai_analysis.categories))

            st.markdown("#### 데이터와 부합하거나 보완된 부분")
            for point in ai_analysis.supported_points:
                st.write(f"- {point}")

            st.markdown("#### 여전히 확인이 필요한 부분")
            for point in ai_analysis.uncertain_points:
                st.write(f"- {point}")

            st.markdown("#### 편향 또는 논리 이동 가능성")
            if ai_analysis.possible_biases:
                for bias in ai_analysis.possible_biases:
                    st.write(f"- {bias}")
            else:
                st.write("- 현재 답변에서 뚜렷한 편향을 확인하기 어렵습니다.")

            st.markdown("#### 남은 확인 질문")
            for question in ai_analysis.devils_advocate_questions:
                st.write(f"- {question}")

            with st.expander("최종 분석의 데이터 한계"):
                for limitation in ai_analysis.data_limitations:
                    st.write(f"- {limitation}")
        else:
            st.info(
                "현재는 답변 제출과 기록까지 완료되었습니다. 답변의 의미, 최초 "
                "논리와의 일관성, 논리 이동 여부를 자동 해석하려면 AI 분석을 "
                "활성화해야 합니다."
            )

    if st.button("새 분석 시작"):
        st.session_state.pop("cross_examination", None)
        st.session_state.pop("final_cross_examination", None)
        for index in range(3):
            st.session_state.pop(f"cross_examination_answer_{index}", None)
        st.rerun()
