# Cache Query Counts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent lookup caching with per-entry query counts for later vocabulary review.

**Architecture:** Add a focused `e2e_cli/cache.py` module backed by SQLite. `cli.py` will wrap the existing lookup function with cache behavior unless `--no-cache` is passed, and `--refresh` will force a new model call while preserving and incrementing the usage counter.

**Tech Stack:** Python standard library `sqlite3`, `pathlib`, existing pytest suite.

---

## File Structure

- Create `e2e_cli/cache.py`: cache key construction, SQLite storage, lookup/update operations, and default cache path.
- Create `tests/test_cache.py`: direct cache behavior tests.
- Modify `e2e_cli/cli.py`: add `--no-cache`, `--refresh`, `--cache-path`, and use cached lookup.
- Modify `tests/test_cli.py`: verify cache flags and cached behavior.
- Modify `README.md`: document cache behavior and query count semantics.

## Semantics

- Cache key includes normalized term, resolved model, examples count, and resolved base URL.
- Query count increments for every cache-enabled user lookup.
- Cache hit: return cached result and increment query count.
- Cache miss: call lookup, store result with query count 1.
- `--refresh`: call lookup even if cached, then replace result and increment query count.
- `--no-cache`: skip cache reads, writes, and counting.
- `--cache-path`: test/debug escape hatch for choosing cache file path.

## Verification

- Write failing tests before each implementation slice.
- Run targeted tests after each slice.
- Run `python -m pytest -v` before completion.
