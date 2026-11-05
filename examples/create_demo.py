"""Create deterministic synthetic NRRD + CSV inputs for the CLI demo.

Run from project root: python examples/create_demo.py
"""
from __future__ import annotations

import csv
import gzip
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent


def main() -> None:
    x, y, z = np.indices((32, 32, 16), dtype=np.uint16)
    # Deliberately recognizable patterned 8-bit volume, no patient data.
    voxels = ((x * 7 + y * 3 + z * 11) % 256).astype(np.uint8)
    raw = voxels.tobytes(order="F")
    header = b"NRRD0005\ntype: unsigned char\ndimension: 3\nsizes: 32 32 16\nencoding: gzip\n\n"
    (OUT / "demo.nrrd").write_bytes(header + gzip.compress(raw))
    with (OUT / "planes.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["shape", "x1", "y1", "z1", "x2", "y2", "z2",
                         "x3", "y3", "z3", "x4", "y4", "z4"])
        rows = [
            ("triangle", ((15, 2, 2), (3, 24, 2), (27, 24, 2))),
            ("trapezoid", ((10, 3, 6), (20, 3, 6), (4, 20, 6), (26, 20, 6))),
            ("triangle", ((15, 3, 11), (9, 17, 11), (21, 17, 11))),
        ]
        for shape, points in rows:
            coords = [value for point in points for value in point]
            writer.writerow([shape, *coords, *([""] * (12 - len(coords)))])
    print("Created examples/demo.nrrd and examples/planes.csv")


if __name__ == "__main__":
    main()
