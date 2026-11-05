"""Immutable geometry types, plane classification, and validation."""
from __future__ import annotations

from dataclasses import dataclass
from math import dist, isfinite, ulp
from numbers import Real
from typing import Sequence

import numpy as np

from .exceptions import InvalidPlaneError

EPS = 0.001  # Strict distance-comparison tolerance from the assignment.
# Reject effectively zero 2-D cross-products, independently of EPS.
_DEGENERATE_SINE = 1e-12


@dataclass(frozen=True, slots=True)
class Point3D:
    """3-D coordinate expressed in voxel-index space, not physical millimeters."""

    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        if not all(isinstance(v, Real) and isfinite(v) for v in (self.x, self.y, self.z)):
            raise InvalidPlaneError("Point coordinates must be finite numbers")

    def as_array(self) -> np.ndarray:
        """Return a NumPy (3,) floating-point vector."""
        return np.array((self.x, self.y, self.z), dtype=np.float64)

    def distance_to(self, other: Point3D) -> float:
        return dist((self.x, self.y, self.z), (other.x, other.y, other.z))


@dataclass(frozen=True, slots=True)
class EdgePair:
    """The common two-side representation consumed by the rasterizer."""

    left_top: Point3D
    left_bottom: Point3D
    right_top: Point3D
    right_bottom: Point3D

    @property
    def side_length(self) -> float:
        return max(
            self.left_top.distance_to(self.left_bottom),
            self.right_top.distance_to(self.right_bottom),
        )

    @property
    def bottom_length(self) -> float:
        return self.left_bottom.distance_to(self.right_bottom)


@dataclass(frozen=True, slots=True)
class Plane:
    """A validated triangle or assignment-defined trapezoid.

    Three points are (a, b, c); four points are (a1, a2, b, c).
    """

    points: tuple[Point3D, ...]

    @classmethod
    def from_points(cls, points: Sequence[Point3D]) -> Plane:
        try:
            result = cls(tuple(points))
        except TypeError as exc:
            raise InvalidPlaneError("Plane points must be a sequence of Point3D instances") from exc
        result.validate()
        return result

    @property
    def shape(self) -> str:
        return {3: "triangle", 4: "trapezoid"}.get(len(self.points), "invalid")

    @property
    def edges(self) -> EdgePair:
        self.validate()
        if len(self.points) == 3:
            a, b, c = self.points
            return EdgePair(a, b, a, c)
        a1, a2, b, c = self.points
        return EdgePair(a1, b, a2, c)

    def validate(self) -> None:
        if not isinstance(EPS, Real) or not isfinite(EPS) or EPS <= 0:
            raise InvalidPlaneError("EPS must be a finite positive tolerance")
        if len(self.points) not in (3, 4):
            raise InvalidPlaneError("A plane requires exactly 3 or 4 points")
        if not all(isinstance(point, Point3D) for point in self.points):
            raise InvalidPlaneError("All plane vertices must be Point3D instances")
        if len(self.points) == 3:
            a, b, c = (p.as_array() for p in self.points)
            ab, ac = b - a, c - a
            lab, lac, lbc = (float(np.linalg.norm(v)) for v in (ab, ac, c - b))
            _finite_lengths(lab, lac, lbc)
            if min(lab, lac, lbc) <= 0:
                raise InvalidPlaneError("Triangle has coincident vertices")
            if np.linalg.norm(np.cross(ab / lab, ac / lac)) <= _DEGENERATE_SINE:
                raise InvalidPlaneError("Triangle vertices are collinear")
            if abs(lab - lac) >= EPS:
                raise InvalidPlaneError("Triangle sides must have equal lengths (difference < EPS=0.001)")
            return

        a1, a2, b, c = (p.as_array() for p in self.points)
        ab, a2c, top, bottom = b - a1, c - a2, a2 - a1, c - b
        leg1, leg2 = float(np.linalg.norm(ab)), float(np.linalg.norm(a2c))
        top_len, bottom_len = float(np.linalg.norm(top)), float(np.linalg.norm(bottom))
        _finite_lengths(leg1, leg2, top_len, bottom_len)
        if min(leg1, leg2, top_len, bottom_len) <= 0:
            raise InvalidPlaneError("Trapezoid contains a zero-length edge")
        # Base order has no EPS allowance in the specification. Permit only
        # floating-point roundoff for mathematically equal rotated bases.
        if top_len - bottom_len > 8 * max(ulp(top_len), ulp(bottom_len)):
            raise InvalidPlaneError("Trapezoid top base must not exceed bottom base")
        normal = np.cross(top / top_len, ab / leg1)
        normal_length = float(np.linalg.norm(normal))
        if not isfinite(normal_length) or normal_length <= _DEGENERATE_SINE:
            raise InvalidPlaneError("Trapezoid defining vertices are collinear")
        # Scale-aware: perpendicular *distance* to the plane, in voxel units.
        perpendicular_distance = abs(float(np.dot(c - a1, normal))) / normal_length
        if perpendicular_distance > EPS:
            raise InvalidPlaneError("Trapezoid vertices are not coplanar")
        if abs(leg1 - leg2) >= EPS:
            raise InvalidPlaneError("Trapezoid legs must have equal lengths (difference < EPS=0.001)")
        # No parallel-base restriction: the SRS calls it an optional check,
        # not part of the assignment's mandatory validation.


def _finite_lengths(*values: float) -> None:
    if not all(isfinite(value) for value in values):
        raise InvalidPlaneError("Plane geometry overflows floating-point range")
