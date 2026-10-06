"""hh2d: dựng video hoạt hình 2D vẽ tay từ kịch bản Python."""
from .doodles import DOODLES, doodle
from .draw import INK, RED, WHITE, YELLOW
from .scene import Actor, Cam, Scene

__all__ = ["Actor", "Cam", "Scene", "doodle", "DOODLES", "INK", "RED", "WHITE", "YELLOW"]
