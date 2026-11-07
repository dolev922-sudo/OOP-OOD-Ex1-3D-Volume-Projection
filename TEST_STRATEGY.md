# Test Strategy — 3D Volume Plane Projection

**Project:** Introduction to Software Engineering (OOP / OOD), Ex1  
**Document version:** 1.0  
**Related documents:** [`SRS.md`](SRS.md), [`README.md`](README.md), [`ALGORITHM.md`](ALGORITHM.md) (where available)  
**Status:** Test plan and verification instructions; not a claim that tests passed on the reader's machine.

## Quick overview

The program reads a 3D **NRRD** volume and an ordered **CSV** list of planes, generates a grayscale 2D projection for each valid plane, and saves the frames as an **MP4** video.

We will verify four things:

1. **Correct input:** NRRD files, CSV rows, and plane geometry are handled correctly.
2. **Correct images:** Projected pixels match known answers and an independent reference algorithm.
3. **Correct video:** The required command creates a playable MP4 with frames in CSV order.
4. **Reliable and fast execution:** Errors are controlled, and measured processing speed meets the course requirement.

> **Acceptance summary:** All required functional tests should pass, the demo should produce the expected MP4, and a measured benchmark on a `500 × 500 × 500` `uint8` volume should report **more than 30 processing FPS**. **100+ FPS** is the course's expected target, not the minimum pass threshold. Report both outcomes honestly.

---

## 1. Testing objectives and scope

The purpose of testing is to show that the implemented system meets the behaviors in [`SRS.md`](SRS.md) and the assignment brief, not only that individual functions run.

**In scope:** file loading; unsigned 8/16/32-bit voxel data; CSV parsing; triangle/trapezoid validation; coordinate rounding and nearest-neighbor sampling; out-of-volume zero values; projection dimensions and pixels; intensity conversion; frame layout and order; MP4 writing; CLI behavior; error handling; and measured speed.

**Out of scope:** medical interpretation, a graphical 3D editor, unsupported NRRD variants, other polygon shapes, and guarantees about performance on hardware that has not been measured.

### Test environments and dependencies

- Python **3.10+**, with dependencies from `requirements.txt` (`numpy`, `opencv-python-headless`, `pytest`; `pynrrd` is an optional cross-check).
- Tests are run from the repository root. The committed `volproj/` package and `tests/` directory must be available.
- Use small synthetic volumes for most correctness tests; use **500³ `uint8`** for the assignment performance test.
- Record operating system, CPU, Python/NumPy/OpenCV versions, and benchmark settings with performance results.

## 2. Testing levels

| Level | Purpose | Main evidence |
|---|---|---|
| **Unit tests** | Check small components independently (geometry, readers, sampling, projection). | `tests/test_geometry.py`, `test_plane.py`, `test_nrrd_reader.py`, `test_csv_reader.py`, `test_projector.py` |
| **Integration tests** | Check that parsing, projection, scaling, layout, and writing work together. | `tests/test_pipeline.py` |
| **End-to-end / CLI tests** | Run `Ex0.py` with actual input files, check output and failure behavior. | `tests/test_cli.py`, `tests/test_pipeline.py`, demo procedure below |
| **Performance tests** | Measure FPS separately for the projection stage, processing stage, and optional video encoding. | `benchmark.py`, `tests/test_benchmark.py` |
| **Manual demo review** | Confirm that the produced MP4 plays and shows meaningful changes across the sequence. | Demo checklist and recorded observations |

The test cases are **not** a replacement for the manual demo required in the assignment.

## 3. Requirements-to-tests traceability

The requirement IDs below match the supplied `SRS.md`. `T-01`–`T-08` are the existing test groups used in the README; extra verification is listed where needed.

