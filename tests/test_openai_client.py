import pytest

from e2e_cli.openai_client import (
    DEFAULT_MODEL,
    DictionaryLookupError,
    MissingApiKeyError,
    _resolve_base_url,
    _resolve_model,
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
            '{"term":"take off","meaning":"To leave the ground.",'
            '"examples":["The plane took off."]}'
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
    assert "Return only a valid JSON object" in call["input"]
    assert call["text"]["format"]["type"] == "json_schema"


def test_explain_term_extracts_final_dictionary_json_from_reasoning_text():
    client = FakeClient(
        FakeResponse(
            'Analysis included a draft: {"term":"draft"}. '
            '</think>{"term":"roll out","meaning":"To introduce something.",'
            '"examples":["The company will roll out the update."]}'
        )
    )

    result = explain_term(
        "roll out",
        model="test-model",
        examples_count=1,
        api_key="test-key",
        client=client,
    )

    assert result.term == "roll out"
    assert result.meaning == "To introduce something."
    assert result.examples == ["The company will roll out the update."]


def test_explain_term_requires_api_key():
    with pytest.raises(MissingApiKeyError, match="OPENAI_API_KEY"):
        explain_term("take off", model="test-model", examples_count=1, api_key="")


def test_resolve_base_url_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example/v1")

    assert _resolve_base_url("https://cli.example/v1") == "https://cli.example/v1"


def test_resolve_base_url_reads_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example/v1")

    assert _resolve_base_url(None) == "https://env.example/v1"


def test_resolve_base_url_ignores_blank_values(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "   ")

    assert _resolve_base_url(None) is None


def test_resolve_model_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    assert _resolve_model("cli-model") == "cli-model"


def test_resolve_model_reads_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    assert _resolve_model(None) == "env-model"


def test_resolve_model_uses_default_for_blank_values(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "   ")

    assert _resolve_model(None) == DEFAULT_MODEL


def test_explain_term_uses_environment_model(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "env-model")
    client = FakeClient(
        FakeResponse(
            '{"term":"take off","meaning":"To leave the ground.",'
            '"examples":["The plane took off."]}'
        )
    )

    explain_term(
        "take off",
        model=None,
        examples_count=1,
        api_key="test-key",
        client=client,
    )

    assert client.responses.calls[0]["model"] == "env-model"


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


def test_explain_term_wraps_api_failures():
    class BrokenResponses:
        def create(self, **kwargs):
            raise RuntimeError("network failed")

    class BrokenClient:
        responses = BrokenResponses()

    with pytest.raises(DictionaryLookupError, match="OpenAI API request failed"):
        explain_term(
            "take off",
            model="test-model",
            examples_count=1,
            api_key="test-key",
            client=BrokenClient(),
        )
