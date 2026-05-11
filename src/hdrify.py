"""调整SSA字幕亮度。"""

from __future__ import annotations

import os
import re
import tempfile
import warnings
from io import StringIO

# Suppress colour-science optional dependency warnings (scipy, matplotlib not needed)
warnings.filterwarnings("ignore", message=".*related API features are not available.*")
# Suppress numpy RuntimeWarning from HLG transfer function boundary (np.log on edge values)
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*invalid value encountered in log.*")

import ass as ssa
import numpy as np
from charset_normalizer import from_bytes
from colour import RGB_Colourspace
from colour.models import (
    eotf_inverse_BT2100_PQ, eotf_BT2100_PQ,
    eotf_inverse_BT2100_HLG, eotf_BT2100_HLG,
    sRGB_to_XYZ, XYZ_to_xyY, xyY_to_XYZ, XYZ_to_RGB,
    RGB_COLOURSPACE_BT2020,
)

import i18n
from conversion_setting import config

COLOURSPACE_BT2100_PQ = RGB_Colourspace(
    name='COLOURSPACE_BT2100_PQ',
    primaries=RGB_COLOURSPACE_BT2020.primaries,
    whitepoint=RGB_COLOURSPACE_BT2020.whitepoint,
    matrix_RGB_to_XYZ=RGB_COLOURSPACE_BT2020.matrix_RGB_to_XYZ,
    matrix_XYZ_to_RGB=RGB_COLOURSPACE_BT2020.matrix_XYZ_to_RGB,
    cctf_encoding=eotf_inverse_BT2100_PQ,
    cctf_decoding=eotf_BT2100_PQ,
)
"""HDR color space — PQ (Perceptual Quantizer, ST 2084)."""

COLOURSPACE_BT2100_HLG = RGB_Colourspace(
    name='COLOURSPACE_BT2100_HLG',
    primaries=RGB_COLOURSPACE_BT2020.primaries,
    whitepoint=RGB_COLOURSPACE_BT2020.whitepoint,
    matrix_RGB_to_XYZ=RGB_COLOURSPACE_BT2020.matrix_RGB_to_XYZ,
    matrix_XYZ_to_RGB=RGB_COLOURSPACE_BT2020.matrix_XYZ_to_RGB,
    cctf_encoding=eotf_inverse_BT2100_HLG,
    cctf_decoding=eotf_BT2100_HLG,
)
"""HDR color space — HLG (Hybrid Log-Gamma, ARIB STD-B67)."""

_COLOURSPACES = {"PQ": COLOURSPACE_BT2100_PQ, "HLG": COLOURSPACE_BT2100_HLG}


def sRgbToHdr(source: tuple[int, int, int], target_brightness: int | None = None, eotf: str = "PQ") -> tuple[int, int, int]:
    """
    Convert RGB color in SDR color space to HDR color space.

    How it works:
     1. Convert the RGB color to reference xyY color space to get absolute chromaticity and linear luminance response
     2. Time the target brightness of SDR color space to the Y because Rec.2100 has an absolute luminance
     3. Convert the xyY color back to RGB under Rec.2100/Rec.2020 color space.

    Notes:
     -  Unlike sRGB and Rec.709 color space which have their OOTF(E) = EOTF(OETF(E)) equals or almost equals to y = x,
        it's OOTF is something close to gamma 2.4. Therefore, to have matched display color for color in SDR color space
        the COLOURSPACE_BT2100_PQ denotes a display color space rather than a scene color space. It wasted me quite some
        time to figure that out :(
     -  Option to set output luminance is removed because PQ has an absolute luminance level, which means any color in
        the Rec.2100 color space will be displayed the same on any accurate display regardless of the capable peak
        brightness of the device if no clipping happens. Therefore, the peak brightness should always target 10000 nits
        so the SDR color can be accurately projected to the sub-range of Rec.2100 color space
    args:
    colour -- (0-255, 0-255, 0-255)
    """
    if source == (0, 0, 0):
        return (0, 0, 0)

    srgb_brightness = target_brightness if target_brightness is not None else config.targetBrightness
    if srgb_brightness <= 0:
        raise ValueError(f"target_brightness must be positive, got {srgb_brightness}")

    normalized_sdr_color = np.array(source) / 255
    xyY_sdr_color = XYZ_to_xyY(sRGB_to_XYZ(normalized_sdr_color, apply_cctf_decoding=True))

    if xyY_sdr_color[2] <= 0:
        return (0, 0, 0)

    xyY_hdr_color = xyY_sdr_color.copy()
    target_luminance = xyY_sdr_color[2] * srgb_brightness
    xyY_hdr_color[2] = target_luminance

    colourspace = _COLOURSPACES.get(eotf.upper(), COLOURSPACE_BT2100_PQ)
    output = XYZ_to_RGB(xyY_to_XYZ(xyY_hdr_color), colourspace=colourspace, apply_cctf_encoding=True)

    if np.any(np.isnan(output)):
        return (0, 0, 0)

    output = np.clip(np.round(output * 255), 0, 255)

    return (int(output[0]), int(output[1]), int(output[2]))


