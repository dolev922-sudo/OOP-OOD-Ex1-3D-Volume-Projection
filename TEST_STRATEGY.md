# Test Strategy — 3D Volume Plane Projection

**Project:** Introduction to Software Engineering (OOP / OOD), Ex1  
**Document version:** 1.1 — synchronized with the implementation on 2026-11-08\
**Related documents:** [SRS.md](SRS.md), [README.md](README.md), [ALGORITHM.md](ALGORITHM.md)\
**Status:** Test plan plus recorded execution evidence. The full automated suite passes (148 tests); the ≥100 FPS target has not been met, and standalone manual demo verification remains outstanding.

## Quick overview

The program reads a 3D **NRRD** volume and an ordered **CSV** list of planes, generates a grayscale 2D projection for each valid plane, and saves the frames as an **MP4** video.

We will verify four things:

1. **Correct input:** NRRD files, CSV rows, and plane geometry are handled correctly.
2. **Correct images:** Projected pixels match known answers and an independent reference algorithm.
3. **Correct video:** The required command creates a playable MP4 with frames in CSV order.
4. **Reliable and fast execution:** Errors are controlled, and measured processing speed meets the course requirement.

> **Acceptance summary:** All required functional tests should pass, the demo should produce the expected MP4, and a measured benchmark on a `500 × 500 × 500` `uint8` volume should report **more than 30 projection FPS**. **≥100 FPS** is the expected target, not the minimum pass threshold. Also report processing without encoding and end-to-end FPS separately. The full automated suite passes and recorded performance exceeds 30 FPS for all three stages; remaining manual checks are listed below.

---

## 1. Testing objectives and scope

The purpose of testing is to show that the implemented system meets the behaviors in [`SRS.md`](SRS.md) and the assignment brief, not only that individual functions run.

**In scope:** file loading; unsigned 8/16/32-bit voxel data and the signed-int16 extension; CSV parsing; triangle/trapezoid validation; coordinate rounding and nearest-neighbor sampling; out-of-volume raw zero values; projection dimensions and pixels; intensity conversion; frame layout and order; MP4 writing; CLI behavior; error handling; and measured speed.

**Out of scope:** medical interpretation, a graphical 3D editor, unsupported NRRD variants, other polygon shapes, and guarantees about performance on hardware that has not been measured.

### Test environments and dependencies

- Python **3.10+**, with dependencies from [requirements.txt](requirements.txt): NumPy, imageio, imageio-ffmpeg, and pytest. Neither OpenCV nor pynrrd is used by the current suite.
- Tests are run from the repository root with the [volume_projection/](volume_projection/) package and [tests/](tests/) directory available.
- Use small synthetic volumes for most correctness tests; use **500³ `uint8`** for the assignment performance test.
- Record operating system, CPU, memory, Python/NumPy/imageio/FFmpeg versions, and benchmark settings with performance results.

## 2. Testing levels

| Level | Purpose | Main evidence |
|---|---|---|
| **Unit tests** | Check geometry, readers, sampling, projection, and intensity conversion. | [test_geometry.py](tests/test_geometry.py), [test_io.py](tests/test_io.py), [test_projection.py](tests/test_projection.py), [test_video_and_cli.py](tests/test_video_and_cli.py) |
| **Integration tests** | Check parsing, projection, conversion, layout, frame count, and ordering together. | [test_video_and_cli.py](tests/test_video_and_cli.py) |
| **End-to-end / CLI tests** | Run the entry point with temporary synthetic input files; check success and missing-file behavior. | [test_video_and_cli.py](tests/test_video_and_cli.py) |
| **Performance measurement** | Measure projection and optional encoding; time processing without encoding separately. | [benchmarks/benchmark.py](benchmarks/benchmark.py); no dedicated benchmark pytest module exists |
| **Manual demo review** | Confirm that the produced MP4 plays and shows meaningful changes across the sequence. | Demo checklist and recorded observations |

The test cases are **not** a replacement for the manual demo required in the assignment.

## 3. Requirements-to-tests traceability

The requirement IDs and `T-01`–`T-08` groups below match [SRS.md](SRS.md).
File presence describes available coverage, not proof that a test passed.

