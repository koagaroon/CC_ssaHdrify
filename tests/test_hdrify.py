"""Regression tests for SSA HDRify core conversion + SRT/SUB extension."""

import os
import re
import tempfile

from hdrify import sRgbToHdr, transformEvent, ssaProcessor, srtSubProcessor, _detect_and_decode
from converter import load_as_ass_text
from output_naming import resolve_output_path
from style_config import StyleConfig


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


def test_regex_ignores_7digit_color():
    """7-digit hex color should NOT be matched (only 6 or 8 are valid)."""
    event = FakeEvent(r"{\1c&HFFFFFFF&}Hello")
    transformEvent(event, target_brightness=100)
    assert event.text == r"{\1c&HFFFFFFF&}Hello"


# --- HLG tests ---

def test_hlg_conversion_in_range():
    """HLG conversion should produce valid RGB values."""
    result = sRgbToHdr((255, 255, 255), target_brightness=100, eotf="HLG")
    assert all(0 <= c <= 255 for c in result)


def test_hlg_differs_from_pq():
    """HLG and PQ should produce different output for same input."""
    pq = sRgbToHdr((200, 100, 50), target_brightness=100, eotf="PQ")
    hlg = sRgbToHdr((200, 100, 50), target_brightness=100, eotf="HLG")
    assert pq != hlg


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


# --- Output naming tests ---

def test_output_naming_default():
    """Default template should produce {name}.hdr.ass."""
    result = resolve_output_path("/movies/subtitle.srt", "{name}.hdr.ass", "PQ")
    assert result == os.path.normpath(os.path.join("/movies", "subtitle.hdr.ass"))


def test_output_naming_with_eotf():
    """Template with {eotf} should substitute lowercase EOTF name."""
    result = resolve_output_path("/movies/subtitle.ass", "{name}.{eotf}.ass", "HLG")
    assert result == os.path.normpath(os.path.join("/movies", "subtitle.hlg.ass"))


def test_output_naming_strips_hdr_tag():
    """Input already ending with .hdr should not produce double .hdr."""
    result = resolve_output_path("/movies/subtitle.hdr.ass", "{name}.hdr.ass", "PQ")
    assert result == os.path.normpath(os.path.join("/movies", "subtitle.hdr.ass"))


def test_output_naming_preserves_non_tag_suffix():
    """Non-tag suffix like .eng should be preserved."""
    result = resolve_output_path("/movies/subtitle.eng.srt", "{name}.hdr.ass", "PQ")
    assert result == os.path.normpath(os.path.join("/movies", "subtitle.eng.hdr.ass"))


# --- Converter tests ---

def test_converter_srt_basic():
    """SRT text should convert to valid ASS text."""
    srt_text = """\
1
00:00:01,000 --> 00:00:05,000
Hello World
"""
    ass_text = load_as_ass_text(srt_text, fmt=".srt")
    assert "[Script Info]" in ass_text
    assert "Hello World" in ass_text
    assert "[V4+ Styles]" in ass_text


def test_converter_srt_font_color():
    """SRT <font color> tags should become ASS inline color overrides."""
    srt_text = """\
1
00:00:01,000 --> 00:00:05,000
<font color="#FF0000">Red text</font>
"""
    ass_text = load_as_ass_text(srt_text, fmt=".srt")
    # pysubs2 converts <font color="#RRGGBB"> to {\1c&HBBGGRR&}
    # FF0000 (red) → 0000FF in BGR order
    assert "Red text" in ass_text
    # The color override should be present in some ASS-compatible form
    assert "\\1c&H" in ass_text or "\\c&H" in ass_text


def test_converter_srt_font_color_reset():
    """</font> should insert color reset tag, not leave trailing color."""
    srt_text = """\
1
00:00:01,000 --> 00:00:05,000
<font color="#FF0000">Red</font> normal
"""
    ass_text = load_as_ass_text(srt_text, fmt=".srt")
    # After "Red", a {\1c} reset should appear before "normal"
    assert r"{\1c}" in ass_text


def test_converter_srt_font_multi_attr():
    """<font> with multiple attributes should still extract color."""
    srt_text = """\
1
00:00:01,000 --> 00:00:05,000
<font face="Arial" color="#00FF00">Green</font>
"""
    ass_text = load_as_ass_text(srt_text, fmt=".srt")
    assert "Green" in ass_text
    assert "\\1c&H" in ass_text


def test_converter_srt_with_custom_style():
    """Custom StyleConfig should override default font/size."""
    srt_text = """\
1
00:00:01,000 --> 00:00:05,000
Styled text
"""
    cfg = StyleConfig(font_name="Noto Sans CJK", font_size=36)
    ass_text = load_as_ass_text(srt_text, fmt=".srt", style_config=cfg)
    assert "Noto Sans CJK" in ass_text
    assert ",36," in ass_text


