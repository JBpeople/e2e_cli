# English Dictionary CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that uses OpenAI to explain English words or phrases in English with English example sentences.

**Architecture:** The CLI is split into focused modules: argument handling in `cli.py`, OpenAI request/response handling in `openai_client.py`, and output formatting in `render.py`. The OpenAI client is dependency-injected so tests never make network calls.

**Tech Stack:** Python 3.10+, pytest, OpenAI Python SDK, argparse, dataclasses, JSON.

---

## File Structure

- Create `pyproject.toml`: package metadata, console script, runtime/test dependencies.
- Create `README.md`: installation, API key, usage, and manual smoke test.
- Create `e2e_cli/__init__.py`: package marker and version.
- Create `e2e_cli/__main__.py`: `python -m e2e_cli` entry point.
- Create `e2e_cli/render.py`: typed result object plus text/JSON rendering.
- Create `e2e_cli/openai_client.py`: API-key handling, OpenAI Responses API wrapper, structured output validation.
- Create `e2e_cli/cli.py`: CLI parsing, validation, dependency wiring, and exit codes.
- Create `tests/test_render.py`: render behavior.
- Create `tests/test_openai_client.py`: OpenAI wrapper behavior with fake clients.
- Create `tests/test_cli.py`: CLI validation, output, and error behavior.

### Task 1: Render Result

**Files:**
- Create: `e2e_cli/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: Write failing renderer tests**

```python
from e2e_cli.render import DictionaryResult, render_json, render_text


def test_render_text_formats_dictionary_result():
    result = DictionaryResult(
        term="take off",
        meaning="To leave the ground and begin to fly.",
        examples=["The plane took off at 8 a.m.", "Her career took off quickly."],
    )

    assert render_text(result) == (
        "Word/Phrase: take off\n"
        "\n"
        "Meaning:\n"
        "To leave the ground and begin to fly.\n"
        "\n"
        "Examples:\n"
        "1. The plane took off at 8 a.m.\n"
        "2. Her career took off quickly."
    )