| SRS ID | What must be shown | Test group / existing file(s) | Pass criterion |
|---|---|---|---|
| **FR-01** | Load supported 3D NRRD volumes. | **T-01** — [test_io.py](tests/test_io.py) | Dimensions, voxel type, byte order, encoding, and values are correct. |
| **FR-02** | Parse 3- or 4-point CSV planes. | **T-02** — [test_io.py](tests/test_io.py) | Both required-header formats parse 13-column rows in source order; triangles leave their final three cells empty. |
| **FR-03** | Validate isosceles triangles. | **T-02** — [test_geometry.py](tests/test_geometry.py) | Valid isosceles/equilateral triangles accepted; unequal legs and degenerate geometry rejected. |
| **FR-04** | Validate trapezoid geometry. | **T-02** — [test_geometry.py](tests/test_geometry.py) | Strict leg tolerance, base ordering with eight-ULP allowance, and perpendicular-distance coplanarity agree with the algorithm. |
| **FR-05** | Calculate the required 2D projection. | **T-03** — [test_projection.py](tests/test_projection.py), [reference_projection.py](tests/reference_projection.py) | Dtype, dimensions, and raw pixels match known/reference results exactly. |
| **FR-06** | Assign raw zero outside the volume. | **T-04** — [test_projection.py](tests/test_projection.py) | Original coordinates are checked before rounding; outside samples are zero. |
| **FR-07, FR-08** | Preserve order and generate MP4. | **T-05** — [test_video_and_cli.py](tests/test_video_and_cli.py) | Decode expected frame count/order on a shared even-sized canvas. |
| **FR-09** | Support the three-argument CLI. | **T-06** — [test_video_and_cli.py](tests/test_video_and_cli.py) | Valid inputs return success and create a video. |
| **FR-10** | Handle invalid input predictably. | **T-08** — [test_io.py](tests/test_io.py), [test_video_and_cli.py](tests/test_video_and_cli.py) | Readable errors; an invalid CSV preserves existing output. Other failure scenarios below still require targeted verification. |
| **NFR-01** | Measure projection speed. | **T-07** — [benchmark](benchmarks/benchmark.py) | Actual median FPS for 500³ `uint8`: **>30** required, **≥100** target; other stages reported separately. |
| **NFR-02** | Prove correctness. | **T-02–T-05** — geometry, projection, pipeline tests | Deterministic expected results and reference comparisons agree. |
| **NFR-03** | Recover cleanly from errors. | **T-08** — failure tests | Controlled exit, readable error, and cleanup of incomplete output. |
| **NFR-04** | Maintain a testable, modular design. | Code review + isolated tests | Geometry, file I/O, projection, and encoding can be tested independently. |
| **NFR-05** | Make the CLI usable. | **T-06, T-08** — [test_video_and_cli.py](tests/test_video_and_cli.py), manual GUI review | Three supplied paths run the CLI; missing paths trigger file selection when Tkinter is available. |

> The following scenarios are acceptance checks. Some are covered by current tests; others need additional checks. In particular, a simulated encoder failure, GUI interaction, and a standalone manual demo are not established by the recorded automated run.

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
| **C-09** | Fractional coordinates at rounding boundaries | Nearest-neighbor with ties-to-even rounding; out-of-bounds coordinates remain zero even if rounding would bring them inside. |
| **C-10** | Signed-int16 frames | Nonnegative frames scale by frame maximum; frames containing negatives use the offset/right-shift mapping, where raw zero becomes gray 128. Added canvas padding stays black. |

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

