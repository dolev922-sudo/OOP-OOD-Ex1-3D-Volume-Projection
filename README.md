# 3D Volume Plane Projection

**Ariel University · Introduction to Software Engineering (OOP/OOD) · Exercise 1**

A Python program that reads a **3D NRRD volume** and a **CSV file of planes** (triangles or trapezoids), projects each plane into a 2D grayscale image, and saves the images in CSV order as an **MP4 video**.

## Run

Requires **Python 3.10+** and the full project, including the `volproj/` package.

```bash
pip install -r requirements.txt
python Ex0.py input.nrrd planes.csv output.mp4
```

## Demo and tests

```bash
python make_example_data.py  # Create sample NRRD, CSV, and MP4
pytest                       # Run tests
python benchmark.py --encode # Measure projection and video performance
```

## Project documents

- [SRS.md](SRS.md) — Software requirements
- [TEST_STRATEGY.md](TEST_STRATEGY.md) — Testing approach and acceptance criteria

**Performance goal:** More than 30 FPS required; 100+ FPS targeted on a 500×500×500 8-bit volume. Actual results depend on the machine and test settings.
