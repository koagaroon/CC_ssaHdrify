import sys
import os
import warnings

import pytest

# Add src/ to Python path so tests can import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Suppress known harmless warnings from colour-science library
warnings.filterwarnings("ignore", message=".*related API features are not available.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*invalid value encountered in log.*")


def make_minimal_ass(dialogue_text: str = "Hello World") -> str:
    """Build a minimal valid ASS file string with the given dialogue text."""
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
        "0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        f"Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{dialogue_text}\n"
    )


@pytest.fixture(autouse=True)
def force_english_locale(monkeypatch):
    """Ensure tests always run in English regardless of system locale."""
    import i18n
    # Prevent tests from writing to the real config file
    monkeypatch.setattr(i18n, "_save_config", lambda data: None)
    original = i18n.current()
    i18n.set_language("en")
    yield
    i18n.set_language(original)
