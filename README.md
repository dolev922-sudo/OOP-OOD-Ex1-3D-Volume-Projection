# OOP/OOD Ex1 — 3D Volume Plane Projection

A Python, object-oriented implementation of the Ariel University introductory software engineering assignment. The program reads a **3-D NRRD volume** and a CSV containing **triangle or isosceles trapezoid** planes, creates a **2-D projection per plane**, and writes the projections in CSV order to **H.264 MP4**.

The original requirements and planned mathematical algorithm are preserved in [`SRS.md`](SRS.md) and [`ALGORITHM.md`](ALGORITHM.md). Choices left open in those documents are explicitly listed below. The implementation emphasizes correctness, predictable failure, and clear separation of responsibilities; it does not claim to meet all performance targets.

## Quick start

Use **Python 3.10+**. These commands run from the repository root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

python -m pip install -r requirements.txt
python Ex0.py examples/demo.nrrd examples/planes.csv output.mp4
```

This repository includes a ready-to-use `examples/demo.nrrd`, `examples/planes.csv`, and `examples/demo.mp4` generated with synthetic data. To regenerate the inputs:

```bash
python examples/create_demo.py
python Ex0.py examples/demo.nrrd examples/planes.csv examples/demo.mp4
```

For your own input files, the exact **required CLI** is:

```bash
python Ex0.py input.nrrd planes.csv output.mp4
```

On success, it prints the number of frames and exits with code `0`. For malformed input or encoding failure it prints a descriptive error to stderr, exits with code `1`, and does not publish a partially written output. The output directory must exist. MP4 encoding is supplied through `imageio-ffmpeg`'s bundled FFmpeg executable.

## Repository structure

```text
OOP-OOD-Ex1/
├── Ex0.py                        # Required three-positional-argument CLI
├── SRS.md                        # Original specification, unchanged
├── ALGORITHM.md                  # Original algorithm design, unchanged
├── README.md                     # Design decisions, usage, limitations
├── TEST_STRATEGY.md              # Requirement/test traceability
├── EXPERIMENT_REPORT.md          # Measured FPS, test results, caveats
├── benchmark_results_500.json    # Recorded 500³ benchmark run
├── requirements.txt
├── pytest.ini
├── volume_projection/
│   ├── application.py            # Workflow and dependency injection
│   ├── geometry.py               # Point3D, Plane, EdgePair, validation
│   ├── volume.py                 # 3D data and vectorized sampling
│   ├── nrrd_reader.py            # NRRD data loading + axis order
│   ├── csv_reader.py             # Strict 13-column CSV parser
│   ├── projector.py              # One NumPy projection implementation
│   ├── video_writer.py           # Dynamic padding, intensity, MP4 output
│   └── exceptions.py             # Meaningful domain errors
├── tests/                        # Unit and end-to-end pytest tests
├── benchmarks/benchmark.py       # Measured processing throughput
└── examples/
    ├── create_demo.py
    ├── demo.nrrd
    ├── planes.csv
    ├── demo.mp4
    └── benchmark_500.mp4         # Output of the recorded experiment
