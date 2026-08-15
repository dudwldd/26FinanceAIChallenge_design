"""Interface reserved for future investment-claim extraction."""

from typing import Any, Protocol


class ClaimExtractor(Protocol):
    """Describe a future claim extraction implementation."""

    def extract(self, thesis: str) -> dict[str, Any]:
        """Extract structured claims and categories from a thesis."""
        ...

