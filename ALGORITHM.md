# Algorithm Design — 3D Volume Projection

## 1. Goal

Convert a plane defined by 3 or 4 points inside a 3D NRRD volume into a 2D grayscale image. Repeat for each plane in the CSV file, then combine the images into an MP4 video in CSV order.

This document describes the implemented algorithm and its explicit design
choices, audited on 2026-11-02. Measurements belong in [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md).

## 2. Supported Plane Shapes

The same projection procedure supports both shapes:

- **Triangle (3 points: `a, b, c`):** The assignment requires an **isosceles** triangle: `|distance(a,b) - distance(a,c)| < EPS`. An **equilateral** triangle is also supported because it is an isosceles triangle; if a strict equilateral mode is desired, also check that `distance(a,b)`, `distance(a,c)` and `distance(b,c)` are equal within `EPS`.
- **Trapezoid (4 points: `a1, a2, b, c`):** The assignment requires equal side lengths `distance(a1,b)` and `distance(a2,c)` within `EPS`, coplanar points, and `distance(a1,a2) <= distance(b,c)`. The algorithm treats `a1-a2` as the top edge and `b-c` as the bottom edge.

`EPS = 0.001` (from the assignment).

> **Validation decision:** Parallel bases are not enforced: the available
> assignment rules require equal legs, ordered bases, and coplanarity only.
> The strict leg test rejects a difference equal to EPS. Coplanarity uses
> perpendicular distance <= EPS; base order allows only eight ULPs of
> floating-point roundoff, not EPS-sized geometric differences.

## 3. Inputs and Outputs

**Inputs**

1. A 3D voxel array `M[x][y][z]` loaded from a `.nrrd` file. The assignment allows unsigned 8-, 16-, or 32-bit values and dimensions `1 <= sx, sy, sz < 1024`.
2. A `.csv` file containing an ordered list of plane definitions, each with 3 or 4 three-dimensional points.

**Intermediate output:** A 2D image `E` for each valid plane.

**Final output:** An `.mp4` containing one frame per plane, in CSV order.

Command-line interface requested by the assignment:

```bash
python Ex0.py <file.nrrd> <file.csv> <file.mp4>
```

CSV has 13 columns and points ordered `(a,b,c)` or `(a1,a2,b,c)`.
The shape-name and numeric-count headers use the same point order. Video
is H.264/YUV420p at 10 FPS. Unsigned video conversion retains the highest
eight bits; signed int16 is a compatibility extension described in the README.

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

For each image row `y`:

1. Set `t = y / (height - 1)`.
2. Find the row's 3D endpoints:
   - `left = lerp(leftTop, leftBottom, t)`
   - `right = lerp(rightTop, rightBottom, t)`
3. Compute `rowLength = distance(left, right)` and `rowPixels = round(rowLength) + 1` (or 1 for a zero-width tip).
4. Center the row in the output image: `startX = floor((width - rowPixels) / 2)`.
5. For each `j` in `0 .. rowPixels - 1`, calculate `u = j / (rowPixels - 1)` (use `0` if `rowPixels == 1`), sample `lerp(left, right, u)`, and write the result to `E[startX + j][y]`.

Initialize `E` to zero. Pixels outside the triangle or trapezoid remain black. If rounding creates a one-pixel discrepancy, clamp the output column to the valid image range.

> The assignment's example updates normalized edge vectors one step at a time. Using interpolation by `t` expresses the same row-by-row idea but makes the handling of triangle and trapezoid shapes easier to share. The precise rounding and endpoint conventions must be tested.

## 5. Main Projection Pseudocode

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
    height = max(2, round(sideLength) + 1)
    width = max(2, round(baseLength) + 1)
    E = zeroFilledImage(width, height)

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
                E[x][y] = pixel

    RETURN E
```

## 6. Plane Validation

Before projection:

1. Check the number of points: exactly 3 or 4.
2. Check that every coordinate is a finite number.
3. Reject coincident or degenerate edges that prevent a meaningful plane/image.
4. **Triangle:** Check `abs(distance(a,b) - distance(a,c)) < EPS`; the cross product `(b-a) × (c-a)` must be nonzero. For an *equilateral-only option*, also verify all three side lengths match within `EPS`.
5. **Trapezoid:** Check `abs(distance(a1,b) - distance(a2,c)) < EPS`, `distance(a1,a2) <= distance(b,c)`, and coplanarity. Optionally check parallel bases as noted above.
6. Reject invalid plane definitions with a clear error message; do not silently generate a misleading image.

For trapezoid coplanarity, one useful test is whether the scalar triple product of three edge vectors is approximately zero. Because its magnitude depends on the scale of the coordinates, use a **scale-aware** tolerance rather than comparing the raw triple product directly with `EPS`.

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

## 8. Suggested OOP Design

| Component | Responsibility |
|---|---|
| `Point3D` / `Vector3D` | Coordinate and vector calculations |
| `Volume` / `NRRDReader` | Store/read voxel data and sample positions |
| `Plane` | Represent triangle or trapezoid and validate geometry |
| `PlaneProjector` | Convert a valid plane into a 2D image |
| `CSVPlaneReader` | Load plane definitions in order |
| `VideoWriter` | Convert images into MP4 frames |
| `Main` | Parse CLI arguments and coordinate the workflow |

These are **suggested** classes, not compulsory names or classes from the assignment.

## 9. Edge Cases and Tests

- Valid equilateral triangle: generates a centered triangular image.
- Valid non-equilateral triangle: generates a centered triangular image.
- Valid isosceles trapezoid: generates rows that expand from the short top base to the longer bottom base.
- Collinear or coincident triangle vertices: rejected.
- Invalid trapezoid side lengths or non-coplanar points: rejected.
- Degenerate geometry (identical points or zero-length edges): rejected.
- Sample point outside the NRRD boundaries: intensity `0`.
- Plane partly outside the volume: valid in-volume samples are preserved; other samples are `0`.
- Multiple CSV planes: one video frame per plane in the same order.
- Varying image dimensions: verify the chosen video padding/resizing rule.

## 10. Performance and Complexity

The assignment requires **at least 30 frames per second** and targets **100+ FPS** on a `500 × 500 × 500` byte volume. These are requirements/targets, **not verified performance claims**.

For a single plane, the projection loops over approximately `height × width` pixel positions, so time complexity is **O(height × width)**, assuming constant-time voxel access. The image uses **O(height × width)** space. To reduce memory use, frames can be streamed into the video encoder instead of storing all frames at once.

## 11. Validation evidence and limits

Exact expected matrices cover axis-aligned and tilted planes. An independent
scalar implementation in the tests checks seeded rotations, out-of-bounds
geometry, all unsigned bit depths, and different array memory layouts.
The original PDF was unavailable for this audit. Inclusive interpolation,
ties-to-even sampling, output padding, and intensity policies are explicit
implementation interpretations rather than independently verified PDF rules.
