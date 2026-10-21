"""Reading of raw IQ files.

Raw files have no header, so the caller supplies sample rate and format via ``IQMetadata``.

Example:
    metadata = IQMetadata(2.4e6, SampleFormat.CU8, center_frequency=100e6)
    recording = read_iq(Path("capture.cu8"), metadata)
"""

from iqscope.io.metadata import IQMetadata, SampleFormat
from iqscope.io.reader import IQRecording, count_samples, decode, read_iq

__all__ = [
    "IQMetadata",
    "IQRecording",
    "SampleFormat",
    "count_samples",
    "decode",
    "read_iq",
]
