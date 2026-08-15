"""Fetch and normalize basic financial data for a US-listed ticker."""

from collections.abc import Callable, Mapping
import re
from typing import Any

import yfinance as yf


TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,9}$")


class FinancialDataError(ValueError):
    """Raised when financial data cannot be retrieved for a ticker."""


def _normalize_ticker(ticker: str) -> str:
    """Normalize and validate a ticker symbol."""
    normalized = ticker.strip().upper()
    if not normalized or not TICKER_PATTERN.fullmatch(normalized):
        raise FinancialDataError(
            "Please enter a valid ticker using letters, numbers, '.' or '-'."
        )
    return normalized


def _first_value(data: Mapping[str, Any], *keys: str) -> Any:
    """Return the first non-null value found for the supplied keys."""
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def get_financial_data(
    ticker: str,
    ticker_factory: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    """Return normalized market and financial data for a ticker."""
    normalized_ticker = _normalize_ticker(ticker)
    factory = ticker_factory or yf.Ticker

    try:
        stock = factory(normalized_ticker)
        info = stock.info
    except Exception as exc:
        raise FinancialDataError(
            f"Could not retrieve financial data for {normalized_ticker}. "
            "Please try again later."
        ) from exc

    if not isinstance(info, Mapping) or not info:
        raise FinancialDataError(
            f"No financial data was found for {normalized_ticker}. "
            "Please check the ticker and try again."
        )

    company_name = _first_value(info, "longName", "shortName")
    current_price = _first_value(
        info, "currentPrice", "regularMarketPrice", "previousClose"
    )

    if company_name is None and current_price is None and info.get("marketCap") is None:
        raise FinancialDataError(
            f"No financial data was found for {normalized_ticker}. "
            "Please check the ticker and try again."
        )

    return {
        "ticker": normalized_ticker,
        "company_name": company_name,
        "market_data": {
            "current_price": current_price,
            "market_cap": info.get("marketCap"),
        },
        "valuation": {
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
        },
        "growth": {"revenue_growth": info.get("revenueGrowth")},
        "profitability": {"profit_margin": info.get("profitMargins")},
        "financial_health": {"debt_to_equity": info.get("debtToEquity")},
    }

