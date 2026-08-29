"""Tests for selecting and validating cross-examination questions."""

import pytest

from logic.cross_examination import (
    CrossExaminationError,
    select_cross_examination_questions,
    validate_cross_examination_answers,
)


def test_standard_questions_are_prioritized_and_limited() -> None:
    """Triggered team rules should appear before generic portfolio questions."""
    findings = [
        {"question": "산업 위험이 발생해도 논리가 유지되나요?"},
        {"question": "장기 논리가 단기에 반영될 근거는 무엇인가요?"},
    ]

    result = select_cross_examination_questions(
        findings,
        ["비중 차이의 근거는 무엇인가요?", "네 번째 질문"],
    )

    assert result == [
        "산업 위험이 발생해도 논리가 유지되나요?",
        "장기 논리가 단기에 반영될 근거는 무엇인가요?",
        "비중 차이의 근거는 무엇인가요?",
    ]


def test_duplicate_questions_are_removed() -> None:
    """The same question should never be shown twice."""
    question = "공통 위험을 확인했나요?"

    assert select_cross_examination_questions(
        [{"question": question}], [question]
    ) == [question]


def test_answers_are_trimmed_and_paired_with_questions() -> None:
    """Valid answers should retain their matching question."""
    result = validate_cross_examination_answers(
        ["가장 강한 반대 근거는 무엇인가요?"],
        ["  경쟁사의 시장점유율 상승을 확인하겠습니다.  "],
    )

    assert result == [
        {
            "question": "가장 강한 반대 근거는 무엇인가요?",
            "answer": "경쟁사의 시장점유율 상승을 확인하겠습니다.",
        }
    ]


def test_short_answers_are_rejected() -> None:
    """Very short answers do not provide enough material for final review."""
    with pytest.raises(CrossExaminationError, match="10자 이상"):
        validate_cross_examination_answers(["질문"], ["모르겠다"])
