import sys
import os
import warnings

# Add src/ to Python path so tests can import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Suppress known harmless warnings from colour-science library
warnings.filterwarnings("ignore", message=".*related API features are not available.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*invalid value encountered in log.*")
