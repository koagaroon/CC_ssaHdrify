"""Minimal regression tests for SSA HDRify core conversion logic."""

import os
import re
import tempfile

from hdrify import sRgbToHdr, transformEvent, ssaProcessor


# --- Color conversion tests ---

def test_black_passthrough():
    """Black (0,0,0) should always map to black."""
    assert sRgbToHdr((0, 0, 0), target_brightness=100) == (0, 0, 0)


def test_white_conversion_in_range():
    """White should produce valid HDR values within 0-255."""
    r, g, b = sRgbToHdr((255, 255, 255), target_brightness=100)
    assert 0 <= r <= 255
    assert 0 <= g <= 255
    assert 0 <= b <= 255


def test_conversion_deterministic():
    """Same input should always produce the same output."""
    a = sRgbToHdr((128, 64, 200), target_brightness=100)
    b = sRgbToHdr((128, 64, 200), target_brightness=100)
    assert a == b


def test_brightness_affects_output():
    """Different brightness values should produce different outputs."""
    low = sRgbToHdr((200, 200, 200), target_brightness=50)
    high = sRgbToHdr((200, 200, 200), target_brightness=200)
    assert low != high


# --- Regex / event transform tests ---

class FakeEvent:
    def __init__(self, text):
        self.text = text


def test_regex_matches_6digit_color():
    """6-digit hex color in ASS override tag should be transformed."""
    event = FakeEvent(r"{\1c&HFFFFFF&}Hello")
    transformEvent(event, target_brightness=100)
    assert event.text != r"{\1c&HFFFFFF&}Hello"
    assert r"\1c&H" in event.text


def test_regex_matches_8digit_color():
    """8-digit hex color (with alpha) should be transformed."""
    event = FakeEvent(r"{\1c&H00FFFFFF&}Hello")
    transformEvent(event, target_brightness=100)
    assert event.text != r"{\1c&H00FFFFFF&}Hello"


def test_regex_ignores_short_color():
    """Colors shorter than 6 hex digits should NOT be matched."""
    event = FakeEvent(r"{\1c&HFF&}Hello")
    transformEvent(event, target_brightness=100)
    assert event.text == r"{\1c&HFF&}Hello"


def test_no_color_tags_unchanged():
    """Text without color tags should pass through unchanged."""
    event = FakeEvent(r"{\b1}No colors here")
    transformEvent(event, target_brightness=100)
    assert event.text == r"{\b1}No colors here"


# --- ssaProcessor tests ---

def test_processor_missing_file(capsys):
    """Missing file should print error, not crash."""
    ssaProcessor("/nonexistent/file.ass", target_brightness=100)
    captured = capsys.readouterr()
    assert "Missing file" in captured.out


def test_processor_roundtrip(tmp_path):
    """End-to-end: write a minimal ASS file, process it, verify output exists."""
    minimal_ass = """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Hello World
"""
    input_file = tmp_path / "test.ass"
    input_file.write_text(minimal_ass, encoding="utf-8")

    ssaProcessor(str(input_file), target_brightness=100)

    output_file = tmp_path / "test.hdr.ass"
    assert output_file.exists(), "Output .hdr.ass file should be created"
    output_content = output_file.read_text(encoding="utf-8-sig")
    assert "Hello World" in output_content
