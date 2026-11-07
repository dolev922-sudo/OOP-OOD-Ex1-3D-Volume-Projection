# Software Requirements Specification (SRS)

**Project:** 3D Volume Plane Projection  
**Course:** Introduction to Software Engineering (OOP / OOD) — Ex1  
**Version:** 1.1\
**Date:** 2026-11-08

## At a glance

| Input | Processing | Output |
|---|---|---|
| A 3D `.nrrd` volume and a `.csv` list of planes | Validate planes and create one 2D image for each plane | An `.mp4` video containing the images in CSV order |

**Requirement types:**
- **Functional requirements (FR):** What the system does.
- **Non-functional requirements (NFR):** How well the system must work (speed, correctness, reliability, maintainability).

---

## 1. Introduction

### 1.1 Purpose

The system samples selected planes in voxel-index coordinates from a 3D volume and combines the resulting 2D grayscale images into a video. Planes may extend outside the volume.

### 1.2 Scope

**In scope:**
- Load a 3D NRRD file.
- Read an ordered list of planes from a CSV file.
- Support planes described by **3 points (triangle)** or **4 points (trapezoid)**.
- Generate one 2D projection per accepted plane.
- Save the projections in an MP4 video.
- Provide a command-line entry point and readable error messages.

**Out of scope:** A graphical 3D editor, medical diagnosis, interactive visualization, and arbitrary polygon shapes.

### 1.3 Definitions

| Term | Meaning |
|---|---|
| **Voxel** | A 3D pixel with coordinates `(x, y, z)` and an intensity value. |
| **NRRD** | File format storing the 3D volume. |
| **Plane** | A region defined by three or four 3D points. |
| **Projection** | A 2D image made by sampling voxel intensities on a plane. |
| **FPS** | Frames processed per second (performance measurement). |
| **EPS** | Allowed geometric difference; the assignment uses `0.001`. |

### 1.4 References

1. Ariel University, *Ex1: Algorithm — Implementing a Plane Projection of 3D Volume*, pages 1–3.
2. Ariel University course slide, *SRS: what the system must do*.
3. Project [entry point](Ex0.py), [implementation](volume_projection/), [benchmark](benchmarks/benchmark.py), and [tests](tests/).

The course materials are the cited origin of the requirements. They were
not available for independent re-verification during this documentation
review. Implemented design choices are specified below and in
[ALGORITHM.md](ALGORITHM.md); measured acceptance status belongs in
[TEST_STRATEGY.md](TEST_STRATEGY.md).

---

## 2. Overall Description

### 2.1 Intended users

Students, instructors, or developers who want to produce a sequence of 2D slices from a 3D volume.

### 2.2 System workflow

1. The user provides the **NRRD input**, **CSV input**, and **MP4 output** paths.
2. The system loads and checks the 3D volume.
3. The system reads the plane definitions in CSV order.
4. The system validates all plane rows and computes the shared canvas dimensions before opening the encoder.
5. The system projects and writes one frame at a time, then atomically replaces the output with the completed video.
6. The system reports success or explains an input error.

### 2.3 Operating environment

The supplied project uses **Python 3.10+**, **NumPy**, **imageio**, and
**imageio-ffmpeg** for FFmpeg-backed H.264 encoding. **pytest** is the test
dependency. Versions are constrained by [requirements.txt](requirements.txt).
It runs from a terminal on a computer with sufficient memory for the volume
and projection arrays. The optional file-selection GUI requires Tkinter and
a graphical environment. OpenCV and pynrrd are not dependencies.

### 2.4 Constraints and assumptions

- The volume is three-dimensional: `M[x, y, z]`.
- Each dimension satisfies `1 <= size < 1024`.
- Required voxel values are unsigned **8-bit**, **16-bit**, or **32-bit** integers; the implementation also supports signed **16-bit** as a compatibility extension.
- Plane coordinates are interpreted as **voxel-index coordinates** by this project (not physical millimeters).
- A plane may extend outside the 3D volume; samples outside it become `0` in the raw projection, before video intensity conversion.
- The project processes one volume per execution.

---

## 3. Specific Requirements

### 3.1 Functional requirements

Each requirement has an ID so it can be referenced in code, tests, and reviews.

