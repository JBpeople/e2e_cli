# e2e-cli

Python CLI for explaining English words or phrases in English with English examples.

## Setup

```powershell
python -m pip install -e ".[dev]"
$env:OPENAI_API_KEY = "your_api_key"
```

For Command Prompt:

```cmd
set OPENAI_API_KEY=your_api_key
```

## Usage

```powershell
e2e "take off"
e2e "take off" --json
e2e "take off" --examples 3
e2e "take off" --model gpt-5.5
e2e "take off" --base-url https://api.openai.com/v1
```

You can also run it without installing the console script:

```powershell
python -m e2e_cli "take off"
```

To use an OpenAI-compatible endpoint by default:

```powershell
$env:OPENAI_BASE_URL = "https://api.example.com/v1"
e2e "take off"
```

To use a model by default:

```powershell
$env:OPENAI_MODEL = "gpt-5.4"
e2e "take off"
```

Command-line options take priority over environment variables. For model selection, the order is `--model`, then `OPENAI_MODEL`, then `gpt-5.5`.

## Output

```text
Word/Phrase: take off

Meaning:
To leave the ground and begin to fly; also, to become successful quickly.

Examples:
1. The plane took off at 8 a.m.
2. Her new business really took off after the interview.
```

## Tests

```powershell
python -m pytest -v
```

The test suite does not call the OpenAI API.
