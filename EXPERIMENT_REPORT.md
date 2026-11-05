# Experiment report — OOP/OOD Ex1

**Date:** 2026-10-26

## Objective and setup

Verify that the implementation passes automated correctness checks, can build an MP4 from a synthetic NRRD+CSV demo, and measure projection and MP4 pipeline throughput on the specified `500 × 500 × 500` unsigned-byte volume.

- Runtime: **Python 3.13.5**, **NumPy 2.3.5**
- Reported processor identifier: **x86_64** (the environment does not provide a specific CPU model)
- Data: seeded random `uint8[500,500,500]` volume (**125,000,000 bytes**, decimal)
- Planes: 30 isosceles triangles using different z-slices and substantial image footprints (approximately 556 × 498 pixels)
- Timing method: `time.perf_counter()` around processing loops. Volume allocation and an initial projection warm-up excluded. The pipeline timing starts with encoder startup and ends after encoder close; it includes projection, frame preparation and H.264 encoding.
- Encoder: libx264, yuv420p; no resizing, video playback set to 10 FPS
- Benchmark script: `python -m benchmarks.benchmark --size 500 --frames 30 --encode --video-path examples/benchmark_500.mp4 --json benchmark_results_500.json`

## Measured results (one execution)

| Measurement | Elapsed | Throughput |
|---|---:|---:|
| Projection algorithm only | 0.77420 s | **38.75 frames/s** |
| Projection + padding + conversion + MP4 encoding | 1.20716 s | **24.85 frames/s** |

**Interpretation:** The **projection component** exceeded the assignment's mandatory 30 FPS threshold in this one environment/run; the **complete processing-to-MP4 pipeline did not**. The 100+ FPS target is **not met or demonstrated**. Repeated trials and target-machine measurements would be required for robust acceptance of the performance requirement. Disk I/O for reading the original NRRD and parsing CSV were not included in either measurement.

The machine-dependent JSON record is [`benchmark_results_500.json`](benchmark_results_500.json). The generated benchmark video is `examples/benchmark_500.mp4`.

## Functional verification

```text
python -m pytest -q
45 passed
```

Tests cover exact triangle and trapezoid projection matrices; equilateral and non-equilateral isosceles triangles; valid/invalid trapezoids; out-of-bounds samples; raw/gzip NRRD with all 8/16/32-bit unsigned types and byte orders; malformed inputs; real H.264 frame order and differing frame dimensions; and the required `Ex0.py` CLI.

## Demo result

```bash
python Ex0.py examples/demo.nrrd examples/planes.csv examples/demo.mp4
# Created 'examples/demo.mp4' with 3 frames
```

The synthetic demo images are included in `examples/demo.nrrd`, `examples/planes.csv`, and `examples/demo.mp4`, without relying on patient image datasets.

## Opportunities for further work (not assignment-completed claims)

The current NumPy implementation is vectorized but creates intermediate row/sample coordinates, which affect throughput. Possible later optimizations include precomputing reusable index grids, reducing coordinate array allocations, batching related operations, benchmarking alternate H.264 presets, or adding a compiled per-pixel kernel. Any optimization should keep the mathematical sampling rules and expected-output tests unchanged and be re-measured on the target machine.
