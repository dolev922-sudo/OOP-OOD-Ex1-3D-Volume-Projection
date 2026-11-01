"""FR-03/FR-04: required geometry and boundary tests."""
import math

import pytest

from volume_projection import EPS, InvalidPlaneError, Plane, Point3D


def point(*xyz):
    return Point3D(*xyz)


def test_non_equilateral_isosceles_and_shared_edges(triangle):
    assert triangle.shape == "triangle"
    assert triangle.edges.left_top == triangle.edges.right_top
    assert triangle.edges.left_bottom == point(0, 2, 0)
    assert triangle.edges.right_bottom == point(4, 2, 0)


def test_equilateral_is_valid():
    plane = Plane.from_points([point(0, math.sqrt(3), 0),
                               point(-1, 0, 0), point(1, 0, 0)])
    assert plane.shape == "triangle"


def test_unequal_triangle_edges_are_supported():
    plane = Plane.from_points([point(0, 0, 0), point(1, 0, 0), point(0, 2, 0)])
    assert plane.shape == "triangle"


def test_collinear_triangle_rejected():
    with pytest.raises(InvalidPlaneError, match="collinear"):
        Plane.from_points([point(0, 0, 0), point(-1, 0, 0), point(1, 0, 0)])


def test_valid_trapezoid(trapezoid):
    assert trapezoid.shape == "trapezoid"
    assert trapezoid.edges.right_bottom == point(4, 2, 0)


def test_trapezoid_non_coplanar_rejected():
    # Leg difference is kept tiny by using small z displacement.
    with pytest.raises(InvalidPlaneError, match="coplanar"):
        Plane.from_points([point(1, 0, 0), point(3, 0, 0),
                           point(0, 2, 0), point(4, 2, EPS * 2)])


def test_trapezoid_unequal_legs_are_supported():
    plane = Plane.from_points([point(1, 0, 0), point(3, 0, 0),
                               point(0, 2, 0), point(5, 2, 0)])
    assert plane.shape == "trapezoid"


def test_trapezoid_invalid_base_order_rejected():
    with pytest.raises(InvalidPlaneError, match="top base"):
        Plane.from_points([point(0, 0, 0), point(4, 0, 0),
                           point(1, 2, 0), point(3, 2, 0)])


def test_trapezoid_accepts_equal_bases_with_float_rounding():
    # These equal 255-unit bases differ only by floating-point roundoff.
    plane = Plane.from_points([
        point(84.59417127, -44.49601041, 97.49942825),
        point(-42.90582873, 176.34046756, 97.49942825),
        point(297.90582873, 78.65953244, 31.50057175),
        point(170.40582873, 299.49601041, 31.50057175),
    ])
    assert plane.shape == "trapezoid"


def test_trapezoid_coincident_top_vertices_rejected():
    with pytest.raises(InvalidPlaneError, match="zero-length"):
        Plane.from_points([point(2, 0, 0), point(2, 0, 0),
                           point(0, 2, 0), point(4, 2, 0)])


def test_wrong_point_count_rejected():
    with pytest.raises(InvalidPlaneError, match="exactly 3 or 4"):
        Plane.from_points([point(1, 2, 3)])


def test_nonfinite_point_rejected():
    with pytest.raises(InvalidPlaneError, match="finite"):
        point(float("nan"), 0, 0)


def test_parallel_bases_not_extra_mandatory_rule():
    # Assignment demands equal legs, ordered bases, coplanarity, NOT
    # parallelism; this intentionally models the optional-validator choice.
    plane = Plane.from_points([point(0, 0, 0), point(2, 0, 0),
                               point(-1, 2, 0), point(1, -2, 0)])
    assert plane.shape == "trapezoid"
