"""
synclair_structure.exceptions
--------------------------------

Exception hierarchy for synclair-structure, rooted in SynClairError so
callers (backend, GUI) can catch a single base type across all modules.
"""

from __future__ import annotations

from synclair_core.exceptions import SynClairError

__all__ = ["StructureError"]


class StructureError(SynClairError):
    """Raised for structure-module-specific errors (e.g. feature-matrix construction)."""