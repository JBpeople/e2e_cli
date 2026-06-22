from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from typing import Callable

from e2e_cli.openai_client import _resolve_base_url, _resolve_model
from e2e_cli.render import DictionaryResult


@dataclass(frozen=True)
class CacheKey:
    term: str
    model: str
    examples_count: int
    base_url: str


@dataclass(frozen=True)
class CacheEntry:
    result: DictionaryResult
    query_count: int


LookupFn = Callable[..., DictionaryResult]


def default_cache_path() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "e2e_cli" / "cache.sqlite3"
    return Path.home() / ".cache" / "e2e_cli" / "cache.sqlite3"


def make_cache_key(
    term: str,
    *,
    model: str,
    examples_count: int,
    base_url: str | None,
) -> CacheKey:
    return CacheKey(
        term=_normalize_term(term),
        model=model.strip(),
        examples_count=examples_count,
        base_url=base_url.strip() if base_url and base_url.strip() else "",
    )


def lookup_with_cache(
    term: str,
    *,
    model: str | None,
    examples_count: int,
    base_url: str | None,
    lookup: LookupFn,
    cache: DictionaryCache,
    refresh: bool = False,
) -> DictionaryResult:
    resolved_model = _resolve_model(model)
    resolved_base_url = _resolve_base_url(base_url)
    key = make_cache_key(
        term,
        model=resolved_model,
        examples_count=examples_count,
        base_url=resolved_base_url,
    )

    if not refresh:
        cached = cache.record_hit(key)
        if cached is not None:
            return cached.result

    result = lookup(
        term,
        model=resolved_model,
        examples_count=examples_count,
        base_url=resolved_base_url,
    )
    cache.store_lookup(key, result)
    return result


class DictionaryCache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def get(self, key: CacheKey) -> CacheEntry | None:
        self._ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT term, meaning, examples_json, query_count
                FROM lookups
                WHERE term_key = ?
                  AND model = ?
                  AND examples_count = ?
                  AND base_url = ?
                """,
                (key.term, key.model, key.examples_count, key.base_url),
            ).fetchone()

        if row is None:
            return None

        return CacheEntry(
            result=DictionaryResult(
                term=row["term"],
                meaning=row["meaning"],
                examples=json.loads(row["examples_json"]),
            ),
            query_count=row["query_count"],
        )

    def record_hit(self, key: CacheKey) -> CacheEntry | None:
        self._ensure_schema()
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE lookups
                SET query_count = query_count + 1,
                    last_accessed_at = ?
                WHERE term_key = ?
                  AND model = ?
                  AND examples_count = ?
                  AND base_url = ?
                """,
                (now, key.term, key.model, key.examples_count, key.base_url),
            )
        return self.get(key)

    def store_lookup(self, key: CacheKey, result: DictionaryResult) -> CacheEntry:
        self._ensure_schema()
        existing = self.get(key)
        query_count = 1 if existing is None else existing.query_count + 1
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO lookups (
                    term_key,
                    model,
                    examples_count,
                    base_url,
                    term,
                    meaning,
                    examples_json,
                    query_count,
                    created_at,
                    updated_at,
                    last_accessed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(term_key, model, examples_count, base_url)
                DO UPDATE SET
                    term = excluded.term,
                    meaning = excluded.meaning,
                    examples_json = excluded.examples_json,
                    query_count = excluded.query_count,
                    updated_at = excluded.updated_at,
                    last_accessed_at = excluded.last_accessed_at
                """,
                (
                    key.term,
                    key.model,
                    key.examples_count,
                    key.base_url,
                    result.term,
                    result.meaning,
                    json.dumps(result.examples, ensure_ascii=False),
                    query_count,
                    now,
                    now,
                    now,
                ),
            )
        entry = self.get(key)
        if entry is None:  # pragma: no cover - defensive guard for SQLite failures.
            raise RuntimeError("Failed to store cache entry.")
        return entry

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS lookups (
                    term_key TEXT NOT NULL,
                    model TEXT NOT NULL,
                    examples_count INTEGER NOT NULL,
                    base_url TEXT NOT NULL,
                    term TEXT NOT NULL,
                    meaning TEXT NOT NULL,
                    examples_json TEXT NOT NULL,
                    query_count INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    last_accessed_at INTEGER NOT NULL,
                    PRIMARY KEY (term_key, model, examples_count, base_url)
                )
                """
            )


def _normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip()).casefold()


def _now() -> int:
    return int(time.time())
