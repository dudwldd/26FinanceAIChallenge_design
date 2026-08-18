"""Interface reserved for future follow-up question generation."""

from typing import Any, Protocol


class QuestionGenerator(Protocol):
    """Describe a future follow-up question generator."""

    def generate(self, analysis: dict[str, Any]) -> list[str]:
        """Generate questions that help a user strengthen a thesis."""
        ...

