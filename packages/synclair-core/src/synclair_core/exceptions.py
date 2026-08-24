"""
synclair_core.exceptions
--------------------------

Shared exception hierarchy for synclair-core. Analysis modules
(synclair-structure, synclair-matching, ...) may subclass SynClairError
for their own error types, keeping a consistent root for the GUI/backend
to catch.
"""

from __future__ import annotations

__all__ = [
    "SynClairError",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigParseError",
    "ConfigValidationError",
    "DatasetLoadError",
]


class SynClairError(Exception):
    """Root exception for all SynClair-specific errors."""


class ConfigError(SynClairError):
    """Base class for DataConfig read/write/parse errors."""


class ConfigNotFoundError(ConfigError):
    """Raised when a config file path does not exist."""


class ConfigParseError(ConfigError):
    """Raised when config content cannot be parsed into a DataConfig."""


class ConfigValidationError(ConfigError):
    """Raised when a DataConfig fails validation against a dataset."""


class DatasetLoadError(SynClairError):
    """Raised when a dataset file cannot be loaded."""


class PipelineError(SynClairError):
    """Base class for pipeline/module lifecycle errors."""


class NotFittedError(PipelineError):
    """Raised when run() is called on a module before fit()."""