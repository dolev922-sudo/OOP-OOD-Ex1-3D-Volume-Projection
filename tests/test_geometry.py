"""FR-03/FR-04: required geometry and boundary tests."""
import math

import numpy as np
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


def test_unequal_triangle_edges_rejected():
    with pytest.raises(InvalidPlaneError, match="equal lengths"):
        Plane.from_points([point(0, 0, 0), point(1, 0, 0), point(0, 2, 0)])


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


def test_trapezoid_unequal_legs_rejected():
    with pytest.raises(InvalidPlaneError, match="equal lengths"):
        Plane.from_points([point(1, 0, 0), point(3, 0, 0),
                           point(0, 2, 0), point(5, 2, 0)])


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


@pytest.mark.parametrize("shape", ["triangle", "trapezoid"])
@pytest.mark.parametrize("other_length,accepted", [
    (np.nextafter(2 * EPS, 0), True),
    (2 * EPS, False),
    (np.nextafter(2 * EPS, math.inf), False),
])
def test_strict_leg_tolerance_boundary(shape, other_length, accepted):
    # Axis-aligned legs make the measured difference exactly EPS at equality,
    # avoiding the cancellation in (1 + EPS) - 1.
    if shape == "triangle":
        vertices = [point(0, 0, 0), point(EPS, 0, 0), point(0, other_length, 0)]
    else:
        vertices = [point(0, 0, 0), point(1, 0, 0),
                    point(0, EPS, 0), point(1, other_length, 0)]
    if accepted:
        assert Plane.from_points(vertices).shape == shape
    else:
        with pytest.raises(InvalidPlaneError, match="equal lengths"):
            Plane.from_points(vertices)


@pytest.mark.parametrize("count", [0, 1, 2, 5])
def test_invalid_vertex_counts(count):
    with pytest.raises(InvalidPlaneError, match="exactly 3 or 4"):
        Plane.from_points([point(0, 0, 0)] * count)


@pytest.mark.parametrize("bad", [None, (0, 0, 0), "point", 7])
def test_invalid_vertex_types(bad):
    with pytest.raises(InvalidPlaneError, match="Point3D"):
        Plane.from_points([point(0, 0, 0), point(1, 1, 0), bad])


@pytest.mark.parametrize("bad", [None, "x", complex(1, 2), math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("axis", [0, 1, 2])
def test_invalid_coordinates(bad, axis):
    coordinates = [0, 0, 0]
    coordinates[axis] = bad
    with pytest.raises(InvalidPlaneError, match="finite numbers"):
        point(*coordinates)


@pytest.mark.parametrize("bad", [0, -0.001, math.nan, math.inf, -math.inf, "invalid"])
def test_invalid_tolerance_configuration(monkeypatch, triangle, bad):
    # EPS is a fixed module constant, not an API parameter. Corrupting it must
    # never silently disable validation.
    monkeypatch.setattr("volume_projection.geometry.EPS", bad)
    with pytest.raises(InvalidPlaneError, match="finite positive tolerance"):
        triangle.validate()


@pytest.mark.parametrize("vertices", [
    [(0, 0, 0), (0, 0, 0), (1, 1, 0)],
    [(0, 0, 0), (1, 1, 0), (1, 1, 0)],
    [(0, 0, 0), (1, 0, 0), (0, 0, 0), (1, 2, 0)],
    [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)],
])
def test_degenerate_geometry(vertices):
    with pytest.raises(InvalidPlaneError, match="coincident|zero-length|collinear"):
        Plane.from_points([point(*v) for v in vertices])


def test_base_order_does_not_use_leg_eps_allowance():
    with pytest.raises(InvalidPlaneError, match="top base"):
        Plane.from_points([point(0, 0, 0), point(2 + EPS / 2, 0, 0),
                           point(EPS / 4, 2, 0), point(2 + EPS / 4, 2, 0)])


@pytest.mark.parametrize("offset,accepted", [(EPS * 0.999, True), (EPS, True), (EPS * 1.001, False)])
def test_coplanarity_distance_boundary(offset, accepted):
    vertices = [point(1, 0, 0), point(3, 0, 0), point(0, 2, 0), point(4, 2, offset)]
    if accepted:
        Plane.from_points(vertices)
    else:
        with pytest.raises(InvalidPlaneError, match="coplanar"):
            Plane.from_points(vertices)


def test_non_sequence_points_rejected():
    with pytest.raises(InvalidPlaneError, match="sequence"):
        Plane.from_points(None)
