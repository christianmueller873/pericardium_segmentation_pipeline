# Local setup

## Environment

The verified development configuration uses Python 3.11, CUDA, PyTorch, MONAI,
nnU-Net v2, NiBabel, NumPy, SciPy, FastAPI, Uvicorn, and python-multipart.
The original SAROS Poetry environment also contains the dataset utilities.

Exact installed ML package versions from the working training environment are
recorded in `docs/environment_versions.json`. Do not replace a working local
environment merely to reproduce a speculative dependency lock.

From the working environment, create the sanitized version report with:

```powershell
poetry run python scripts/report_environment.py --output docs/environment_versions.json
```

The report contains only Python and package versions; it omits usernames,
machine names, filesystem paths, and environment variables. Regenerate it after
intentional environment upgrades.

## Checkpoint placement

The default configuration expects:

```text
nnUNet_training/nnUNet_results/
  Dataset557_BCA_2d_regions/
    nnUNetTrainer__nnUNetPlans__2d/
      fold_0/checkpoint_best.pth

agent2_finetune_runs/v2_gold_boundary/final/final_model.pt
```

To keep models elsewhere, set:

```powershell
$env:AGENT1_MODEL_DIR = "D:\models\agent1"
$env:AGENT2_CHECKPOINT = "D:\models\agent2\final_model.pt"
```

The expected SHA-256 hashes remain in `dual_agent_config_v1.json`; overrides do
not bypass integrity verification.

## Verify

```powershell
.\scripts\verify_installation.ps1
```

For a faster path/file/dependency check that omits hashing large checkpoints:

```powershell
.\scripts\verify_installation.ps1 -SkipHashes
```

The Windows scripts also look for Poetry in its standard user-local installation
folder when it is unavailable on `PATH`. To bypass Poetry entirely, point
directly to the project environment:

```powershell
$env:DUAL_AGENT_PYTHON = "C:\path\to\environment\Scripts\python.exe"
```

## Launch

```powershell
.\scripts\run_ct_viewer.ps1
```

Useful options:

```powershell
.\scripts\run_ct_viewer.ps1 -SkipHashes
.\scripts\run_ct_viewer.ps1 -Port 8010
.\scripts\run_ct_viewer.ps1 -NoBrowser
```

The launcher keeps the source and model directories unchanged. Uploaded scans
are copied into a request-scoped temporary directory and removed after
inference.

## Manual launch

```powershell
poetry run python -m uvicorn server_dual_agent_v1:app --host 127.0.0.1 --port 8000
```

Open `ct_viewer.html`, load an authorized `.nii` or `.nii.gz` CT, and choose
Run Segmentation. Fused is selected automatically; Agent 1 and Agent 2 remain
available for comparison.
