from e2e_cli.cli import main
from e2e_cli.openai_client import DictionaryLookupError
from e2e_cli.render import DictionaryResult


def test_cli_prints_text_output(capsys):
    def lookup(term, *, model, examples_count, base_url):
        return DictionaryResult(
            term=term,
            meaning="A test meaning.",
            examples=["A test example."],
        )

    exit_code = main(["take off"], lookup=lookup)

    assert exit_code == 0
    assert "Word/Phrase: take off" in capsys.readouterr().out


def test_cli_prints_json_output(capsys):
    def lookup(term, *, model, examples_count, base_url):
        return DictionaryResult(
            term=term,
            meaning="A test meaning.",
            examples=["A test example."],
        )

    exit_code = main(["take off", "--json"], lookup=lookup)

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

    exit_code = main(["take off"], lookup=lookup)

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

    exit_code = main(["take off"], lookup=lookup)

    assert exit_code == 1
    assert "OPENAI_API_KEY is required." in capsys.readouterr().err
