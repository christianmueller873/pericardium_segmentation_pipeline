[CmdletBinding()]
param(
    [switch]$SkipHashes,
    [string]$PythonExecutable = $env:DUAL_AGENT_PYTHON
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

function Resolve-ProjectPython {
    if ($PythonExecutable) {
        if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
            throw "DUAL_AGENT_PYTHON does not point to a Python executable: $PythonExecutable"
        }
        return [pscustomobject]@{
            File = (Resolve-Path -LiteralPath $PythonExecutable).Path
            Prefix = @()
            Description = "DUAL_AGENT_PYTHON"
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
            Description = "Poetry environment"
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return [pscustomobject]@{
            File = $pythonCommand.Source
            Prefix = @()
            Description = "python on PATH"
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return [pscustomobject]@{
            File = $pyLauncher.Source
            Prefix = @("-3.11")
            Description = "Windows Python launcher"
        }
    }

    throw "Python was not found. Install the Poetry environment or set DUAL_AGENT_PYTHON to the environment's python.exe."
}

$runner = Resolve-ProjectPython
$arguments = @($runner.Prefix) + @("-B", (Join-Path $projectRoot "preflight_dual_agent_v1.py"))
if ($SkipHashes) {
    $arguments += "--skip-hashes"
}

Write-Host "Using $($runner.Description)."
Push-Location $projectRoot
try {
    & $runner.File @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
