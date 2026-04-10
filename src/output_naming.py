"""Output filename template resolution for subtitle conversion."""

from __future__ import annotations

import os

# Preset templates shown in the UI dropdown
PRESETS: list[str] = [
    "{name}.hdr.ass",
    "{name}.{eotf}.ass",
    "{name}.hdr.{eotf}.ass",
]

DEFAULT_TEMPLATE = PRESETS[0]


def resolve_output_path(input_path: str, template: str, eotf: str) -> str:
    """Build output file path from *input_path* and a naming *template*.

    Supported template variables:
    - ``{name}``  — input filename without extension
    - ``{eotf}``  — transfer function in lowercase (``pq`` / ``hlg``)
    - ``{dir}``   — input file directory (rarely used in template, but available)

    The result is always placed in the same directory as *input_path*.
    """
    dir_name = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    # Strip secondary subtitle extensions so "movie.eng" stays but
    # "movie.hdr" or "movie.sdr" (from previous conversions) are removed.
    for tag in (".hdr", ".sdr"):
        if base_name.lower().endswith(tag):
            base_name = base_name[: -len(tag)]

    # Use str.replace() instead of str.format() to prevent attribute access
    # via malicious templates like "{name.__class__}"
    output_name = (template
                   .replace("{name}", base_name)
                   .replace("{eotf}", eotf.lower())
                   .replace("{dir}", dir_name))
    result = os.path.normpath(os.path.join(dir_name, output_name))

    # Defense-in-depth: reject templates that escape the input directory
    if dir_name and not result.startswith(os.path.normpath(dir_name)):
        raise ValueError(f"Output path escapes input directory: {result}")

    return result
