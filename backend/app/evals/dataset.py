from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from ..config import EVAL_DIR


@lru_cache(maxsize=1)
def load_golden() -> list[dict[str, Any]]:
    path = EVAL_DIR / "golden.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw["items"]


def by_id(item_id: str) -> dict[str, Any] | None:
    for item in load_golden():
        if item["id"] == item_id:
            return item
    return None
