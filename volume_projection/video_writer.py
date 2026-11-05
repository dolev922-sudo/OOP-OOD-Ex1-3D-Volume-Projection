"""Streaming grayscale-to-H.264 video adapter with deterministic padding."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator

import imageio.v2 as imageio
import numpy as np

from .exceptions import VideoEncodingError

VIDEO_FPS = 10  # Playback speed, distinct from benchmark processing throughput.


class VideoWriter:
    """Encode frames as MP4/H.264 with black centering (no geometric resize)."""

    def __init__(self, output_path: str | Path, max_height: int, max_width: int,
                 fps: int = VIDEO_FPS) -> None:
        self.output_path = Path(output_path)
        if self.output_path.suffix.lower() != ".mp4":
            raise VideoEncodingError("Output file must end with .mp4")
        if min(max_height, max_width) < 1 or fps < 1:
            raise VideoEncodingError("Video dimensions and fps must be positive")
        self.height = max_height + max_height % 2
        self.width = max_width + max_width % 2
        self.fps = fps

    @staticmethod
    def to_uint8(image: np.ndarray) -> np.ndarray:
        """Map supported voxel ranges to visible grayscale values.

        Unsigned values drop low bits. Signed int16 values are offset from
        [-32768, 32767] to [0, 65535] before dropping low bits. If a signed
        frame contains only non-negative values, zero is treated as the
        background and the frame's actual range is stretched to 0..255.
        """
        if image.dtype.kind == "u" and image.dtype.itemsize in (1, 2, 4):
            shift = (image.dtype.itemsize - 1) * 8
            return (image >> shift).astype(np.uint8, copy=False)
        if image.dtype.kind == "i" and image.dtype.itemsize == 2:
            if image.size and image.min() >= 0:
                maximum = int(image.max())
                if maximum == 0:
                    return np.zeros_like(image, dtype=np.uint8)
                return np.rint(image.astype(np.float32) * 255 / maximum).astype(np.uint8)
            return ((image.astype(np.int32) + 32768) >> 8).astype(np.uint8)
        raise VideoEncodingError(
            "Frames must contain unsigned 8-/16-/32-bit or signed 16-bit values"
        )

    def prepare_frame(self, image: np.ndarray) -> np.ndarray:
        """Center a 2-D projected image within a common even-sized canvas."""
        if image.ndim != 2 or image.shape[0] > self.height or image.shape[1] > self.width:
            raise VideoEncodingError("Frame is not a 2-D image fitting the video canvas")
        gray = self.to_uint8(image)
        result = np.zeros((self.height, self.width), dtype=np.uint8)
        top = (self.height - image.shape[0]) // 2
        left = (self.width - image.shape[1]) // 2
        result[top:top + image.shape[0], left:left + image.shape[1]] = gray
        return result

    @contextmanager
    def open(self) -> Iterator[object]:
        """Atomically publish a completed file; remove partial MP4 on error."""
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(prefix=f".{self.output_path.stem}-", suffix=".mp4",
                                    dir=self.output_path.parent, delete=False) as tmp:
                temporary = Path(tmp.name)
            # `macro_block_size=None` preserves exact even dimensions.
            with imageio.get_writer(str(temporary), format="FFMPEG", mode="I",
                                    fps=self.fps, codec="libx264", pixelformat="yuv420p",
                                    macro_block_size=None, ffmpeg_log_level="error",
                                    quality=8) as writer:
                yield writer
            temporary.replace(self.output_path)
        except Exception as exc:
            if isinstance(exc, VideoEncodingError):
                raise
            raise VideoEncodingError(f"Failed to create MP4: {exc}") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
