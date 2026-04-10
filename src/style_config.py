"""Default style configuration for SRT/SUB → ASS conversion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StyleConfig:
    """Style parameters applied when converting SRT/SUB to ASS format.

    Color values use ASS format: ``&HAABBGGRR`` (hex, blue-green-red order).
    These settings are ignored for ASS/SSA input (which already has styles).
    """

    font_name: str = "Arial"
    font_size: int = 48
    primary_color: str = "&H00FFFFFF"   # white, fully opaque
    outline_color: str = "&H00000000"   # black outline
    outline_width: float = 2.0
    shadow_depth: float = 1.0
    fps: float = 23.976                 # only used for SUB (MicroDVD) format
