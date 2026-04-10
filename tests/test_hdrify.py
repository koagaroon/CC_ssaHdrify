"""Regression tests for SSA HDRify core conversion + SRT/SUB extension."""

import os
import re
import tempfile

import pytest

from conftest import make_minimal_ass
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


def test_regex_matches_comma_separated_tags():
    """Color tag followed by comma (Aegisub multi-tag syntax) should be transformed."""
    event = FakeEvent(r"{\1c&HFFFFFF,\blur3}Hello")
    transformEvent(event, target_brightness=100)
    # Color should be transformed (not left as FFFFFF)
    assert r"\1c&H" in event.text
    assert "Hello" in event.text
    assert "FFFFFF" not in event.text.upper().replace("\\1C&H", "")


def test_transform_event_none_text():
    """Event with text=None (e.g. comment line) should not crash."""
    event = FakeEvent(None)
    transformEvent(event, target_brightness=100)
    assert event.text is None


def test_transform_event_empty_text():
    """Event with empty string text should pass through without error."""
    event = FakeEvent("")
    transformEvent(event, target_brightness=100)
    assert event.text == ""


# --- ssaProcessor tests ---

def test_processor_missing_file(capsys):
    """Missing file should print error, not crash."""
    ssaProcessor("/nonexistent/file.ass", target_brightness=100)
    captured = capsys.readouterr()
    assert "Missing file" in captured.out


def test_processor_roundtrip(tmp_path):
    """End-to-end: write a minimal ASS file, process it, verify output exists."""
    input_file = tmp_path / "test.ass"
    input_file.write_text(make_minimal_ass("Hello World"), encoding="utf-8")

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


# --- Path traversal / output naming regression tests ---

def test_output_naming_rejects_path_traversal():
    """Template with ../ should raise ValueError."""
    with pytest.raises(ValueError, match="escapes input directory"):
        resolve_output_path("/movies/sub/file.srt", "../escape/{name}.ass", "PQ")


def test_output_naming_rejects_prefix_ambiguity():
    """Path that escapes via prefix collision should be caught."""
    with pytest.raises(ValueError, match="escapes input directory"):
        resolve_output_path("/movies/sub/file.srt", "../subtitles/{name}.ass", "PQ")


def test_output_naming_rejects_traversal_relative_input():
    """Relative input path with ../ template should be caught."""
    with pytest.raises(ValueError, match="escapes input directory"):
        resolve_output_path("subtitle.srt", "../escape/{name}.ass", "PQ")


def test_output_naming_rejects_empty_template():
    """Empty template should raise ValueError."""
    with pytest.raises(ValueError, match="empty filename"):
        resolve_output_path("/movies/subtitle.srt", "", "PQ")


def test_output_naming_strips_stacked_tags():
    """Stacked .hdr.sdr tags should both be stripped."""
    result = resolve_output_path("/movies/subtitle.hdr.sdr.ass", "{name}.hdr.ass", "PQ")
    assert "subtitle.hdr.ass" in result
    assert "subtitle.hdr.hdr.ass" not in result


def test_output_naming_rejects_windows_reserved(monkeypatch):
    """Windows reserved names (CON, NUL, etc.) should raise ValueError."""
    monkeypatch.setattr("output_naming.platform.system", lambda: "Windows")
    with pytest.raises(ValueError, match="Windows reserved name"):
        resolve_output_path("/movies/subtitle.srt", "CON.ass", "PQ")


def test_output_naming_rejects_conin_dollar(monkeypatch):
    """CONIN$ and CONOUT$ are also reserved Windows device names."""
    monkeypatch.setattr("output_naming.platform.system", lambda: "Windows")
    with pytest.raises(ValueError, match="Windows reserved name"):
        resolve_output_path("/movies/subtitle.srt", "CONIN$.ass", "PQ")


def test_output_naming_rejects_trailing_dot_space(monkeypatch):
    """Windows strips trailing dots/spaces — 'CON .ass' equals 'CON.ass'."""
    monkeypatch.setattr("output_naming.platform.system", lambda: "Windows")
    with pytest.raises(ValueError, match="Windows reserved name"):
        resolve_output_path("/movies/subtitle.srt", "CON .ass", "PQ")


def test_processor_skips_self_overwrite(tmp_path, capsys):
    """Processing should skip when output would overwrite input."""
    input_file = tmp_path / "test.ass"
    input_file.write_text(make_minimal_ass("Hello World"), encoding="utf-8")
    original_content = input_file.read_text(encoding="utf-8")

    ssaProcessor(str(input_file), target_brightness=100,
                 output_path=str(input_file))

    captured = capsys.readouterr()
    assert "overwrite" in captured.out.lower()
    assert input_file.read_text(encoding="utf-8") == original_content


def test_detect_and_decode_utf32_le_bom(tmp_path):
    """UTF-32-LE BOM file should not be misdetected as UTF-16."""
    content = "[Script Info]\nScriptType: v4.00+"
    bom = b'\xff\xfe\x00\x00'
    encoded = content.encode('utf-32-le')
    f = tmp_path / "utf32le.txt"
    f.write_bytes(bom + encoded)
    result = _detect_and_decode(str(f))
    assert result is not None
    assert "Script Info" in result


