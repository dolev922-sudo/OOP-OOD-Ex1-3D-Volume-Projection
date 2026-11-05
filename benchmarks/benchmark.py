"""Measure actual projection FPS on a synthetic N^3 unsigned-byte volume.

Usage:
  python -m benchmarks.benchmark --size 500 --frames 40
  python -m benchmarks.benchmark --size 500 --frames 40 --encode

Setup (allocation) and warm-up are EXCLUDED from processing FPS.
--encode adds frame conversion + H.264 writing, separately timed.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

from volume_projection import Plane, PlaneProjector, Point3D, VideoWriter, Volume


def make_planes(size: int, count: int) -> list[Plane]:
    """Use broad, in-bounds 2-D slices with a different z per frame."""
    if size < 6:
        raise ValueError("Benchmark volume side must be at least 6")
    center = (size - 1) / 2
    return [Plane.from_points([
        Point3D(center, 1, float(i % size)),
        Point3D(1, size - 2, float(i % size)),
        Point3D(size - 2, size - 2, float(i % size)),
    ]) for i in range(count)]


def run(size: int, frames: int, encode: bool = False,
        video_path: Path | None = None) -> dict:
    if frames < 1:
        raise ValueError("--frames must be positive")
    random = np.random.default_rng(2026)
    raw = random.integers(0, 256, size=(size, size, size), dtype=np.uint8)
    volume = Volume(raw)
    planes = make_planes(size, frames)
    projector = PlaneProjector(volume)
    projector.project(planes[0])  # warm up NumPy paths/cache before timing.

    start = time.perf_counter()
    for plane in planes:
        projector.project(plane)
    projection_seconds = time.perf_counter() - start
    report = {
        "size": [size] * 3,
        "dtype": "uint8",
        "frames": frames,
        "projection_seconds": round(projection_seconds, 5),
        "projection_fps": round(frames / projection_seconds, 2),
        "processor": platform.processor() or platform.machine(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "encoder_included_in_projection_fps": False,
    }
    if encode:
        target = video_path or Path("benchmark_output.mp4")
        dimensions = [projector.dimensions(plane) for plane in planes]
        video = VideoWriter(target, max(h for h, _ in dimensions),
                            max(w for _, w in dimensions))
        start = time.perf_counter()
        with video.open() as writer:
            for plane in planes:
                writer.append_data(video.prepare_frame(projector.project(plane)))
        end_to_end_seconds = time.perf_counter() - start
        report["pipeline_seconds"] = round(end_to_end_seconds, 5)
        report["pipeline_fps"] = round(frames / end_to_end_seconds, 2)
        report["video_path"] = str(target)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure projection and MP4 processing FPS")
    parser.add_argument("--size", type=int, default=500, help="cubic volume side length")
    parser.add_argument("--frames", type=int, default=40, help="number of frames to process")
    parser.add_argument("--encode", action="store_true", help="also measure H.264 video pipeline")
    parser.add_argument("--video-path", type=Path, default=None, help="benchmark output MP4")
    parser.add_argument("--json", type=Path, default=None, help="write JSON report to this path")
    args = parser.parse_args()
    report = run(args.size, args.frames, args.encode, args.video_path)
    print(json.dumps(report, indent=2))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
