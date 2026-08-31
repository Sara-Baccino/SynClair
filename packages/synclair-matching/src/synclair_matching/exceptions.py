from __future__ import annotations
from synclair_core.exceptions import SynClairError

__all__ = ["MatchingError", "UnsupportedCapabilityError"]


class MatchingError(SynClairError):
    """Raised for matching-module-specific errors."""

# --- aggiunta a synclair_matching/exceptions.py ---

class UnsupportedCapabilityError(ValueError):
    """Raised when a configuration selects a capability whose status is
    not SUPPORTED. Carries structured detail for the frontend."""

    def __init__(self, field: str, value: str, status: str) -> None:
        self.field = field
        self.value = value
        self.status = status
        super().__init__(
            f"Configuration field '{field}' = '{value}' is not supported yet (status: '{status}')."
        )