```

The `ProjectionApplication` creates a volume and list of planes, validates all input rows, determines one shared video canvas size, then projects and encodes frames **one at a time**. No list of full video frames is held in memory. Components can be instantiated and tested independently.

## CSV schema (design choice)

The specification requires 3 or 4 points but does **not** prescribe file layout. We use **one header and one plane per subsequent row**, with exactly 13 comma-separated columns:

```csv
shape,x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
triangle,2,0,0,0,2,0,4,2,0,,,
trapezoid,1,0,0,3,0,0,0,2,0,4,2,0
```

- `triangle`: `(P1, P2, P3)` means `(a, b, c)`; **P1 is the apex**. The last three cells must be empty.
- `trapezoid`: `(P1, P2, P3, P4)` means `(a1, a2, b, c)`; `a1-a2` is the short/top base, `b-c` is the longer/bottom base. They may have equal lengths.
- Coordinates can be floating-point numbers and are expressed in **voxel-index coordinates**. All must be finite.
- Rows are used in file order. Blank rows are ignored. Header is exact and mandatory; names `triangle`/`trapezoid` are case-insensitive.
- Invalid rows, invalid plane geometry, or an empty file **fail the entire command** with a line-numbered error. No invalid row is silently skipped.

## Mathematical algorithm (as in `ALGORITHM.md`)

**Plane validation:** three-point planes may be any non-degenerate triangle; four-point planes may have unequal side lengths, but must have ordered bases and coplanarity. Degenerate edges are rejected. This accepts the supplied CSV.

Both cases are converted to two side edges:

| Geometry | Left side | Right side |
|---|---|---|
| Triangle | `a → b` | `a → c` |
| Trapezoid | `a1 → b` | `a2 → c` |

Define `L` as a side length and `B` as the bottom-base length. The image dimensions follow the planned algorithm:

```text
height = max(2, round(L) + 1)
width  = max(2, round(B) + 1)
```

For each output row `y`, `t = y/(height - 1)`. Interpolate its 3-D left and right endpoints along the two side edges. Let their distance be `D`. The row has `max(1, round(D)+1)` samples, centered horizontally at `floor((width - rowPixels)/2)`. Interpolate each 3-D point using `u=j/(rowPixels-1)`; for one-pixel rows use `u=0`. Projected pixels outside the shape remain black. Any attempted column overflow from rounding is clipped to the image. **`PlaneProjector` performs these operations via NumPy arrays rather than Python loops over pixels.**

The output array is `image[y, x]` (rows then columns), equivalent to the algorithm's conceptual `E[x][y]`. A video frame is a view of the volume **sampled on the plane**, not a maximum-intensity projection or a sum along a ray.

## Explicit choices where the assignment is underspecified

| Question | Chosen policy | Why |
|---|---|---|
| Non-integer voxel coordinates | **Nearest neighbor**, round each axis with NumPy `rint` (ties-to-even) | Mirrors planned `M[p]` sampling choice |
| Out-of-bounds | Sample value `0` whenever an original coordinate is outside inclusive `[0, size-1]` or nonfinite | Don't round an outside point back inside |
| Non-integer image geometry | Python `round()` (ties-to-even) plus `+1` inclusive endpoints; minimum dimension 2 | Exact convention stated in `ALGORITHM.md` |
| Coplanarity | Perpendicular distance of the fourth point from the plane `<= 0.001` in voxel units | Scale-aware compared with a raw triple product |
| Trapezoid base parallelism | **Not enforced** | Optional additional check mentioned in algorithm design, not a mandatory SRS/Q&A rule; adding it silently would reject spec-valid input |
| 8-bit image | Retain intensity unchanged | Native 8-bit already suitable for video |
| 16-/32-bit MP4 image | `uint16 >> 8`, `uint32 >> 24` | Fixed full-range mapping; no flickering, but dark images are possible for medical low-range intensities |
| Different-sized projections | Center unchanged on **black canvas** sized to maximum projection height/width; round canvas dimensions up to even | Preserves geometry and supports H.264 `yuv420p` |
| Video codec and playback FPS | **H.264** with **10 FPS** presentation, YUV420p | Widely readable; playback FPS is not benchmark processing FPS |
| Invalid input | Fail fast, stderr error; no partial MP4 | Exactly one frame for **every accepted CSV row**, without accidental omissions |
| Enormous off-volume coordinates | Reject images above **20 million pixels** | Avoid unintended out-of-memory failures |
| Spatial metadata | Use raw voxel **index** coordinates, not world-space mm | SRS defines `M[x][y][z]`; does not define coordinate transforms |

For NRRD, this implementation supports `.nrrd` (embedded data) and `.nhdr` (single detached data file), NRRD `raw`/`gzip` (`gz`) encodings, little/big endian 16-/32-bit numbers, unsigned 8-/16-/32-bit scalar voxels, and signed 16-bit (`short`) scalar voxels. NRRD's first axis varies fastest, so payload data is reshaped with Fortran ordering to make `M[x,y,z]` correct. Arbitrary multichannel NRRD, unsupported encodings (e.g. bzip2 and ASCII), data file lists, and world-to-voxel transforms are **not** supported and should not be represented as implemented features.

> **Note about strictness:** The sample projection algorithm has edge/rounding ambiguities compared with the handout's incremental example, and `ALGORITHM.md` deliberately chooses inclusive interpolation. This implementation follows that **documented design**; it does not pretend the handout fixes nearest-neighbor, rounding, or output size conventions.

## Testing

```bash
python -m pytest -q
```

The suite includes known expected 2-D pixel arrays, equilateral and unequal-side triangles, trapezoids, impossible geometry, non-coplanarity, half-way coordinate rounding, out-of-volume samples, unsigned and signed-short voxel types with both byte orders, gzip/raw NRRD, detached headers, CSV errors, no partial output, actual MP4 decoding to check frame count/order, and CLI subprocess execution.

See [`TEST_STRATEGY.md`](TEST_STRATEGY.md) for a requirement-to-test matrix and [`EXPERIMENT_REPORT.md`](EXPERIMENT_REPORT.md) for results.

## Measured performance

**Assignment threshold:** more than 30 FPS on a 500³-byte volume, with 100+ FPS expected. These are not assumed outcomes.

Run:

```bash
python -m benchmarks.benchmark --size 500 --frames 30 --encode --video-path benchmark_output.mp4 --json benchmark_results.json
```

The benchmark uses a seeded **125 MB synthetic `uint8` volume**, real triangle planes, and a NumPy warm-up. It reports (1) projection-only throughput, excluding volume creation/loading and encoding, and (2) projection **plus** padding/conversion/MP4 encoding. It excludes NRRD file reading, CSV parsing, and process startup. Playback is fixed at 10 FPS independently of benchmark processing FPS.

The recorded environment obtained **38.75 FPS projection-only** and **24.85 FPS including MP4 encoding** for 30 frames; see the JSON and experiment report. Projection-only exceeded 30 FPS **for this one run**; overall pipeline did not. The 100 FPS target is **not** demonstrated. Repeat on your submission computer and record the environment; performance varies with CPU, memory and FFmpeg behavior.

## Assignment vs optional extensions

**Implemented from the SRS/design:** both plane types; unified row-interpolation algorithm; correct axis order and voxel data; zero for OOB; exact CSV order; MP4 and CLI; failure handling; tests; benchmark; example data.

**Explicit implementation policies (not extra assignment mandates):** chosen CSV schema, nearest-neighbor/ties-to-even rounding, fixed intensity bit shifts, black padding, 10 playback FPS/H.264, fail-fast CSV, upper pixel bound, and limited NRRD encoding support.

**Not implemented / optional future improvements:** physically meaningful voxel spacing/coordinate transforms, trilinear interpolation, medical window/level contrast for uint16/uint32, strict parallel-base checking, multiple alternative CSV formats, more NRRD encodings, GUI, and parallel/C-accelerated processing for higher FPS. None are substituted into the required mathematical algorithm.

## Limitations and academic submission checklist

- **Check the CSV coordinates are already voxel indices.** The program intentionally ignores NRRD `space origin` and `space directions` fields.
- Fixed high-bit intensity mapping may produce low contrast when source values occupy only a narrow fraction of the datatype range; improving contrast would be a distinct, documented video-visualization option.
- H.264 is lossy, so exact pixel equivalence must be tested on the returned raw projection (as the tests do), not decoded MP4 bytes.
- Volume bytes reside in RAM; full 500³ unsigned-byte data require at least 125 MB, and higher bit depth or decompression can require considerably more.
- The original assignment expects an actual repository and frequent commits. Git history cannot be generated retroactively; initialize the repo and commit meaningful stages yourselves.

Suggested local Git start:

```bash
git init
git add .
git commit -m "Implement NRRD volume projection and verification suite"
```

A self-contained submission should include the original two design documents, source, tests, example data/video, and a new benchmark measurement from the target machine.
