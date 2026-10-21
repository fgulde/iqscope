"""Sample format and metadata of raw (headerless) IQ recordings."""

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
    """On-disk layout of interleaved I/Q samples (``I0, Q0, I1, Q1, ...``).

    Names follow the SigMF ``core:datatype`` convention. Integer formats are assumed to use
    the full range of their type.

    Attributes:
        CU8: Unsigned 8 bit (RTL-SDR).
        CI8: Signed 8 bit (HackRF).
        CI16_LE: Signed 16 bit, little endian.
        CF32_LE: 32 bit float, little endian (GNU Radio).
        CF64_LE: 64 bit float, little endian.
    """

    CU8 = "cu8"
    CI8 = "ci8"
    CI16_LE = "ci16_le"
    CF32_LE = "cf32_le"
    CF64_LE = "cf64_le"

    @property
    def component_dtype(self) -> np.dtype[Any]:
        """NumPy dtype of one I or Q component, including byte order."""
        return np.dtype(_SPECS[self].dtype)

    @property
    def bytes_per_sample(self) -> int:
        """Bytes per complex sample (I and Q)."""
        return 2 * self.component_dtype.itemsize

    @property
    def offset(self) -> float:
        """Subtracted from each raw component before scaling."""
        return _SPECS[self].offset

    @property
    def scale(self) -> float:
        """Divisor applied after ``offset``; maps integer formats onto [-1, 1]."""
        return _SPECS[self].scale

    @classmethod
    def from_suffix(cls, path: Path) -> "SampleFormat":
        """Infer the format from the file extension (e.g. ``.cu8``, ``.cs16``, ``.cfile``).

        Args:
            path: File path. Only the suffix is inspected, case-insensitively.

        Raises:
            IQFormatError: If the suffix is not recognized.
        """
        suffix = path.suffix.lower()
        try:
            return _SUFFIXES[suffix]
        except KeyError:
            known = ", ".join(sorted(_SUFFIXES))
            msg = f"cannot infer sample format from suffix {suffix!r} (known: {known})"
            raise IQFormatError(msg) from None


@dataclass(frozen=True, slots=True)
class _FormatSpec:
    """Decoding recipe of one ``SampleFormat``: component dtype and ``(x - offset) / scale``."""

    dtype: str
    offset: float = 0.0
    scale: float = 1.0


# Kept outside the Enum: class-level names inside an Enum would become members.
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
    """What a raw IQ file does not say about itself.

    Attributes:
        sample_rate: Complex samples per second in Hz; equals the observable bandwidth.
        sample_format: Storage format of the samples.
        center_frequency: RF frequency that maps to 0 Hz in baseband, in Hz. Zero if unknown.
    """

    sample_rate: Hertz
    sample_format: SampleFormat
    center_frequency: Hertz = 0.0

    def __post_init__(self) -> None:
        """Validate sample rate and center frequency.

        Raises:
            MetadataError: If a value is not finite or the sample rate is not positive.
        """
        if not (math.isfinite(self.sample_rate) and self.sample_rate > 0):
            msg = f"sample_rate must be finite and positive, got {self.sample_rate}"
            raise MetadataError(msg)
        if not math.isfinite(self.center_frequency):
            msg = f"center_frequency must be finite, got {self.center_frequency}"
            raise MetadataError(msg)
