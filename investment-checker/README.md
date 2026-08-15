# Portfolio Thesis Checker

A minimal Streamlit proof of concept that retrieves financial data to help users
evaluate the reasoning behind a US-listed stock portfolio. It does not optimize
portfolio weights, make buy/sell decisions, or recommend securities.

## Project structure

```text
investment-checker/
├── app.py
├── data/financial_data.py
├── ai/claim_extractor.py
├── ai/question_generator.py
├── logic/fact_check.py
├── tests/test_financial_data.py
├── requirements.txt
├── .env.example
└── .gitignore
```

The `ai` interfaces and fact-checking module are placeholders for later stages.
The current POC retrieves normalized data from yfinance only.

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

Set `FMP_API_KEY` in `.env`. The current POC does not call FMP, so a key is not
required to run it. `.env` is excluded from Git.

## Run the app

```bash
streamlit run app.py
```

Enter portfolio tickers and weights, describe the portfolio thesis, answer the
five multiple-choice questions, then select **Check my thesis**. The app shows
simple concentration metrics and a table of available financial data. It does
not score the answers, forecast returns, or calculate optimal weights at this
POC stage. Missing provider values are displayed as `null`.

## Run tests

```bash
pytest
```

Tests use a fake ticker provider and do not require network access.
