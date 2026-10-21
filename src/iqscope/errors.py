"""Project exception hierarchy.

Callers can handle every intentional error with a single ``except IQScopeError``.
"""

__all__ = ["IQFormatError", "IQScopeError", "MetadataError"]


class IQScopeError(Exception):
    """Base class for all project-specific errors."""


class IQFormatError(IQScopeError):
    """Raw IQ data does not match its declared format (size, shape, suffix, read window)."""


class MetadataError(IQScopeError):
    """Recording metadata is invalid (e.g. non-positive sample rate)."""
