# Algorithm Design — 3D Volume Projection

## 1. Goal

Convert a plane defined by 3 or 4 points in voxel-index coordinates into a 2D grayscale image sampled from a 3D NRRD volume. Points may lie outside the volume; those samples return zero. Repeat for each plane in the CSV file, then combine the images into an MP4 video in CSV order.

This document describes the implemented algorithm and its explicit design
choices, checked against the source on 2026-11-08. Performance is measured
separately with [the benchmark](benchmarks/benchmark.py).

## 2. Supported Plane Shapes

The same projection procedure supports both shapes:

- **Triangle (3 points: `a, b, c`):** The implementation requires an **isosceles** triangle: `|distance(a,b) - distance(a,c)| < EPS`. An **equilateral** triangle is also supported. There is no separate equilateral-only mode.
- **Trapezoid (4 points: `a1, a2, b, c`):** The assignment requires equal side lengths `distance(a1,b)` and `distance(a2,c)` within `EPS`, coplanar points, and `distance(a1,a2) <= distance(b,c)`. The algorithm treats `a1-a2` as the top edge and `b-c` as the bottom edge.

`EPS = 0.001` (from the assignment).

> **Validation decision:** Parallel bases are not enforced: the available
> assignment rules require equal legs, ordered bases, and coplanarity only.
> The strict leg test rejects a difference equal to EPS. Coplanarity uses
> perpendicular distance <= EPS; base order allows only eight ULPs of
> floating-point roundoff, not EPS-sized geometric differences.

## 3. Inputs and Outputs

**Inputs**

1. A 3D voxel array `M[x, y, z]` loaded from a `.nrrd` file. Supported voxel types are unsigned 8-, 16-, or 32-bit values, plus signed 16-bit values as a compatibility extension. Dimensions satisfy `1 <= sx, sy, sz < 1024`. Coordinates are voxel indices; NRRD physical-space metadata is not applied.
2. A `.csv` file containing an ordered list of plane definitions, each with 3 or 4 three-dimensional points.

**Intermediate output:** A 2D image `E` of shape `(height, width)` for each valid plane, indexed as `E[y, x]` and retaining the volume's voxel dtype.

**Final output:** An `.mp4` containing one frame per plane, in CSV order.

Command-line interface requested by the assignment:

```bash
python Ex0.py <file.nrrd> <file.csv> <file.mp4>
```