def transformColour(colour, target_brightness: int | None = None, eotf: str = "PQ"):
    rgb = (colour.r, colour.g, colour.b)
    transformed = sRgbToHdr(rgb, target_brightness, eotf=eotf)
    # TODO process alpha channel in styles
    colour.r = transformed[0]
    colour.g = transformed[1]
    colour.b = transformed[2]


def transformEvent(event, target_brightness: int | None = None, eotf: str = "PQ"):
    if event.text is None:
        return

    def _replaceColor(match):
        prefix = match.group(1)
        hex_colour = match.group(2)

        alpha = hex_colour[:2] if len(hex_colour) == 8 else ''
        hex_colour = hex_colour[2:] if len(hex_colour) == 8 else hex_colour
        hex_colour = hex_colour.rjust(6, '0')
        b = int(hex_colour[0:2], 16)
        g = int(hex_colour[2:4], 16)
        r = int(hex_colour[4:6], 16)

        (r, g, b) = sRgbToHdr((r, g, b), target_brightness, eotf=eotf)
        return prefix + alpha + '{:02x}{:02x}{:02x}'.format(b, g, r)

    event.text = re.sub(r'(\\[0-9]?c&H)([0-9a-fA-F]{6}|[0-9a-fA-F]{8})(?=[&}),\\])', _replaceColor, event.text)


_MAX_SUBTITLE_SIZE = 50 * 1024 * 1024  # 50 MB — generous for any real subtitle


def _detect_and_decode(fname: str) -> str | None:
    """Read *fname* as raw bytes and decode using BOM detection + charset inference.

    Returns decoded text on success, or ``None`` on failure (error printed to stdout).
    Reused by both ``ssaProcessor`` and ``srtSubProcessor``.
    """
    # Guard against adversarial multi-GB files that would exhaust memory
    try:
        file_size = os.path.getsize(fname)
    except OSError as e:
        print(i18n.get("msg_read_error").format(fname, e))
        return None
    if file_size > _MAX_SUBTITLE_SIZE:
        print(i18n.get("msg_file_too_large").format(fname, file_size))
        return None

    try:
        with open(fname, 'rb') as raw_file:
            raw_data = raw_file.read()
    except OSError as e:
        print(i18n.get("msg_read_error").format(fname, e))
        return None

    # Double-check after read to close TOCTOU gap (file could be swapped after getsize)
    if len(raw_data) > _MAX_SUBTITLE_SIZE:
        print(i18n.get("msg_file_too_large").format(fname, len(raw_data)))
        return None

    # Explicit BOM detection — bypasses statistical inference when BOM is present
    bom_encoding = None
    if raw_data[:3] == b'\xef\xbb\xbf':
        bom_encoding = 'utf-8-sig'
    elif raw_data[:4] == b'\xff\xfe\x00\x00':
        bom_encoding = 'utf-32-le'
    elif raw_data[:4] == b'\x00\x00\xfe\xff':
        bom_encoding = 'utf-32-be'
    elif raw_data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        bom_encoding = 'utf-16'

    if bom_encoding:
        try:
            decoded_text = raw_data.decode(bom_encoding)
        except (UnicodeDecodeError, LookupError) as e:
            print(i18n.get("msg_decode_error").format(fname, bom_encoding, e))
            return None
    else:
        detected = from_bytes(raw_data)
        content = detected.best()
        if content is None:
            print(i18n.get("msg_detect_encoding_fail").format(fname))
            return None
        # ASCII/UTF-8 and Chinese CJK encodings are unambiguous —
        # only reject low coherence for encodings where mis-detection could
        # reinterpret bytes dangerously.
        # Note: .replace("-", "_") normalizes encoding names before lookup.
        safe_encodings = {
            "ascii", "utf_8",
            "gb18030", "gb2312", "gbk",
            "big5",
        }
        if content.coherence < 0.5 and content.encoding.lower().replace("-", "_") not in safe_encodings:
            print(i18n.get("msg_low_confidence").format(fname, content.encoding, f"{content.coherence:.1%}"))
            return None
        decoded_text = str(content)

    return decoded_text


