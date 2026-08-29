"""Select and validate questions for the second-stage cross-examination."""

from typing import Any


class CrossExaminationError(ValueError):
    """Raised when follow-up answers are incomplete."""


def select_cross_examination_questions(
    standard_findings: list[dict[str, Any]],
    portfolio_questions: list[str],
    *,
    limit: int = 3,
) -> list[str]:
    """Prioritize triggered standards and return unique follow-up questions."""
    candidates = [
        str(finding["question"])
        for finding in standard_findings
        if finding.get("question")
    ]
    candidates.extend(portfolio_questions)

    unique_questions: list[str] = []
    for question in candidates:
        if question not in unique_questions:
            unique_questions.append(question)
        if len(unique_questions) == limit:
            break
    return unique_questions


def validate_cross_examination_answers(
    questions: list[str], answers: list[str]
) -> list[dict[str, str]]:
    """Require one substantive answer for every generated question."""
    if len(questions) != len(answers):
        raise CrossExaminationError("모든 반대심문 질문에 답변해주세요.")

    records: list[dict[str, str]] = []
    for question, raw_answer in zip(questions, answers, strict=True):
        answer = raw_answer.strip()
        if len(answer) < 10:
            raise CrossExaminationError(
                "각 답변은 판단 근거를 알 수 있도록 10자 이상 작성해주세요."
            )
        records.append({"question": question, "answer": answer})
    return records
