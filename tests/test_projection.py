"""FR-05/FR-06: exact row-by-row outputs, vectorized OOB sampling."""
from typing import Literal

import numpy as np
import pytest

from volume_projection import InvalidPlaneError, Plane, PlaneProjector, Point3D, Volume, VolumeFormatError


def test_triangle_exact_pixels(gradient_volume: Volume, triangle: Plane):
    image = PlaneProjector(gradient_volume).project(triangle)
    assert image.dtype == np.uint8
    np.testing.assert_array_equal(image, [
        [0, 0, 2, 0, 0],
        [0, 11, 13, 0, 0],
        [11, 12, 12, 13, 0],
        [20, 21, 22, 23, 24],
    ])


def test_trapezoid_exact_pixels(gradient_volume: Volume, trapezoid: Plane):
    image = PlaneProjector(gradient_volume).project(trapezoid)
    assert image.shape == (3, 5)
    assert image.dtype == np.uint8
    np.testing.assert_array_equal(image, [
        [0, 1, 2, 3, 0],
        [10, 12, 12, 14, 0],
        [20, 21, 22, 23, 24],
    ])


def test_out_of_bounds_positions_never_round_inside():
    data = np.full((4, 4, 4), 9, dtype=np.uint8)
    volume = Volume(data)
    samples = np.array([[-0.1, 2, 1], [3.1, 1, 2], [1, 2, 3.01],
                        [0, 0, 0], [3, 3, 3]])
    np.testing.assert_array_equal(volume.sample_many(samples), [0, 0, 0, 9, 9])


def test_partly_outside_plane_keeps_in_bounds_samples():
    volume = Volume(np.full((6, 6, 2), 111, dtype=np.uint8))
    # Top outside x/y; some bottom vertices inside.
    plane = Plane.from_points([Point3D(2, -1, 0), Point3D(0, 2, 0),
                               Point3D(4, 2, 0)])
    projected = PlaneProjector(volume).project(plane)
    assert projected[0].sum() == 0
    assert projected[-1].sum() > 0


def test_uint16_and_uint32_precision_survives_projection(triangle: Plane):
    for dtype, value in ((np.uint16, 50000), (np.uint32, 3_000_000_000)):
        projector = PlaneProjector(Volume(np.full((7, 7, 3), value, dtype=dtype)))
        image = projector.project(triangle)
        assert image.dtype == dtype
        assert image[0, 2] == value
        assert image[0, 0] == 0


def test_tiny_equilateral_triangle_has_minimum_dimensions():
    plane = Plane.from_points([Point3D(1, 1, 1), Point3D(1.1, 1, 1),
                               Point3D(1.05, 1.0866025403784438, 1)])
    volume = Volume(np.full((3, 3, 3), 7, dtype=np.uint8))
    image = PlaneProjector(volume).project(plane)
    assert image.shape == (2, 2) and image.dtype == np.uint8
    np.testing.assert_array_equal(image, [[7, 0], [7, 0]])


