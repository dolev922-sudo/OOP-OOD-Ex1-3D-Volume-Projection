"""FR-01/FR-02: synthetic files, ordering, and controlled errors."""
import numpy as np
import pytest

from volume_projection import CSVPlaneReader, NRRDReader, PlaneFormatError, VolumeFormatError
from .conftest import write_csv, write_nrrd


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.uint32])
@pytest.mark.parametrize("encoding", ["raw", "gzip"])
@pytest.mark.parametrize("endian", ["little", "big"])
def test_nrrd_bit_depth_encoding_and_endian(tmp_path, dtype, encoding, endian):
    volume = np.arange(3 * 4 * 2, dtype=dtype).reshape((3, 4, 2)) * 9
    path = tmp_path / "test.nrrd"
    write_nrrd(path, volume, encoding=encoding, endian=endian)
    loaded = NRRDReader().load(path)
    np.testing.assert_array_equal(loaded.data, volume)
    assert int(loaded.data[2, 3, 1]) == int(volume[2, 3, 1])


def test_nrrd_detached_raw(tmp_path):
    volume = np.arange(24, dtype=np.uint16).reshape(2, 3, 4)
    path = tmp_path / "sample.nhdr"
    write_nrrd(path, volume, detached=True)
    np.testing.assert_array_equal(NRRDReader().load(path).data, volume)


def test_truncated_nrrd_rejected(tmp_path):
    path = tmp_path / "broken.nrrd"
    write_nrrd(path, np.zeros((2, 3, 4), dtype=np.uint8))
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(VolumeFormatError, match="length mismatch"):
        NRRDReader().load(path)


def test_signed_short_nrrd_supported(tmp_path):
    path = tmp_path / "signed.nrrd"
    values = np.array([-32768, -1, 0, 1, 255, 256, 32767, 1024], dtype="<i2")
    header = b"NRRD0005\ntype: short\ndimension: 3\nsizes: 2 2 2\nencoding: raw\nendian: little\n\n"
    path.write_bytes(header + values.tobytes())
    loaded = NRRDReader().load(path)
    np.testing.assert_array_equal(loaded.data.reshape(-1, order="F"), values)


def test_missing_nrrd_rejected(tmp_path):
    with pytest.raises(VolumeFormatError, match="Cannot read"):
        NRRDReader().load(tmp_path / "absent.nrrd")


def test_csv_reads_both_shapes_in_order(tmp_path):
    path = tmp_path / "planes.csv"
    write_csv(path, [
        ("triangle", [(2, 0, 0), (0, 2, 0), (4, 2, 0)]),
        ("trapezoid", [(1, 0, 0), (3, 0, 0), (0, 2, 0), (4, 2, 0)]),
    ])
    planes = CSVPlaneReader().load(path)
    assert [plane.shape for plane in planes] == ["triangle", "trapezoid"]


def test_csv_reads_number_of_points_format(tmp_path):
    path = tmp_path / "planes.csv"
    path.write_text(
        "Number of Points (3 or 4),x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4\n"
        "3,2,0,0,0,2,0,4,2,0,,,\n"
        "4,1,0,0,3,0,0,0,2,0,4,2,0\n"
    )
    planes = CSVPlaneReader().load(path)
    assert [plane.shape for plane in planes] == ["triangle", "trapezoid"]


def test_csv_wrong_header_rejected(tmp_path):
    path = tmp_path / "planes.csv"
    path.write_text("x,y,z\n1,2,3\n")
    with pytest.raises(PlaneFormatError, match="header"):
        CSVPlaneReader().load(path)


def test_csv_malformed_numeric_fails_with_line_number(tmp_path):
    path = tmp_path / "planes.csv"
    write_csv(path, [("triangle", [(2, 0, 0), (0, 2, 0), (4, 2, 0)])])
    path.write_text(path.read_text().replace("2,0,0", "not-a-number,0,0"))
    with pytest.raises(PlaneFormatError, match="line 2"):
        CSVPlaneReader().load(path)


def test_csv_missing_coordinate_rejected(tmp_path):
    path = tmp_path / "planes.csv"
    write_csv(path, [("triangle", [(2, 0, 0), (0, 2, 0), (4, 2, 0)])])
    path.write_text(path.read_text().replace("2,0,0", ",0,0"))
    with pytest.raises(PlaneFormatError, match="line 2"):
        CSVPlaneReader().load(path)


def test_csv_triangle_fourth_coordinate_rejected(tmp_path):
    path = tmp_path / "planes.csv"
    write_csv(path, [("triangle", [(2, 0, 0), (0, 2, 0), (4, 2, 0)])])
    text = path.read_text()
    path.write_text(text.rstrip() + ",9\n")
    with pytest.raises(PlaneFormatError, match="columns"):
        CSVPlaneReader().load(path)


def test_csv_empty_rejected(tmp_path):
    path = tmp_path / "planes.csv"
    write_csv(path, [])
    with pytest.raises(PlaneFormatError, match="no plane"):
        CSVPlaneReader().load(path)
