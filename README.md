# 3D Volume Projection

A Python OOP/OOD project that extracts 2D triangle and trapezoid slices from a 3D NRRD volume and combines them into an MP4 video.

## Quick start

Install Python 3.10+, then run these commands in PowerShell:

```powershell
git clone https://github.com/dolev922-sudo/OOP-OOD-Ex1-3D-Volume-Projection.git
cd OOP-OOD-Ex1-3D-Volume-Projection
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Ex0.py examples/demo.nrrd examples/planes.csv output.mp4
```

Open `output.mp4` to view the three example frames.

## Usage example

With your environment activated:

```bash
python Ex0.py input.nrrd planes.csv result.mp4
```

The CSV defines one plane per row, for example:

```csv
shape,x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4
triangle,2,0,0,0,2,0,4,2,0,,,
trapezoid,1,0,0,3,0,0,0,2,0,4,2,0
```

Triangle points are `(a,b,c)`, with apex `a`. Trapezoid points are
`(a1,a2,b,c)`, with top base `a1–a2` and bottom base `b–c`.
Coordinates are voxel indices. See [examples/planes.csv](examples/planes.csv)
for a complete input. Run `python Ex0.py` without arguments for the optional file picker.

## Configuration and environment

- Activate on Windows: `.\.venv\Scripts\Activate.ps1`; on macOS/Linux: `source .venv/bin/activate`.
  On macOS/Linux, use `.venv/bin/python` instead of the Windows executable in the quick start.
- Dependencies: NumPy, imageio, imageio-ffmpeg, and pytest; versions are in [requirements.txt](requirements.txt).
- FFmpeg is supplied by imageio-ffmpeg. Tkinter is needed only for the file picker.
- Inputs: raw/gzip NRRD with unsigned 8/16/32-bit or signed 16-bit voxels, plus a plane CSV.
- Output: H.264 MP4 at 10 playback FPS. The destination directory must exist.
- No API keys or environment variables are required.

## Tests

Run from the project root with the environment activated:

```bash
python -m pytest -q
```

To measure processing speed separately:

```bash
python -m benchmarks.benchmark --size 500 --frames 30 --encode
```

Coverage and measured results are documented in [TEST_STRATEGY.md](TEST_STRATEGY.md)
and [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md).

## Project structure

```text
Ex0.py                CLI and optional file picker
volume_projection/    Input readers, geometry, projection, and video output
tests/                Automated tests
examples/             Sample inputs, videos, and data generator
benchmarks/           Performance measurement
```

Requirements: [SRS.md](SRS.md). Algorithm design: [ALGORITHM.md](ALGORITHM.md).

## Contributing

Create a branch, make a focused change, add or update relevant tests, and run
the test suite before opening a pull request. Keep documentation consistent
with behavior; do not commit temporary outputs or caches.

## License and contact

Licensed under [Apache License 2.0](LICENSE).

For questions or bug reports, [open an issue](https://github.com/dolev922-sudo/OOP-OOD-Ex1-3D-Volume-Projection/issues).
