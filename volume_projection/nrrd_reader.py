"""Small standard-library NRRD reader for scalar 3-D volumes.

Supported: embedded .nrrd and detached .nhdr; raw and gzip/gz encoding;
little/big endian; comments and CRLF headers. The NRRD axis-0-fastest
ordering is respected. Other NRRD encodings are intentionally rejected.
"""
from __future__ import annotations

import gzip
import zlib
from pathlib import Path

import numpy as np

from .exceptions import VolumeFormatError
from .volume import Volume

_TYPE_TO_DTYPE: dict[str, str] = {
    "uchar": "u1", "unsigned char": "u1", "uint8": "u1", "uint8_t": "u1",
    "ushort": "u2", "unsigned short": "u2", "uint16": "u2", "uint16_t": "u2",
    "uint": "u4", "unsigned int": "u4", "uint32": "u4", "uint32_t": "u4",
    "short": "i2", "signed short": "i2", "int16": "i2", "int16_t": "i2",
}
_MAX_HEADER_BYTES = 1024 * 1024


class NRRDReader:
    """Read NRRD voxels without depending on an external NRRD package."""

    def load(self, filename: str | Path) -> Volume:
        path = Path(filename)
        try:
            with path.open("rb") as stream:
                fields = self._read_header(stream)
                return self._load_data(path, fields, stream)
        except OSError as exc:
            raise VolumeFormatError(f"Cannot read NRRD '{path}': {exc}") from exc
        except (ValueError, OverflowError, EOFError, gzip.BadGzipFile, zlib.error) as exc:
            raise VolumeFormatError(f"Invalid NRRD '{path}': {exc}") from exc

    @staticmethod
    def _read_header(stream) -> dict[str, str]:
        header_size = 0
        magic = stream.readline()
        header_size += len(magic)
        if not magic.startswith(b"NRRD000") or not magic.strip().decode("ascii", "replace")[-1:].isdigit():
            raise VolumeFormatError("Not a supported NRRD header (expected NRRD000x)")
        fields: dict[str, str] = {}
        while True:
            line = stream.readline()
            header_size += len(line)
            if header_size > _MAX_HEADER_BYTES:
                raise VolumeFormatError("NRRD header exceeds 1 MiB")
            if not line:
                raise VolumeFormatError("NRRD header is missing its blank separator line")
            if not line.strip():
                break
            if line.startswith(b"#"):
                continue
            try:
                decoded = line.decode("ascii").strip()
            except UnicodeDecodeError as exc:
                raise VolumeFormatError("NRRD metadata is not ASCII") from exc
            if ":=" in decoded:  # NRRD key/value metadata, not a structural field.
                continue
            if ":" not in decoded:
                raise VolumeFormatError(f"Malformed NRRD header field: {decoded}")
            key, value = decoded.split(":", 1)
            fields[key.strip().lower()] = value.strip()
        return fields

    @staticmethod
    def _load_data(path: Path, fields: dict[str, str], stream) -> Volume:
        try:
            if int(fields["dimension"]) != 3:
                raise VolumeFormatError("NRRD dimension must be 3")
            sizes = tuple(int(s) for s in fields["sizes"].split())
            type_name = fields["type"].strip().lower()
        except KeyError as exc:
            raise VolumeFormatError(f"Missing NRRD header field: {exc.args[0]}") from exc
        if len(sizes) != 3 or any(s < 1 or s >= 1024 for s in sizes):
            raise VolumeFormatError("NRRD sizes must contain exactly three integers in [1, 1023]")
        if type_name not in _TYPE_TO_DTYPE:
            raise VolumeFormatError(f"Unsupported NRRD voxel type: {type_name}")
        dtype = np.dtype(_TYPE_TO_DTYPE[type_name])
        if dtype.itemsize > 1:
            endian = fields.get("endian", "").lower()
            if endian not in ("little", "big"):
                raise VolumeFormatError("16-/32-bit NRRD files must specify little/big endian")
            dtype = dtype.newbyteorder("<" if endian == "little" else ">")
        encoding = fields.get("encoding", "raw").lower()
        if encoding not in ("raw", "gzip", "gz"):
            raise VolumeFormatError(f"Unsupported NRRD encoding: {encoding} (raw/gzip only)")
        if any(key in fields for key in ("byte skip", "line skip")):
            raise VolumeFormatError("NRRD byte skip / line skip are not supported")
        count = sizes[0] * sizes[1] * sizes[2]
        expected_bytes = count * dtype.itemsize
        if "data file" in fields:
            # Single-file detached payloads, relative to the .nhdr file.
            data_file = fields["data file"]
            if not data_file or data_file.startswith("LIST") or "%" in data_file:
                raise VolumeFormatError("NRRD data file lists/patterns are unsupported")
            data_path = path.parent / data_file
            try:
                with data_path.open("rb") as data_stream:
                    payload = NRRDReader._read_payload(data_stream, encoding, expected_bytes)
            except OSError as exc:
                raise VolumeFormatError(f"Cannot read detached NRRD data: {exc}") from exc
        else:
            payload = NRRDReader._read_payload(stream, encoding, expected_bytes)
        array = np.frombuffer(payload, dtype=dtype, count=count)
        # NRRD axis 0 varies fastest. M[x,y,z] MUST NOT swap axes.
        data = array.reshape(sizes, order="F")
        return Volume(data)

    @staticmethod
    def _read_payload(stream, encoding: str, expected_bytes: int) -> bytes:
        if encoding in ("gz", "gzip"):
            with gzip.GzipFile(fileobj=stream, mode="rb") as gz:
                payload = gz.read(expected_bytes + 1)
        else:
            payload = stream.read(expected_bytes + 1)
        if len(payload) != expected_bytes:
            raise VolumeFormatError(
                f"NRRD payload length mismatch: expected {expected_bytes} bytes, got {len(payload)}"
            )
        return payload