| ID | The system shall... | How to verify |
|---|---|---|
| **FR-01** | Load a 3D NRRD file with unsigned 8-, 16-, or 32-bit voxels and dimensions of 1–1023 per axis. | Read sample files; check dimensions and voxel values. |
| **FR-02** | Read a CSV containing one plane per row, described by 3 or 4 points in 3D. | Parse valid triangle and trapezoid rows. |
| **FR-03** | Accept a triangle `(a, b, c)` only if `abs(dist(a,b) - dist(a,c)) < 0.001`, and reject invalid/degenerate triangles. | Test valid isosceles, equilateral, scalene and collinear cases. |
| **FR-04** | Validate trapezoid `(a1, a2, b, c)`: equal side lengths within EPS, top edge no longer than bottom edge, and coplanar points. | Test valid trapezoids and invalid geometry. |
| **FR-05** | Generate a 2D image for each accepted plane using the row-interpolation interpretation documented in [ALGORITHM.md](ALGORITHM.md). | Compare results with an independent reference implementation. |
| **FR-06** | Give a raw projection intensity of `0` to samples outside the 3D volume. | Test partially and fully out-of-bounds planes before video conversion. |
| **FR-07** | Preserve CSV plane order when generating video frames. | Compare the sequence of output frames to input rows. |
| **FR-08** | Save the projected images in an MP4 video at the requested path. | Open the result and check its frames. |
| **FR-09** | Support the required command-line invocation shown below. | Run it with real sample files. |
| **FR-10** | Report missing, corrupt, or invalid inputs with readable messages, without an uncontrolled crash. | Test invalid files and malformed CSV rows. |

**Required command:**

```bash
python Ex0.py file.nrrd file.csv file.mp4
```

### 3.2 External interfaces

| Interface | Format | Role |
|---|---|---|
| Volume input | `.nrrd` or `.nhdr` | Embedded data or a single detached payload; raw/gzip encoding. |
| Plane input | `.csv` | Contains plane coordinates, one plane per row. |
| Command line | `python Ex0.py ...` | Starts the processing pipeline. |
| Video output | `.mp4` | Contains the projected 2D frames. |

**CSV format used by this project:** A required header and exactly **13
columns** per data row. The first cell names the shape; the remaining cells
hold points in `(a,b,c)` or `(a1,a2,b,c)` order. Triangle rows contain nine
coordinate values and three empty trailing cells.

```csv
shape,x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
triangle,5,0,0,2,4,0,8,4,0,,,
trapezoid,2,0,5,6,0,5,0,4,5,8,4,5
```

The alternate supported format uses a point-count header and `3`/`4` values:

```csv
number of points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
3,5,0,0,2,4,0,8,4,0,,,
4,2,0,5,6,0,5,0,4,5,8,4,5
```

Header names and shape names are case-insensitive and surrounding whitespace
is stripped. Blank rows are ignored. Comments, headerless files, empty plane
lists, and nonempty fourth-point cells on triangles are rejected. All point
coordinates must be finite. These are project interface decisions.

### 3.3 Non-functional requirements

| ID | Requirement | How to verify |
|---|---|---|
| **NFR-01 — Performance** | With a `500 × 500 × 500` **byte** volume, projection speed must exceed **30 FPS**; **≥100 FPS** is the expected target. | Run `python -m benchmarks.benchmark --size 500 --frames 200 --encode` five times and record median/best speeds, hardware, and frame sizes. Report processing and end-to-end rates separately. |
| **NFR-02 — Correctness** | The output must match the specified projection rules, including geometry, sampling, and frame order. | Use unit tests and reference-image comparisons. |
| **NFR-03 — Reliability** | Bad inputs must result in controlled errors; a failed run must not leave a misleading partial video. | Test invalid inputs and simulated output failures. |
| **NFR-04 — Maintainability** | Input reading, geometry, projection, and video encoding must be separate, testable components. | Review architecture and test modules independently. |
| **NFR-05 — Usability** | The required command must be straightforward, and success/error messages must be understandable. | Run successful and failing CLI examples. |

> **Important:** The video's **10 FPS playback rate** is independent of measured projection/processing throughput. The benchmark reports projection and end-to-end rates; processing without encoding needs a separate timed loop. Performance results depend on hardware and plane dimensions. See [recorded measurements](TEST_STRATEGY.md#performance-results-measured-2026-11-08).

### 3.4 Project design decisions (not specified by the assignment)

These choices make unspecified behavior predictable. They describe the supplied project and should not be confused with university requirements.

