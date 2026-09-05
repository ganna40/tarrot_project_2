$ErrorActionPreference = "Stop"

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$body = @{
    question = "게임을 만들면 실제 투자로 이어질까?"
    context = "투자자가 실제 게임을 만들면 투자하겠다고 말했다."
    reading_context = "BUSINESS"
    spread_type = "three_card"
    cards = @(
        @{ code = "TEN_OF_SWORDS"; orientation = "UPRIGHT" },
        @{ code = "EIGHT_OF_WANDS"; orientation = "UPRIGHT" },
        @{ code = "HIEROPHANT"; orientation = "UPRIGHT" }
    )
    response_length = "SHORT"
    include_trace = $true
    use_llm = $true
} | ConvertTo-Json -Depth 8

Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$content = New-Object System.Net.Http.StringContent($body, [System.Text.Encoding]::UTF8, "application/json")

try {
    $response = $client.PostAsync(
        "http://127.0.0.1:8000/api/v1/readings",
        $content
    ).GetAwaiter().GetResult()

    $responseBytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
    $responseText = [System.Text.Encoding]::UTF8.GetString($responseBytes)

    if (-not $response.IsSuccessStatusCode) {
        throw "HTTP $([int]$response.StatusCode): $responseText"
    }

    $result = $responseText | ConvertFrom-Json
}
finally {
    $content.Dispose()
    $client.Dispose()
}

Write-Host ""
Write-Host "=== Codex subscription validation ==="
Write-Host "Context : $($result.reading_context)"
Write-Host "Verdict : $($result.verdict)"
Write-Host "Score   : $($result.score)"
Write-Host "Flow    : $($result.flow_summary)"
Write-Host "LLM used: $($result.llm_used)"
Write-Host ""
Write-Host "Interpretation:"
Write-Host $result.overall_interpretation

if (-not $result.llm_used) {
    throw "llm_used=false 입니다. 첫 번째 터미널의 FastAPI 로그에서 Codex CLI 오류를 확인하세요."
}

Write-Host ""
Write-Host "PASS: 로컬 ChatGPT/Codex 구독을 통한 문장화가 동작했습니다."
