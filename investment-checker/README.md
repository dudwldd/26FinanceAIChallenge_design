# Portfolio Thesis Checker

A minimal Streamlit proof of concept that retrieves financial data to help users
evaluate the reasoning behind a US-listed stock portfolio. It does not optimize
portfolio weights, make buy/sell decisions, or recommend securities. An optional
AI layer classifies the thesis, separates supported and uncertain points, flags
possible biases, and produces devil's-advocate questions.

## Project structure

```text
investment-checker/
├── app.py
├── data/financial_data.py
├── ai/portfolio_analyzer.py
├── logic/fact_check.py
├── tests/test_financial_data.py
├── requirements.txt
├── .env.example
└── .gitignore
```

The financial-data layer currently retrieves normalized data from yfinance. The
optional AI analysis uses OpenAI Structured Outputs so its result has a stable
shape for the Streamlit UI.

Users can enter up to ten tickers and portfolio weights. The app validates that
weights total 100%, rejects duplicate or malformed tickers, retrieves each
holding's basic financial data, and displays the largest holding and combined
weight of the top two holdings. It also aggregates weights by sector and shows a
one-year daily-return correlation matrix. Correlation is presented as historical
context, not as a forecast or investment recommendation.

For thesis checking, the app compares the user's weights with equal weights and
inverse-volatility weights. It shows historical return, annualized volatility,
and maximum drawdown under each weighting method, then generates deterministic
questions about material differences. These are comparison references, not
recommended or target allocations.

Users may optionally attach one text-based PDF up to 10MB. The app extracts
page-aware text in memory, shows a short preview, and includes the bounded text
in the optional AI analysis. The PDF is not stored in a database. Image-only
scans and encrypted PDFs are not supported in this MVP.

The app also applies three deterministic team review standards: diversification
illusion (sector weight of at least 70% or average correlation of at least
0.70), mismatch between long-term reasoning and a horizon below one year, and
quantitative claims made with a low level of supporting research. Each triggered
standard shows its measured basis, a neutral diagnosis, and a follow-up question.

## Installation

Python 3.10 or newer is recommended.

```bash
cd investment-checker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment variables

Copy the example file if you plan to add Financial Modeling Prep later:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` to enable the optional AI checkbox. `OPENAI_MODEL` defaults
to `gpt-5.4-mini`. `FMP_API_KEY` is reserved for a later FMP integration. No key
is required for the existing deterministic portfolio analysis, and `.env` is
excluded from Git.

```text
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.4-mini
```

## Run the app

```bash
streamlit run app.py
```

Enter portfolio tickers and weights, describe the portfolio thesis, answer the
five multiple-choice questions, optionally enable AI analysis, then select
**Check my thesis**. The app shows
simple concentration metrics and a table of available financial data. It does
not score the answers, forecast returns, or calculate optimal weights at this
POC stage. Missing provider values are displayed as `null`. When AI analysis is
enabled, the thesis and the displayed portfolio-data summary are sent to the
OpenAI API; they are not stored by this app.

## Run tests

```bash
pytest
```

Tests use a fake ticker provider and do not require network access.
