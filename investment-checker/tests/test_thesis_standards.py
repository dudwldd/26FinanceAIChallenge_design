"""Tests for the team's deterministic thesis review standards."""

from logic.thesis_standards import evaluate_thesis_standards


def evaluate(**overrides: object) -> list[dict[str, object]]:
    """Evaluate standards using a neutral complete questionnaire by default."""
    inputs = {
        "holding_count": 3,
        "dominant_sector_weight": 40.0,
        "average_correlation": 0.30,
        "thesis_factors": ["수익성이 좋다고 판단했다"],
        "investment_horizon": "3년 이상",
        "evidence_level": "여러 출처를 비교하고 반대 근거도 확인했다",
    }
    inputs.update(overrides)
    return evaluate_thesis_standards(**inputs)  # type: ignore[arg-type]


def test_flags_diversification_illusion_at_team_thresholds() -> None:
    """A 70% sector or 0.70 correlation should trigger the diversification rule."""
    findings = evaluate(dominant_sector_weight=70.0, average_correlation=0.70)

    assert findings[0]["rule"] == "분산 착각 탐지"
    assert findings[0]["evidence"] == [
        "최대 산업 비중 70.0%",
        "종목 간 평균 상관계수 0.70",
    ]


def test_flags_long_term_reason_with_short_horizon() -> None:
    """Long-term growth reasoning should conflict with a sub-one-year horizon."""
    findings = evaluate(
        thesis_factors=["산업·제품의 미래 전망이 좋다고 판단했다"],
        investment_horizon="6개월 이상 1년 미만",
    )

    assert any(item["rule"] == "투자 논리와 기간의 불일치 탐지" for item in findings)


def test_flags_quantitative_claim_with_low_evidence() -> None:
    """A numerical claim without quantitative research should trigger review."""
    findings = evaluate(
        thesis_factors=["밸류에이션이 매력적이라고 판단했다"],
        evidence_level="뉴스·영상·커뮤니티 자료를 주로 확인했다",
    )

    assert any(item["rule"] == "근거보다 확신이 앞서는 경우 탐지" for item in findings)


def test_returns_no_findings_when_no_rule_is_triggered() -> None:
    """A neutral, supported response should not be forced into a diagnosis."""
    assert evaluate() == []
