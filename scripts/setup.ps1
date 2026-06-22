param(
    [switch]$SkipEnv
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed. Install it first: https://docs.astral.sh/uv/getting-started/installation/"
}

uv sync --extra dev

if (-not $SkipEnv -and -not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "Created .env from .env.example. Set OPENAI_API_KEY before real lookups."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run tests: uv run pytest -v"
Write-Host "Lookup:    uv run e2e `"take off`""
