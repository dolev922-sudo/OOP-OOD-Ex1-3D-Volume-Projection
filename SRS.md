# Software Requirements Specification (SRS)

**Project:** OOP-OOD-Ex1 — 3D Volume Projection  
**Version:** 1.1  
**Status:** Requirements and implementation interpretations, audited 2026-11-02

The original assignment PDF was not present in the inspected project,
Downloads, Documents, or Desktop locations during this audit. Assignment
rules quoted in the requested task and this specification are the available
requirements source; this is not a claim of independent PDF verification.

## 1. Introduction

### 1.1 Purpose
This document defines the requirements for a program that creates 2D images from selected planes in a 3D medical imaging volume and saves the images as frames in an MP4 video.

### 1.2 Scope
The program reads a 3D NRRD file and a CSV file containing a sequence of planes. Each plane is defined by three or four 3D points. The program samples the volume along each plane, creates a 2D image, and writes the images to a video in CSV order.

The assignment focuses on **object-oriented design, correctness, stability, and performance**.

## 2. Inputs and Outputs

| Item | Description |
| --- | --- |
| NRRD input | A 3D volume of unsigned 8-, 16-, or 32-bit values, or signed 16-bit (`short`) voxel values. |
| CSV input | A list of planes, each represented by 3 or 4 points with 3D coordinates. |
| MP4 output | A video containing one frame per plane, in the same order as the CSV input. |

The volume dimensions are `sx × sy × sz`, where `1 ≤ sx, sy, sz < 1024`.

## 3. Functional Requirements

### FR-01 — Load volume
The program shall read a 3D volume from a NRRD file and make its voxel values available for projection.

### FR-02 — Read planes
The program shall read a sequence of plane definitions from a CSV file. Each definition shall contain either three or four 3D points.

### FR-03 — Validate three-point planes
For a three-point plane `(a, b, c)`, the program shall check that the points form an isosceles triangle within the assignment tolerance:

`|dist(a,b) - dist(a,c)| < 0.001`

This comparison is strict: a difference equal to 0.001 is invalid.
Equilateral triangles qualify. Coincident or collinear vertices are invalid.

### FR-04 — Validate four-point planes
For a four-point plane `(a1, a2, b, c)`, the program shall check that:

- `|dist(a1,b) - dist(a2,c)| < 0.001`
- `dist(a1,a2) ≤ dist(b,c)`
- The four points lie on the same plane.

Equal-leg tolerance is strict, as for triangles. Base ordering does not use
the leg tolerance; only eight floating-point ULPs are allowed for roundoff
between mathematically equal lengths. Coplanarity is interpreted as a
perpendicular distance at most 0.001 voxel units. Degenerate defining edges
are rejected. Parallel bases are not an extra mandatory validation rule.

### FR-05 — Create a 2D projection
For each valid plane, the program shall create a 2D image by sampling voxel values from the 3D volume along that plane, following the projection algorithm described in the assignment.

### FR-06 — Handle out-of-bounds samples
When a sampled point is outside the volume, the program shall use the value `0` for that sample.

### FR-07 — Preserve plane order
The program shall process the planes in the order they appear in the CSV file, with one video frame corresponding to each plane.

### FR-08 — Export video
The program shall combine the projected images into an MP4 file at the output path provided by the user.

### FR-09 — Command-line execution
The program shall support execution using three file-path arguments (or the equivalent command in the implementation language):

```bash
python Ex0.py <file.nrrd> <file.csv> <file.mp4>
```

## 4. Non-Functional Requirements

### NFR-01 — Performance
For a `500³`-byte volume, the implementation must achieve **more than 30 frames per second**, with **100 or more FPS** as the expected target, as specified in the assignment. Performance shall be measured and reported during testing.

### NFR-02 — Correctness
Projected images shall follow the geometric and sampling rules in the assignment, including handling samples outside the volume.

### NFR-03 — Stability
The program shall handle invalid input or processing failures without an uncontrolled crash. The specific error messages and recovery behavior will be defined during detailed design.

### NFR-04 — Maintainability
The solution shall use clear, modular, object-oriented design, with responsibilities such as file loading, geometry, projection, and video output separated where appropriate.

## 5. Constraints and Assumptions

- Implementation language: **Java, Python, C, or C++**.
- The required input volume is 3D NRRD data.
- Plane definitions contain either three or four points.
- Geometric comparison tolerance: `EPS = 0.001`.
- This assignment does not require an interactive graphical interface, changes to the original NRRD file, or curved projections.

**Documented implementation choices:** CSV points are `(a,b,c)` or
`(a1,a2,b,c)` even when using the numeric point-count header. Sampling uses
nearest-neighbor ties-to-even, testing bounds before rounding. Inclusive
row interpolation and a common even black canvas are used. Video is H.264
at 10 playback FPS. Invalid rows fail the entire operation; output publication
is atomic. Signed int16 and the optional GUI are compatibility extensions.
See [ALGORITHM.md](ALGORITHM.md) and [README.md](README.md) for details.

Performance acceptance is reported separately for projection and projection
plus encoding. Volume initialization, input loading, and warm-up are not in
projection FPS. Ordinary tests do not enforce machine-dependent FPS thresholds.

## 6. Verification and Acceptance

| Test ID | Requirement(s) | Expected result |
| --- | --- | --- |
| T-01 | FR-01 | A supported NRRD file loads with the correct dimensions and voxel values. |
| T-02 | FR-02–FR-04 | Valid three- and four-point planes pass geometry checks; invalid ones are identified. |
| T-03 | FR-05 | A known test volume produces the expected projected pixel values. |
| T-04 | FR-06 | Samples outside the volume have value `0`. |
| T-05 | FR-07–FR-08 | The resulting MP4 has one frame per input plane, in CSV order. |
| T-06 | FR-09 | The application accepts the three specified command-line paths. |
| T-07 | NFR-01 | FPS is measured on a `500³`-byte volume and compared with the required minimum and target. |
| T-08 | NFR-03 | Invalid files and malformed input are handled predictably. |

## 7. Planned Deliverables

- Source code and a command-line demo
- NRRD test dataset(s) and CSV plane definitions
- Test strategy and test results
- A short experiment report including measured performance and an example MP4 output

## 8. Reference

*Introduction to Software Engineering — Ex1: Algorithm: Implementing a plane projection of 3D volume*, Ariel University (assignment handout).
