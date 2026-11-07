# Software Requirements Specification (SRS)

**Project:** 3D Volume Plane Projection  
**Course:** Introduction to Software Engineering (OOP / OOD) — Ex1  
**Version:** 1.0  
**Date:** 2026-11-05

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

The system converts selected planes inside a 3D volume into 2D grayscale images and combines those images into a video.

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
3. Project implementation and tests (`Ex0.py`, `benchmark.py`, and associated test files).

---

## 2. Overall Description

### 2.1 Intended users

Students, instructors, or developers who want to produce a sequence of 2D slices from a 3D volume.

### 2.2 System workflow

1. The user provides the **NRRD input**, **CSV input**, and **MP4 output** paths.
2. The system loads and checks the 3D volume.
3. The system reads the plane definitions in CSV order.
4. The system validates each plane and calculates its 2D projection.
5. The system writes the projected images as video frames.
6. The system reports success or explains an input error.

### 2.3 Operating environment

The supplied project uses **Python 3.10+**, **NumPy**, and **OpenCV**. It runs from a terminal on a computer with sufficient memory for the volume.

### 2.4 Constraints and assumptions

- The volume is three-dimensional: `M[x, y, z]`.
- Each dimension satisfies `1 <= size < 1024`.
- Voxel values are unsigned **8-bit**, **16-bit**, or **32-bit** integers.
- Plane coordinates are interpreted as **voxel-index coordinates** by this project (not physical millimeters).
- A plane may extend outside the 3D volume; samples outside it become `0`.
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
| **FR-05** | Generate a 2D image for each accepted plane using the assignment's plane-sampling algorithm. | Compare results with an independent reference implementation. |
| **FR-06** | Give an intensity of `0` to samples outside the 3D volume. | Test partially and fully out-of-bounds planes. |
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
| Volume input | `.nrrd` | Contains the 3D voxel data. |
| Plane input | `.csv` | Contains plane coordinates, one plane per row. |
| Command line | `python Ex0.py ...` | Starts the processing pipeline. |
| Video output | `.mp4` | Contains the projected 2D frames. |

**CSV format used by this project:** Three `(x,y,z)` coordinates = **9 numbers** for a triangle; four coordinates = **12 numbers** for a trapezoid.

```csv
# Triangle: a, b, c
5,0,0,2,4,0,8,4,0
# Trapezoid: a1, a2, b, c
2,0,5,6,0,5,0,4,5,8,4,5
```

> The assignment requires a CSV list of coordinates but does not prescribe the exact column layout. The flat 9/12-number layout is a **project design decision**.

### 3.3 Non-functional requirements

| ID | Requirement | How to verify |
|---|---|---|
| **NFR-01 — Performance** | With a `500 × 500 × 500` **byte** volume, projection speed must exceed **30 FPS**; **100+ FPS** is the expected target. | Run `python benchmark.py --encode` and record measured speeds, hardware, and frame sizes. |
| **NFR-02 — Correctness** | The output must match the specified projection rules, including geometry, sampling, and frame order. | Use unit tests and reference-image comparisons. |
| **NFR-03 — Reliability** | Bad inputs must result in controlled errors; a failed run must not leave a misleading partial video. | Test invalid inputs and simulated output failures. |
| **NFR-04 — Maintainability** | Input reading, geometry, projection, and video encoding must be separate, testable components. | Review architecture and test modules independently. |
| **NFR-05 — Usability** | The required command must be straightforward, and success/error messages must be understandable. | Run successful and failing CLI examples. |

> **Important:** The video playback rate (e.g., 30 FPS) is **not** the same as measured projection-processing FPS. Performance results depend on hardware and plane dimensions; do not claim the target is met without measurement.

### 3.4 Project design decisions (not specified by the assignment)

These choices make unspecified behavior predictable. They describe the supplied project and should not be confused with university requirements.

| Topic | Project choice |
|---|---|
| CSV rows | 9 values for triangles; 12 for trapezoids; optional header, comments, and blank lines. |
| Sampling | Nearest-neighbor voxel lookup. |
| Rounding | Round-half-up (`floor(value + 0.5)`). |
| Higher-bit-depth input | Use one volume-wide linear mapping to 8-bit grayscale for MP4 frames. |
| Frames of different sizes | Center on a common black canvas without stretching. |
| Playback speed | Default MP4 playback at 30 FPS. |
| Invalid planes | Stop with a line-numbered error by default; optional `--skip-invalid` mode. |
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

The project's floating-point checks allow a small EPS tolerance. The course handout describes the row-by-row projection algorithm; the exact implementation and its rounding choices belong in `ALGORITHM.md`.

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
pip install -r requirements.txt

# Generate example inputs and a demonstration video
python make_example_data.py

# Run with your own inputs
python Ex0.py input.nrrd planes.csv output.mp4

# Run the automated tests
pytest

# Measure projection and video-processing performance
python benchmark.py --encode
```

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
