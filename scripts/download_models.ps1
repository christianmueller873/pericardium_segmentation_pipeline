[CmdletBinding()]
param(
    [string]$Repository = "christianmueller873/pericardium_segmentation_pipeline",
    [string]$ReleaseTag = "v0.1.0",
    [string]$DestinationRoot,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $DestinationRoot) { $DestinationRoot = $projectRoot }
$destination = [System.IO.Path]::GetFullPath($DestinationRoot)
$agent1Target = Join-Path $destination "nnUNet_training\nnUNet_results\Dataset557_BCA_2d_regions\nnUNetTrainer__nnUNetPlans__2d"
$agent2Target = Join-Path $destination "agent2_finetune_runs\v2_gold_boundary\final"
$agent1Checkpoint = Join-Path $agent1Target "fold_0\checkpoint_best.pth"
$agent2Checkpoint = Join-Path $agent2Target "final_model.pt"
$agent1Expected = "c893c5d8f54cb8113e43db361c9382cf3dceb693402049f67902d43d912ea95a"
$agent2Expected = "8a0842046f37fb40f58f336651f792e505ef2b282588260d85e9fa8a9d63771b"

function Test-ExpectedHash([string]$Path, [string]$Expected) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -eq $Expected
}

if ((Test-ExpectedHash $agent1Checkpoint $agent1Expected) -and
    (Test-ExpectedHash $agent2Checkpoint $agent2Expected)) {
    Write-Host "Both verified checkpoints are already installed."
    exit 0
}

foreach ($path in @($agent1Checkpoint, $agent2Checkpoint)) {
    if ((Test-Path -LiteralPath $path) -and -not $Force) {
        throw "A checkpoint already exists but is not the expected frozen artifact: $path. Use -Force only after reviewing it."
    }
}

$temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$temporaryDirectory = Join-Path $temporaryRoot ("dual-agent-models-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temporaryDirectory | Out-Null

try {
    $baseUrl = "https://github.com/$Repository/releases/download/$ReleaseTag"
    $agent1Archive = Join-Path $temporaryDirectory "agent1_pericardium_guide_v1.zip"
    $agent2Archive = Join-Path $temporaryDirectory "agent2_gold_refined_v2.zip"
    Invoke-WebRequest -Uri "$baseUrl/agent1_pericardium_guide_v1.zip" -OutFile $agent1Archive
    Invoke-WebRequest -Uri "$baseUrl/agent2_gold_refined_v2.zip" -OutFile $agent2Archive

    New-Item -ItemType Directory -Path $agent1Target, $agent2Target -Force | Out-Null
    Expand-Archive -LiteralPath $agent1Archive -DestinationPath $agent1Target -Force:$Force
    Expand-Archive -LiteralPath $agent2Archive -DestinationPath $agent2Target -Force:$Force

    if (-not (Test-ExpectedHash $agent1Checkpoint $agent1Expected)) {
        throw "Downloaded Agent 1 checkpoint failed SHA-256 verification."
    }
    if (-not (Test-ExpectedHash $agent2Checkpoint $agent2Expected)) {
        throw "Downloaded Agent 2 checkpoint failed SHA-256 verification."
    }
    Write-Host "Both model packages were installed and SHA-256 verified."
}
finally {
    $resolvedTemporary = [System.IO.Path]::GetFullPath($temporaryDirectory)
    if ($resolvedTemporary.StartsWith($temporaryRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $resolvedTemporary)) {
        Remove-Item -LiteralPath $resolvedTemporary -Recurse -Force
    }
}
