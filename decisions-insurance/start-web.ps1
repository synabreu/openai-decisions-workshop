param([int]$Port = 8093)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& "$PSScriptRoot/.venv/Scripts/python.exe" server.py --port $Port
exit $LASTEXITCODE
