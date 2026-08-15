# Investment Thesis Checker

미국 상장주식 포트폴리오에 대한 사용자의 투자 논리를 금융 데이터와 비교해 점검하는
Streamlit 기반 금융 AI Challenge MVP입니다.

이 서비스는 종목이나 매수·매도 시점을 추천하지 않습니다. 사용자가 직접
제시한 투자 근거를 구조화하고, 실제 데이터와 얼마나 부합하는지 검증할 수
있도록 돕는 것이 목표입니다.

## 현재 구현된 기능

- 최대 10개 미국 상장주식 ticker와 비중 입력
- 비중 합계 100%, 중복 ticker, 잘못된 ticker 검증
- 포트폴리오 구성 논리 입력
- 판단 근거, 계기, 확인한 자료, 투자 기간, 손실 대응에 관한 객관식 문항
- yfinance를 이용한 종목별 기본 금융 데이터 조회
- 최대 비중 종목과 상위 2개 종목 집중도 표시
- 종목별 금융 데이터 표 출력
- 잘못된 ticker와 외부 API 오류 처리
- 누락된 금융 데이터를 `None`으로 처리하는 일관된 데이터 구조

현재 조회하는 데이터는 다음과 같습니다.

- 회사명과 현재 주가
- 시가총액
- Trailing P/E와 P/B
- 매출 성장률과 이익률
- 부채비율

## 현재 구현하지 않은 기능

- 실제 LLM API 연동
- 투자 주장 자동 분류와 Fact Check
- 편향 탐지와 반대 질문 생성
- 점수 산정
- 종목 간 상관관계와 산업 집중도 분석
- 매수·매도 및 종목 추천
- 포트폴리오 최적화와 비중 추천
- 사용자 입력과 분석 결과의 영구 저장

현재 MVP는 사용자가 입력한 내용을 처리한 뒤 화면에만 보여주며 데이터베이스에
저장하지 않습니다.

## 프로젝트 구조

```text
investment-checker/
├── app.py
├── data/
│   └── financial_data.py
├── ai/
│   ├── claim_extractor.py
│   └── question_generator.py
├── logic/
│   └── fact_check.py
├── tests/
│   └── test_financial_data.py
├── requirements.txt
├── .env.example
└── README.md
```

## 로컬 실행 방법

Python 3.10 이상을 권장합니다.

```bash
git clone https://github.com/haebong1020/26FinanceAIChallenge.git
cd 26FinanceAIChallenge/investment-checker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저가 자동으로 열리지 않으면 다음 주소로 접속합니다.

```text
http://localhost:8501
```

## 환경변수

현재 POC는 yfinance만 사용하므로 API 키 없이 실행할 수 있습니다. 향후 FMP를
연결할 때는 예시 파일을 복사한 뒤 키를 설정합니다.

```bash
cp .env.example .env
```

```text
FMP_API_KEY=your_api_key_here
```

`.env`는 Git에 올라가지 않도록 `.gitignore`에 포함되어 있습니다. API 키를
코드나 README에 직접 작성하지 마세요.

## 테스트

```bash
cd investment-checker
pytest
```

테스트에서는 외부 API를 직접 호출하지 않고 가짜 ticker provider를 사용합니다.

## 주의사항

이 프로젝트가 제공하는 정보는 투자 자문이 아니며, 최종 투자 판단과 책임은
사용자에게 있습니다.
