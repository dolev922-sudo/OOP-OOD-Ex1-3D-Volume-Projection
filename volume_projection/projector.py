"""One vectorized projection algorithm for triangles and trapezoids."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import numpy as np

from .exceptions import InvalidPlaneError
from .geometry import Plane
from .volume import Volume

MAX_IMAGE_PIXELS = 20_000_000  # Defensive memory bound for absurd coordinates.


@dataclass(slots=True)
class PlaneProjector:
    """Rasterize the two side edges specified by a validated Plane.

    There is no per-pixel Python loop. NumPy creates the row/column mapping,
    interpolates 3-D samples, and performs one advanced-index voxel lookup.
    The output uses image[row=y, column=x] memory order.
    """

    volume: Volume

    @staticmethod
    def dimensions(plane: Plane) -> tuple[int, int]:
        """Return (height, width) using `max(2, round(length) + 1)`."""
        edges = plane.edges
        side, base = edges.side_length, edges.bottom_length
        if not (isfinite(side) and isfinite(base)):
            raise InvalidPlaneError("Plane dimensions are not finite")
        height = max(2, round(side) + 1)
        width = max(2, round(base) + 1)
        if height * width > MAX_IMAGE_PIXELS:
            raise InvalidPlaneError(
                f"Projection requires {height}x{width} pixels; maximum is {MAX_IMAGE_PIXELS}"
            )
        return height, width

    def project(self, plane: Plane) -> np.ndarray:
        """Return a native-bit-depth 2-D projection, black outside the shape."""
        height, width = self.dimensions(plane)
        edges = plane.edges
        left_top = edges.left_top.as_array()
        right_top = edges.right_top.as_array()
        left_bottom = edges.left_bottom.as_array()
        right_bottom = edges.right_bottom.as_array()

        t = np.arange(height, dtype=np.float64) / (height - 1)
        left = left_top + t[:, None] * (left_bottom - left_top)
        right = right_top + t[:, None] * (right_bottom - right_top)
        row_length = np.linalg.norm(right - left, axis=1)
        row_pixels = np.maximum(1, np.rint(row_length).astype(np.intp) + 1)
        starts = np.floor_divide(width - row_pixels, 2)

        # (row, col) map generated in one vectorized operation. Excludes
        # background pixels and clips possible one-pixel rounding overflow.
        columns = np.arange(width, dtype=np.intp)[None, :]
        local_column = columns - starts[:, None]
        active = (local_column >= 0) & (local_column < row_pixels[:, None])
        ys, xs = np.nonzero(active)
        js = local_column[ys, xs]
        denominators = row_pixels[ys] - 1
        u = np.divide(js, denominators, out=np.zeros(len(js), dtype=np.float64),
                      where=denominators > 0)
        samples = left[ys] + u[:, None] * (right[ys] - left[ys])
        image = np.zeros((height, width), dtype=self.volume.data.dtype)
        image[ys, xs] = self.volume.sample_many(samples)
        return image
