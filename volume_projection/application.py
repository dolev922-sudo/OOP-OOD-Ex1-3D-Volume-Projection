"""Dependency-injected orchestration of the projection pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .csv_reader import CSVPlaneReader
from .nrrd_reader import NRRDReader
from .projector import PlaneProjector
from .video_writer import VideoWriter


@dataclass(slots=True)
class ProjectionApplication:
    """Load, validate, determine canvas size, then stream projected frames."""

    nrrd_reader: NRRDReader = field(default_factory=NRRDReader)
    csv_reader: CSVPlaneReader = field(default_factory=CSVPlaneReader)

    def run(self, volume_path: str | Path, csv_path: str | Path,
            output_path: str | Path) -> int:
        """Create an MP4 and return the count of written frames."""
        inputs = [Path(volume_path).resolve(), Path(csv_path).resolve()]
        if Path(output_path).resolve() in inputs:
            from .exceptions import ProjectionError
            raise ProjectionError("Output path must differ from input paths")

        volume = self.nrrd_reader.load(volume_path)
        planes = self.csv_reader.load(csv_path)  # Entire CSV checked before output.
        projector = PlaneProjector(volume)
        dimensions = [projector.dimensions(plane) for plane in planes]
        target_height = max(height for height, _ in dimensions)
        target_width = max(width for _, width in dimensions)
        video = VideoWriter(output_path, target_height, target_width)

        with video.open() as writer:
            for plane in planes:
                image = projector.project(plane)
                writer.append_data(video.prepare_frame(image))
        return len(planes)