**Design-choice check:** There is no skip-invalid mode. All nonblank CSV rows must be valid before encoding starts. The required header and 13-column formats are specified in [SRS.md](SRS.md#32-external-interfaces). Reject projected images larger than 20,000,000 pixels before allocating them.

## 5. How correctness is verified

Use **two independent checks**, whenever possible:

1. **Hand-checked examples:** A known volume has easily predicted voxel values. For example, an axis-aligned rectangle should reproduce the corresponding volume slice, and a simple triangle should yield known pixels.
2. **Reference comparison:** [reference_projection.py](tests/reference_projection.py) is a separate, slower row-by-row algorithm. Compare its entire output matrix to the optimized projector output, including dtype, dimensions, pixel values, and boundary behavior.

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
python -m pip install -r requirements.txt

# Supply existing NRRD/CSV files and an existing output directory
python Ex0.py input.nrrd planes.csv output.mp4
```

The filenames above are placeholders. This checkout currently has no bundled
example dataset or demo generator. Record the actual dataset shape, dtype,
CSV row count, and paths used for a standalone demo. The CLI and integration
tests generate their own synthetic NRRD/CSV inputs in temporary directories;
they do not depend on bundled examples.

### Demo acceptance checklist

-  Command exits successfully (exit code `0`).
-  Output `.mp4` exists and can be opened in a video player.
-  Number of decoded frames equals the number of nonblank input plane rows; all rows must be valid.
-  Frame order matches the CSV row order; compare pre-encoding frames where exact validation is needed.
-  Frames show changing cross-sections; no unexpected blank or corrupted frames.
-  Video width and height remain constant even when plane sizes differ.
-  Out-of-volume raw pixels are zero. Check their display values against the unsigned/signed conversion rules in [ALGORITHM.md](ALGORITHM.md#7-processing-the-csv-and-creating-the-video).
-  Record the command, input filenames, output filename, and one or two representative screenshots or frames.

**Note:** A successful standalone demo verifies that dataset's pipeline run. The 500³ `uint8` FPS requirement needs the separate benchmark below.

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
- Report the three stages separately. The program's **10 FPS MP4 playback rate does not establish processing throughput**.
- Never put hard-coded “PASS” results in the report; decide from actual measured output.

### Performance results (measured 2026-11-08)

| Field | Observed value |
|---|---|
| Date and OS | 2026-11-08 (Asia/Jerusalem); Windows 11 Home, 64-bit, build 10.0.26300 |
| CPU / memory | 13th Gen Intel Core i9-13900HX; 24 cores / 32 logical processors; 15.75 GiB usable physical RAM (16,907,100,160 bytes) |
| Software versions | Python 3.13.14 / NumPy 2.5.4 / imageio 2.38.1 / imageio-ffmpeg 0.6.0 / FFmpeg 7.1 / pytest 9.1.1 |
| Volume | `500 × 500 × 500`, `uint8`; deterministic random data, seed `2026` |
| Plane count / repeats | `200` / `5` for each stage |
| Plane type | In-bounds isosceles triangles on successive Z slices (`z=0..199`), from `benchmarks.benchmark.make_planes(500, 200)` |
| Image size range | Constant `557 × 498` pixels (height × width); padded video canvas `558 × 498` |
| Projection median FPS | **36.64** (best: 39.95) |
| Processing median FPS | **37.85** (best: 39.29) |
| End-to-end median FPS | **33.36** (best: 34.52) |
| Required threshold (>30 FPS) | **PASS** — projection median 36.64 FPS; processing and end-to-end medians also exceed 30 FPS |
| Expected target (≥100 FPS) | **NOT MET** — all three measured medians are below 100 FPS |

Measured from the current checkout at `C:/Users/dolev/.vscode/New folder/OOP-OOD-Ex1-3D-Volume-Projection`. These results apply to this machine and triangle workload; other plane sizes, orientations, or system load may produce different speeds.

The checkout uses [benchmarks/benchmark.py](benchmarks/benchmark.py) and imageio/FFmpeg. The benchmark has no `--dtype` or `--repeats` flags: `uint8` is fixed, and repetition was performed by a temporary measurement runner calling `benchmarks.benchmark.run(500, 200, True, output_path)` five times, sequentially. These are preserved measurements from the earlier 2026-11-08 run, not a new performance run during documentation synchronization.

Projection and end-to-end values below are the benchmark's actual outputs. Processing was separately timed with `time.perf_counter()` around 200 calls to `video.prepare_frame(projector.project(plane))`, using the same seeded volume, planes, and canvas, with one warm-up frame per pass. Allocation, geometry setup, and warm-up were excluded. End-to-end timing includes opening, writing, and closing the H.264 MP4, but excludes input generation/loading. The three stages were timed separately; processing includes extra work, but independent timing and machine variation can make its measured FPS higher than projection FPS. MP4 playback is 10 FPS and is unrelated to measured throughput.

| Pass | Projection FPS | Processing FPS | End-to-end FPS |
|---|---:|---:|---:|
| 1 | 34.03 | 35.05 | 31.15 |
| 2 | 35.83 | 35.52 | 32.29 |
| 3 | 36.64 | 38.83 | 33.42 |
| 4 | 39.95 | 39.29 | 34.52 |
| 5 | 39.34 | 37.85 | 33.36 |

Medians and best values above are calculated across these five passes.

> The README summarizes this same measurement record. Results are specific to the recorded machine and workload; remeasure after code, hardware, or workload changes.

## 8. Running the automated tests

```bash
# All tests configured by pytest.ini
python -m pytest -q

# Extra detail
python -m pytest -v

# Examples of targeted checks
python -m pytest tests/test_projection.py -v
python -m pytest tests/test_geometry.py tests/test_io.py tests/test_video_and_cli.py -v

# Diagnose remaining modules when one module fails to collect
python -m pytest -q --continue-on-collection-errors
```

The current suite has no dedicated benchmark test module and does not enforce FPS thresholds. Performance acceptance comes from the separately recorded benchmark. The continue-on-collection-errors command still exits unsuccessfully if collection fails; it must not be reported as a full suite pass.

### Test execution record (2026-11-08)

| Item | Result |
|---|---|
| `pytest` command/date | 2026-11-08: `python -m pytest -q` completed successfully (exit 0) after fixing the projection test annotations. |
| Passed | **148** in **2.61 seconds**, including all **60 projection tests** |
| Failed | **0 failures; 0 collection errors** |
| Skipped | **0** |
| Demo command and output | Standalone manual demo not run during this verification; CLI/video tests are included in the 148 passes. Five benchmark MP4 exports completed during the earlier performance measurement. |
| Open issues | The ≥100 FPS target was not met, and a standalone manual demo is still unverified. No automated test failures remain in this run. |

The test commands used the same checkout and Python environment as the
performance measurements. Earlier runs passed 88 tests but could not collect
the projection module because it imported private NumPy types `_Array` and
`_Array1D`. The fix removed that import and replaced the two affected parameter
annotations with public `np.ndarray`. No production algorithm, test inputs,
or assertions changed. The newly collected 60 projection tests all passed.
The earlier algorithm review also passed **216 direct scalar-reference
comparisons** across unsigned bit depths, seeded rotations, and array layouts;
the full suite now executes the corresponding reference-comparison tests too.

If tests are skipped, report them separately rather than counting them as passes. Collection errors are a separate category and must not be counted as skips. Include a short explanation for every failure.

## 9. Overall exit criteria and deliverables

The project is ready for submission when:

- [ ] The checked-in code matches the behavior described in `SRS.md`.
- [x] The current automated correctness, integration, and CLI tests pass on the recorded environment (148 tests).
- [ ] The required three-argument CLI produces a decodable MP4 with correctly ordered frames.
- [ ] Error-handling tests show controlled failures without misleading partial outputs.
- [x] A real 500³ `uint8` benchmark result is documented and checked against **>30 projection FPS**, with the **≥100 FPS target** reported separately as not met.
- [ ] A short experiment summary states the dataset, command, outputs, observations, and limitations.
- [ ] A representative dataset and reproducible standalone demo are supplied for submission; the current checkout has no bundled demo dataset.

### Evidence to keep with the submission

1. Test command and actual `pytest` summary (passed / failed / skipped).
2. The NRRD dataset description and CSV example used for the demo.
3. The command that created the MP4 and the MP4 output (or a clearly documented download/location).
4. Benchmark command, machine specifications, and measured FPS table.
5. A brief interpretation: what worked, what did not, and any known limitations.

---

**Source of requirements:** Ariel University Ex1 handout and the project's `SRS.md`.  
**Source of test coverage:** [tests/](tests/), [benchmarks/benchmark.py](benchmarks/benchmark.py), and the execution record above.\
**Important:** Only evidence-backed checklist items are marked complete. Unchecked items require verification before submission.
