# 3D Volume Plane Projection

**Ariel University · Introduction to Software Engineering (OOP/OOD) · Exercise 1**

A Python program that reads a **3D NRRD volume** and a **CSV file of planes** (triangles or trapezoids), projects each plane into a 2D grayscale image, and saves the images in CSV order as an **MP4 video**.

## Run

Requires **Python 3.10+** and the full project, including the
[volume_projection/](volume_projection/) package. Install NumPy, imageio,
imageio-ffmpeg, and pytest from [requirements.txt](requirements.txt).

```bash
python -m pip install -r requirements.txt
python Ex0.py input.nrrd planes.csv output.mp4
```

Replace the input names with existing files and use an existing output
directory. This checkout currently has no bundled example dataset or demo
generator. If any of the three paths is omitted, the application opens a
Tkinter file-selection form when a graphical environment is available.

## Inputs and output

- **Volume:** 3D NRRD, dimensions 1–1023 per axis; unsigned 8/16/32-bit or signed 16-bit voxels. Raw and gzip encoding, single-file detached data, and little/big endian multibyte data are supported. Coordinates are voxel indices; physical spacing/orientation are not applied.
- **CSV:** A required 13-column header, followed by `triangle` or `trapezoid` rows. Triangles leave the last three cells empty. The alternate header uses `number of points (3 or 4)` and numeric shape values `3`/`4`. See [the exact CSV formats](SRS.md#32-external-interfaces). Blank rows are ignored; comments and headerless input are not supported. Invalid rows stop the run.
- **Sampling:** Nearest-neighbor with ties-to-even rounding, checking original coordinates against the volume bounds first. Out-of-volume samples are zero in the raw projection.
- **Video:** H.264/YUV420p MP4 at **10 FPS playback**, with centered black padding to a shared even-sized canvas and no resizing. Unsigned conversion keeps the highest eight bits; signed-int16 conversion is frame-dependent and can map raw zero background to gray. See [intensity conversion](ALGORITHM.md#7-processing-the-csv-and-creating-the-video).

## Tests and performance

```bash
python -m pytest -q
python -m benchmarks.benchmark --size 500 --frames 200 --encode
```

The benchmark generates its own `uint8` volume and reports projection FPS
and, with `--encode`, end-to-end FPS. Repeat it five times to calculate
median/best FPS. Processing without encoding requires separate timing.

**Performance goal:** More than **30 projection FPS** required; **≥100 FPS**
targeted on a 500×500×500 `uint8` volume. Playback FPS is independent of
processing throughput.

**Recorded results (2026-11-08):** Five 200-frame passes measured medians of
36.64 projection FPS, 37.85 processing FPS, and 33.36 end-to-end FPS on the
recorded machine. The >30 FPS requirement passed; the ≥100 FPS target was
not met. After correcting the projection test annotations, the latest full
test run reported **148 passed, 0 failed, 0 skipped**, with no collection errors.
The projection algorithm and test assertions were unchanged. Machine details,
commands, evidence, and remaining checks are in [TEST_STRATEGY.md](TEST_STRATEGY.md).

## Project documents

- [SRS.md](SRS.md) — Software requirements
- [TEST_STRATEGY.md](TEST_STRATEGY.md) — Testing approach and acceptance criteria
- [ALGORITHM.md](ALGORITHM.md) — Implemented geometry, sampling, and video rules
