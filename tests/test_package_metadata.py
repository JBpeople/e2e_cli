import tomllib
from pathlib import Path


def test_openai_dependency_requires_responses_api_capable_sdk():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "openai>=1.68.0" in pyproject["project"]["dependencies"]