| SRS ID | What must be shown | Test group / existing file(s) | Pass criterion |
|---|---|---|---|
| **FR-01** | Load supported 3D NRRD volumes. | **T-01** — `test_nrrd_reader.py` | Shape, voxel type, byte order, and values are read correctly; unsupported input is rejected. |
| **FR-02** | Parse 3- or 4-point CSV planes. | **T-02** — `test_csv_reader.py` | 9-number triangles and 12-number trapezoids are parsed in source order. |
| **FR-03** | Validate isosceles triangles. | **T-02** — `test_plane.py` | Valid triangles are accepted; scalene and degenerate triangles are rejected. |
| **FR-04** | Validate trapezoid geometry. | **T-02** — `test_plane.py` | Equal side lengths (EPS), base-length rule, and coplanarity are checked. |
| **FR-05** | Calculate the required 2D projection. | **T-03** — `test_projector.py`, `reference_projector.py` | Pixels and image sizes match known cases and independent reference calculations exactly. |
| **FR-06** | Assign zero outside the volume. | **T-04** — `test_projector.py` | Partly/fully outside samples produce `0`, while valid inside samples remain correct. |
| **FR-07** | Keep plane order in the output. | **T-05** — `test_pipeline.py` | One frame per valid plane in the same order as the CSV (strict/default mode). |
| **FR-08** | Generate an MP4 file. | **T-05** — `test_pipeline.py`, `test_cli.py` | The file exists, decodes, and has the expected number of frames. |
| **FR-09** | Support the exact three-argument CLI. | **T-06** — `test_cli.py` | `python Ex0.py file.nrrd file.csv file.mp4` returns success and writes a video. |
| **FR-10** | Handle invalid input predictably. | **T-08** — `test_cli.py`, `test_csv_reader.py`, `test_nrrd_reader.py`, `test_pipeline.py` | Useful message identifies the cause; failures do not leave a misleading partial output. |
| **NFR-01** | Measure projection speed. | **T-07** — `benchmark.py`, `test_benchmark.py` | Actual FPS is recorded for 500³ `uint8`; **>30** required, **≥100** target, separately marked. |
| **NFR-02** | Prove correctness. | **T-02–T-05** — geometry, projection, pipeline tests | Deterministic expected results and reference comparisons agree. |
| **NFR-03** | Recover cleanly from errors. | **T-08** — failure tests | Controlled exit, readable error, and cleanup of incomplete output. |
| **NFR-04** | Maintain a testable, modular design. | Code review + isolated tests | Geometry, file I/O, projection, and encoding can be tested independently. |
| **NFR-05** | Make the CLI usable. | **T-06, T-08** — `test_cli.py` | Documented command works; incorrect usage produces understandable feedback. |

> **File-location note:** Test files supplied for this review are shown above under their intended `tests/` paths. Verify that the GitHub repository actually uses these paths. The supplied README also mentions `test_volume.py` and `test_video.py`, which were **not present in the uploaded set**; do not claim those files exist until verified.

## 4. Key test scenarios

### 4.1 Normal and boundary inputs

| Case | Test input | Expected outcome |
|---|---|---|
| **C-01** | Small valid `uint8` NRRD | Correct volume dimensions and voxel intensities. |
| **C-02** | Valid `uint16` and `uint32` NRRD files | Correct types and voxel values; video values converted to 8-bit. |
| **C-03** | Isosceles triangle, including equilateral case | Accepted; projected image matches known/reference output. |
| **C-04** | Valid isosceles trapezoid or rectangle | Accepted; correct image size and pixels. |
| **C-05** | Plane partly beyond any volume boundary | In-bounds pixels preserved; outside pixels set to zero. |
| **C-06** | Plane fully outside the volume | Black projection (all zeros). |
| **C-07** | Multiple planes with different image sizes | Frames centered on a common canvas without resizing. |
| **C-08** | Multiple distinct CSV rows | Video frames appear in exactly the same order. |
| **C-09** | Fractional coordinates at rounding boundaries | Deterministic round-half-up/nearest-neighbor behavior. |

### 4.2 Invalid inputs and failure handling

| Case | Test input | Expected outcome |
|---|---|---|
| **E-01** | Missing or corrupt `.nrrd` | Clear error identifying the input file. |
| **E-02** | Unsupported voxel type, wrong dimensions, or invalid NRRD encoding | Controlled rejection. |
| **E-03** | CSV row with wrong number of values, text, `NaN`, or empty required cell | Error names the row/column where applicable. |
| **E-04** | Scalene, collinear, or coincident-point triangle | Geometry rejection. |
| **E-05** | Trapezoid with unequal legs, longer top base, or noncoplanar points | Geometry rejection. |
| **E-06** | Empty plane list | No misleading empty success video. |
| **E-07** | Bad output path or error during video writing | Failure is reported; incomplete video is removed. |
| **E-08** | Invalid CSV row in default strict mode | Run stops with a line-numbered error; no video is produced. |

**Design-choice check:** The optional `--skip-invalid` mode is an extra feature, **not** the default assignment behavior. If it is used, report skipped lines and verify the retained rows remain in their original order.

## 5. How correctness is verified

Use **two independent checks**, whenever possible:

1. **Hand-checked examples:** A known volume has easily predicted voxel values. For example, an axis-aligned rectangle should reproduce the corresponding volume slice, and a simple triangle should yield known pixels.
2. **Reference comparison:** `tests/reference_projector.py` is a separate, slower row-by-row algorithm. Compare its entire output matrix to the optimized `PlaneProjector` output, including dtype, dimensions, pixel values, and boundary behavior.

These comparisons are stronger than checking only whether an image is nonempty. Tests should also verify **repeatability** (same input → same output) and that projection does **not modify** the source volume.

