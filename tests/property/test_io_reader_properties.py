"""Property tests for the IQ reader."""

from pathlib import Path
from typing import Any

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp
from numpy.typing import NDArray

from iqscope.io import IQMetadata, SampleFormat, decode, read_iq

INTEGER_FORMATS = [SampleFormat.CU8, SampleFormat.CI8, SampleFormat.CI16_LE]

# tmp_path is reused across examples; every example overwrites the file it reads.
reuses_tmp_path = settings(suppress_health_check=[HealthCheck.function_scoped_fixture])


@st.composite
def raw_components(draw: st.DrawFn, sample_format: SampleFormat) -> NDArray[Any]:
    num_samples = draw(st.integers(min_value=0, max_value=64))
    dtype = sample_format.component_dtype
    # Keep float components within float32 range: decoding to complex64 would overflow otherwise.
    elements = st.floats(width=32) if dtype.kind == "f" else None
    return draw(hnp.arrays(dtype, 2 * num_samples, elements=elements))


@given(data=st.data(), sample_format=st.sampled_from(INTEGER_FORMATS))
def test_integer_formats_decode_into_unit_range(
    data: st.DataObject, sample_format: SampleFormat
) -> None:
    samples = decode(data.draw(raw_components(sample_format)), sample_format)
    assert np.all(np.abs(samples.real) <= 1)
    assert np.all(np.abs(samples.imag) <= 1)


@given(data=st.data(), sample_format=st.sampled_from(list(SampleFormat)))
def test_decode_halves_component_count(data: st.DataObject, sample_format: SampleFormat) -> None:
    raw = data.draw(raw_components(sample_format))
    assert decode(raw, sample_format).size == raw.size // 2


@reuses_tmp_path
@given(
    samples=hnp.arrays(
        np.complex64,
        st.integers(min_value=0, max_value=64),
        elements=st.complex_numbers(allow_nan=False, allow_infinity=False, width=64),
    )
)
def test_cf32_roundtrip_is_exact(tmp_path: Path, samples: NDArray[np.complex64]) -> None:
    path = tmp_path / "x.cf32"
    samples.tofile(path)
    recording = read_iq(path, IQMetadata(1e6, SampleFormat.CF32_LE))
    np.testing.assert_array_equal(recording.samples, samples)


@reuses_tmp_path
@given(data=st.data(), sample_format=st.sampled_from(list(SampleFormat)))
def test_windowed_read_equals_slice_of_full_read(
    tmp_path: Path, data: st.DataObject, sample_format: SampleFormat
) -> None:
    path = tmp_path / "x.iq"
    data.draw(raw_components(sample_format)).tofile(path)
    metadata = IQMetadata(1e6, sample_format)
    full = read_iq(path, metadata).samples

    offset = data.draw(st.integers(min_value=0, max_value=full.size))
    count = data.draw(st.integers(min_value=0, max_value=full.size - offset))
    window = read_iq(path, metadata, offset=offset, count=count)

    np.testing.assert_array_equal(window.samples, full[offset : offset + count])
    assert window.start_sample == offset
