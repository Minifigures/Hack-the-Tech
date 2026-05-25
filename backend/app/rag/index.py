"""Knowledge base indexer.

Chunks markdown files in data/kb by '## anchor' sections and a 600-char window
fallback. Persists a JSON index with deterministic 256-dim hash embeddings.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from ..config import INDEX_PATH, KB_DIR

EMBED_DIM = 256
CHUNK_MAX = 600


@dataclass
class Chunk:
    source_id: str
    text: str
    embedding: list[float]


def hash_embed(text: str) -> list[float]:
    """A deterministic, dependency-free vectoriser.

    We tokenise on word boundaries, hash each token into a 256-dim bucket with
    a tiny TF-IDF-ish weighting, and L2-normalise. Good enough for our offline
    demo and identical across machines.
    """
    vec = [0.0] * EMBED_DIM
    tokens = re.findall(r"[A-Za-z0-9_.-]+", text.lower())
    if not tokens:
        return vec
    # token frequency
    tf: dict[str, int] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    # hash bucket assignment with light tf-idf-ish damping
    for tok, count in tf.items():
        h = hash((tok, len(tok))) % EMBED_DIM
        weight = (1.0 + math.log(1 + count)) / (1.0 + math.log(1 + len(tok)))
        vec[h] += weight
        h2 = hash((tok[::-1], "rev")) % EMBED_DIM
        vec[h2] += weight * 0.5
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _chunk_markdown(path: Path) -> Iterable[tuple[str, str]]:
    """Yield (source_id, text) for each ## section, or fallback by char window."""
    rel = path.relative_to(KB_DIR).as_posix()
    text = path.read_text(encoding="utf-8")
    # Split on '## anchor' style headings.
    pattern = re.compile(r"^##\s+([\w\-]+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if not matches:
        for i in range(0, len(text), CHUNK_MAX):
            chunk = text[i : i + CHUNK_MAX].strip()
            if chunk:
                yield f"{rel}#chunk-{i // CHUNK_MAX}", chunk
        return
    for idx, m in enumerate(matches):
        anchor = m.group(1)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            yield f"{rel}#{anchor}", body


def build_index() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(KB_DIR.rglob("*.md")):
        for source_id, body in _chunk_markdown(path):
            chunks.append(Chunk(source_id=source_id, text=body, embedding=hash_embed(body)))
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps([asdict(c) for c in chunks]), encoding="utf-8")
    return chunks


def load_index() -> list[Chunk]:
    if not INDEX_PATH.exists():
        return build_index()
    raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return [Chunk(**c) for c in raw]


def sources_summary() -> dict[str, int]:
    summary: dict[str, int] = {}
    for chunk in load_index():
        bucket = chunk.source_id.split("/", 1)[0]
        summary[bucket] = summary.get(bucket, 0) + 1
    return summary
