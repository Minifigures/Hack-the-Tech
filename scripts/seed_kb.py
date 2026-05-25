"""Build the hash-based KB index and initialise the SQLite DB."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import init_db  # noqa: E402
from app.rag.index import build_index, sources_summary  # noqa: E402


def main() -> None:
    chunks = build_index()
    init_db()
    print(f"[seed] indexed {len(chunks)} chunks from KB")
    for bucket, count in sorted(sources_summary().items()):
        print(f"  - {bucket}: {count} chunks")
    print("[seed] SQLite initialised")


if __name__ == "__main__":
    main()
