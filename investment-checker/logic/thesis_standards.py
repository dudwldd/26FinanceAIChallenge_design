"""Apply the team's deterministic investment-thesis review standards."""

from typing import Any


LONG_TERM_FACTORS = {
    "매출·이익 등 성장성이 높다고 판단했다",
    "산업·제품의 미래 전망이 좋다고 판단했다",
}

QUANTITATIVE_FACTORS = {
    "밸류에이션이 매력적이라고 판단했다",
    "매출·이익 등 성장성이 높다고 판단했다",
    "부채·현금흐름 등 재무 상태가 안정적이라고 판단했다",
}

SHORT_HORIZONS = {"6개월 미만", "6개월 이상 1년 미만"}

LOW_EVIDENCE_LEVELS = {
    "아직 별도의 자료를 확인하지 않았다",
    "뉴스·영상·커뮤니티 자료를 주로 확인했다",
}


def evaluate_thesis_standards(
    *,
    holding_count: int,
    dominant_sector_weight: float,
    average_correlation: float | None,
    thesis_factors: list[str],
    investment_horizon: str,
    evidence_level: str,
) -> list[dict[str, Any]]:
    """Return triggered team standards with diagnoses and follow-up questions."""
    findings: list[dict[str, Any]] = []
    selected_factors = set(thesis_factors)

    sector_triggered = holding_count >= 2 and dominant_sector_weight >= 70
    correlation_triggered = (
        holding_count >= 2
        and average_correlation is not None
        and average_correlation >= 0.70
    )
    if sector_triggered or correlation_triggered:
        evidence: list[str] = []
        if sector_triggered:
            evidence.append(f"최대 산업 비중 {dominant_sector_weight:.1f}%")
        if correlation_triggered and average_correlation is not None:
            evidence.append(f"종목 간 평균 상관계수 {average_correlation:.2f}")
        findings.append(
            {
                "rule": "분산 착각 탐지",
                "diagnosis": (
                    "여러 종목을 보유했지만 동일 산업에 집중되어 있거나 "
                    "함께 움직이는 경향이 강합니다."
                ),
                "evidence": evidence,
                "question": (
                    "이 종목들에 공통으로 영향을 미치는 산업 위험이 발생해도 "
                    "현재 투자 논리가 유지되나요?"
                ),
            }
        )

    if selected_factors & LONG_TERM_FACTORS and investment_horizon in SHORT_HORIZONS:
        findings.append(
            {
                "rule": "투자 논리와 기간의 불일치 탐지",
                "diagnosis": (
                    "장기적인 성장 전망을 근거로 선택했지만 실제 투자 기간은 "
                    "1년 미만이어서 투자 논리와 실행 계획이 일치하지 않을 수 있습니다."
                ),
                "evidence": [f"예상 투자 기간: {investment_horizon}"],
                "question": (
                    "장기 성장 논리가 1년 이내 주가에 반영될 것이라고 판단한 "
                    "구체적인 근거는 무엇인가요?"
                ),
            }
        )

    if selected_factors & QUANTITATIVE_FACTORS and evidence_level in LOW_EVIDENCE_LEVELS:
        findings.append(
            {
                "rule": "근거보다 확신이 앞서는 경우 탐지",
                "diagnosis": (
                    "수치 확인이 필요한 재무적 판단을 투자 근거로 선택했지만 "
                    "정량 자료 확인 수준이 충분하지 않아 현재 확신을 데이터로 "
                    "검증하기 어렵습니다."
                ),
                "evidence": [f"자료 확인 수준: {evidence_level}"],
                "question": (
                    "이 판단이 틀렸다고 결론 내리게 만들 수 있는 재무지표나 "
                    "기준값은 무엇인가요?"
                ),
            }
        )

    return findings
