"""Tests for portfolio validation and concentration calculations."""

import pytest

from logic.portfolio import (
    PortfolioValidationError,
    calculate_concentration,
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

