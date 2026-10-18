"""Sample rate, center frequency, format description."""

import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from iqscope.errors import IQFormatError, MetadataError
from iqscope.types import Hertz

__all__ = ["IQMetadata", "SampleFormat"]


class SampleFormat(Enum):
    """On-disk layout of interleaved I/Q samples.

    Values follow the SigMF ``core:datatype`` names.
    """

    CU8 = "cu8"
    CI8 = "ci8"
    CI16_LE = "ci16_le"
    CF32_LE = "cf32_le"
    CF64_LE = "cf64_le"

    @property
    def component_dtype(self) -> np.dtype[Any]:
        """dtype of a single I or Q component."""
        return np.dtype(_SPECS[self].dtype)

    @property
    def bytes_per_sample(self) -> int:
        """Size of one complex sample (I and Q) in bytes."""
        return 2 * self.component_dtype.itemsize

    @property
    def offset(self) -> float:
        """Value subtracted from each raw component before scaling."""
        return _SPECS[self].offset

    @property
    def scale(self) -> float:
        """Divisor mapping the raw component range onto [-1, 1]."""
        return _SPECS[self].scale

    @classmethod
    def from_suffix(cls, path: Path) -> "SampleFormat":
        """Infer the format from common SDR file extensions (``.cu8``, ``.cs16``, ``.cfile``)."""
        suffix = path.suffix.lower()
        try:
            return _SUFFIXES[suffix]
        except KeyError:
            known = ", ".join(sorted(_SUFFIXES))
            msg = f"cannot infer sample format from suffix {suffix!r} (known: {known})"
            raise IQFormatError(msg) from None


@dataclass(frozen=True, slots=True)
class _FormatSpec:
    dtype: str
    offset: float = 0.0
    scale: float = 1.0


_SPECS: dict[SampleFormat, _FormatSpec] = {
    SampleFormat.CU8: _FormatSpec("u1", offset=127.5, scale=127.5),
    SampleFormat.CI8: _FormatSpec("i1", scale=128.0),
    SampleFormat.CI16_LE: _FormatSpec("<i2", scale=32768.0),
    SampleFormat.CF32_LE: _FormatSpec("<f4"),
    SampleFormat.CF64_LE: _FormatSpec("<f8"),
}

_SUFFIXES: dict[str, SampleFormat] = {
    ".cu8": SampleFormat.CU8,
    ".cs8": SampleFormat.CI8,
    ".ci8": SampleFormat.CI8,
    ".cs16": SampleFormat.CI16_LE,
    ".ci16": SampleFormat.CI16_LE,
    ".cf32": SampleFormat.CF32_LE,
    ".fc32": SampleFormat.CF32_LE,
    ".cfile": SampleFormat.CF32_LE,
    ".cf64": SampleFormat.CF64_LE,
    ".fc64": SampleFormat.CF64_LE,
}


@dataclass(frozen=True, slots=True)
class IQMetadata:
    """Everything needed to interpret a raw IQ recording."""

    sample_rate: Hertz
    sample_format: SampleFormat
    center_frequency: Hertz = 0.0

    def __post_init__(self) -> None:
        if not (math.isfinite(self.sample_rate) and self.sample_rate > 0):
            msg = f"sample_rate must be finite and positive, got {self.sample_rate}"
            raise MetadataError(msg)
        if not math.isfinite(self.center_frequency):
            msg = f"center_frequency must be finite, got {self.center_frequency}"
            raise MetadataError(msg)