# Hand-derived voxel locations for the existing small planes. These are not
# calculated by the projector, so axis permutations expose swapped axes too.
TRIANGLE_SAMPLES = [
    [None, None, (2, 0, 1), None, None],
    [None, (1, 1, 1), (3, 1, 1), None, None],
    [(1, 1, 1), (2, 1, 1), (2, 1, 1), (3, 1, 1), None],
    [(0, 2, 1), (1, 2, 1), (2, 2, 1), (3, 2, 1), (4, 2, 1)],
]
TRAPEZOID_SAMPLES = [
    [None, (1, 0, 1), (2, 0, 1), (3, 0, 1), None],
    [(0, 1, 1), (2, 1, 1), (2, 1, 1), (4, 1, 1), None],
    [(0, 2, 1), (1, 2, 1), (2, 2, 1), (3, 2, 1), (4, 2, 1)],
]


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
@pytest.mark.parametrize("axes", [(0, 1, 2), (2, 0, 1), (0, 2, 1)], ids=["z-slice", "x-slice", "y-slice"])
@pytest.mark.parametrize("shape", ["triangle", "trapezoid"])
def test_axis_aligned_exact_matrices_non_cubic(dtype: np.uint8 | np.uint16 | np.uint32, axes: Literal[0] | Literal[2], shape: Literal['triangle'] | Literal['trapezoid']):
    x, y, z = np.indices((7, 6, 5))
    volume = Volume((x + 5 * y + 25 * z).astype(dtype))
    vertices = ([(2, 0, 1), (0, 2, 1), (4, 2, 1)] if shape == "triangle"
                else [(1, 0, 1), (3, 0, 1), (0, 2, 1), (4, 2, 1)])
    plane = Plane.from_points([Point3D(*(v[a] for a in axes)) for v in vertices])
    samples = TRIANGLE_SAMPLES if shape == "triangle" else TRAPEZOID_SAMPLES
    expected = [[0 if v is None else v[axes[0]] + 5*v[axes[1]] + 25*v[axes[2]]
                 for v in row] for row in samples]
    image = PlaneProjector(volume).project(plane)
    assert image.shape == (len(samples), 5) and image.dtype == dtype
    np.testing.assert_array_equal(image, expected)


@pytest.mark.parametrize("vertices,expected", [
    ([(1, 0, 1), (0, 2, 2), (2, 2, 0)],
     [[0, 101, 0, 0], [0, 210, 12, 0], [220, 121, 121, 22]]),
    ([(0.5, 0, 1.5), (1.5, 0, 0.5), (0, 2, 2), (2, 2, 0)],
     [[0, 200, 2, 0], [210, 111, 12, 0], [220, 121, 121, 22]]),
])
@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
def test_rotated_real_3d_planes_exact_pixels(vertices: list[tuple[int, int, int]] | list[tuple[float, int, float] | tuple[int, int, int]], expected: list[list[int]], dtype: np.uint8 | np.uint16 | np.uint32):
    x, y, z = np.indices((3, 3, 3))
    volume = Volume((x + 10*y + 100*z).astype(dtype))
    plane = Plane.from_points([Point3D(*v) for v in vertices])
    image = PlaneProjector(volume).project(plane)
    assert image.shape == (3, 4) and image.dtype == dtype
    np.testing.assert_array_equal(image, expected)


@pytest.mark.parametrize("dtype,value", [(np.uint8, 0), (np.uint8, 255),
                                        (np.uint16, 65535), (np.uint32, 2**32-1)])
@pytest.mark.parametrize("shape", ["triangle", "trapezoid"])
def test_constant_and_zero_volumes_exact_shape_mask(dtype: np.uint8 | np.uint16 | np.uint32, value: Literal[0] | Literal[255] | Literal[65535] | Literal[4294967295], shape: Literal['triangle'] | Literal['trapezoid'], triangle: Plane, trapezoid: Plane):
    plane = triangle if shape == "triangle" else trapezoid
    samples = TRIANGLE_SAMPLES if shape == "triangle" else TRAPEZOID_SAMPLES
    expected = [[0 if v is None else value for v in row] for row in samples]
    image = PlaneProjector(Volume(np.full((5, 3, 1), value, dtype=dtype))).project(plane)
    assert image.shape == (len(samples), 5) and image.dtype == dtype
    np.testing.assert_array_equal(image, expected)


def test_minimum_volume_exact_projection():
    plane = Plane.from_points([Point3D(0, 0, 0), Point3D(-1, 1, 0), Point3D(1, 1, 0)])
    image = PlaneProjector(Volume(np.array([[[37]]], dtype=np.uint16))).project(plane)
    assert image.shape == (2, 3) and image.dtype == np.uint16
    np.testing.assert_array_equal(image, [[0, 37, 0], [0, 0, 0]])


