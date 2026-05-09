"""Add scripts/ to sys.path so tests can import lesson_core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