MP4 compression can change individual pixel values. Therefore, require **exact pixel equality before encoding**, but check decoded MP4 for frame count, size, sensible content, and order rather than demanding byte-for-byte equality with uncompressed images.

## 6. Required demo: NRRD + CSV → MP4

The university requires this exact invocation:

```bash
python Ex0.py file.nrrd file.csv file.mp4
```

### Repeatable demo steps

```bash
# Install dependencies (once)
pip install -r requirements.txt

# Generate a small example NRRD, CSV, and MP4 with the project helper
python make_example_data.py

# Or run the required entry point with your own dataset
python Ex0.py examples/phantom.nrrd examples/planes.csv examples/demo.mp4
```

`make_example_data.py` is configured to create a **64³ synthetic `uint16` volume**, **24 planes** (triangles and trapezoids), and a demo video under `examples/`. If the repository does not contain those files yet, run the generator first. Use the project's **actual paths** when reporting results.

### Demo acceptance checklist

-  Command exits successfully (exit code `0`).
-  Output `.mp4` exists and can be opened in a video player.
-  Number of decoded frames equals the number of **valid** input plane rows (24 for the generated demo).
-  Frame order matches the CSV row order; compare pre-encoding frames where exact validation is needed.
-  Frames show changing cross-sections; no unexpected blank or corrupted frames.
-  Video width and height remain constant even when plane sizes differ.
-  If any planes cross the volume boundary, outside pixels appear black.
-  Record the command, input filenames, output filename, and one or two representative screenshots or frames.

**Note:** A successful demo on a 64³ volume proves the full pipeline works, **not** that the 500³ FPS requirement is met. That needs a separate benchmark.

## 7. Performance-test procedure (NFR-01)

The assignment specifies a **500 × 500 × 500 byte volume**. This project measures speed with a generated `uint8` volume and a sequence of planes. Use the provided benchmark:

```bash
# Current checkout: one pass; repeat five times for median/best FPS
python -m benchmarks.benchmark --size 500 --frames 200 --encode
```

The measurements cover three stages. The current benchmark reports projection and end-to-end timing; processing was measured separately as described in the results below:

| Stage | Meaning | Why it matters |
|---|---|---|
| `projection` | Compute only the 2D plane image. | Closest measure of the core algorithm. |
| `processing` | Projection + 8-bit conversion + placing on the video canvas. | Practical per-frame computation cost. |
| `end-to-end` | Processing + MP4 writing (`--encode`). | Shows total export overhead. |

**Performance rules:**

- Record **median FPS** across repeated passes; also retain the reported best FPS for context.
- Mark **> 30 FPS** as the required threshold and **≥ 100 FPS** as the expected target. Do not confuse the two.
- Record **plane size and type**: bigger 2D images may process more slowly even for the same 500³ volume.
- Record machine and software information; do not generalize measured results to all computers.
- Report the three stages separately. **30 FPS MP4 playback does not prove 30 FPS processing speed.**
- Never put hard-coded “PASS” results in the report; decide from actual measured output.

### Performance results (measured 2026-11-08)

| Field | Observed value |
|---|---|
| Date and OS | 2026-11-08 (Asia/Jerusalem); Windows 11 Home, 64-bit, build 10.0.26300 |
| CPU / memory | 13th Gen Intel Core i9-13900HX; 24 cores / 32 logical processors; 15.75 GiB usable physical RAM (16,907,100,160 bytes) |
| Python / NumPy / OpenCV versions | Python 3.13.14 / NumPy 2.5.4 / OpenCV not used by this checkout; imageio 2.38.1, imageio-ffmpeg 0.6.0, FFmpeg 7.1, pytest 9.1.1 |
| Volume | `500 × 500 × 500`, `uint8`; deterministic random data, seed `2026` |
| Plane count / repeats | `200` / `5` for each stage |
| Plane type | In-bounds isosceles triangles on successive Z slices (`z=0..199`), from `benchmarks.benchmark.make_planes(500, 200)` |
| Image size range | Constant `557 × 498` pixels (height × width); padded video canvas `558 × 498` |
| Projection median FPS | **36.64** (best: 39.95) |
| Processing median FPS | **37.85** (best: 39.29) |
| End-to-end median FPS | **33.36** (best: 34.52) |
| Required threshold (>30 FPS) | **PASS** — processing median 37.85 FPS; projection and end-to-end medians also exceed 30 FPS |
| Expected target (≥100 FPS) | **NOT MET** — all three measured medians are below 100 FPS |

Measured from the current checkout at `C:/Users/dolev/.vscode/New folder/OOP-OOD-Ex1-3D-Volume-Projection`. These results apply to this machine and triangle workload; other plane sizes, orientations, or system load may produce different speeds.