def test_converter_sub_basic():
    """MicroDVD SUB text should convert to valid ASS text."""
    sub_text = "{0}{120}Hello from SUB\n"
    ass_text = load_as_ass_text(sub_text, fmt=".sub", fps=24.0)
    assert "[Script Info]" in ass_text
    assert "Hello from SUB" in ass_text


def test_converter_unsupported_format():
    """Unsupported format should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="Unsupported subtitle format"):
        load_as_ass_text("data", fmt=".vtt")


# --- srtSubProcessor end-to-end tests ---

def test_srt_processor_roundtrip(tmp_path):
    """SRT → HDR ASS roundtrip: input SRT, get .hdr.ass output."""
    srt_content = """\
1
00:00:01,000 --> 00:00:05,000
Hello SRT World

2
00:00:06,000 --> 00:00:10,000
Second line
"""
    input_file = tmp_path / "test.srt"
    input_file.write_bytes(b'\xef\xbb\xbf' + srt_content.encode('utf-8'))

    srtSubProcessor(str(input_file), target_brightness=100)

    output_file = tmp_path / "test.hdr.ass"
    assert output_file.exists(), "SRT conversion should produce .hdr.ass"
    output_content = output_file.read_text(encoding="utf-8-sig")
    assert "Hello SRT World" in output_content
    assert "Second line" in output_content


def test_srt_processor_with_colors(tmp_path):
    """SRT with font colors should have colors transformed to HDR."""
    srt_content = """\
1
00:00:01,000 --> 00:00:05,000
<font color="#FFFFFF">White text</font>
"""
    input_file = tmp_path / "colored.srt"
    input_file.write_bytes(b'\xef\xbb\xbf' + srt_content.encode('utf-8'))

    srtSubProcessor(str(input_file), target_brightness=100)

    output_file = tmp_path / "colored.hdr.ass"
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8-sig")
    assert "White text" in content


def test_srt_processor_custom_output_path(tmp_path):
    """srtSubProcessor should respect custom output_path."""
    srt_content = "1\n00:00:01,000 --> 00:00:05,000\nTest\n"
    input_file = tmp_path / "input.srt"
    input_file.write_bytes(b'\xef\xbb\xbf' + srt_content.encode('utf-8'))

    custom_output = str(tmp_path / "custom_name.pq.ass")
    srtSubProcessor(str(input_file), target_brightness=100, output_path=custom_output)

    assert os.path.exists(custom_output)


def test_srt_processor_missing_file(capsys):
    """Missing SRT file should print error, not crash."""
    srtSubProcessor("/nonexistent/file.srt", target_brightness=100)
    captured = capsys.readouterr()
    assert "Missing file" in captured.out


# --- _detect_and_decode tests ---

def test_detect_and_decode_utf8_bom(tmp_path):
    """UTF-8 BOM file should decode correctly."""
    content = "Hello BOM"
    f = tmp_path / "bom.txt"
    f.write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))
    result = _detect_and_decode(str(f))
    assert result is not None
    assert "Hello BOM" in result


def test_detect_and_decode_plain_utf8(tmp_path):
    """Plain UTF-8 file (no BOM) should decode via charset inference."""
    content = "Plain text content for charset detection. " * 5
    f = tmp_path / "plain.txt"
    f.write_text(content, encoding="utf-8")
    result = _detect_and_decode(str(f))
    assert result is not None
    assert "Plain text" in result


def test_detect_and_decode_file_too_large(tmp_path, capsys, monkeypatch):
    """Files exceeding the size limit should be rejected."""
    import hdrify
    monkeypatch.setattr(hdrify, '_MAX_SUBTITLE_SIZE', 100)  # 100 bytes for test
    f = tmp_path / "big.srt"
    f.write_text("x" * 200, encoding="utf-8")
    result = _detect_and_decode(str(f))
    assert result is None
    captured = capsys.readouterr()
    assert "too large" in captured.out


def test_output_naming_safe_template():
    """Template with unknown variables should pass through literally (str.replace)."""
    result = resolve_output_path("/movies/sub.srt", "{name}.{unknown}.ass", "PQ")
    # str.replace leaves {unknown} as-is since it's not a recognized variable
    assert "{unknown}" in result


def test_sub_processor_roundtrip(tmp_path):
    """SUB (MicroDVD) → HDR ASS roundtrip."""
    sub_content = "{0}{120}Hello from SUB format\n{121}{240}Second subtitle\n"
    input_file = tmp_path / "test.sub"
    input_file.write_bytes(b'\xef\xbb\xbf' + sub_content.encode('utf-8'))

    srtSubProcessor(str(input_file), target_brightness=100)

    output_file = tmp_path / "test.hdr.ass"
    assert output_file.exists(), "SUB conversion should produce .hdr.ass"
    content = output_file.read_text(encoding="utf-8-sig")
    assert "Hello from SUB format" in content
