param(
    [ValidateSet("start", "stop", "restart", "status", "menu")]
    [string]$Action = "menu",
    [switch]$All,
    [ValidateSet("hindsight", "backend", "frontend")]
    [string[]]$Service = @(),
    [switch]$ForceKillPort,
    [switch]$OpenBrowser
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if ($ForceKillPort) { throw "不再支持按端口终止进程，请在进程所属终端管理它。" }
if ($Action -eq "menu") {
    $OpenBrowser = $true
    $Action = Read-Host "操作 (start/stop/restart/status)"
}
# All Windows entrypoints share launcher.stack and infrastructure.processes.
# Explicit service selection is forwarded, never implemented as a separate killer.
$Arguments = @($Action) + @($Service)
if (-not $OpenBrowser) { $Arguments += "--no-browser" }
& python (Join-Path $PSScriptRoot "one_click.py") @Arguments
exit $LASTEXITCODE
