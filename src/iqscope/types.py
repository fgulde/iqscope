"""Shared type aliases. Unit aliases such as ``Hertz`` document intent and are not enforced."""

import numpy as np
from numpy.typing import NDArray

__all__ = ["Hertz", "IQArray", "RealArray", "Seconds"]

type IQArray = NDArray[np.complex64]
"""Complex baseband samples ``I + jQ``."""

type RealArray = NDArray[np.float64]
"""Real-valued data, e.g. power spectra."""

type Hertz = float
"""Frequency or sample rate in Hz."""

type Seconds = float
"""Time in seconds."""
