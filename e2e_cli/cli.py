from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import sys

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
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    lookup: LookupFn | None = explain_term,
) -> int:
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
        result = active_lookup(
            term,
            model=args.model,
            examples_count=args.examples,
            base_url=args.base_url,
        )
    except DictionaryLookupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = render_json(result) if args.json else render_text(result)
    print(output)
    return 0
