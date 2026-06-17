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
