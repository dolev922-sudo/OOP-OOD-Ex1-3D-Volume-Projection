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
        delta = right[ys] - left[ys]
        data = self.volume.data
        shape = data.shape
        # Construct each coordinate separately and directly gather the voxels.
        # Keep the pre-rounding bounds test required by Volume.sample_many.
        x = left[ys, 0] + u * delta[:, 0]
        y = left[ys, 1] + u * delta[:, 1]
        z = left[ys, 2] + u * delta[:, 2]
        valid = ((x >= 0) & (x <= shape[0] - 1) &
                 (y >= 0) & (y <= shape[1] - 1) &
                 (z >= 0) & (z <= shape[2] - 1) &
                 np.isfinite(x) & np.isfinite(y) & np.isfinite(z))
        image = np.zeros((height, width), dtype=data.dtype)
        if np.any(valid):
            image[ys[valid], xs[valid]] = data[
                np.rint(x[valid]).astype(np.intp),
                np.rint(y[valid]).astype(np.intp),
                np.rint(z[valid]).astype(np.intp)]
        return image
