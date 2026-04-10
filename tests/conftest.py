import sys
import os
import warnings

import pytest

# Add src/ to Python path so tests can import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Suppress known harmless warnings from colour-science library
warnings.filterwarnings("ignore", message=".*related API features are not available.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*invalid value encountered in log.*")


@pytest.fixture(autouse=True)
def force_english_locale(monkeypatch):
    """Ensure tests always run in English regardless of system locale."""
    import i18n
    original = i18n._current_lang
    i18n._current_lang = "en"
    # Prevent tests from writing to the real config file
    monkeypatch.setattr(i18n, "_save_config", lambda data: None)
    yield
    i18n._current_lang = original