| Topic | Project choice |
|---|---|
| CSV rows | Required header and 13 cells per data row, as specified above. Blank rows ignored; comments rejected. |
| Sampling | Nearest-neighbor voxel lookup; test finite original coordinates against inclusive `[0,size-1]` bounds before rounding. |
| Rounding | Ties-to-even: Python `round` for dimensions, NumPy `rint` for row lengths and voxel indices. |
| Projection dimensions | `height=max(2,round(longerSide)+1)`, `width=max(2,round(bottomBase)+1)`; output indexed `[y,x]`, retaining voxel dtype. Reject more than 20,000,000 pixels. |
| Unsigned video conversion | Right-shift by 0/8/24 bits for uint8/uint16/uint32, retaining the highest eight bits. |
| Signed-int16 video conversion | If all frame values are nonnegative, scale by that frame's maximum to 0–255 (all-zero remains zero). If any value is negative, use `(int32(value)+32768)>>8`; raw zero then becomes gray 128. |
| Frames of different sizes | Center on a common black canvas rounded up to even height and width; no resizing. Added padding remains black after intensity conversion. |
| Playback speed | H.264/YUV420p at 10 FPS; no CLI playback-rate option. |
| Invalid planes | Stop with a line-numbered error; no skip-invalid option. Validate the entire CSV before creating the temporary video. |
| Output publication | Write a temporary MP4 beside the target, then replace the target on success. Clean up failed temporary output and preserve existing output. Output must differ from input paths; its parent directory must exist. |
| Optional GUI | Omitted CLI paths trigger a Tkinter selection form; supplying all three paths runs without the GUI. |
| NRRD metadata | Coordinates are voxel indices; physical orientation/spacing are not applied. |

---

## 4. Appendices

### Appendix A — Geometry rules

**Triangle (3 points):** `a`, `b`, `c` must form an isosceles triangle:

```text
abs(dist(a, b) - dist(a, c)) < 0.001
```

**Trapezoid (4 points):** `a1`, `a2`, `b`, `c` must satisfy:

```text
abs(dist(a1, b) - dist(a2, c)) < 0.001
dist(a1, a2) <= dist(b, c)
a1, a2, b and c are coplanar
```

Side-length differences must be strictly less than EPS. Base ordering allows
only eight ULPs of floating-point roundoff, not an EPS-sized difference.
Coplanarity uses perpendicular distance `<= EPS`. Defining normalized
cross-product magnitudes must exceed `1e-12`; zero-length edges are rejected.
Parallel bases, convexity, and self-intersection are not checked. Exact formulas
and the implemented row interpolation are in [ALGORITHM.md](ALGORITHM.md).

### Appendix B — Requirements traceability / test checklist

| Test | Requirements | Expected result |
|---|---|---|
| T-01 | FR-01 | Correct NRRD dimensions and voxel values. |
| T-02 | FR-02, FR-03, FR-04 | Correct plane parsing and geometry validation. |
| T-03 | FR-05, NFR-02 | Correct pixels compared with the reference algorithm. |
| T-04 | FR-06 | Out-of-volume samples equal zero. |
| T-05 | FR-07, FR-08 | MP4 has the correct ordered frames. |
| T-06 | FR-09, NFR-05 | Required command works. |
| T-07 | NFR-01 | Benchmark reports real, measured FPS. |
| T-08 | FR-10, NFR-03 | Errors are clear and controlled. |

### Appendix C — Run and test the project

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run with your own inputs
python Ex0.py input.nrrd planes.csv output.mp4

# Run the automated tests
python -m pytest -q

# Measure projection and video-processing performance
python -m benchmarks.benchmark --size 500 --frames 200 --encode
```

Input filenames are placeholders for user-supplied files. This checkout
currently contains no example dataset or demo generator. The tests create
their own small synthetic inputs in temporary directories. Repeat the
benchmark five times for median/best FPS; it generates its own volume.

### Appendix D — Submission checklist

-  `README.md` describes the project and how to run it.
-  `SRS.md` specifies the requirements.
-  `ALGORITHM.md` explains the detailed algorithm.
-  A representative NRRD dataset and CSV plane definitions are available.
-  The tests and testing strategy are documented.
-  The required command produces an MP4 demo.
-  Benchmark results are recorded **from an actual run**.
-  A short experiment summary describes the results.

---

**Document note:** This SRS separates assignment requirements from choices made in the supplied Python implementation. It describes intended and testable behavior; it is not a claim that every requirement has passed on every machine.
