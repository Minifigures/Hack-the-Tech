import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("EVALFORGE_USE_MOCK", "always")
