from __future__ import annotations

import json
import os
import re
import sqlite3
from math import sqrt
from pathlib import Path
from typing import List, Optional, Tuple

from openai import OpenAI

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency may be absent
    def load_dotenv(*_args, **_kwargs):
        return False


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
POLICY_DIR = ROOT / "policies"
DB_PATH = ROOT / "output" / "policies.sqlite"


def _tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2]


def _ensure_schema() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS policy_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            tokens TEXT NOT NULL,
            embedding TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _get_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else "https://api.openai.com/v1"
    return OpenAI(api_key=api_key, base_url=base_url)


def _embed_texts(texts: List[str]) -> List[List[float]]:
    client = _get_client()
    if client is None:
        return []
    try:
        response = client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in response.data]
    except Exception:
        return []


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _load_chunks() -> List[Tuple[int, str, str, Optional[str]]]:
    _ensure_schema()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, source, chunk_text, embedding FROM policy_chunks").fetchall()
    conn.close()
    if rows:
        return rows

    for path in sorted(POLICY_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
        for chunk in chunks:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "INSERT INTO policy_chunks (source, chunk_text, tokens, embedding) VALUES (?, ?, ?, ?)",
                (path.name, chunk, " ".join(_tokenize(chunk)), None),
            )
            conn.commit()
            conn.close()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, source, chunk_text, embedding FROM policy_chunks").fetchall()
    conn.close()
    return rows


def _populate_missing_embeddings(rows: List[Tuple[int, str, str, Optional[str]]]) -> List[Tuple[int, str, str, Optional[str]]]:
    client = _get_client()
    if client is None:
        return rows

    missing = [(chunk_id, chunk_text) for chunk_id, _, chunk_text, embedding_json in rows if not embedding_json]
    if not missing:
        return rows

    batch_texts = [chunk_text for _, chunk_text in missing]
    embeddings = _embed_texts(batch_texts)
    if not embeddings:
        return rows

    conn = sqlite3.connect(DB_PATH)
    for (chunk_id, _), embedding in zip(missing, embeddings):
        conn.execute(
            "UPDATE policy_chunks SET embedding = ? WHERE id = ?",
            (json.dumps(embedding), chunk_id),
        )
    conn.commit()
    conn.close()
    return _load_chunks()


def retrieve_policy(query: str, top_k: int = 15) -> str:
    rows = _load_chunks()
    if not rows:
        return ""

    rows = _populate_missing_embeddings(rows)

    client = _get_client()
    query_embedding: Optional[List[float]] = None
    if client is not None:
        try:
            response = client.embeddings.create(model="text-embedding-3-small", input=[query])
            query_embedding = response.data[0].embedding
        except Exception:
            query_embedding = None

    scored: List[Tuple[float, str]] = []
    for _, source, chunk_text, embedding_json in rows:
        if query_embedding is not None and embedding_json:
            try:
                embedding = json.loads(embedding_json)
            except Exception:
                embedding = []
            score = _cosine_similarity(query_embedding, embedding)
        else:
            query_tokens = set(_tokenize(query))
            chunk_tokens = set(_tokenize(chunk_text))
            score = len(query_tokens & chunk_tokens) / max(1, len(query_tokens))

        scored.append((score, f"[{source}] {chunk_text}"))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [chunk_text for _, chunk_text in scored[: max(1, min(15, top_k))]]
    return "\n\n".join(selected)
