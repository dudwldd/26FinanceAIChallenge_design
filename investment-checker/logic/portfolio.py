"""Validate portfolio inputs and calculate simple concentration metrics."""

from math import isclose, isnan
from typing import Any


MAX_HOLDINGS = 10


class PortfolioValidationError(ValueError):
    """Raised when portfolio rows do not form a valid portfolio."""


def validate_portfolio(rows: list[dict[str, Any]]) -> list[dict[str, float | str]]:
    """Normalize ticker-weight rows and require weights to total 100%."""
    holdings: list[dict[str, float | str]] = []

    for row in rows:
        raw_ticker = row.get("ticker")
        raw_weight = row.get("weight")
        ticker_missing = raw_ticker is None or (
            isinstance(raw_ticker, float) and isnan(raw_ticker)
        )
        weight_missing = raw_weight is None or (
            isinstance(raw_weight, float) and isnan(raw_weight)
        )
        ticker = "" if ticker_missing else str(raw_ticker).strip().upper()

        if not ticker and weight_missing:
            continue
        if not ticker or weight_missing:
            raise PortfolioValidationError("각 행에 ticker와 비중을 모두 입력해주세요.")

        try:
            weight = float(raw_weight)
        except (TypeError, ValueError) as exc:
            raise PortfolioValidationError("비중은 숫자로 입력해주세요.") from exc

        if weight <= 0 or weight > 100:
            raise PortfolioValidationError("각 종목의 비중은 0보다 크고 100 이하여야 합니다.")

        holdings.append({"ticker": ticker, "weight": weight})

    if not holdings:
        raise PortfolioValidationError("최소 한 개의 종목을 입력해주세요.")
    if len(holdings) > MAX_HOLDINGS:
        raise PortfolioValidationError(f"종목은 최대 {MAX_HOLDINGS}개까지 입력할 수 있습니다.")

    tickers = [str(holding["ticker"]) for holding in holdings]
    duplicates = sorted({ticker for ticker in tickers if tickers.count(ticker) > 1})
    if duplicates:
        raise PortfolioValidationError(
            "중복된 ticker를 하나로 합쳐주세요: " + ", ".join(duplicates)
        )

    total_weight = sum(float(holding["weight"]) for holding in holdings)
    if not isclose(total_weight, 100.0, abs_tol=0.01):
        raise PortfolioValidationError(
            f"비중 합계를 100%로 맞춰주세요. 현재 합계: {total_weight:.2f}%"
        )

    return holdings


def calculate_concentration(
    holdings: list[dict[str, float | str]],
) -> dict[str, float | str]:
    """Return the largest holding and combined weight of the top two."""
    ranked = sorted(holdings, key=lambda item: float(item["weight"]), reverse=True)
    return {
        "largest_ticker": str(ranked[0]["ticker"]),
        "largest_weight": float(ranked[0]["weight"]),
        "top_two_weight": sum(float(item["weight"]) for item in ranked[:2]),
    }
