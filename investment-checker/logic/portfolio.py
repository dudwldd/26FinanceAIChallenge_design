"""Validate portfolio inputs and calculate simple concentration metrics."""

from math import isclose, isnan, sqrt
from typing import Any

import pandas as pd


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


def calculate_sector_concentration(
    holdings: list[dict[str, float | str]],
    sectors: dict[str, str | None],
) -> dict[str, Any]:
    """Aggregate portfolio weights by sector and return the largest sector."""
    sector_weights: dict[str, float] = {}
    for holding in holdings:
        ticker = str(holding["ticker"])
        sector = sectors.get(ticker) or "Unknown"
        sector_weights[sector] = sector_weights.get(sector, 0.0) + float(
            holding["weight"]
        )

    dominant_sector = max(sector_weights, key=sector_weights.get)
    return {
        "sector_weights": dict(
            sorted(sector_weights.items(), key=lambda item: item[1], reverse=True)
        ),
        "dominant_sector": dominant_sector,
        "dominant_weight": sector_weights[dominant_sector],
    }


def calculate_return_correlation(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate a return correlation matrix from historical prices."""
    returns = prices.pct_change(fill_method=None).dropna(how="all")
    if returns.empty:
        raise PortfolioValidationError("상관관계를 계산할 가격 데이터가 부족합니다.")
    return returns.corr()


def calculate_average_correlation(correlation: pd.DataFrame) -> float | None:
    """Return the mean of unique pairwise correlations."""
    values = [
        float(correlation.iloc[row, column])
        for row in range(len(correlation.index))
        for column in range(row + 1, len(correlation.columns))
        if pd.notna(correlation.iloc[row, column])
    ]
    return sum(values) / len(values) if values else None


def build_comparison_weights(
    holdings: list[dict[str, float | str]], prices: pd.DataFrame
) -> pd.DataFrame:
    """Build current, equal, and inverse-volatility comparison weights."""
    tickers = [str(holding["ticker"]) for holding in holdings]
    returns = prices[tickers].pct_change(fill_method=None).dropna(how="any")
    if returns.empty:
        raise PortfolioValidationError("비교 비중을 계산할 가격 데이터가 부족합니다.")

    volatility = returns.std()
    if volatility.isna().any() or (volatility <= 0).any():
        raise PortfolioValidationError("일부 종목의 변동성을 계산할 수 없습니다.")

    current = pd.Series(
        {str(item["ticker"]): float(item["weight"]) / 100 for item in holdings}
    ).reindex(tickers)
    equal = pd.Series(1 / len(tickers), index=tickers)
    inverse_volatility = (1 / volatility) / (1 / volatility).sum()

    return pd.DataFrame(
        {
            "현재 비중": current,
            "동일 비중": equal,
            "역변동성 비교 비중": inverse_volatility.reindex(tickers),
        }
    )


def calculate_historical_portfolio_metrics(
    prices: pd.DataFrame, comparison_weights: pd.DataFrame
) -> pd.DataFrame:
    """Compare historical return, volatility, and drawdown by weight method."""
    returns = prices[comparison_weights.index].pct_change(fill_method=None).dropna(
        how="any"
    )
    metrics: list[dict[str, float | str]] = []

    for name in comparison_weights.columns:
        portfolio_returns = returns @ comparison_weights[name]
        cumulative = (1 + portfolio_returns).cumprod()
        drawdown = cumulative / cumulative.cummax() - 1
        metrics.append(
            {
                "비교 기준": name,
                "과거 1년 누적수익률": float(cumulative.iloc[-1] - 1),
                "연환산 변동성": float(portfolio_returns.std() * sqrt(252)),
                "최대 낙폭": float(drawdown.min()),
            }
        )

    return pd.DataFrame(metrics).set_index("비교 기준")


def generate_portfolio_questions(
    holdings: list[dict[str, float | str]],
    comparison_weights: pd.DataFrame,
    dominant_sector: str,
    dominant_weight: float,
    average_correlation: float | None,
) -> list[str]:
    """Generate deterministic questions about material portfolio differences."""
    questions: list[str] = []
    current = comparison_weights["현재 비중"]
    equal = comparison_weights["동일 비중"]

    largest_gap_ticker = max(current.index, key=lambda ticker: abs(current[ticker] - equal[ticker]))
    gap = float(current[largest_gap_ticker] - equal[largest_gap_ticker])
    if abs(gap) >= 0.10:
        direction = "높습니다" if gap > 0 else "낮습니다"
        questions.append(
            f"{largest_gap_ticker} 비중이 동일 비중보다 {abs(gap) * 100:.1f}%p "
            f"{direction}. 이 차이를 설명하는 구체적인 근거는 무엇인가요?"
        )

    if dominant_weight >= 60:
        questions.append(
            f"{dominant_sector} 산업 비중이 {dominant_weight:.1f}%입니다. "
            "이 산업에 공통으로 영향을 줄 수 있는 위험 요인을 확인했나요?"
        )

    if average_correlation is not None and average_correlation >= 0.70:
        questions.append(
            f"종목 간 과거 평균 상관계수가 {average_correlation:.2f}입니다. "
            "종목 수가 아닌 위험 요인 기준에서도 분산되어 있다고 판단한 근거는 무엇인가요?"
        )

    if not questions:
        questions.append(
            "현재 비중을 동일 비중이나 변동성 기준과 다르게 구성한 핵심 근거는 무엇인가요?"
        )
    return questions