@pytest.mark.parametrize("z", [-0.01, 2.01])
def test_completely_outside_plane_exact_zero(triangle: Plane, z: float):
    plane = Plane.from_points([Point3D(p.x, p.y, z) for p in triangle.points])
    image = PlaneProjector(Volume(np.full((5, 3, 3), 99, dtype=np.uint32))).project(plane)
    assert image.shape == (4, 5) and image.dtype == np.uint32
    np.testing.assert_array_equal(image, np.zeros((4, 5), dtype=np.uint32))


def test_partly_outside_exact_matrix(triangle: Plane):
    plane = Plane.from_points([Point3D(p.x, p.y-1, p.z) for p in triangle.points])
    image = PlaneProjector(Volume(np.full((5, 3, 1), 9, dtype=np.uint8))).project(plane)
    assert image.shape == (4, 5) and image.dtype == np.uint8
    np.testing.assert_array_equal(image, [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
                                         [9, 9, 9, 9, 0], [9, 9, 9, 9, 9]])


def test_rounding_half_to_even_and_nonfinite_samples():
    volume = Volume(np.arange(1, 5, dtype=np.uint16).reshape(4, 1, 1))
    points = np.array([[x, 0, 0] for x in [0, 0.5, 1.5, 2.5, 3, -0.01, 3.01,
                                         np.nan, np.inf, -np.inf]])
    actual = volume.sample_many(points)
    assert actual.shape == (10,) and actual.dtype == np.uint16
    np.testing.assert_array_equal(actual, [1, 1, 3, 3, 4, 0, 0, 0, 0, 0])


@pytest.mark.parametrize("data", [np.zeros((2, 2), dtype=np.uint8),
                                  np.zeros((0, 2, 2), dtype=np.uint8),
                                  np.zeros((1024, 1, 1), dtype=np.uint8),
                                  np.zeros((2, 2, 2), dtype=np.float32)])
def test_invalid_volume_arrays(data: np.ndarray):
    with pytest.raises(VolumeFormatError):
        Volume(data)


def test_unreasonable_projection_size_rejected():
    plane = Plane.from_points([Point3D(5000, 0, 0), Point3D(0, 10000, 0),
                               Point3D(10000, 10000, 0)])
    with pytest.raises(InvalidPlaneError, match="maximum"):
        PlaneProjector.dimensions(plane)


@pytest.mark.parametrize("points", [np.zeros(3), np.zeros((2, 2)), np.zeros((1, 3, 1))])
def test_sample_array_wrong_shape(points: np.ndarray, gradient_volume: Volume):
    with pytest.raises(ValueError, match="shape"):
        gradient_volume.sample_many(points)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
@pytest.mark.parametrize("layout", ["C", "F", "strided"])
def test_seeded_rotations_match_independent_scalar_reference(dtype: np.uint8 | np.uint16 | np.uint32, layout: Literal['C'] | Literal['F'] | Literal['strided']):
    from .reference_projection import scalar_projection

    rng = np.random.default_rng(20261102)
    data = rng.integers(0, np.iinfo(dtype).max, size=(24, 18, 20), dtype=dtype)
    if layout == "strided":
        data = data[::2, ::2, ::2]
    else:
        data = np.array(data[:12, :9, :10], order=layout)
    projector = PlaneProjector(Volume(data))
    for trial in range(24):
        rotation, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        vertices = np.array([(0, -2, 0), (-2, 2, 0), (2, 2, 0)] if trial % 2 == 0
                            else [(-1, -2, 0), (1, -2, 0), (-2, 2, 0), (2, 2, 0)])
        vertices = vertices @ rotation * rng.uniform(0.1, 2) + rng.uniform(-2, 12, size=3)
        plane = Plane.from_points([Point3D(*v) for v in vertices])
        expected = scalar_projection(data, vertices)
        actual = projector.project(plane)
        assert actual.shape == expected.shape and actual.dtype == dtype
        np.testing.assert_array_equal(actual, expected, err_msg=f"rotation {trial}, {layout}, {dtype}")
