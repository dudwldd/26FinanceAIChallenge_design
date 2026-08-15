# Investment Thesis Checker

A minimal Streamlit proof of concept that retrieves financial data to help users
evaluate their own investment reasoning for US-listed stocks. It does not make
buy/sell decisions or recommend securities.

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

Enter a ticker and an investment thesis, answer the five multiple-choice
questions, then select **Check my thesis**. The questions capture the thesis's
main basis, decision trigger, evidence level, investment horizon, and likely
response to a 30% loss. The app shows the submitted inputs and available
financial data. It does not score the answers at this POC stage. Missing provider
values are displayed as `null`.

## Run tests

```bash
pytest
```

Tests use a fake ticker provider and do not require network access.
