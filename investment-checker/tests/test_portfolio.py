"""Tests for portfolio validation and concentration calculations."""

import pandas as pd
import pytest

from logic.portfolio import (
    PortfolioValidationError,
    calculate_average_correlation,
    calculate_concentration,
    calculate_return_correlation,
    calculate_sector_concentration,
    validate_portfolio,
)


def test_validate_portfolio_normalizes_tickers_and_weights() -> None:
    """Valid rows should be normalized when their weights total 100%."""
    result = validate_portfolio(
        [{"ticker": " aapl ", "weight": 60}, {"ticker": "msft", "weight": 40}]
    )

    assert result == [
        {"ticker": "AAPL", "weight": 60.0},
        {"ticker": "MSFT", "weight": 40.0},
    ]


def test_validate_portfolio_rejects_duplicate_tickers() -> None:
    """The same ticker should not appear in multiple rows."""
    with pytest.raises(PortfolioValidationError, match="중복된 ticker"):
        validate_portfolio(
            [{"ticker": "AAPL", "weight": 50}, {"ticker": "aapl", "weight": 50}]
        )


def test_validate_portfolio_requires_one_hundred_percent() -> None:
    """Portfolio weights should total exactly 100% within rounding tolerance."""
    with pytest.raises(PortfolioValidationError, match="현재 합계: 90.00%"):
        validate_portfolio(
            [{"ticker": "AAPL", "weight": 50}, {"ticker": "MSFT", "weight": 40}]
        )


def test_validate_portfolio_limits_holding_count() -> None:
    """The POC should accept no more than ten holdings."""
    rows = [{"ticker": f"T{i}", "weight": 100 / 11} for i in range(11)]

    with pytest.raises(PortfolioValidationError, match="최대 10개"):
        validate_portfolio(rows)


def test_calculate_concentration_returns_top_weights() -> None:
    """Concentration should report the largest and top-two combined weights."""
    result = calculate_concentration(
        [
            {"ticker": "AAPL", "weight": 20.0},
            {"ticker": "NVDA", "weight": 50.0},
            {"ticker": "MSFT", "weight": 30.0},
        ]
    )

    assert result == {
        "largest_ticker": "NVDA",
        "largest_weight": 50.0,
        "top_two_weight": 80.0,
    }


def test_calculate_sector_concentration_aggregates_weights() -> None:
    """Holdings in the same sector should be combined."""
    holdings = [
        {"ticker": "AAPL", "weight": 40.0},
        {"ticker": "MSFT", "weight": 30.0},
        {"ticker": "JPM", "weight": 30.0},
    ]

    result = calculate_sector_concentration(
        holdings,
        {"AAPL": "Technology", "MSFT": "Technology", "JPM": "Financial Services"},
    )

    assert result["sector_weights"] == {
        "Technology": 70.0,
        "Financial Services": 30.0,
    }
    assert result["dominant_sector"] == "Technology"
    assert result["dominant_weight"] == 70.0


def test_return_correlation_and_average() -> None:
    """Price returns should produce a symmetric correlation matrix and mean."""
    prices = pd.DataFrame(
        {
            "AAPL": [100.0, 110.0, 99.0, 108.9],
            "MSFT": [200.0, 220.0, 198.0, 217.8],
            "JPM": [50.0, 45.0, 49.5, 44.55],
        }
    )

    correlation = calculate_return_correlation(prices)

    assert correlation.loc["AAPL", "MSFT"] == pytest.approx(1.0)
    assert correlation.loc["AAPL", "JPM"] == pytest.approx(-1.0)
    assert calculate_average_correlation(correlation) == pytest.approx(-1 / 3)
