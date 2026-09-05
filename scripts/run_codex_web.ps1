$ErrorActionPreference = "Stop"

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Assert-PortFree([int]$Port) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        throw "포트 $Port 가 이미 사용 중입니다. 기존 프로세스를 종료한 뒤 다시 실행하세요."
    }
}

function Wait-Http([string]$Url, [int]$Retries = 40) {
    for ($i = 0; $i -lt $Retries; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    throw "$Url 가 준비되지 않았습니다."
}

$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codex) {
    throw "Codex CLI를 찾을 수 없습니다. 먼저 codex --version 을 확인하세요."
}

Write-Host "[1/5] Codex CLI 확인"
& codex --version

Write-Host "[2/5] ChatGPT/Codex 로그인 상태 확인"
& codex login status
if ($LASTEXITCODE -ne 0) {
    throw "Codex 로그인이 필요합니다. 먼저 codex login 또는 codex login --device-auth 를 실행하세요."
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[3/5] Python 가상환경 생성"
    py -m venv .venv
}

Write-Host "[3/5] 백엔드 의존성 확인"
& $venvPython -m pip install -q -r backend\requirements.txt

Assert-PortFree 8000
Assert-PortFree 8080

$env:LLM_PROVIDER = "codex_subscription"
$env:DATABASE_URL = "sqlite:///./tarot-local.db"
$env:AUTO_SEED_CURATED = "true"
$env:CODEX_EXECUTABLE = "codex"
if (-not $env:CODEX_TIMEOUT_SECONDS) {
    $env:CODEX_TIMEOUT_SECONDS = "180"
}

$logDir = Join-Path $repoRoot ".local"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$backendOut = Join-Path $logDir "codex-web-backend.out.log"
$backendErr = Join-Path $logDir "codex-web-backend.err.log"
$frontendOut = Join-Path $logDir "codex-web-frontend.out.log"
$frontendErr = Join-Path $logDir "codex-web-frontend.err.log"

Remove-Item $backendOut, $backendErr, $frontendOut, $frontendErr -ErrorAction SilentlyContinue

$backendArgs = @(
    "-m", "uvicorn", "app.main:app",
    "--app-dir", "backend",
    "--host", "127.0.0.1",
    "--port", "8000"
)
$frontendArgs = @(
    "-m", "http.server", "8080",
    "--bind", "127.0.0.1",
    "--directory", "docs"
)

$backend = $null
$frontend = $null

try {
    Write-Host "[4/5] Tarot Engine + Local Codex 백엔드 시작"
    $backend = Start-Process `
        -FilePath $venvPython `
        -ArgumentList $backendArgs `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr

    Wait-Http "http://127.0.0.1:8000/health"

    Write-Host "[5/5] Tarot Engine Lab 프론트엔드 시작"
    $frontend = Start-Process `
        -FilePath $venvPython `
        -ArgumentList $frontendArgs `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr

    Wait-Http "http://127.0.0.1:8080/"

    $webUrl = "http://127.0.0.1:8080/?mode=local-codex"
    Write-Host ""
    Write-Host "Local Codex Web 테스트 준비 완료"
    Write-Host "Web     : $webUrl"
    Write-Host "Backend : http://127.0.0.1:8000"
    Write-Host "Swagger : http://127.0.0.1:8000/docs"
    Write-Host "LLM     : codex_subscription"
    Write-Host "Defaults: gpt-5.6-sol / XHigh / 풍부하게 / 상세하게"
    Write-Host "Logs    : $logDir"
    Write-Host "종료    : Ctrl+C"
    Write-Host ""

    Start-Process $webUrl

    while ($true) {
        if ($backend.HasExited) {
            $errorText = if (Test-Path $backendErr) { Get-Content $backendErr -Raw } else { "" }
            throw "백엔드가 종료되었습니다.`n$errorText"
        }
        if ($frontend.HasExited) {
            $errorText = if (Test-Path $frontendErr) { Get-Content $frontendErr -Raw } else { "" }
            throw "프론트엔드가 종료되었습니다.`n$errorText"
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    if ($frontend -and -not $frontend.HasExited) {
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    }
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
}
