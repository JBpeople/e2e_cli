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
