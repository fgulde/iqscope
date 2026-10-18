"""Raw IQ formats → complex64, with windowed reads for large files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from iqscope.errors import IQFormatError
from iqscope.io.metadata import IQMetadata, SampleFormat
from iqscope.types import IQArray, Seconds

__all__ = ["IQRecording", "count_samples", "decode", "read_iq"]


@dataclass(frozen=True, slots=True, eq=False)
class IQRecording:
    """A block of decoded samples together with its metadata.

    ``start_sample`` is the index of ``samples[0]`` within the source file.
    """

    samples: IQArray
    metadata: IQMetadata
    start_sample: int = 0

    @property
    def num_samples(self) -> int:
        return int(self.samples.size)

    @property
    def duration(self) -> Seconds:
        return self.num_samples / self.metadata.sample_rate

    @property
    def start_time(self) -> Seconds:
        return self.start_sample / self.metadata.sample_rate


def decode(raw: NDArray[Any], sample_format: SampleFormat) -> IQArray:
    """Convert interleaved raw components (I0, Q0, I1, Q1, ...) to normalized complex64.

    Integer formats are mapped onto [-1, 1]; float formats are passed through.
    Always returns a new, writeable array.
    """
    if raw.ndim != 1 or raw.size % 2 != 0:
        msg = f"expected a 1-D array with an even number of components, got shape {raw.shape}"
        raise IQFormatError(msg)
    components = np.array(raw, dtype=np.float32)
    if sample_format.offset != 0.0:
        components -= np.float32(sample_format.offset)
    if sample_format.scale != 1.0:
        components /= np.float32(sample_format.scale)
    return components.view(np.complex64)


def count_samples(path: Path, sample_format: SampleFormat) -> int:
    """Number of complex samples in a raw IQ file."""
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
    """Read ``count`` samples starting at sample ``offset`` (default: to end of file).

    Only the requested window is read from disk, so large recordings can be
    processed in pieces.
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

    raw = np.fromfile(
        path,
        dtype=sample_format.component_dtype,
        count=2 * count,
        offset=offset * sample_format.bytes_per_sample,
    )
    return IQRecording(decode(raw, sample_format), metadata, start_sample=offset)
