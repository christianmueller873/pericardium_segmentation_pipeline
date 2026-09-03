# Model artifacts

Model checkpoints are prepared as `v0.1.0` GitHub Release assets and are not
stored in ordinary Git history. They are distributed under
[`CC BY-NC 4.0`](../citations/MODEL_WEIGHTS_LICENSE.md), separately from the
MIT licensed source code.

| Model | Default location | SHA-256 |
|---|---|---|
| Agent 1 | `nnUNet_training/nnUNet_results/Dataset557_BCA_2d_regions/nnUNetTrainer__nnUNetPlans__2d/fold_0/checkpoint_best.pth` | `c893c5d8f54cb8113e43db361c9382cf3dceb693402049f67902d43d912ea95a` |
| Agent 2 | `agent2_finetune_runs/v2_gold_boundary/final/final_model.pt` | `8a0842046f37fb40f58f336651f792e505ef2b282588260d85e9fa8a9d63771b` |

Use `AGENT1_MODEL_DIR` and `AGENT2_CHECKPOINT` to point to authorized external
locations. The preflight and `/health?check_hashes=true` checks validate the
same hashes regardless of location.

Download and verify both release packages with:

```powershell
.\scripts\download_models.ps1
```

Release assets:

- `agent1_pericardium_guide_v1.zip` — `dataset.json`, `plans.json`, the frozen
  best checkpoint, its model card, model weight license, and third party notice.
- `agent2_gold_refined_v2.zip` — the frozen final Agent 2 checkpoint, its model
  card, model weight license, and third party notice.

The download script installs the expected repository-relative layout and
rejects checkpoint hash mismatches after the release is published.

Exact archive sizes and SHA-256 values are recorded in
[`release_assets_v0.1.0.json`](release_assets_v0.1.0.json). Upload the generated
`release_assets/SHA256SUMS.txt` alongside both archives in the GitHub Release.
Each package contains its model card, model weight license, and third party
notice.
