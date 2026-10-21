"""Reading raw IQ files into normalized ``complex64`` arrays, optionally one window at a time."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from iqscope.errors import IQFormatError
from iqscope.io.metadata import IQMetadata, SampleFormat
from iqscope.types import IQArray, Seconds

__all__ = ["IQRecording", "count_samples", "decode", "read_iq"]


# eq=False: the generated __eq__ cannot compare ndarray fields.
@dataclass(frozen=True, slots=True, eq=False)
class IQRecording:
    """Decoded samples together with their metadata.

    Attributes:
        samples: 1-D complex samples; integer formats are normalized to [-1, 1].
        metadata: Metadata of the source recording.
        start_sample: Index of ``samples[0]`` in the source file.
    """

    samples: IQArray
    metadata: IQMetadata
    start_sample: int = 0

    @property
    def num_samples(self) -> int:
        """Number of complex samples."""
        return int(self.samples.size)

    @property
    def duration(self) -> Seconds:
        """Length in seconds."""
        return self.num_samples / self.metadata.sample_rate

    @property
    def start_time(self) -> Seconds:
        """Time of ``samples[0]`` since the start of the file, in seconds."""
        return self.start_sample / self.metadata.sample_rate


def decode(raw: NDArray[Any], sample_format: SampleFormat) -> IQArray:
    """Convert interleaved raw components to normalized ``complex64``.

    Integer formats are mapped onto [-1, 1], float formats are passed through. ``cf64`` is
    narrowed to single precision.

    Args:
        raw: 1-D array ``I0, Q0, I1, Q1, ...``. Its dtype is converted, not checked against
            ``sample_format``.
        sample_format: Determines offset and scale.

    Returns:
        New, writeable 1-D array of ``raw.size // 2`` samples.

    Raises:
        IQFormatError: If ``raw`` is not 1-D or has an odd length.
    """
    if raw.ndim != 1 or raw.size % 2 != 0:
        msg = f"expected a 1-D array with an even number of components, got shape {raw.shape}"
        raise IQFormatError(msg)
    # Always copy: the in-place operations below must not modify the caller's array.
    components = np.array(raw, dtype=np.float32)
    if sample_format.offset != 0.0:
        components -= np.float32(sample_format.offset)
    if sample_format.scale != 1.0:
        components /= np.float32(sample_format.scale)
    # Interleaved I/Q floats already have the memory layout of complex64.
    return components.view(np.complex64)


def count_samples(path: Path, sample_format: SampleFormat) -> int:
    """Count the complex samples in a file from its size.

    A matching size does not prove the format: ``cu8`` and ``ci8`` both use 2 bytes per sample.

    Args:
        path: Raw IQ file.
        sample_format: Determines the bytes per sample.

    Raises:
        IQFormatError: If the size is not a multiple of the sample size (truncated file or
            wrong format).
        FileNotFoundError: If ``path`` does not exist.
    """
    size = path.stat().st_size
    bytes_per_sample = sample_format.bytes_per_sample
    if size % bytes_per_sample != 0:
        msg = (
            f"{path}: size {size} B is not a multiple of {bytes_per_sample} B "
            f"per {sample_format.value} sample (truncated file or wrong format?)"
        )
        raise IQFormatError(msg)
    return size // bytes_per_sample


def read_iq(
    path: Path,
    metadata: IQMetadata,
    *,
    offset: int = 0,
    count: int | None = None,
) -> IQRecording:
    """Read a window of samples from a raw IQ file.

    Only the requested window is read from disk, so large files can be processed in pieces.

    Args:
        path: Raw IQ file.
        metadata: Sample rate and format of the file.
        offset: Index of the first sample to read.
        count: Number of samples to read; ``None`` reads to the end of the file.

    Raises:
        IQFormatError: If the file size does not fit the format or the window lies outside
            the file.
        FileNotFoundError: If ``path`` does not exist.
    """
    sample_format = metadata.sample_format
    total = count_samples(path, sample_format)
    if not 0 <= offset <= total:
        msg = f"offset {offset} out of range for {total} samples"
        raise IQFormatError(msg)
    available = total - offset
    if count is None:
        count = available
    elif not 0 <= count <= available:
        msg = f"count {count} out of range: {available} samples available from offset {offset}"
        raise IQFormatError(msg)

    # fromfile instead of memmap: no open handle outlives the call (file locks on Windows).
    raw = np.fromfile(
        path,
        dtype=sample_format.component_dtype,
        count=2 * count,
        offset=offset * sample_format.bytes_per_sample,
    )
    return IQRecording(decode(raw, sample_format), metadata, start_sample=offset)
