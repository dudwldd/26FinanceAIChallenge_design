"""Optional OpenAI-powered analysis of a portfolio thesis."""

import json
import os
from collections.abc import Callable
from typing import Any, Literal

from openai import APIConnectionError, APITimeoutError, AuthenticationError, OpenAI
from openai import RateLimitError
from pydantic import BaseModel, Field


ClaimCategory = Literal[
    "valuation",
    "profitability",
    "growth",
    "financial_health",
    "momentum",
    "risk",
    "future_outlook",
]


class PortfolioAIAnalysis(BaseModel):
    """Structured, non-advisory AI analysis returned to the UI."""

    categories: list[ClaimCategory] = Field(min_length=1)
    summary: str
    supported_points: list[str]
    uncertain_points: list[str]
    possible_biases: list[str]
    devils_advocate_questions: list[str] = Field(min_length=1, max_length=5)
    data_limitations: list[str]


class AIAnalysisError(RuntimeError):
    """Raised when the optional AI analysis cannot be completed."""


SYSTEM_INSTRUCTIONS = """
You are the analysis layer of a Portfolio Thesis Checker.
Respond in Korean and evaluate only whether the user's stated reasoning is
supported by the supplied portfolio data. Separate facts from interpretations.
Never recommend a security, trade, buy/sell action, target allocation, expected
return, or portfolio optimization. Never claim causality from correlation.
Treat missing values as unknown and explicitly state relevant data limitations.
Use neutral language such as '부합한다', '확인되지 않는다', and '추가 확인이 필요하다'.
Generate concise devil's-advocate questions that help the user test assumptions.
Do not introduce financial facts that are absent from the supplied JSON.
""".strip()


def analyze_portfolio_thesis(
    thesis: str,
    analysis_context: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
    client_factory: Callable[..., Any] = OpenAI,
) -> PortfolioAIAnalysis:
    """Return structured AI feedback grounded only in supplied context."""
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise AIAnalysisError("OPENAI_API_KEY가 설정되지 않았습니다.")

    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    payload = {
        "user_thesis": thesis,
        "portfolio_analysis": analysis_context,
    }

    try:
        client = client_factory(api_key=resolved_key, timeout=30.0, max_retries=0)
        response = client.responses.parse(
            model=resolved_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=json.dumps(payload, ensure_ascii=False, default=str),
            text_format=PortfolioAIAnalysis,
        )
        parsed = response.output_parsed
    except AuthenticationError as exc:
        raise AIAnalysisError(
            "OpenAI API 키가 유효하지 않습니다. API 키를 다시 확인해주세요."
        ) from exc
    except RateLimitError as exc:
        error_code = getattr(exc, "code", None)
        if error_code == "insufficient_quota":
            raise AIAnalysisError(
                "OpenAI API 잔액이 없거나 사용 한도에 도달했습니다. "
                "OpenAI Platform의 Billing에서 크레딧과 사용 한도를 확인해주세요."
            ) from exc
        raise AIAnalysisError(
            "OpenAI API 요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
        ) from exc
    except APITimeoutError as exc:
        raise AIAnalysisError(
            "AI 분석이 30초 안에 완료되지 않았습니다. 다시 시도해주세요."
        ) from exc
    except APIConnectionError as exc:
        raise AIAnalysisError(
            "OpenAI API에 연결하지 못했습니다. 네트워크를 확인해주세요."
        ) from exc
    except Exception as exc:
        raise AIAnalysisError(
            "AI 분석을 완료하지 못했습니다. 잠시 후 다시 시도해주세요."
        ) from exc

    if parsed is None:
        raise AIAnalysisError("AI가 분석 결과를 반환하지 않았습니다.")
    return parsed