The current checkout uses `benchmarks/benchmark.py` and imageio/FFmpeg, rather than the older root-level benchmark and OpenCV described elsewhere in this plan. It has no `--dtype` or `--repeats` flags: `uint8` is fixed, and repetition was performed by a temporary measurement runner calling `benchmarks.benchmark.run(500, 200, True, output_path)` five times, sequentially.

Projection and end-to-end values below are the benchmark's actual outputs. Processing was separately timed with `time.perf_counter()` around 200 calls to `video.prepare_frame(projector.project(plane))`, using the same seeded volume, planes, and canvas, with one warm-up frame per pass. Allocation, geometry setup, and warm-up were excluded. End-to-end timing includes opening, writing, and closing the H.264 MP4, but excludes input generation/loading. The three stages were timed separately; processing includes extra work, but independent timing and machine variation can make its measured FPS higher than projection FPS. MP4 playback is 10 FPS and is unrelated to measured throughput.

| Pass | Projection FPS | Processing FPS | End-to-end FPS |
|---|---:|---:|---:|
| 1 | 34.03 | 35.05 | 31.15 |
| 2 | 35.83 | 35.52 | 32.29 |
| 3 | 36.64 | 38.83 | 33.42 |
| 4 | 39.95 | 39.29 | 34.52 |
| 5 | 39.34 | 37.85 | 33.36 |

Medians and best values above are calculated across these five passes.

> The README includes example measurements from a development environment, but **those numbers are not a substitute for running the benchmark on the submission machine**.

## 8. Running the automated tests

```bash
# All tests configured by pytest.ini
pytest

# Extra detail
pytest -v

# Examples of targeted checks
pytest tests/test_projector.py -v
pytest tests/test_pipeline.py tests/test_cli.py -v

# Validate benchmark tooling (not actual speed thresholds)
pytest tests/test_benchmark.py -v
```

The benchmark test file checks that timing and reporting work; it **does not enforce a real-time FPS threshold inside pytest**, because shared or loaded machines make timing assertions unreliable. The real performance decision comes from a separately recorded benchmark run.

### Test execution record (2026-11-08)

| Item | Result |
|---|---|
| `pytest` command/date | 2026-11-08: `python -m pytest -q` stopped during collection (exit 1); `python -m pytest -q --continue-on-collection-errors` ran the remaining tests (exit 1) |
| Passed | **88** in the second run (4.52 seconds) |
| Failed | **0 executed test failures; 1 collection error** — the full suite did not pass |
| Skipped | **0 reported**; tests in the projection module could not be collected and are not counted as passes or skips |
| Demo command and output | Standalone manual demo not run during this measurement; CLI/video tests are included in the 88 passes, and five benchmark MP4 exports completed successfully |
| Open issues | `tests/test_projection.py:5` imports private NumPy names `_Array` and `_Array1D`; `_Array` cannot be imported from `numpy._core.multiarray` with NumPy 2.5.4. Projection-module tests remain unverified. The 100 FPS target was not met. Several paths and dependency descriptions elsewhere in this plan refer to an older project layout. |

Both test commands used the same checkout and Python environment as the performance measurements. No source or test code was changed for this run.

If tests are skipped (for example, an optional `pynrrd` cross-check), **report them separately** rather than counting them as passes. Include a short explanation for every failure.

## 9. Overall exit criteria and deliverables

The project is ready for submission when:

- [ ] The checked-in code matches the behavior described in `SRS.md`.
- [ ] Required correctness, integration, and CLI tests pass on the submission environment.
- [ ] The required three-argument CLI produces a decodable MP4 with correctly ordered frames.
- [ ] Error-handling tests show controlled failures without misleading partial outputs.
- [ ] A real 500³ `uint8` benchmark result is documented and checked against **>30 FPS**, with the **100+ FPS target** reported separately.
- [ ] A short experiment summary states the dataset, command, outputs, observations, and limitations.
- [ ] The committed repository contains the referenced test files and a reproducible demo or instructions to generate it.

### Evidence to keep with the submission

1. Test command and actual `pytest` summary (passed / failed / skipped).
2. The NRRD dataset description and CSV example used for the demo.
3. The command that created the MP4 and the MP4 output (or a clearly documented download/location).
4. Benchmark command, machine specifications, and measured FPS table.
5. A brief interpretation: what worked, what did not, and any known limitations.

---

**Source of requirements:** Ariel University Ex1 handout and the project's `SRS.md`.  
**Source of test coverage:** The supplied README, `benchmark.py`, `make_example_data.py`, and Python test files.  
**Important:** Checklists and blank result tables are intentionally **not pre-marked as passed**. They must be completed from actual execution before submission.