CSV has 13 columns and points ordered `(a,b,c)` or `(a1,a2,b,c)`.
The shape-name and numeric-count headers use the same point order. Video
is H.264/YUV420p at 10 FPS. The header is required, triangle rows have three
empty trailing cells, blank rows are ignored, and comments are not supported.
See [SRS CSV examples](SRS.md#32-external-interfaces) for the exact headers.
Intensity conversion is described in Section 7.

## 4. Geometry and Sampling

### 4.1 Common geometric operations

```text
vector(p, q) = q - p
distance(p, q) = length(vector(p, q))
lerp(p, q, t) = p + t * (q - p)      // 0 <= t <= 1
```

Use floating-point coordinates during sampling. Return a pixel intensity of `0` when the sampled position lies outside the volume.

**Sampling decision:** Nearest-neighbor, ties-to-even rounding. Test the
original coordinates against inclusive `[0,size-1]` bounds first; outside
positions return zero even if rounding would bring them inside. The
assignment describes `M[p]` without specifying fractional sampling.

### 4.2 Convert either shape into two side edges

The projection is built row-by-row from a **left edge** and a **right edge**.

| Shape | Left edge | Right edge | Top width | Bottom width |
|---|---|---|---|---|
| Triangle | `a -> b` | `a -> c` | `0` | `distance(b,c)` |
| Trapezoid | `a1 -> b` | `a2 -> c` | `distance(a1,a2)` | `distance(b,c)` |

Because both shapes now have two side edges, they can share the same rasterization algorithm.

### 4.3 Image size and pixel mapping

Let `L` be the longer of the two near-equal accepted side edges, and `B` the
bottom-edge length. Since distances are real but dimensions are integers:

```text
height = max(2, round(L) + 1)
width  = max(2, round(B) + 1)
```

The `+1` includes the first and last sampled positions. This is a **design choice**: the assignment describes an image of size `Dab × Dbc` without explaining how to convert non-integer distances into pixel counts.

Dimension rounding uses Python's ties-to-even `round`; row lengths and voxel
coordinates use NumPy's ties-to-even `rint`. Nonfinite side/base lengths and
images with `height * width > 20,000,000` raise `InvalidPlaneError` before
image allocation.

For each image row `y`:

1. Set `t = y / (height - 1)`.
2. Find the row's 3D endpoints:
   - `left = lerp(leftTop, leftBottom, t)`
   - `right = lerp(rightTop, rightBottom, t)`
3. Compute `rowLength = distance(left, right)` and `rowPixels = round(rowLength) + 1` (or 1 for a zero-width tip).
4. Center the row in the output image: `startX = floor((width - rowPixels) / 2)`.
5. For each `j` in `0 .. rowPixels - 1`, calculate `u = j / (rowPixels - 1)` (use `0` if `rowPixels == 1`), sample `lerp(left, right, u)`, and write the result to `E[y, startX + j]` if the output column is in range.

Initialize `E` to zero. Pixels outside the rasterized rows remain zero in the raw projection. If rounding produces an out-of-range output column, discard that sample; do not clamp it onto an edge pixel. Zero maps to black for unsigned video conversion; signed conversion has the exception described in Section 7.

> The assignment's example updates normalized edge vectors one step at a time. Using interpolation by `t` expresses the same row-by-row idea but makes the handling of triangle and trapezoid shapes easier to share. The precise rounding and endpoint conventions must be tested.

## 5. Main Projection Pseudocode

The loops below express the mathematical mapping. The production
[projector](volume_projection/projector.py) evaluates it with vectorized
NumPy arrays and masks, without a per-pixel Python loop. It gathers voxels
directly using the same bounds and rounding rules as
[Volume.sample_many](volume_projection/volume.py).

```text
FUNCTION projectPlane(volume M, points):
    shape = validateAndClassify(points, EPS)
    IF shape is invalid:
        RAISE InvalidPlaneError

    IF shape == TRIANGLE:
        (leftTop, leftBottom)   = (a, b)
        (rightTop, rightBottom) = (a, c)
    ELSE IF shape == TRAPEZOID:
        (leftTop, leftBottom)   = (a1, b)
        (rightTop, rightBottom) = (a2, c)

    sideLength = max(distance(leftTop, leftBottom), distance(rightTop, rightBottom))
    baseLength = distance(leftBottom, rightBottom)
    IF sideLength or baseLength is not finite:
        RAISE InvalidPlaneError
    height = max(2, round(sideLength) + 1)
    width = max(2, round(baseLength) + 1)
    IF height * width > 20_000_000:
        RAISE InvalidPlaneError
    E = zeroFilledImage(shape=(height, width), dtype=M.dtype)

    FOR y FROM 0 TO height - 1:
        t = y / (height - 1)
        left = lerp(leftTop, leftBottom, t)
        right = lerp(rightTop, rightBottom, t)
        rowLength = distance(left, right)
        rowPixels = max(1, round(rowLength) + 1)
        startX = floor((width - rowPixels) / 2)

        FOR j FROM 0 TO rowPixels - 1:
            u = 0 IF rowPixels == 1 ELSE j / (rowPixels - 1)
            samplePoint = lerp(left, right, u)
            pixel = sampleNearestVoxelOrZero(M, samplePoint)
            x = startX + j
            IF 0 <= x < width:
                E[y, x] = pixel

    RETURN E
```

## 6. Plane Validation

Before projection:

1. Check the number of points: exactly 3 or 4.
2. Check that every coordinate is a finite number.
3. Require finite edge lengths. Reject triangles with any zero-length edge and trapezoids with a zero-length top, bottom, or side edge.
4. **Triangle:** Check `abs(distance(a,b) - distance(a,c)) < EPS`. Also require `norm(cross((b-a)/distance(a,b), (c-a)/distance(a,c))) > 1e-12`. This rejects nearly collinear triangles even when their cross product is nonzero.
5. **Trapezoid:** Check `abs(distance(a1,b) - distance(a2,c)) < EPS`, base order with the eight-ULP allowance described in Section 2, and coplanarity using the formula below. Parallelism, convexity, and self-intersection are not checked.
6. Reject invalid plane definitions with a clear error message; do not silently generate a misleading image.

For trapezoids, let `n = cross((a2-a1)/distance(a1,a2), (b-a1)/distance(a1,b))`.
Reject a nonfinite `norm(n)` or `norm(n) <= 1e-12`. The perpendicular distance
`abs(dot(c-a1, n)) / norm(n)` must be `<= EPS`, in voxel units. These checks
implement the scale-aware coplanarity test in
[Plane.validate](volume_projection/geometry.py).

## 7. Processing the CSV and Creating the Video

```text
FUNCTION run(nrrdPath, csvPath, mp4Path):
    volume = loadNRRD(nrrdPath)
    planes = parseCSV(csvPath)
    validate all planes and find the shared even-sized canvas
    OPEN temporary MP4 encoder beside the output path
        FOR each plane IN planes IN INPUT ORDER:
            image = projectPlane(volume, plane.points)
            frame = centerOnBlackCanvas(convertToVideoFrame(image))
            write frame
    CLOSE encoder and atomically replace output on success
    REMOVE temporary file on failure, preserving existing output
```

All frames use the maximum height/width rounded up to even numbers, with
centered black padding and no resizing. Only one projected frame is held
at a time. Playback is 10 FPS, independent of processing FPS.

Before padding, [VideoWriter.to_uint8](volume_projection/video_writer.py)
converts each raw projected image as follows:

- **Unsigned 8/16/32-bit:** Shift right by `0`, `8`, or `24` bits respectively, then cast to `uint8`, retaining the highest eight bits.
- **Signed int16, all pixels nonnegative:** An all-zero image stays zero. Otherwise, compute `rint(image.astype(float32) * 255 / image.max())` and cast to `uint8`. The scale is determined independently for each frame.
- **Signed int16, any pixel negative:** Compute `(image.astype(int32) + 32768) >> 8`, then cast to `uint8`. Raw zeros, including shape background and out-of-volume samples, become gray value `128` in this case.

The additional canvas padding is created after conversion and always stays
black. These values describe frames before lossy H.264 encoding.

## 8. Implemented OOP Design

| Component | Responsibility |
|---|---|
| [Point3D / EdgePair](volume_projection/geometry.py) | Store coordinates and the common side-edge representation; vector calculations use NumPy arrays |
| [Volume](volume_projection/volume.py) / [NRRDReader](volume_projection/nrrd_reader.py) | Store/read voxel data and sample positions |
| [Plane](volume_projection/geometry.py) | Represent triangle or trapezoid and validate geometry |
| [PlaneProjector](volume_projection/projector.py) | Convert a valid plane into a 2D image |
| [CSVPlaneReader](volume_projection/csv_reader.py) | Load plane definitions in order |
| [VideoWriter](volume_projection/video_writer.py) | Convert images into MP4 frames |
| [ProjectionApplication](volume_projection/application.py) | Coordinate loading, projection, and video writing |
| [main](Ex0.py) | Parse CLI arguments, optionally request paths through a GUI, and invoke the application |

These are the components in the current checkout.

## 9. Edge Cases and Tests

- Valid equilateral triangle: generates a centered triangular image.
- Valid non-equilateral isosceles triangle: generates a centered triangular image.
- Conventional isosceles trapezoid with consistently ordered parallel bases: generates rows that expand from the short top base to the longer bottom base. Other accepted four-point arrangements can produce rows that shrink and expand, because parallelism and self-intersection are not validated.
- Collinear, nearly collinear, or coincident triangle vertices: rejected according to Section 6.
- Invalid trapezoid side lengths or non-coplanar points: rejected.
- Degenerate geometry (identical points or zero-length edges): rejected.
- Sample point outside the NRRD boundaries: intensity `0`.
- Plane partly outside the volume: valid in-volume samples are preserved; other samples are `0`.
- Multiple CSV planes: one video frame per plane in the same order.
- Varying image dimensions: center on the shared even-sized canvas with black padding and no resizing.
- Image size exceeding 20,000,000 pixels: rejected before allocation.

## 10. Performance and Complexity

NFR-01 requires **more than 30 projection FPS** and targets **≥100 FPS** on a
`500 × 500 × 500` `uint8` volume. Processing without encoding and end-to-end
rates are reported separately. Playback remains 10 FPS. Hardware, workload,
and actual measurements are recorded in
[TEST_STRATEGY.md](TEST_STRATEGY.md#performance-results-measured-2026-11-08).

For a single plane, vectorized NumPy operations construct the row/column map,
select active pixels, interpolate coordinates, check bounds, and gather voxel
values. Time complexity is **O(height × width)**, assuming constant-time voxel
access. The output and temporary mapping, mask, and coordinate arrays use
**O(height × width)** space, in addition to the loaded volume. The application
already streams frames into the encoder rather than storing the full video
in memory; it retains the plane list and shared canvas dimensions.

## 11. Validation evidence and limits

Exact expected matrices in [the projection tests](tests/test_projection.py)
cover axis-aligned and tilted planes. An independent
[scalar implementation](tests/reference_projection.py) checks seeded rotations,
out-of-bounds geometry, all unsigned bit depths, and different array memory layouts.
During the 2026-11-08 review, 216 direct comparisons against that reference
passed. A later test-only correction replaced unavailable private NumPy
annotation types with the public `np.ndarray` type. The full suite then
passed **148 tests**, including all 60 projection tests, with the production
algorithm and assertions unchanged. See [the execution record](TEST_STRATEGY.md#test-execution-record-2026-11-08).
The original PDF was unavailable for this audit. Inclusive interpolation,
ties-to-even sampling, output padding, and intensity policies are explicit
implementation interpretations rather than independently verified PDF rules.
