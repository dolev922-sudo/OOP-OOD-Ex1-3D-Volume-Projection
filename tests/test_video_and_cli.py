"""FR-07..FR-09: MP4 frame order, size differences, CLI and cleanup."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pytest

from volume_projection import ProjectionApplication, VideoWriter
from .conftest import write_csv, write_nrrd

ROOT = Path(__file__).resolve().parents[1]


def test_uint8_conversion_deterministic():
    np.testing.assert_array_equal(VideoWriter.to_uint8(np.array([0, 255], dtype=np.uint8)), [0, 255])
    np.testing.assert_array_equal(VideoWriter.to_uint8(np.array([0, 257, 65535], dtype=np.uint16)), [0, 1, 255])
    np.testing.assert_array_equal(VideoWriter.to_uint8(np.array([0, 2**24, 2**32 - 1], dtype=np.uint32)), [0, 1, 255])
    np.testing.assert_array_equal(VideoWriter.to_uint8(np.array([-32768, -1, 32767], dtype=np.int16)), [0, 127, 255])
    np.testing.assert_array_equal(VideoWriter.to_uint8(np.array([0, 140, 280], dtype=np.int16)), [0, 128, 255])


def test_padding_centers_without_resizing(tmp_path):
    writer = VideoWriter(tmp_path / "out.mp4", max_height=3, max_width=5)
    prepared = writer.prepare_frame(np.full((2, 3), 111, dtype=np.uint8))
    assert prepared.shape == (4, 6)  # YUV420 requires even canvas dimensions.
    assert (prepared[1:3, 1:4] == 111).all()
    assert np.count_nonzero(prepared) == 6


def test_integration_video_preserves_csv_order_and_frame_count(tmp_path):
    data = np.zeros((12, 12, 3), dtype=np.uint8)
    data[:, :, 0] = 45
    data[:, :, 1] = 210
    nrrd_path = tmp_path / "input.nrrd"
    csv_path = tmp_path / "planes.csv"
    output_path = tmp_path / "result.mp4"
    write_nrrd(nrrd_path, data, encoding="gzip")
    write_csv(csv_path, [
        ("triangle", [(5, 0, 0), (0, 5, 0), (10, 5, 0)]),
        ("triangle", [(5, 0, 1), (3, 2, 1), (7, 2, 1)]),
        ("trapezoid", [(3, 0, 0), (7, 0, 0), (1, 4, 0), (9, 4, 0)]),
    ])
    assert ProjectionApplication().run(nrrd_path, csv_path, output_path) == 3
    assert output_path.exists() and output_path.stat().st_size > 0
    with imageio.get_reader(str(output_path), format="FFMPEG") as reader:
        frames = [frame for frame in reader]  # imageio length may be infinite
    assert len(frames) == 3
    assert len({frame.shape for frame in frames}) == 1
    assert frames[0].shape[0] % 2 == 0 and frames[0].shape[1] % 2 == 0
    # H.264 is lossy: test relative intensity, not exact pixel equality.
    assert np.asarray(frames[1]).max() > np.asarray(frames[0]).max() + 80
    assert np.asarray(frames[2]).max() < np.asarray(frames[1]).max() - 80


def test_required_cli_success_and_error_exit_codes(tmp_path):
    data = np.full((6, 6, 2), 192, dtype=np.uint8)
    nrrd_path = tmp_path / "in.nrrd"
    csv_path = tmp_path / "in.csv"
    mp4_path = tmp_path / "out.mp4"
    write_nrrd(nrrd_path, data)
    write_csv(csv_path, [("triangle", [(2, 0, 0), (0, 2, 0), (4, 2, 0)])])
    ok = subprocess.run([sys.executable, str(ROOT / "Ex0.py"), str(nrrd_path),
                         str(csv_path), str(mp4_path)], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert "1 frames" in ok.stdout
    assert mp4_path.is_file()
    invalid = subprocess.run([sys.executable, str(ROOT / "Ex0.py"), str(nrrd_path),
                              str(tmp_path / "missing.csv"), str(tmp_path / "bad.mp4")],
                             capture_output=True, text=True)
    assert invalid.returncode != 0 and "Error:" in invalid.stderr
    assert not (tmp_path / "bad.mp4").exists()


def test_existing_output_unchanged_if_csv_invalid(tmp_path):
    data = np.full((6, 6, 2), 42, dtype=np.uint8)
    input_path = tmp_path / "input.nrrd"
    csv_path = tmp_path / "bad.csv"
    output_path = tmp_path / "saved.mp4"
    write_nrrd(input_path, data)
    csv_path.write_text("bad header")
    output_path.write_bytes(b"existing")
    with pytest.raises(Exception):
        ProjectionApplication().run(input_path, csv_path, output_path)
    assert output_path.read_bytes() == b"existing"
