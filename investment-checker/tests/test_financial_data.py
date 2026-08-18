"""Tests for normalized financial data retrieval."""

import pandas as pd
import pytest

from data.financial_data import (
    FinancialDataError,
    get_financial_data,
    get_historical_prices,
)


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
            "sector": "Technology",
        }


def test_get_financial_data_returns_normalized_structure() -> None:
    """The provider should map source fields into stable sections."""
    result = get_financial_data(" aapl ", ticker_factory=FakeTicker)

    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["company_profile"]["sector"] == "Technology"
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


def test_get_historical_prices_extracts_close_data() -> None:
    """Multi-ticker downloads should return ordered adjusted close columns."""
    columns = pd.MultiIndex.from_product([["Close"], ["MSFT", "AAPL"]])
    downloaded = pd.DataFrame(
        [[300.0, 200.0], [303.0, 202.0]], columns=columns
    )

    def fake_download(**kwargs: object) -> pd.DataFrame:
        assert kwargs["tickers"] == ["AAPL", "MSFT"]
        return downloaded

    result = get_historical_prices(["aapl", "msft"], downloader=fake_download)

    assert list(result.columns) == ["AAPL", "MSFT"]
    assert result.iloc[0].to_dict() == {"AAPL": 200.0, "MSFT": 300.0}


def test_get_historical_prices_handles_empty_response() -> None:
    """An empty price response should become a readable provider error."""
    with pytest.raises(FinancialDataError, match="No historical prices"):
        get_historical_prices(
            ["AAPL", "MSFT"], downloader=lambda **kwargs: pd.DataFrame()
        )
