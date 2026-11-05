# Test strategy / SRS verification matrix

Testing tools: `pytest`, NumPy, generated synthetic 3-D NRRD fixtures, and actual FFmpeg-backed MP4 round trips. Run `python -m pytest -q` from the project root.

| SRS verification | Relevant tests | Pass criteria |
|---|---|---|
| T-01 / FR-01 | `test_io.py::test_nrrd_bit_depth_encoding_and_endian` (12 combinations), `test_nrrd_detached_raw`, `test_signed_short_nrrd_supported`, `test_truncated_nrrd_rejected` | Correct axis ordering, voxel precision, endian and encoding; bad files rejected |
| T-02 / FR-02–FR-04 | `test_io.py::test_csv_reads_both_shapes_in_order`, `test_geometry.py` | Points parsed in order, 3/4-point geometry checked, invalid definitions rejected |
| T-03 / FR-05 | `test_projection.py::test_triangle_exact_pixels`, `test_trapezoid_exact_pixels`, `test_uint16_and_uint32_precision_survives_projection` | Pixel-for-pixel raw image matrices equal manually determined expectations |
| T-04 / FR-06 | `test_out_of_bounds_positions_never_round_inside`, `test_partly_outside_plane_keeps_in_bounds_samples` | Outside coordinates yield zero, inside samples survive |
| T-05 / FR-07–FR-08 | `test_video_and_cli.py::test_integration_video_preserves_csv_order_and_frame_count`, `test_padding_centers_without_resizing` | MP4 decodes to one frame per CSV plane in order; varying shapes padded without resizing |
| T-06 / FR-09 | `test_required_cli_success_and_error_exit_codes` | Required CLI succeeds with 3 paths; fails predictably on missing input |
| T-07 / NFR-01 | `python -m benchmarks.benchmark --size 500 --frames 30 --encode` | FPS is **measured**, projection and full encoding separated, both compared with requirement |
| T-08 / NFR-03 | `test_io.py` malformed cases; `test_existing_output_unchanged_if_csv_invalid` | Invalid inputs produce controlled failures without overwriting existing output |

## Synthetic fixture design

- Patterned `M[x,y,z] = x + 10y + 100z` enables exact coordinate/pixel assertions at known positions.
- A triangle at `(2,0,0),(0,2,0),(4,2,0)` has `height=4`, `width=5`, allowing exact checks of tip, sloped rows and full base.
- A trapezoid at `(1,0,0),(3,0,0),(0,2,0),(4,2,0)` has `height=3`, `width=5`, allowing exact checks of variable widths.
- Unsigned and signed-short fixtures test raw/gzip and little/big endian. Video tests use spatially constant but distinct Z slices to verify frame order despite lossy H.264.

## Limits of this test evidence

The tests validate the **documented algorithm** and input/output behavior, not clinical correctness for NRRD physical-space metadata. MP4 intensity is not required to round-trip losslessly. The benchmark is performance evidence for its specified machine and workload, not a universal performance guarantee. Detailed measurements are in `EXPERIMENT_REPORT.md`.
