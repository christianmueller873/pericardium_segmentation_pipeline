[CmdletBinding()]
param(
    [string]$OutputDirectory,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $projectRoot "release_assets"
}
$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null

$agent1Root = Join-Path $projectRoot "nnUNet_training\nnUNet_results\Dataset557_BCA_2d_regions\nnUNetTrainer__nnUNetPlans__2d"
$agent1Checkpoint = Join-Path $agent1Root "fold_0\checkpoint_best.pth"
$agent2Checkpoint = Join-Path $projectRoot "agent2_finetune_runs\v2_gold_boundary\final\final_model.pt"
$agent1Expected = "c893c5d8f54cb8113e43db361c9382cf3dceb693402049f67902d43d912ea95a"
$agent2Expected = "8a0842046f37fb40f58f336651f792e505ef2b282588260d85e9fa8a9d63771b"
$thirdPartyNotices = Join-Path $projectRoot "citations\THIRD_PARTY_NOTICES.md"
$agent1ModelCard = Join-Path $projectRoot "models\agent1_model_card.md"
$agent2ModelCard = Join-Path $projectRoot "models\agent2_model_card.md"

function Assert-Hash([string]$Path, [string]$Expected) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required model file is missing: $Path"
    }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected) {
        throw "Checkpoint hash mismatch for ${Path}: expected $Expected, found $actual"
    }
}

Assert-Hash $agent1Checkpoint $agent1Expected
Assert-Hash $agent2Checkpoint $agent2Expected
foreach ($document in @($thirdPartyNotices, $agent1ModelCard, $agent2ModelCard)) {
    if (-not (Test-Path -LiteralPath $document -PathType Leaf)) {
        throw "Required release document is missing: $document"
    }
}

$agent1Archive = Join-Path $outputRoot "agent1_pericardium_guide_v1.zip"
$agent2Archive = Join-Path $outputRoot "agent2_gold_refined_v2.zip"
foreach ($archive in @($agent1Archive, $agent2Archive)) {
    if (Test-Path -LiteralPath $archive) {
        if (-not $Force) {
            throw "Release asset already exists: $archive. Use -Force to replace verified local packages."
        }
        Remove-Item -LiteralPath $archive -Force
    }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function New-ModelArchive([string]$Destination, [hashtable]$Entries) {
    $archive = [System.IO.Compression.ZipFile]::Open(
        $Destination,
        [System.IO.Compression.ZipArchiveMode]::Create
    )
    try {
        foreach ($entryName in $Entries.Keys) {
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive,
                $Entries[$entryName],
                $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }
    }
    finally {
        $archive.Dispose()
    }
}

$sanitizedDataset = Join-Path $outputRoot ".agent1_dataset_release.json"
try {
    $dataset = Get-Content -LiteralPath (Join-Path $agent1Root "dataset.json") -Raw |
        ConvertFrom-Json
    $dataset.licence = "See THIRD_PARTY_NOTICES.md and agent1_model_card.md"
    $dataset.converted_by = "Christian Mueller"
    $dataset | ConvertTo-Json -Depth 100 |
        Set-Content -LiteralPath $sanitizedDataset -Encoding UTF8

    New-ModelArchive $agent1Archive @{
        "dataset.json" = $sanitizedDataset
        "plans.json" = (Join-Path $agent1Root "plans.json")
        "fold_0/checkpoint_best.pth" = $agent1Checkpoint
        "agent1_model_card.md" = $agent1ModelCard
        "THIRD_PARTY_NOTICES.md" = $thirdPartyNotices
    }
    New-ModelArchive $agent2Archive @{
        "final_model.pt" = $agent2Checkpoint
        "agent2_model_card.md" = $agent2ModelCard
        "THIRD_PARTY_NOTICES.md" = $thirdPartyNotices
    }
}
finally {
    if (Test-Path -LiteralPath $sanitizedDataset) {
        Remove-Item -LiteralPath $sanitizedDataset -Force
    }
}

$sumLines = foreach ($archive in @($agent1Archive, $agent2Archive)) {
    $hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $([System.IO.Path]::GetFileName($archive))"
}
$sumPath = Join-Path $outputRoot "SHA256SUMS.txt"
[System.IO.File]::WriteAllLines($sumPath, $sumLines, [System.Text.Encoding]::ASCII)

Write-Host "Release assets created in $outputRoot"
Get-Item -LiteralPath $agent1Archive, $agent2Archive, $sumPath |
    Select-Object Name, Length, LastWriteTime
