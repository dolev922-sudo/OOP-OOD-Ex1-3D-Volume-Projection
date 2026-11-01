"""Synthetic fixtures shared by the unit and integration tests."""
from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
import pytest

from volume_projection import Plane, Point3D, Volume
from volume_projection.csv_reader import CSV_HEADER


def write_nrrd(path: Path, data: np.ndarray, encoding: str = "raw",
               endian: str = "little", detached: bool = False) -> None:
    """Write a minimal standards-conforming file with axis 0 fastest."""
    dtype_name = {1: "unsigned char", 2: "unsigned short", 4: "unsigned int"}[data.dtype.itemsize]
    data_type = data.dtype.newbyteorder("<" if endian == "little" else ">")
    payload = np.asarray(data, dtype=data_type).tobytes(order="F")
    if encoding == "gzip":
        payload = gzip.compress(payload)
    header = ["NRRD0005", f"type: {dtype_name}", "dimension: 3",
              "sizes: " + " ".join(str(v) for v in data.shape),
              f"encoding: {encoding}"]
    if data.dtype.itemsize > 1:
        header.append(f"endian: {endian}")
    if detached:
        data_file = path.stem + ".raw"
        header.append(f"data file: {data_file}")
        (path.parent / data_file).write_bytes(payload)
        path.write_bytes(("\n".join(header) + "\n\n").encode("ascii"))
    else:
        path.write_bytes(("\n".join(header) + "\n\n").encode("ascii") + payload)


def write_csv(path: Path, rows: list[tuple[str, list[tuple[float, float, float]]]]) -> None:
    import csv
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(CSV_HEADER)
        for shape, points in rows:
            coordinates = [v for point in points for v in point]
            writer.writerow([shape, *coordinates, *([""] * (12 - len(coordinates)))])


@pytest.fixture
def gradient_volume() -> Volume:
    x, y, z = np.indices((7, 7, 3))
    return Volume((x + 10 * y + 100 * z).astype(np.uint8))


@pytest.fixture
def triangle() -> Plane:
    return Plane.from_points([Point3D(2, 0, 0), Point3D(0, 2, 0), Point3D(4, 2, 0)])


@pytest.fixture
def trapezoid() -> Plane:
    return Plane.from_points([Point3D(1, 0, 0), Point3D(3, 0, 0),
                              Point3D(0, 2, 0), Point3D(4, 2, 0)])
