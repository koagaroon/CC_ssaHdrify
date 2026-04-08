"""调整SSA字幕亮度。"""

from __future__ import annotations

import os
import re
from io import StringIO

import ass as ssa
import numpy as np
from charset_normalizer import from_bytes
from colour import RGB_Colourspace
from colour.models import eotf_inverse_BT2100_PQ, sRGB_to_XYZ, XYZ_to_xyY, xyY_to_XYZ, XYZ_to_RGB, \
    RGB_COLOURSPACE_BT2020, eotf_BT2100_PQ

from conversion_setting import config

COLOURSPACE_BT2100_PQ = RGB_Colourspace(
    name='COLOURSPACE_BT2100',
    primaries=RGB_COLOURSPACE_BT2020.primaries,
    whitepoint=RGB_COLOURSPACE_BT2020.whitepoint,
    matrix_RGB_to_XYZ=RGB_COLOURSPACE_BT2020.matrix_RGB_to_XYZ,
    matrix_XYZ_to_RGB=RGB_COLOURSPACE_BT2020.matrix_XYZ_to_RGB,
    cctf_encoding=eotf_inverse_BT2100_PQ,
    cctf_decoding=eotf_BT2100_PQ,
)
"""HDR color space on display side."""


def sRgbToHdr(source: tuple[int, int, int], target_brightness: int | None = None) -> tuple[int, int, int]:
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

    normalized_sdr_color = np.array(source) / 255
    xyY_sdr_color = XYZ_to_xyY(sRGB_to_XYZ(normalized_sdr_color, apply_cctf_decoding=True))

    xyY_hdr_color = xyY_sdr_color.copy()
    target_luminance = xyY_sdr_color[2] * srgb_brightness
    xyY_hdr_color[2] = target_luminance

    output = XYZ_to_RGB(xyY_to_XYZ(xyY_hdr_color), colourspace=COLOURSPACE_BT2100_PQ, apply_cctf_encoding=True)

    output = np.clip(np.round(output * 255), 0, 255)

    return (int(output[0]), int(output[1]), int(output[2]))


def transformColour(colour, target_brightness: int | None = None):
    rgb = (colour.r, colour.g, colour.b)
    transformed = sRgbToHdr(rgb, target_brightness)
    # TODO process alpha channel in styles
    colour.r = transformed[0]
    colour.g = transformed[1]
    colour.b = transformed[2]


def transformEvent(event, target_brightness: int | None = None):
    def _replaceColor(match):
        prefix = match.group(1)
        hex_colour = match.group(2)

        alpha = hex_colour[:2] if len(hex_colour) == 8 else ''
        hex_colour = hex_colour[2:] if len(hex_colour) == 8 else hex_colour
        hex_colour = hex_colour.rjust(6, '0')
        b = int(hex_colour[0:2], 16)
        g = int(hex_colour[2:4], 16)
        r = int(hex_colour[4:6], 16)

        (r, g, b) = sRgbToHdr((r, g, b), target_brightness)
        return prefix + alpha + '{:02x}{:02x}{:02x}'.format(b, g, r)

    event.text = re.sub(r'(\\[0-9]?c&H)([0-9a-fA-F]{6,8})(?=[&})\\])', _replaceColor, event.text)


def ssaProcessor(fname: str, target_brightness: int | None = None):
    if not os.path.isfile(fname):
        print(f'Missing file: {fname}')
        return

    try:
        with open(fname, 'rb') as raw_file:
            detected = from_bytes(raw_file.read())
            content = detected.best()
    except OSError as e:
        print(f'Error reading {fname}: {e}')
        return

    if content is None:
        print(f'Error: could not detect encoding for {fname}')
        return

    try:
        sub = ssa.parse(StringIO(str(content)))
    except Exception as e:
        print(f'Error parsing {fname}: {e}')
        return

    for s in sub.styles:
        transformColour(s.primary_color, target_brightness)
        transformColour(s.secondary_color, target_brightness)
        transformColour(s.outline_color, target_brightness)
        transformColour(s.back_color, target_brightness)

    for e in sub.events:
        transformEvent(e, target_brightness)

    output_fname = os.path.splitext(fname)[0] + '.hdr.ass'
    tmp_fname = output_fname + '.tmp'

    try:
        with open(tmp_fname, 'w', encoding='utf_8_sig') as f:
            sub.dump_file(f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_fname, output_fname)
        print(f'Wrote {output_fname}')
    except OSError as e:
        print(f'Error writing {output_fname}: {e}')
        if os.path.exists(tmp_fname):
            os.remove(tmp_fname)
