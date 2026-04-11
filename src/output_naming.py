"""Output filename template resolution for subtitle conversion."""

from __future__ import annotations

import os
import platform

# Windows reserved device names (case-insensitive, with or without extension)
_WIN_RESERVED = frozenset({
    "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
})

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
    changed = True
    while changed:
        changed = False
        for tag in (".hdr", ".sdr"):
            if base_name.lower().endswith(tag):
                base_name = base_name[: -len(tag)]
                changed = True

    # Use str.replace() instead of str.format() to prevent attribute access
    # via malicious templates like "{name.__class__}"
    output_name = (template
                   .replace("{name}", base_name)
                   .replace("{eotf}", eotf.lower())
                   .replace("{dir}", dir_name))

    if not os.path.basename(output_name):
        raise ValueError("Template resolves to empty filename")

    # Reject Windows reserved device names (CON.ass, NUL.ass, etc.)
    # Windows silently strips trailing dots and spaces from filenames,
    # so "CON .ass" and "CON..ass" are equivalent to "CON.ass".
    if platform.system() == "Windows":
        stem = os.path.splitext(os.path.basename(output_name))[0].rstrip(". ").upper()
        if stem in _WIN_RESERVED:
            raise ValueError(f"Output filename is a Windows reserved name: {stem}")

    result = os.path.normpath(os.path.join(dir_name, output_name))

    # Defense-in-depth: reject templates that escape the input directory
    # normcase needed on Windows where filesystem is case-insensitive
    safe_dir = os.path.normcase(os.path.normpath(os.path.abspath(dir_name if dir_name else ".")))
    result_abs = os.path.normcase(os.path.normpath(os.path.abspath(result)))
    if not (result_abs + os.sep).startswith(safe_dir + os.sep):
        raise ValueError(f"Output path escapes input directory: {result}")

    return result
