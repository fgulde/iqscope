"""Project exception hierarchy."""

__all__ = ["IQFormatError", "IQScopeError", "MetadataError"]


class IQScopeError(Exception):
    """Base class for all project-specific errors."""


class IQFormatError(IQScopeError):
    """Raw IQ data does not match its declared format (size, shape, suffix)."""


class MetadataError(IQScopeError):
    """Recording metadata is invalid (e.g. non-positive sample rate)."""