def _write_ass_output(sub, output_fname: str):
    """Write parsed ASS document to *output_fname* atomically (temp + replace)."""
    output_dir = os.path.dirname(os.path.abspath(output_fname))
    tmp_fname = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf_8_sig', newline='\n',
            dir=output_dir, prefix='.tmp_', suffix='.ass', delete=False
        ) as f:
            tmp_fname = f.name
            sub.dump_file(f)
            f.flush()
            os.fsync(f.fileno())
        # No EXDEV fallback: tmp file is created in output_dir (line above), so
        # cross-device rename literally cannot happen. The previous broad
        # `except OSError → shutil.copy2()` fallback caught permission/lock
        # errors AND silently switched from atomic os.replace (which replaces
        # the path in place) to symlink-following copy semantics. If the
        # destination path were a symlink to a file outside the subtitle
        # directory (placed by an attacker or accidentally by the user), the
        # fallback would have written ASS content through the symlink,
        # bypassing the path-containment check that resolved the original
        # output path. Letting OSError propagate keeps the operation atomic
        # (caller sees a clear write error, original destination unchanged).
        os.replace(tmp_fname, output_fname)
        print(i18n.get("msg_wrote").format(output_fname))
    except Exception as e:
        print(i18n.get("msg_write_error").format(output_fname, e))
        if tmp_fname is not None and os.path.exists(tmp_fname):
            try:
                os.remove(tmp_fname)
            except OSError:
                pass
        raise


def _transform_and_write(sub, fname: str, target_brightness: int | None,
                         eotf: str, output_path: str | None, cancel_event) -> None:
    """Apply HDR color transform to parsed ASS document and write output.

    Shared pipeline for both ASS/SSA and SRT/SUB processing paths.
    """
    for s in sub.styles:
        if cancel_event is not None and cancel_event.is_set():
            print(i18n.get("cancelled"))
            return
        transformColour(s.primary_color, target_brightness, eotf=eotf)
        transformColour(s.secondary_color, target_brightness, eotf=eotf)
        transformColour(s.outline_color, target_brightness, eotf=eotf)
        transformColour(s.back_color, target_brightness, eotf=eotf)

    for e in sub.events:
        if cancel_event is not None and cancel_event.is_set():
            print(i18n.get("cancelled"))
            return
        transformEvent(e, target_brightness, eotf=eotf)

    output_fname = output_path if output_path is not None else os.path.splitext(fname)[0] + '.hdr.ass'
    if os.path.normcase(os.path.normpath(os.path.abspath(output_fname))) == os.path.normcase(os.path.normpath(os.path.abspath(fname))):
        print(i18n.get("msg_overwrite_self").format(fname))
        return
    _write_ass_output(sub, output_fname)


def ssaProcessor(fname: str, target_brightness: int | None = None, eotf: str = "PQ",
                 output_path: str | None = None, cancel_event=None):
    """Process an ASS/SSA file: convert all colors to HDR and write output."""
    if not os.path.isfile(fname):
        print(i18n.get("msg_missing_file").format(fname))
        return

    decoded_text = _detect_and_decode(fname)
    if decoded_text is None:
        return

    try:
        sub = ssa.parse(StringIO(decoded_text))
    except Exception as e:
        print(i18n.get("msg_parse_error").format(fname, e))
        return

    try:
        _transform_and_write(sub, fname, target_brightness, eotf, output_path, cancel_event)
    except Exception as e:
        print(i18n.get("msg_convert_error").format(fname, e))


def srtSubProcessor(fname: str, target_brightness: int | None = None, eotf: str = "PQ",
                    output_path: str | None = None, style_config=None, cancel_event=None):
    """Process an SRT/SUB file: convert to ASS via pysubs2, then apply HDR colors.

    Uses ``converter.load_as_ass_text()`` to bridge SRT/SUB → ASS text,
    then feeds into the same ``ass.parse()`` + color transform pipeline.
    """
    if not os.path.isfile(fname):
        print(i18n.get("msg_missing_file").format(fname))
        return

    decoded_text = _detect_and_decode(fname)
    if decoded_text is None:
        return

    from converter import load_as_ass_text

    ext = os.path.splitext(fname)[1].lower()
    fps = style_config.fps if style_config else 23.976

    try:
        ass_text = load_as_ass_text(decoded_text, fmt=ext, style_config=style_config, fps=fps)
    except Exception as e:
        print(i18n.get("msg_convert_error").format(fname, e))
        return

    try:
        sub = ssa.parse(StringIO(ass_text))
    except Exception as e:
        print(i18n.get("msg_parse_error").format(fname, e))
        return

    try:
        _transform_and_write(sub, fname, target_brightness, eotf, output_path, cancel_event)
    except Exception as e:
        print(i18n.get("msg_convert_error").format(fname, e))
