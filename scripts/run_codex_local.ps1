$ErrorActionPreference = "Stop"

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codex) {
    throw "Codex CLI를 찾을 수 없습니다. Codex CLI 설치 후 'codex --version'을 확인하세요."
}

Write-Host "[1/4] Codex CLI 확인"
& codex --version

Write-Host "[2/4] ChatGPT/Codex 로그인 상태 확인"
& codex login status
if ($LASTEXITCODE -ne 0) {
    throw "Codex 로그인이 필요합니다. 먼저 'codex login'을 실행한 뒤 다시 시도하세요."
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[3/4] Python 가상환경 생성"
    py -m venv .venv
}

Write-Host "[3/4] 백엔드 의존성 확인"
& $venvPython -m pip install -q -r backend\requirements.txt

$env:LLM_PROVIDER = "codex_subscription"
$env:DATABASE_URL = "sqlite:///./tarot-local.db"
$env:AUTO_SEED_CURATED = "true"
$env:CODEX_EXECUTABLE = "codex"
if (-not $env:CODEX_TIMEOUT_SECONDS) {
    $env:CODEX_TIMEOUT_SECONDS = "120"
}

Write-Host "[4/4] Tarot Engine 시작"
Write-Host "Swagger: http://127.0.0.1:8000/docs"
Write-Host "Health : http://127.0.0.1:8000/health"
Write-Host "Provider: codex_subscription"
Write-Host "종료: Ctrl+C"

& $venvPython -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