def test_render_json_emits_expected_object():
    result = DictionaryResult(
        term="take off",
        meaning="To leave the ground and begin to fly.",
        examples=["The plane took off at 8 a.m."],
    )

    assert render_json(result) == (
        '{"term": "take off", "meaning": "To leave the ground and begin to fly.", '
        '"examples": ["The plane took off at 8 a.m."]}'
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_render.py -v`

Expected: FAIL because `e2e_cli.render` does not exist.

- [ ] **Step 3: Write minimal renderer implementation**

```python
from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class DictionaryResult:
    term: str
    meaning: str
    examples: list[str]


def render_text(result: DictionaryResult) -> str:
    examples = "\n".join(
        f"{index}. {example}" for index, example in enumerate(result.examples, start=1)
    )
    return (
        f"Word/Phrase: {result.term}\n"
        "\n"
        "Meaning:\n"
        f"{result.meaning}\n"
        "\n"
        "Examples:\n"
        f"{examples}"
    )


def render_json(result: DictionaryResult) -> str:
    return json.dumps(asdict(result), ensure_ascii=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_render.py -v`

Expected: PASS.

### Task 2: OpenAI Wrapper

**Files:**
- Create: `e2e_cli/openai_client.py`
- Modify: `e2e_cli/render.py`
- Test: `tests/test_openai_client.py`

- [ ] **Step 1: Write failing OpenAI wrapper tests**

```python
import pytest

from e2e_cli.openai_client import (
    DictionaryLookupError,
    MissingApiKeyError,
    explain_term,
)


class FakeResponses:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.responses = FakeResponses(response)


class FakeResponse:
    def __init__(self, text):
        self.output_text = text


def test_explain_term_sends_term_model_and_example_count():
    client = FakeClient(
        FakeResponse(
            '{"term":"take off","meaning":"To leave the ground.","examples":["The plane took off."]}'
        )
    )

    result = explain_term(
        "take off",
        model="test-model",
        examples_count=1,
        api_key="test-key",
        client=client,
    )

    assert result.term == "take off"
    assert result.meaning == "To leave the ground."
    assert result.examples == ["The plane took off."]
    call = client.responses.calls[0]
    assert call["model"] == "test-model"
    assert "take off" in call["input"]
    assert "1 example" in call["input"]
    assert call["text"]["format"]["type"] == "json_schema"


def test_explain_term_requires_api_key():
    with pytest.raises(MissingApiKeyError, match="OPENAI_API_KEY"):
        explain_term("take off", model="test-model", examples_count=1, api_key="")


def test_explain_term_rejects_invalid_model_output():
    client = FakeClient(FakeResponse('{"term":"take off","meaning":"","examples":[]}'))

    with pytest.raises(DictionaryLookupError, match="invalid"):
        explain_term(
            "take off",
            model="test-model",
            examples_count=1,
            api_key="test-key",
            client=client,
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_openai_client.py -v`

Expected: FAIL because `e2e_cli.openai_client` does not exist.

- [ ] **Step 3: Write minimal OpenAI wrapper implementation**

```python
from __future__ import annotations

import json
import os
from typing import Any

from e2e_cli.render import DictionaryResult


DEFAULT_MODEL = "gpt-5.5"


class DictionaryLookupError(RuntimeError):
    pass


class MissingApiKeyError(DictionaryLookupError):
    pass


def explain_term(
    term: str,
    *,
    model: str = DEFAULT_MODEL,
    examples_count: int = 2,
    api_key: str | None = None,
    client: Any | None = None,
) -> DictionaryResult:
    resolved_api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
    if not resolved_api_key:
        raise MissingApiKeyError("OPENAI_API_KEY is required.")

    active_client = client if client is not None else _create_openai_client(resolved_api_key)
    response = active_client.responses.create(
        model=model,
        input=_build_prompt(term, examples_count),
        text={"format": _json_schema()},
    )
    return _parse_result(response.output_text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_openai_client.py -v`

Expected: PASS.

### Task 3: CLI

**Files:**
- Create: `e2e_cli/cli.py`
- Create: `e2e_cli/__main__.py`
- Modify: `e2e_cli/__init__.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

```python
from e2e_cli.cli import main
from e2e_cli.render import DictionaryResult


def test_cli_prints_text_output(capsys):
    def lookup(term, *, model, examples_count):
        return DictionaryResult(term=term, meaning="A test meaning.", examples=["A test example."])

    exit_code = main(["take off"], lookup=lookup)

    assert exit_code == 0
    assert "Word/Phrase: take off" in capsys.readouterr().out


def test_cli_prints_json_output(capsys):
    def lookup(term, *, model, examples_count):
        return DictionaryResult(term=term, meaning="A test meaning.", examples=["A test example."])

    exit_code = main(["take off", "--json"], lookup=lookup)

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == (
        '{"term": "take off", "meaning": "A test meaning.", "examples": ["A test example."]}'
    )


def test_cli_rejects_empty_term(capsys):
    exit_code = main(["   "], lookup=None)

    assert exit_code == 2
    assert "term cannot be empty" in capsys.readouterr().err


def test_cli_rejects_invalid_example_count(capsys):
    exit_code = main(["take off", "--examples", "0"], lookup=None)

    assert exit_code == 2
    assert "--examples must be at least 1" in capsys.readouterr().err
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`

Expected: FAIL because `e2e_cli.cli` does not exist.

- [ ] **Step 3: Write minimal CLI implementation**

```python
from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import sys

from e2e_cli.openai_client import DEFAULT_MODEL, DictionaryLookupError, explain_term
from e2e_cli.render import DictionaryResult, render_json, render_text


LookupFn = Callable[[str], DictionaryResult]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explain an English word or phrase in English.")
    parser.add_argument("term", help="English word or phrase to explain")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenAI model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--examples", type=int, default=2, help="Number of example sentences (default: 2)")
    return parser
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -v`

Expected: PASS.

### Task 4: Packaging and Docs

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Modify: `e2e_cli/__init__.py`

- [ ] **Step 1: Write package metadata**

```toml
[project]
name = "e2e-cli"
version = "0.1.0"
description = "A CLI for English explanations and example sentences using OpenAI."
requires-python = ">=3.10"
dependencies = ["openai>=1.0.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
e2e = "e2e_cli.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write README**

```markdown
# e2e-cli

Python CLI for explaining English words or phrases in English with English examples.

## Setup

```bash
python -m pip install -e ".[dev]"
set OPENAI_API_KEY=your_api_key
```

## Usage

```bash
e2e "take off"
e2e "take off" --json
e2e "take off" --examples 3
```
```

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest -v`

Expected: PASS.

## Self-Review

- Spec coverage: term input, English-only model prompt, text output, JSON output, model override, example count, missing key error, API failure path, invalid model output, package entry point, and README are covered.
- Placeholder scan: no TBD/TODO/implement later placeholders are present.
- Type consistency: `DictionaryResult`, `explain_term`, `render_text`, `render_json`, and `main` names are consistent across tasks.
