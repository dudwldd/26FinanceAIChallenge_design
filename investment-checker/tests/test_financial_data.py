"""Tests for normalized financial data retrieval."""

import pytest

from data.financial_data import FinancialDataError, get_financial_data


class FakeTicker:
    """Small yfinance ticker substitute used by unit tests."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.info = {
            "longName": "Apple Inc.",
            "currentPrice": 200.0,
            "marketCap": 3_000_000_000_000,
            "trailingPE": 30.0,
            "priceToBook": 40.0,
            "revenueGrowth": 0.05,
            "profitMargins": 0.24,
            "debtToEquity": 150.0,
        }


def test_get_financial_data_returns_normalized_structure() -> None:
    """The provider should map source fields into stable sections."""
    result = get_financial_data(" aapl ", ticker_factory=FakeTicker)

    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["market_data"]["current_price"] == 200.0
    assert result["valuation"]["pe_ratio"] == 30.0
    assert result["growth"]["revenue_growth"] == 0.05
    assert result["profitability"]["profit_margin"] == 0.24
    assert result["financial_health"]["debt_to_equity"] == 150.0


def test_get_financial_data_preserves_missing_values() -> None:
    """Missing source values should be returned as None, not fail the request."""
    class PartialTicker:
        info = {"shortName": "Example Corp", "regularMarketPrice": 10.0}

        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

    result = get_financial_data("EXM", ticker_factory=PartialTicker)

    assert result["valuation"]["pe_ratio"] is None
    assert result["financial_health"]["debt_to_equity"] is None


def test_get_financial_data_rejects_invalid_ticker() -> None:
    """Malformed tickers should fail before any provider call."""
    with pytest.raises(FinancialDataError, match="valid ticker"):
        get_financial_data("AAPL!", ticker_factory=FakeTicker)


def test_get_financial_data_handles_empty_provider_response() -> None:
    """An empty provider response should become a user-readable error."""
    class EmptyTicker:
        info: dict[str, object] = {}

        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

    with pytest.raises(FinancialDataError, match="No financial data"):
        get_financial_data("NONE", ticker_factory=EmptyTicker)

