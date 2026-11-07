$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:FEISHU_WEBHOOK_URL = [Environment]::GetEnvironmentVariable('FEISHU_WEBHOOK_URL', 'User')
if (-not $env:FEISHU_WEBHOOK_URL) { throw 'Missing Feishu environment variable' }
python -X utf8 -m radar --send
exit $LASTEXITCODE
