"""Unit tests for sample formats and recording metadata."""

from pathlib import Path

import pytest

from iqscope.errors import IQFormatError, MetadataError
from iqscope.io import IQMetadata, SampleFormat


@pytest.mark.parametrize(
    ("sample_format", "bytes_per_sample"),
    [
        (SampleFormat.CU8, 2),
        (SampleFormat.CI8, 2),
        (SampleFormat.CI16_LE, 4),
        (SampleFormat.CF32_LE, 8),
        (SampleFormat.CF64_LE, 16),
    ],
)
def test_bytes_per_sample(sample_format: SampleFormat, bytes_per_sample: int) -> None:
    assert sample_format.bytes_per_sample == bytes_per_sample


def test_format_values_are_sigmf_datatypes() -> None:
    assert SampleFormat("ci16_le") is SampleFormat.CI16_LE
    assert SampleFormat("cf32_le") is SampleFormat.CF32_LE


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("capture.cu8", SampleFormat.CU8),
        ("capture.cs8", SampleFormat.CI8),
        ("capture.cs16", SampleFormat.CI16_LE),
        ("capture.cfile", SampleFormat.CF32_LE),
        ("CAPTURE.CF32", SampleFormat.CF32_LE),
        ("capture.fc64", SampleFormat.CF64_LE),
    ],
)
def test_from_suffix(filename: str, expected: SampleFormat) -> None:
    assert SampleFormat.from_suffix(Path(filename)) is expected


@pytest.mark.parametrize("filename", ["capture.wav", "capture", "capture.raw"])
def test_from_suffix_unknown(filename: str) -> None:
    with pytest.raises(IQFormatError, match="cannot infer sample format"):
        SampleFormat.from_suffix(Path(filename))


def test_metadata_defaults_to_baseband() -> None:
    metadata = IQMetadata(sample_rate=2.4e6, sample_format=SampleFormat.CU8)
    assert metadata.center_frequency == 0.0


@pytest.mark.parametrize("sample_rate", [0.0, -1.0, float("nan"), float("inf")])
def test_metadata_rejects_invalid_sample_rate(sample_rate: float) -> None:
    with pytest.raises(MetadataError, match="sample_rate"):
        IQMetadata(sample_rate=sample_rate, sample_format=SampleFormat.CU8)


@pytest.mark.parametrize("center_frequency", [float("nan"), float("inf"), float("-inf")])
def test_metadata_rejects_non_finite_center_frequency(center_frequency: float) -> None:
    with pytest.raises(MetadataError, match="center_frequency"):
        IQMetadata(1e6, SampleFormat.CU8, center_frequency=center_frequency)


def test_metadata_accepts_negative_center_frequency() -> None:
    # Negative offsets occur e.g. for down-converted or shifted captures.
    assert IQMetadata(1e6, SampleFormat.CU8, center_frequency=-250e3).center_frequency == -250e3
