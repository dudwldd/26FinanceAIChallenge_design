"""Tests for the optional OpenAI portfolio analysis layer."""

import pytest

from ai.portfolio_analyzer import (
    AIAnalysisError,
    PortfolioAIAnalysis,
    analyze_portfolio_thesis,
)


class FakeResponses:
    """Return a fixed parsed response without calling the network."""

    def parse(self, **kwargs: object) -> object:
        assert kwargs["model"] == "test-model"
        assert "Never recommend" in str(kwargs["instructions"])
        parsed = PortfolioAIAnalysis(
            categories=["risk"],
            summary="입력 논리의 일부가 데이터와 부합합니다.",
            supported_points=["비중 집중이 수치로 확인됩니다."],
            uncertain_points=["미래 전망은 현재 데이터로 확인되지 않습니다."],
            possible_biases=["최근성 편향 가능성을 점검할 필요가 있습니다."],
            devils_advocate_questions=["핵심 전제가 틀렸음을 보여주는 지표는 무엇인가요?"],
            data_limitations=["최근 1년 가격만 사용했습니다."],
        )
        return type("FakeResponse", (), {"output_parsed": parsed})()


class FakeClient:
    """Small OpenAI client substitute used by unit tests."""

    def __init__(self, api_key: str) -> None:
        assert api_key == "test-key"
        self.responses = FakeResponses()


def test_analyze_portfolio_thesis_returns_structured_output() -> None:
    """The analyzer should return the parsed schema from the client."""
    result = analyze_portfolio_thesis(
        "기술주에 분산 투자했다.",
        {"holdings": [{"ticker": "AAPL", "weight": 100}]},
        api_key="test-key",
        model="test-model",
        client_factory=FakeClient,
    )

    assert result.categories == ["risk"]
    assert len(result.devils_advocate_questions) == 1


def test_analyze_portfolio_thesis_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing credentials should produce a readable error before client creation."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(AIAnalysisError, match="OPENAI_API_KEY"):
        analyze_portfolio_thesis("논리", {})


def test_analyze_portfolio_thesis_wraps_client_errors() -> None:
    """Provider failures should not leak low-level exceptions into the UI."""
    def failing_factory(**kwargs: object) -> object:
        raise RuntimeError("provider unavailable")

    with pytest.raises(AIAnalysisError, match="AI 분석을 완료하지 못했습니다"):
        analyze_portfolio_thesis(
            "논리", {}, api_key="test-key", client_factory=failing_factory
        )
