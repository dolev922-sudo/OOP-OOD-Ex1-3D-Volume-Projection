"""Volume ownership and vectorized nearest-neighbor voxel access."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .exceptions import VolumeFormatError


@dataclass(slots=True)
class Volume:
    """3-D voxel array indexed as M[x, y, z], with voxel-index coordinates."""

    data: np.ndarray

    def __post_init__(self) -> None:
        if self.data.ndim != 3:
            raise VolumeFormatError("Volume must be exactly 3-dimensional")
        if any(size < 1 or size >= 1024 for size in self.data.shape):
            raise VolumeFormatError("Every volume axis must have length in [1, 1023]")
        supported = self.data.dtype.kind == "u" and self.data.dtype.itemsize in (1, 2, 4)
        supported |= self.data.dtype.kind == "i" and self.data.dtype.itemsize == 2
        if not supported:
            raise VolumeFormatError(
                "Volume must contain unsigned 8-/16-/32-bit or signed 16-bit voxels"
            )

    def sample_many(self, points: np.ndarray) -> np.ndarray:
        """Sample (N,3) floating positions, returning N raw-precision values.

        Positions outside the closed grid range [0, size-1] return zero,
        even if a nearby in-bounds voxel would be chosen by rounding.
        Rounding follows NumPy's ties-to-even (`rint`) convention.
        """
        samples = np.asarray(points, dtype=np.float64)
        if samples.ndim != 2 or samples.shape[1] != 3:
            raise ValueError("Expected sample coordinates with shape (N, 3)")
        result = np.zeros(samples.shape[0], dtype=self.data.dtype)
        valid = np.isfinite(samples).all(axis=1) & (samples >= 0).all(axis=1)
        valid &= (samples <= (np.asarray(self.data.shape) - 1)).all(axis=1)
        if np.any(valid):
            indices = np.rint(samples[valid]).astype(np.intp)
            result[valid] = self.data[indices[:, 0], indices[:, 1], indices[:, 2]]
        return result
