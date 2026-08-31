"""Shared type aliases and units."""

import numpy as np
from numpy.typing import NDArray

__all__ = ["Hertz", "IQArray", "RealArray", "Seconds"]

type IQArray = NDArray[np.complex64]
type RealArray = NDArray[np.float64]
type Hertz = float
type Seconds = float
