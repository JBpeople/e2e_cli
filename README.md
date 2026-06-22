# e2e-cli

Python CLI for explaining English words or phrases in English with English examples.

## Setup

Using uv:

```powershell
.\scripts\setup.ps1
```

Then edit `.env` and set `OPENAI_API_KEY`.

Run with uv:

```powershell
uv run e2e "take off"
```

The CLI automatically loads `.env` from the current working directory. Existing shell environment variables take priority over `.env` values.

Without uv:

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
e2e "take off" --refresh
e2e "take off" --no-cache
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

## Model compatibility

This project has only been manually tested with:

- `gpt-5.5`
- `GLM-5.1` through an OpenAI-compatible endpoint

Other models and compatible API providers may work, but they have not been verified.

## Cache

Lookups are cached in a local SQLite database by default. The cache key includes the normalized term, resolved model, example count, and resolved base URL.

Default cache path on Windows:

```text
%LOCALAPPDATA%\e2e_cli\cache.sqlite3
```

If `LOCALAPPDATA` is unavailable, the fallback path is:

```text
~/.cache/e2e_cli/cache.sqlite3
```

Cache options:

```powershell
e2e "take off" --refresh
e2e "take off" --no-cache
e2e "take off" --cache-path .\cache.sqlite3
```

- `--refresh` ignores a cached result, calls the model, updates the cache, and increments the query count.
- `--no-cache` skips cache reads, writes, and query counting for that lookup.
- Every cache-enabled lookup increments `query_count`, including cache hits. This is stored for future review features such as vocabulary recap.

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
uv run pytest -v
```

or:

```powershell
python -m pytest -v
```

The test suite does not call the OpenAI API.
