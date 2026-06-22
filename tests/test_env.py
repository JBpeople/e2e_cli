import os

from e2e_cli.env import load_dotenv


def test_load_dotenv_sets_values_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=test-key",
                "OPENAI_MODEL='test-model'",
                'OPENAI_BASE_URL="https://example.test/v1"',
                "# ignored comment",
            ]
        ),
        encoding="utf-8",
    )

    load_dotenv(env_file)

    assert os.environ["OPENAI_API_KEY"] == "test-key"
    assert os.environ["OPENAI_MODEL"] == "test-model"
    assert os.environ["OPENAI_BASE_URL"] == "https://example.test/v1"


def test_load_dotenv_does_not_override_existing_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "existing-key")
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")

    load_dotenv(env_file)

    assert os.environ["OPENAI_API_KEY"] == "existing-key"
