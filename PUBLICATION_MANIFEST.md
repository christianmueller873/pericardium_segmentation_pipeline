# Proposed public-file manifest

This file defines the intended first public release. It is not a staging command.

## Include

- Root: `README.md`, `LICENSE`, `CITATION.cff`, `.gitignore`, `pyproject.toml`,
  `poetry.lock`.
- Runtime: `ct_viewer.html`, `server_dual_agent_v1.py`,
  `dual_agent_fusion_v1.py`, `dual_agent_config_v1.json`,
  `dual_agent_paths_v1.py`, `preflight_dual_agent_v1.py`,
  `requirements_dual_agent_v1.txt`.
- Tests: `test_dual_agent_config_v1.py`, `test_dual_agent_fusion_v1.py`,
  `test_dual_agent_paths_v1.py`, `test_ct_viewer_smoothing.js`, and
  `test_static_demo.js`.
- Public documentation: `docs/`, `models/`, `results/`.
- Reproducibility: `scripts/` and `.github/workflows/`.
- Lightweight CI dependencies: `requirements-ci.txt`.
- Demonstration: `demo/` with the synthetic static demo and the reviewed,
  audio-free real-inference recording made from the selected public SAROS CT.
- Release assets (outside Git history): the two archives and checksum file
  produced by `scripts/package_release_models.ps1`.

## Exclude from the first release

- All medical images, labels, manifests, review galleries, and generated data.
- All model weights except the two frozen, hash-verified GitHub Release assets.
- Redundant/intermediate checkpoints, including `checkpoint_latest.pth`.
- `safe to remove/`, `uncertain/`, test outputs, caches, and local history.
- Patient-specific data-preparation, registration, finalization, and evaluation
  scripts until aliases, paths, and data assumptions are separately reviewed.
- Internal handoffs, resume dossiers, and local training-readiness notes.
- Modified upstream SAROS download/training utilities unless a change is
  intentionally required by the public inference package.

## Final gate

Before staging, compare every candidate to this manifest, scan for secrets and
personal paths, check file sizes, and show the exact staged diff to the project
owner. Do not push to the upstream SAROS remote.
