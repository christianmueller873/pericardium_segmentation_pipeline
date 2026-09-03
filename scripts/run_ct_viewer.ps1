[CmdletBinding()]
param(
    [string]$BindAddress = "127.0.0.1",
    [ValidateRange(1, 65535)]
    [int]$Port = 8000,
    [switch]$SkipHashes,
    [switch]$NoBrowser,
    [string]$PythonExecutable = $env:DUAL_AGENT_PYTHON
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$viewerPath = Join-Path $projectRoot "ct_viewer.html"

if (-not (Test-Path -LiteralPath $viewerPath -PathType Leaf)) {
    throw "Viewer not found: $viewerPath"
}

$verifyArguments = @{}
if ($SkipHashes) { $verifyArguments.SkipHashes = $true }
if ($PythonExecutable) { $verifyArguments.PythonExecutable = $PythonExecutable }
& (Join-Path $PSScriptRoot "verify_installation.ps1") @verifyArguments
if ($LASTEXITCODE -ne 0) {
    throw "Installation verification failed. Correct the reported dependency or model problem before starting inference."
}

function Resolve-ProjectPython {
    if ($PythonExecutable) {
        return [pscustomobject]@{
            File = (Resolve-Path -LiteralPath $PythonExecutable).Path
            Prefix = @()
        }
    }
    $poetryCommand = Get-Command poetry -ErrorAction SilentlyContinue
    $poetryPath = if ($poetryCommand) { $poetryCommand.Source } else { $null }
    if (-not $poetryPath -and $env:APPDATA) {
        $standardPoetryPath = Join-Path $env:APPDATA "pypoetry\venv\Scripts\poetry.exe"
        if (Test-Path -LiteralPath $standardPoetryPath -PathType Leaf) {
            $poetryPath = $standardPoetryPath
        }
    }
    if ($poetryPath) {
        return [pscustomobject]@{
            File = $poetryPath
            Prefix = @("run", "python")
        }
    }
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return [pscustomobject]@{
            File = $pythonCommand.Source
            Prefix = @()
        }
    }
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return [pscustomobject]@{
            File = $pyLauncher.Source
            Prefix = @("-3.11")
        }
    }
    throw "Python was not found. Set DUAL_AGENT_PYTHON to the project environment's python.exe."
}

$runner = Resolve-ProjectPython
$serverArguments = @($runner.Prefix) + @(
    "-B", "-m", "uvicorn", "server_dual_agent_v1:app",
    "--host", $BindAddress, "--port", [string]$Port
)

$serverProcess = Start-Process `
    -FilePath $runner.File `
    -ArgumentList $serverArguments `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -PassThru

$clientAddress = if ($BindAddress -in @("0.0.0.0", "::")) { "127.0.0.1" } else { $BindAddress }
$healthUri = "http://${clientAddress}:$Port/health"

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        if ($serverProcess.HasExited) {
            throw "The inference server exited before becoming ready (exit code $($serverProcess.ExitCode))."
        }
        try {
            $health = Invoke-RestMethod -Uri $healthUri -TimeoutSec 2
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $ready) {
        throw "The inference server did not become ready within 60 seconds: $healthUri"
    }

    Write-Host "Inference server ready at $healthUri"
    if (-not $NoBrowser) {
        Start-Process -FilePath $viewerPath
    }
    Write-Host "Press Enter to stop the inference server."
    [void][Console]::ReadLine()
}
finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id
        $serverProcess.WaitForExit()
    }
}
