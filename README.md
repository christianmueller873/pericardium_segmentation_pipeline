# Dual-Agent Pericardial-Sac Segmentation

A research prototype for automatic pericardial-sac segmentation in CT volumes.
It combines a coarse 2D nnU-Net anatomical guide with a precise 3D residual
U-Net and a conservative fusion layer designed to reject incompatible model
outputs rather than silently merge them.

## See it working

**[Watch the real-inference demo (75 seconds)](demo/full_pipeline_demo.mp4)**

The recording shows the complete local workflow on a public SAROS CT: loading
the volume, running both segmentation agents, reviewing the fused result, and
using the viewer's editing controls. The 1-minute-59-second inference wait is
clearly shortened in the recording, and the results portion is shown at 2x
speed. The video has no audio.

Research use only. This software is not a medical device, has not been
clinically validated, and must not be used for diagnosis or patient care.

## What this repository demonstrates

- End-to-end NIfTI inference through a FastAPI service.
- Two-model comparison plus an automatic fused result.
- Safety gates for disconnected, out-of-domain, or mutually incompatible masks.
- A browser CT viewer with slice navigation, windowing, overlay control, and
  local paint/erase/smooth/undo tools.
- Checkpoint SHA-256 verification and held-out leakage guards.
- Patient-level refinement and one-time held-out evaluation.
- A reviewed real-inference recording made from an approved public SAROS CT.

## System overview

![Dual-agent segmentation system overview](docs/system_overview.svg)

Agent 2 supplies the default boundary. Agent 1 can contribute only when its
location, volume, overlap, axial support, and connectedness are compatible with
Agent 2. The final automatic mask is restricted to one coherent 3D component.
See [`docs/architecture.md`](docs/architecture.md) for the detailed decision
path.

## Held-out evidence

Agent 2 was pretrained on 947 pseudo-labeled volumes, calibrated on a
patient-level 16/3 split, and fit on 19 accepted gold-standard patients. One
additional patient, published here only as `heldout-001`, was kept outside
optimization and checkpoint selection.

| Metric | Pretrained Agent 2 | Refined Agent 2 |
|---|---:|---:|
| Dice | 0.8684 | **0.9273** |
| Precision | **0.9450** | 0.9405 |
| Recall | 0.8033 | **0.9143** |
| Boundary F1 at 1.5 mm | 0.5794 | **0.6666** |

These measurements cover 39 annotated slices from one held-out patient. They
demonstrate improvement on that case, not population-level generalization.
Nine unannotated slices were excluded. On this scan, Agent 1 failed the
agreement gate and the fused output was exactly Agent 2, with zero changed
voxels. See [`docs/evaluation.md`](docs/evaluation.md) and
[`results/benchmark_summary.csv`](results/benchmark_summary.csv).

## Run locally

Requirements:

- Windows PowerShell and Python 3.11.
- A CUDA-capable environment containing PyTorch, MONAI, nnU-Net v2, NiBabel,
  SciPy, FastAPI, Uvicorn, and multipart support.
- Authorized Agent 1 and Agent 2 checkpoints.

The exact verified development versions are recorded in
[`docs/environment_versions.json`](docs/environment_versions.json).

Default model locations are repository-relative. They can be overridden:

```powershell
$env:AGENT1_MODEL_DIR = "D:\models\agent1"
$env:AGENT2_CHECKPOINT = "D:\models\agent2\final_model.pt"
```

Verify the environment and frozen assets:

```powershell
.\scripts\verify_installation.ps1
```

Start the API and viewer:

```powershell
.\scripts\run_ct_viewer.ps1
```

The launcher verifies the installation, starts the API on `127.0.0.1:8000`,
opens `ct_viewer.html`, and stops the hidden server process when Enter is
pressed. Full setup and troubleshooting are in [`docs/setup.md`](docs/setup.md).

## Test without model weights

```powershell
python -m unittest -v test_dual_agent_config_v1.py
python -m unittest -v test_dual_agent_paths_v1.py
python -m unittest -v test_dual_agent_fusion_v1.py
node test_ct_viewer_smoothing.js
```

The fusion and frontend tests use synthetic arrays and do not load medical
images or checkpoints.

## Repository guide

| Path | Purpose |
|---|---|
| `server_dual_agent_v1.py` | FastAPI inference and comparison endpoints |
| `dual_agent_fusion_v1.py` | Safety-gated fusion algorithm |
| `dual_agent_config_v1.json` | Frozen thresholds, hashes, and portable paths |
| `dual_agent_paths_v1.py` | Environment and repository-relative path resolver |
| `ct_viewer.html` | Local live-inference viewer and mask editor |
| `demo/` | Real-inference demonstration recording |
| `docs/` | Architecture, setup, training, evaluation, privacy, and limitations |
| `models/` | Checkpoint placement guidance and model cards |
| `results/` | Machine-readable held-out metrics |
| `scripts/` | Installation verification and launcher |

## Models and data

Model weights and medical images are intentionally excluded from ordinary Git
history. The two frozen checkpoints are distributed as hash-verified `v0.1.0`
GitHub Release assets; install them with `scripts/download_models.ps1`. No
training images or patient-derived labels are distributed. See
[`models/README.md`](models/README.md) and
[`docs/privacy_and_data.md`](docs/privacy_and_data.md).

## Limitations

The final refined model has only one held-out patient evaluation. Agent 1 was
out of domain on that case, fused accuracy has not been established on a
multi-patient external set, and no clinical-reader or regulatory validation has
been performed. Empty or incoherent results may be intentionally withheld.
See [`docs/limitations.md`](docs/limitations.md).

## Upstream work and license

This project began from the University Medicine Essen SAROS dataset repository
and retains its MIT license and copyright notice. SAROS dataset access and
citations remain governed by their original sources. See
[`docs/upstream_saros_attribution.md`](docs/upstream_saros_attribution.md),
[`citations/LICENSE`](citations/LICENSE), and
[`citations/CITATION.cff`](citations/CITATION.cff).
