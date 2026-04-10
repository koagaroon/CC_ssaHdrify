"""Bridge layer: load SRT/SUB subtitle text and produce ASS-formatted text.

The output feeds directly into ``ass.parse()`` so the existing HDR color
transform pipeline works without modification.
"""

from __future__ import annotations

import re

import pysubs2

from style_config import StyleConfig

# Map file extensions to pysubs2 format identifiers
_FORMAT_MAP: dict[str, str] = {
    ".srt": "srt",
    ".sub": "microdvd",
}


def _parse_ass_color(ass_color: str) -> pysubs2.Color:
    """Parse ASS color string ``&HAABBGGRR`` into a pysubs2 Color.

    ASS color byte order is reversed: ``&H<alpha><blue><green><red>``.
    Alpha: 00 = opaque, FF = transparent.
    """
    s = ass_color.lstrip("&Hh").rjust(8, "0")
    a = int(s[0:2], 16)
    b = int(s[2:4], 16)
    g = int(s[4:6], 16)
    r = int(s[6:8], 16)
    return pysubs2.Color(r=r, g=g, b=b, a=a)


def _apply_style(subs: pysubs2.SSAFile, cfg: StyleConfig) -> None:
    """Override the default style in *subs* with values from *cfg*."""
    if "Default" not in subs.styles:
        subs.styles["Default"] = pysubs2.SSAStyle()

    style = subs.styles["Default"]
    style.fontname = cfg.font_name
    style.fontsize = cfg.font_size
    style.primarycolor = _parse_ass_color(cfg.primary_color)
    style.outlinecolor = _parse_ass_color(cfg.outline_color)
    style.outlinewidth = cfg.outline_width
    style.shadow = cfg.shadow_depth


def _preprocess_srt_colors(text: str) -> str:
    r"""Convert SRT ``<font color="#RRGGBB">`` to ASS inline ``{\1c&HBBGGRR&}``.

    pysubs2 strips HTML ``<font>`` tags during SRT parsing, losing inline
    color information.  By converting them to ASS override syntax *before*
    parsing, pysubs2 preserves the tags and ``transformEvent`` can process
    them in the HDR pipeline.
    """
    def _replace(m: re.Match) -> str:
        hex_rgb = m.group(1)
        r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
        return r'{\1c&H' + b + g + r + '&}'

    text = re.sub(r'<font\b[^>]*\bcolor="?#([0-9a-fA-F]{6})"?[^>]*>', _replace, text, flags=re.IGNORECASE)
    text = re.sub(r'</font>', r'{\\1c}', text, flags=re.IGNORECASE)
    return text


def load_as_ass_text(
    text: str,
    fmt: str,
    style_config: StyleConfig | None = None,
    fps: float = 23.976,
) -> str:
    """Convert decoded subtitle *text* (SRT or SUB) into ASS-formatted text.

    Parameters
    ----------
    text:
        Already-decoded subtitle content (from ``_detect_and_decode``).
    fmt:
        File extension including the dot, e.g. ``".srt"`` or ``".sub"``.
    style_config:
        Optional style overrides for the generated ASS.  If ``None``,
        ``StyleConfig`` defaults are used.
    fps:
        Frames per second — only meaningful for SUB (MicroDVD) format.

    Returns
    -------
    str
        Complete ASS document as text, ready for ``ass.parse(StringIO(...))``.
    """
    pysubs2_fmt = _FORMAT_MAP.get(fmt.lower())
    if pysubs2_fmt is None:
        raise ValueError(f"Unsupported subtitle format: {fmt}")

    if pysubs2_fmt == "srt":
        text = _preprocess_srt_colors(text)

    kwargs: dict = {"format_": pysubs2_fmt}
    if pysubs2_fmt == "microdvd":
        kwargs["fps"] = fps

    subs = pysubs2.SSAFile.from_string(text, **kwargs)

    cfg = style_config or StyleConfig()
    _apply_style(subs, cfg)

    return subs.to_string("ass")
