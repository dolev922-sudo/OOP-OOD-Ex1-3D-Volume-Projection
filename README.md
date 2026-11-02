# 3D Volume Plane Projection

An object-oriented Python implementation of OOP/OOD Ex1: sample triangle or
trapezoid planes from a 3D NRRD volume, then write one H.264 MP4 frame per CSV
row. Coordinates are voxel indices, not physical millimeters.

## Run

Use Python 3.10+; FFmpeg is provided by imageio-ffmpeg.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python Ex0.py examples/demo.nrrd examples/planes.csv output.mp4
```

On macOS/Linux, activate with `source .venv/bin/activate`.
Running `python Ex0.py` without paths opens the optional Tkinter file picker.
The three-path CLI works without a GUI. The output directory must exist and
the extension must be `.mp4`. Failures retain an existing output file.

## Project map

| Location | Purpose |
|---|---|
| [Ex0.py](Ex0.py) | CLI and optional file picker |
| [volume_projection/](volume_projection/) | Geometry, NRRD/CSV input, projection, video output |
| [tests/](tests/) | Deterministic unit, scalar-reference, and integration checks |
| [examples/](examples/) | Synthetic inputs, demo video, and input generator |
| [benchmarks/](benchmarks/) | Configurable, separately run performance experiments |
| [SRS.md](SRS.md) | Requirements and explicit interpretations |
| [ALGORITHM.md](ALGORITHM.md) | Geometry, sampling, and design |
| [TEST_STRATEGY.md](TEST_STRATEGY.md) | Coverage matrix and limitations |
| [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md) | Measured verification and performance results |
| [COMPARISON_REPORT.md](COMPARISON_REPORT.md) | Historical comparison before strict validation |

## Input and geometry

NRRD supports raw/gzip data, embedded or one detached payload, unsigned
8/16/32-bit values, and signed 16-bit values as an extension. Axes must each
have 1–1023 voxels. NRRD axis 0 varies fastest; data is loaded in Fortran
order without swapping coordinate axes. Multichannel data, ASCII/bzip2,
file lists, and world-coordinate transforms are unsupported.

CSV uses a header and exactly 13 columns:

```csv
shape,x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
triangle,2,0,0,0,2,0,4,2,0,,,
trapezoid,1,0,0,3,0,0,0,2,0,4,2,0
```

- Triangle points are `(a,b,c)`, with apex `a`; fourth-point cells must be empty.
- Trapezoid points are `(a1,a2,b,c)`; top is `a1–a2`, bottom is `b–c`.
- The alternate first header `Number of Points (3 or 4)` accepts `3`/`4`
  instead of shape names. **Point order stays the same**, unlike the
  `(a1,b,a2,c)` convention used by some external projects.
- Coordinates must be finite. Blank rows are ignored; malformed rows fail
  the run with a line number. No invalid plane is silently skipped.

Validation enforces:

```text
triangle:  abs(distance(a,b) - distance(a,c)) < 0.001
trapezoid: abs(distance(a1,b) - distance(a2,c)) < 0.001
           distance(a1,a2) <= distance(b,c)
           all four points coplanar
```

Equality at EPS is rejected. Equilateral triangles are valid. Coincident
vertices and degenerate defining planes are rejected. Base ordering allows
only floating-point roundoff (eight ULPs), not a 0.001 geometric allowance.
Coplanarity uses perpendicular distance <= 0.001 voxel units. Parallel
bases are not an extra requirement. EPS is fixed, not a CLI option.

## Sampling and video

Row interpolation between two side edges uses inclusive endpoints and
horizontal centering. Image height is `max(2,round(L)+1)` and width is
`max(2,round(B)+1)`, where L is the longer accepted near-equal leg and B is
the bottom base. This is a documented rasterization choice, not a claim
that the assignment resolves all rounding ambiguities.

| Policy | Behavior |
|---|---|
| Fractional coordinates | Nearest neighbor, ties-to-even (rint) |
| Outside volume | Zero; bounds checked before rounding |
| Outside shape | Zero |
| Allocation limit | At most 20 million projection pixels |
| Different image sizes | Center on common even black canvas, no resize |
| Unsigned video intensity | uint8 unchanged; uint16 >> 8; uint32 >> 24 |
| Signed int16 extension | Nonnegative frames scale by their maximum; otherwise offset full signed range |
| Video | H.264/YUV420p, 10 playback FPS, lossy |

Signed frame scaling can change brightness across frames; it is retained for
compatibility, not medical window/level processing. Raw projections retain
original precision. Frames are streamed instead of accumulated.

## Verify

```powershell
python -m pytest -q
python -m benchmarks.benchmark --size 500 --frames 30 --trials 3 --warmup 3 --scenario mixed --encode --json benchmark_results.json
```

Scenarios include axis-aligned, rotated, large in-bounds, and mixed planes;
supported benchmark dtypes are uint8, uint16, and uint32. Normal tests have
no machine-dependent speed assertions. Projection and encoding-pipeline
FPS are reported separately, with trial/frame timings and process memory
where available. See the experiment report for actual >30 FPS minimum and
100 FPS target outcomes; neither is the video playback rate.

The assignment PDF was unavailable during the 2026-11-02 audit. The rules
quoted in the requested task and SRS were used. Unspecified sampling
policies remain explicit implementation decisions.
