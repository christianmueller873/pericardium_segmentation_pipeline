# Model artifacts

The Agent 2 checkpoint is prepared as a `v0.1.0` GitHub Release asset and is
not stored in ordinary Git history. It is distributed under
[`CC BY-NC 4.0`](../citations/MODEL_WEIGHTS_LICENSE.md), separately from the
MIT licensed source code.

| Model | Default location | SHA-256 |
|---|---|---|
| Agent 1 | `nnUNet_training/nnUNet_results/Dataset557_BCA_2d_regions/nnUNetTrainer__nnUNetPlans__2d/fold_0/checkpoint_best.pth` | `c893c5d8f54cb8113e43db361c9382cf3dceb693402049f67902d43d912ea95a` |
| Agent 2 | `agent2_finetune_runs/v2_gold_boundary/final/final_model.pt` | `8a0842046f37fb40f58f336651f792e505ef2b282588260d85e9fa8a9d63771b` |

Agent 1 is listed for local verification only. Its checkpoint is not included
in `v0.1.0` because its SAROS training split included controlled access source
CTs and public checkpoint distribution has not been confirmed. Use
`AGENT1_MODEL_DIR` and `AGENT2_CHECKPOINT` to point to authorized external
locations. The preflight and `/health?check_hashes=true` checks validate the
same hashes regardless of location.

Download and verify the Agent 2 release package with:

```powershell
.\scripts\download_models.ps1
```

Release assets:

- `agent2_gold_refined_v2.zip` — the frozen final Agent 2 checkpoint, its model
  card, model weight license, and third party notice.

The download script installs the expected Agent 2 repository-relative layout
and rejects checkpoint hash mismatches after the release is published. Agent 1
must be supplied separately by an authorized holder.

Exact archive sizes and SHA-256 values are recorded in
[`release_assets_v0.1.0.json`](release_assets_v0.1.0.json). Upload the generated
`release_assets/SHA256SUMS.txt` alongside the archive in the GitHub Release.
The package contains its model card, model weight license, and third party
notice.