# --- sRgbToHdr validation tests ---

def test_srgb_to_hdr_invalid_brightness():
    """Passing brightness <= 0 should raise ValueError, not silently return black."""
    with pytest.raises(ValueError, match="target_brightness must be positive"):
        sRgbToHdr((128, 128, 128), target_brightness=0)


# --- Cancel event tests ---

def test_processor_cancel_mid_conversion(tmp_path):
    """Setting cancel_event should stop processing and not produce output."""
    import threading
    input_file = tmp_path / "test.ass"
    input_file.write_text(make_minimal_ass("Cancel Test"), encoding="utf-8")
    cancel = threading.Event()
    cancel.set()  # pre-cancelled
    ssaProcessor(str(input_file), target_brightness=100, cancel_event=cancel)
    output_file = tmp_path / "test.hdr.ass"
    assert not output_file.exists(), "Cancelled conversion should not produce output"


# --- Write fallback tests ---

def test_write_ass_output_cross_device_fallback(tmp_path, monkeypatch):
    """When os.replace raises OSError, shutil.copy2 fallback should work."""
    import ass as ass_lib
    input_file = tmp_path / "test.ass"
    input_file.write_text(make_minimal_ass("Fallback Test"), encoding="utf-8")
    with open(str(input_file), encoding="utf_8_sig") as f:
        sub = ass_lib.parse(f)
    # Force os.replace to fail
    def _fake_replace(src, dst): raise OSError("fake cross-device")
    monkeypatch.setattr("os.replace", _fake_replace)
    from hdrify import _write_ass_output
    output_file = tmp_path / "output.ass"
    _write_ass_output(sub, str(output_file))
    assert output_file.exists(), "Fallback write should produce output"
    content = output_file.read_text(encoding="utf-8-sig")
    assert "Fallback Test" in content


# --- HLG end-to-end tests ---

def test_processor_roundtrip_hlg(tmp_path):
    """End-to-end: write a minimal ASS file, process with HLG EOTF, verify output exists."""
    input_file = tmp_path / "test.ass"
    input_file.write_text(make_minimal_ass("Hello HLG World"), encoding="utf-8")

    ssaProcessor(str(input_file), target_brightness=100, eotf="HLG")

    output_file = tmp_path / "test.hdr.ass"
    assert output_file.exists(), "Output .hdr.ass file should be created for HLG"
    output_content = output_file.read_text(encoding="utf-8-sig")
    assert "Hello HLG World" in output_content


# --- Encoding detection tests (extended) ---

def test_detect_and_decode_gbk(tmp_path):
    """GBK-encoded ASS file (no BOM) should be detected and decoded correctly.

    CJK encodings are in the safe_encodings set so they bypass the coherence
    threshold (charset_normalizer gives inherently low coherence for CJK).
    Needs enough Chinese text for charset_normalizer to identify gb18030.
    """
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,\u5fae\u8f6f\u96c5\u9ed1,48,&H00FFFFFF,&H000000FF,"
        "&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    zh_dialogues = [
        "\u4eca\u5929\u7684\u5929\u6c14\u771f\u597d\uff0c\u6211\u4eec\u51fa\u53bb\u8d70\u8d70\u5427",
        "\u8fd9\u90e8\u7535\u5f71\u7684\u753b\u9762\u8d28\u91cf\u975e\u5e38\u51fa\u8272\uff0c\u5c24\u5176\u662f\u8272\u5f69\u8868\u73b0",
        "\u5b57\u5e55\u7ec4\u8f9b\u82e6\u4e86\uff0c\u611f\u8c22\u4f60\u4eec\u7684\u4ed8\u51fa",
        "\u8bf7\u786e\u8ba4\u5b57\u5e55\u663e\u793a\u662f\u5426\u6b63\u5e38\uff0c\u5982\u6709\u95ee\u9898\u8bf7\u53cd\u9988",
        "\u4e0b\u4e00\u96c6\u66f4\u52a0\u7cbe\u5f69\uff0c\u656c\u8bf7\u671f\u5f85",
        "\u8fd9\u662f\u4e00\u6bb5\u7528\u4e8e\u6d4b\u8bd5\u7f16\u7801\u68c0\u6d4b\u7684\u4e2d\u6587\u5b57\u5e55\u6587\u672c",
        "\u652f\u6301\u7b80\u4f53\u4e2d\u6587\u548c\u7e41\u4f53\u4e2d\u6587\u7684\u7f16\u7801\u8f6c\u6362",
        "\u9ad8\u52a8\u6001\u8303\u56f4\u5b57\u5e55\u8272\u5f69\u7a7a\u95f4\u8f6c\u6362\u5de5\u5177",
    ]
    for i, text in enumerate(zh_dialogues):
        start = f"0:{i:02d}:00.00"
        end = f"0:{i:02d}:05.00"
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
    content = "\n".join(lines) + "\n"
    f = tmp_path / "gbk.ass"
    f.write_bytes(content.encode("gbk"))
    result = _detect_and_decode(str(f))
    assert result is not None, "GBK file should decode successfully"
    assert "Script Info" in result
    assert "\u4e2d\u6587" in result
