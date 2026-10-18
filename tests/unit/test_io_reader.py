"""Unit tests for decoding and reading raw IQ files."""

from pathlib import Path

import numpy as np
import pytest

from iqscope.errors import IQFormatError
from iqscope.io import IQMetadata, SampleFormat, count_samples, decode, read_iq

SAMPLE_RATE = 1e6


def _write(path: Path, components: list[float] | list[int], sample_format: SampleFormat) -> Path:
    np.asarray(components, dtype=sample_format.component_dtype).tofile(path)
    return path


# --- decode -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sample_format", "raw", "expected"),
    [
        (SampleFormat.CU8, [0, 255], [-1 + 1j]),
        (SampleFormat.CI8, [-128, 64], [-1 + 0.5j]),
        (SampleFormat.CI16_LE, [-32768, 16384], [-1 + 0.5j]),
        (SampleFormat.CF32_LE, [0.25, -3.0], [0.25 - 3j]),
        (SampleFormat.CF64_LE, [1.5, 2.0], [1.5 + 2j]),
    ],
)
def test_decode_known_values(
    sample_format: SampleFormat, raw: list[float], expected: list[complex]
) -> None:
    samples = decode(np.asarray(raw, dtype=sample_format.component_dtype), sample_format)
    assert samples.dtype == np.complex64
    np.testing.assert_allclose(samples, expected, rtol=1e-6)


def test_decode_cu8_midscale_is_near_zero() -> None:
    # 127/128 straddle the unsigned midpoint 127.5 symmetrically.
    samples = decode(np.array([127, 128], dtype=np.uint8), SampleFormat.CU8)
    assert samples[0].real == pytest.approx(-samples[0].imag)
    assert abs(samples[0].real) < 1 / 127


def test_decode_interleaving_order() -> None:
    samples = decode(np.array([1, 2, 3, 4], dtype=np.float32), SampleFormat.CF32_LE)
    np.testing.assert_array_equal(samples, [1 + 2j, 3 + 4j])


def test_decode_returns_independent_copy() -> None:
    raw = np.array([1.0, 2.0], dtype=np.float32)
    samples = decode(raw, SampleFormat.CF32_LE)
    samples[0] = 0
    assert raw[0] == 1.0


def test_decode_empty() -> None:
    samples = decode(np.array([], dtype=np.int16), SampleFormat.CI16_LE)
    assert samples.shape == (0,)
    assert samples.dtype == np.complex64


@pytest.mark.parametrize("shape", [(3,), (2, 2)])
def test_decode_rejects_bad_shape(shape: tuple[int, ...]) -> None:
    with pytest.raises(IQFormatError, match="even number of components"):
        decode(np.zeros(shape, dtype=np.int16), SampleFormat.CI16_LE)


# --- count_samples / read_iq --------------------------------------------------------------------


def test_count_samples(tmp_path: Path) -> None:
    path = _write(tmp_path / "x.cs16", [0] * 10, SampleFormat.CI16_LE)
    assert count_samples(path, SampleFormat.CI16_LE) == 5


def test_count_samples_rejects_truncated_file(tmp_path: Path) -> None:
    path = tmp_path / "x.cs16"
    path.write_bytes(b"\x00" * 6)
    with pytest.raises(IQFormatError, match="not a multiple of 4 B"):
        count_samples(path, SampleFormat.CI16_LE)


def test_read_iq_whole_file(tmp_path: Path) -> None:
    path = _write(tmp_path / "x.cf32", [1, 2, 3, 4, 5, 6], SampleFormat.CF32_LE)
    metadata = IQMetadata(SAMPLE_RATE, SampleFormat.CF32_LE, center_frequency=100e6)

    recording = read_iq(path, metadata)

    np.testing.assert_array_equal(recording.samples, [1 + 2j, 3 + 4j, 5 + 6j])
    assert recording.metadata is metadata
    assert recording.start_sample == 0
    assert recording.num_samples == 3
    assert recording.duration == pytest.approx(3 / SAMPLE_RATE)


def test_read_iq_window(tmp_path: Path) -> None:
    path = _write(tmp_path / "x.cs16", list(range(20)), SampleFormat.CI16_LE)
    metadata = IQMetadata(SAMPLE_RATE, SampleFormat.CI16_LE)

    recording = read_iq(path, metadata, offset=3, count=4)

    expected = (np.arange(6, 14, 2) + 1j * np.arange(7, 15, 2)) / 32768
    np.testing.assert_allclose(recording.samples, expected, rtol=1e-6)
    assert recording.start_sample == 3
    assert recording.start_time == pytest.approx(3 / SAMPLE_RATE)


def test_read_iq_offset_at_end_gives_empty(tmp_path: Path) -> None:
    path = _write(tmp_path / "x.cu8", [0, 0, 0, 0], SampleFormat.CU8)
    recording = read_iq(path, IQMetadata(SAMPLE_RATE, SampleFormat.CU8), offset=2)
    assert recording.num_samples == 0


def test_read_iq_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "x.cu8"
    path.touch()
    recording = read_iq(path, IQMetadata(SAMPLE_RATE, SampleFormat.CU8))
    assert recording.num_samples == 0
    assert recording.duration == 0.0


@pytest.mark.parametrize(("offset", "count"), [(-1, None), (3, None), (0, 3), (1, 2), (0, -1)])
def test_read_iq_rejects_out_of_range_window(
    tmp_path: Path, offset: int, count: int | None
) -> None:
    path = _write(tmp_path / "x.cu8", [0, 0, 0, 0], SampleFormat.CU8)
    with pytest.raises(IQFormatError, match="out of range"):
        read_iq(path, IQMetadata(SAMPLE_RATE, SampleFormat.CU8), offset=offset, count=count)


def test_read_iq_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_iq(tmp_path / "missing.cu8", IQMetadata(SAMPLE_RATE, SampleFormat.CU8))
