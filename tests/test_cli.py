from e2e_cli.cli import main
from e2e_cli.openai_client import DictionaryLookupError
from e2e_cli.render import DictionaryResult


def test_cli_loads_dotenv_before_lookup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    (tmp_path / ".env").write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")
    calls = []

    def lookup(term, *, model, examples_count, base_url):
        import os

        calls.append(os.environ.get("OPENAI_API_KEY"))
        return DictionaryResult(term=term, meaning="A test meaning.", examples=["One."])

    exit_code = main(["take off", "--no-cache"], lookup=lookup)

    assert exit_code == 0
    assert calls == ["file-key"]


def test_cli_prints_text_output(capsys):
    def lookup(term, *, model, examples_count, base_url):
        return DictionaryResult(
            term=term,
            meaning="A test meaning.",
            examples=["A test example."],
        )

    exit_code = main(["take off", "--no-cache"], lookup=lookup)

    assert exit_code == 0
    assert "Word/Phrase: take off" in capsys.readouterr().out


def test_cli_prints_json_output(capsys):
    def lookup(term, *, model, examples_count, base_url):
        return DictionaryResult(
            term=term,
            meaning="A test meaning.",
            examples=["A test example."],
        )

    exit_code = main(["take off", "--json", "--no-cache"], lookup=lookup)

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == (
        '{"term": "take off", "meaning": "A test meaning.", '
        '"examples": ["A test example."]}'
    )


def test_cli_passes_model_example_count_and_base_url():
    calls = []

    def lookup(term, *, model, examples_count, base_url):
        calls.append((term, model, examples_count, base_url))
        return DictionaryResult(term=term, meaning="A test meaning.", examples=["One."])

    exit_code = main(
        [
            "take off",
            "--model",
            "test-model",
            "--examples",
            "1",
            "--base-url",
            "https://example.test/v1",
            "--no-cache",
        ],
        lookup=lookup,
    )

    assert exit_code == 0
    assert calls == [("take off", "test-model", 1, "https://example.test/v1")]


def test_cli_leaves_model_unset_when_no_model_argument():
    calls = []

    def lookup(term, *, model, examples_count, base_url):
        calls.append(model)
        return DictionaryResult(term=term, meaning="A test meaning.", examples=["One."])

    exit_code = main(["take off", "--no-cache"], lookup=lookup)

    assert exit_code == 0
    assert calls == [None]


def test_cli_rejects_empty_term(capsys):
    exit_code = main(["   "], lookup=None)

    assert exit_code == 2
    assert "term cannot be empty" in capsys.readouterr().err


def test_cli_rejects_invalid_example_count(capsys):
    exit_code = main(["take off", "--examples", "0"], lookup=None)

    assert exit_code == 2
    assert "--examples must be at least 1" in capsys.readouterr().err


def test_cli_reports_lookup_errors(capsys):
    def lookup(term, *, model, examples_count, base_url):
        raise DictionaryLookupError("OPENAI_API_KEY is required.")

    exit_code = main(["take off", "--no-cache"], lookup=lookup)

    assert exit_code == 1
    assert "OPENAI_API_KEY is required." in capsys.readouterr().err


def test_cli_uses_cached_result_on_second_lookup(tmp_path, capsys):
    cache_path = tmp_path / "cache.sqlite3"
    calls = []

    def lookup(term, *, model, examples_count, base_url):
        calls.append(term)
        return DictionaryResult(
            term=term,
            meaning="Cached after first lookup.",
            examples=["First example."],
        )

    first_exit = main(["take off", "--cache-path", str(cache_path)], lookup=lookup)
    capsys.readouterr()
    second_exit = main(["take off", "--cache-path", str(cache_path)], lookup=lookup)

    assert first_exit == 0
    assert second_exit == 0
    assert calls == ["take off"]
    assert "Cached after first lookup." in capsys.readouterr().out


def test_cli_refresh_bypasses_existing_cache(tmp_path, capsys):
    cache_path = tmp_path / "cache.sqlite3"
    meanings = iter(["Original meaning.", "Refreshed meaning."])

    def lookup(term, *, model, examples_count, base_url):
        return DictionaryResult(term=term, meaning=next(meanings), examples=["Example."])

    assert main(["take off", "--cache-path", str(cache_path)], lookup=lookup) == 0
    capsys.readouterr()
    assert (
        main(["take off", "--cache-path", str(cache_path), "--refresh"], lookup=lookup)
        == 0
    )

    assert "Refreshed meaning." in capsys.readouterr().out


def test_cli_no_cache_calls_lookup_each_time(tmp_path, capsys):
    calls = []

    def lookup(term, *, model, examples_count, base_url):
        calls.append(term)
        return DictionaryResult(term=term, meaning="Meaning.", examples=["Example."])

    args = [
        "take off",
        "--cache-path",
        str(tmp_path / "cache.sqlite3"),
        "--no-cache",
    ]

    assert main(args, lookup=lookup) == 0
    capsys.readouterr()
    assert main(args, lookup=lookup) == 0

    assert calls == ["take off", "take off"]
