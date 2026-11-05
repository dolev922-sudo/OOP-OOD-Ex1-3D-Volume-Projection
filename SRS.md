# Software Requirements Specification

**Project:** OOP/OOD Ex1 — 3D Volume Projection

## 1. Introduction

**Purpose:** Convert planes sampled from a 3D NRRD volume into a sequence of 2D images saved as an MP4 video.

**Scope:** Volume loading, plane validation, projection, and video export. Volume editing, curved projections, and interactive 3D visualization are out of scope.

**Definitions:** A *voxel* is one volume element; a *plane* is defined by three or four points; *FPS* measures frames processed per second.

**Reference:** Ariel University, *Introduction to Software Engineering — Ex1: Algorithm: Implementing a plane projection of 3D volume*. The rules below reflect the available assignment excerpts; the original PDF was unavailable during review.

## 2. Overall description

- **Product and users:** A standalone Python tool for students and users generating plane slices.
- **Environment:** Python 3.10+, NumPy, and an FFmpeg-backed video writer.
- **Inputs:** A 3D NRRD volume and a CSV listing planes in output order.
- **Constraints:** Each volume axis has 1–1023 voxels; required voxel types are unsigned 8/16/32-bit integers.
- **Assumptions:** Coordinates are voxel indices, sufficient RAM is available, and the output folder exists.
- **Extensions:** Signed 16-bit input and an optional file picker are supported but are not core assignment requirements.

## 3. Specific requirements

### Functional requirements

| ID | The system shall… |
|---|---|
| FR-01 | Load a supported NRRD volume without changing its values or axis order. |
| FR-02 | Read ordered CSV planes containing three or four finite 3D points. |
| FR-03 | Accept triangle `(a,b,c)` only when `abs(dist(a,b)-dist(a,c)) < 0.001`; reject coincident or collinear vertices. |
| FR-04 | Accept trapezoid `(a1,a2,b,c)` only when `abs(dist(a1,b)-dist(a2,c)) < 0.001`, the top base is no longer than the bottom, and the vertices are coplanar; reject degenerate geometry. |
| FR-05 | Generate one 2D projection for each valid plane using the documented sampling rules. |
| FR-06 | Use zero for sample positions outside the volume. |
| FR-07 | Preserve CSV plane order in the output frames. |
| FR-08 | Save the frames as one MP4 with consistent frame dimensions. |
| FR-09 | Support the command-line interface below. |

### External interface

```bash
python Ex0.py <volume.nrrd> <planes.csv> <output.mp4>
```

CSV uses the header and point order documented in [README.md](README.md).
Invalid input shall produce a descriptive error and a nonzero exit code.

### Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Process a 500×500×500-byte volume at more than 30 FPS, with 100+ FPS as the target; report measured projection-only and encoding-pipeline throughput separately. |
| NFR-02 | Produce deterministic projections consistent with the documented geometry and sampling rules. |
| NFR-03 | Handle invalid inputs and encoding failures without an uncontrolled crash, preserving existing output on failure. |
| NFR-04 | Separate geometry, input loading, projection, and video writing into maintainable object-oriented components. |

Performance targets are acceptance goals, not claims of achieved results.
Playback FPS is independent of processing FPS.

## 4. Appendices

**Main use case:** Select inputs and an output path → validate → project each plane → save MP4.

**Design decisions:** Strict leg tolerance rejects equality at 0.001. Coplanarity uses perpendicular distance ≤ 0.001 voxel units; base ordering allows only floating-point roundoff. Parallel bases are not an extra check. Sampling, rounding, intensity conversion, and padding are defined in [ALGORITHM.md](ALGORITHM.md) and [README.md](README.md).

**Traceability:** [TEST_STRATEGY.md](TEST_STRATEGY.md) maps requirements to tests; [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md) records verification and performance results.
