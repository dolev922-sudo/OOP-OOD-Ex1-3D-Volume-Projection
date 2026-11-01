"""Strict, unambiguous, ordered CSV plane reader."""
from __future__ import annotations

import csv
from pathlib import Path

from .exceptions import InvalidPlaneError, PlaneFormatError
from .geometry import Plane, Point3D

CSV_HEADER = ("shape", "x1", "y1", "z1", "x2", "y2", "z2",
              "x3", "y3", "z3", "x4", "y4", "z4")
POINT_COUNT_HEADER = ("number of points (3 or 4)", "x1", "y1", "z1",
                      "x2", "y2", "z2", "x3", "y3", "z3",
                      "x4", "y4", "z4")


class CSVPlaneReader:
    """Parse one plane per CSV row; reject malformed rows with line numbers."""

    def load(self, filename: str | Path) -> list[Plane]:
        path = Path(filename)
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream, strict=True)
                header = next(reader, None)
                normalized_header = tuple(v.strip().lower() for v in header) if header else None
                canonical_header = tuple(v.lower() for v in CSV_HEADER)
                point_count_header = tuple(v.lower() for v in POINT_COUNT_HEADER)
                if normalized_header == canonical_header:
                    uses_point_count = False
                elif normalized_header == point_count_header:
                    uses_point_count = True
                else:
                    expected = ",".join(CSV_HEADER)
                    alternate = ",".join(POINT_COUNT_HEADER)
                    raise PlaneFormatError(
                        f"CSV header must be either: {expected} or {alternate}"
                    )
                planes: list[Plane] = []
                for row in reader:
                    if not row or all(not field.strip() for field in row):
                        continue
                    planes.append(self._parse_row(row, reader.line_num, uses_point_count))
                if not planes:
                    raise PlaneFormatError("CSV contains no plane rows")
                return planes
        except OSError as exc:
            raise PlaneFormatError(f"Cannot read CSV '{path}': {exc}") from exc
        except (csv.Error, UnicodeError) as exc:
            raise PlaneFormatError(f"Malformed CSV '{path}': {exc}") from exc

    @staticmethod
    def _parse_row(row: list[str], line_number: int, uses_point_count: bool = False) -> Plane:
        if len(row) != len(CSV_HEADER):
            raise PlaneFormatError(f"CSV line {line_number}: expected 13 columns, got {len(row)}")
        shape = row[0].strip().lower()
        if uses_point_count:
            if shape == "3":
                shape = "triangle"
            elif shape == "4":
                shape = "trapezoid"
            else:
                raise PlaneFormatError(
                    f"CSV line {line_number}: number of points must be 3 or 4"
                )
        elif shape not in ("triangle", "trapezoid"):
            raise PlaneFormatError(f"CSV line {line_number}: shape must be triangle or trapezoid")
        count = 3 if shape == "triangle" else 4
        if count == 3 and any(field.strip() for field in row[10:]):
            raise PlaneFormatError(f"CSV line {line_number}: triangle x4/y4/z4 must be empty")
        points: list[Point3D] = []
        try:
            for index in range(count):
                start = 1 + 3 * index
                x, y, z = (float(v.strip()) for v in row[start:start + 3])
                points.append(Point3D(x, y, z))
            return Plane.from_points(points)
        except (ValueError, InvalidPlaneError) as exc:
            raise PlaneFormatError(f"CSV line {line_number}: {exc}") from exc
