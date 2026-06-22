from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
import sys

from e2e_cli.cache import DictionaryCache, default_cache_path, lookup_with_cache
from e2e_cli.env import load_dotenv
from e2e_cli.openai_client import DEFAULT_MODEL, DictionaryLookupError, explain_term
from e2e_cli.render import DictionaryResult, render_json, render_text


LookupFn = Callable[..., DictionaryResult]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explain an English word or phrase in English."
    )
    parser.add_argument("term", help="English word or phrase to explain")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "OpenAI model to use "
            f"(or set OPENAI_MODEL; default: {DEFAULT_MODEL})"
        ),
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=2,
        help="Number of example sentences (default: 2)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible API base URL (or set OPENAI_BASE_URL)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip cache reads, writes, and query counting for this lookup",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh a cached lookup by calling the model and updating the cache",
    )
    parser.add_argument(
        "--cache-path",
        type=Path,
        default=None,
        help="Path to the SQLite cache file",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    lookup: LookupFn | None = explain_term,
) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    term = args.term.strip()
    if not term:
        print("error: term cannot be empty", file=sys.stderr)
        return 2

    if args.examples < 1:
        print("error: --examples must be at least 1", file=sys.stderr)
        return 2

    active_lookup = lookup if lookup is not None else explain_term

    try:
        if args.no_cache:
            result = active_lookup(
                term,
                model=args.model,
                examples_count=args.examples,
                base_url=args.base_url,
            )
        else:
            cache_path = args.cache_path if args.cache_path is not None else default_cache_path()
            result = lookup_with_cache(
                term,
                model=args.model,
                examples_count=args.examples,
                base_url=args.base_url,
                lookup=active_lookup,
                cache=DictionaryCache(cache_path),
                refresh=args.refresh,
            )
    except DictionaryLookupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = render_json(result) if args.json else render_text(result)
    print(output)
    return 0
