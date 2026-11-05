"""Predictable domain exceptions for all user-facing failures."""


class ProjectionError(Exception):
    """Base exception for input, geometry, projection, or output failures."""


class VolumeFormatError(ProjectionError):
    """Invalid or unsupported NRRD volume."""


class PlaneFormatError(ProjectionError):
    """Malformed CSV or coordinate data."""


class InvalidPlaneError(ProjectionError):
    """Plane geometry does not meet the assignment constraints."""


class VideoEncodingError(ProjectionError):
    """Failed to create a valid MP4 file."""
