"""FR-05/FR-06: exact row-by-row outputs, vectorized OOB sampling."""
import numpy as np

from volume_projection import Plane, PlaneProjector, Point3D, Volume


def test_triangle_exact_pixels(gradient_volume, triangle):
    image = PlaneProjector(gradient_volume).project(triangle)
    assert image.dtype == np.uint8
    np.testing.assert_array_equal(image, [
        [0, 0, 2, 0, 0],
        [0, 11, 13, 0, 0],
        [11, 12, 12, 13, 0],
        [20, 21, 22, 23, 24],
    ])


def test_trapezoid_exact_pixels(gradient_volume, trapezoid):
    image = PlaneProjector(gradient_volume).project(trapezoid)
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


def test_uint16_and_uint32_precision_survives_projection(triangle):
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
    assert PlaneProjector(volume).project(plane).shape == (2, 2)
