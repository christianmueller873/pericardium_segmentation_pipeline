# Agent 2 model card

## Summary

Agent 2 is the primary precise pericardial-boundary predictor: a MONAI 3D
residual U-Net with 12,861,646 parameters.

## Inputs and inference

- CT NIfTI input.
- 1.5 mm isotropic working spacing.
- HU window [-160, 240].
- Patch size 224 × 224 × 192.
- Fixed foreground threshold 0.5.
- Native-grid probability resampling before thresholding.

## Training

- Pretrained on 947 CT volumes from TotalSegmentator dataset Version 2.0.1.
- Pretraining manifests: 805 training and 142 validation cases.
- Pseudolabel source: TotalSegmentator `trunk_cavities` task, `pericardium`
  output, with 10% trimmed from each end of positive axial support.
- Refined on 19 accepted gold-standard patients.
- Patient-level 16/3 calibration split.
- Final all-19 fit length: 34 epochs.
- AdamW, learning rate 1e-5, weight decay 1e-5.
- 75% regional and 25% boundary-weighted objective.

## Frozen artifact

- Checkpoint: `agent2_finetune_runs/v2_gold_boundary/final/final_model.pt`.
- SHA-256: `8a0842046f37fb40f58f336651f792e505ef2b282588260d85e9fa8a9d63771b`.

## Evaluation

On one held-out patient (`heldout-001`), gold refinement achieved 0.927257 Dice,
0.914337 recall, 1.9719 mm mean symmetric surface distance, and 9.4102 mm HD95.
See [`../docs/evaluation.md`](../docs/evaluation.md) for the full comparison and
interpretation constraints.

## Limitations

The result represents one patient and is not clinical or population-level
validation. Range ends remain difficult. The exact TotalSegmentator package
version used for historical pseudolabel generation was not recorded. The
checkpoint must not be published until the model weight terms and distribution
authorization described in the
[third party notices](../citations/THIRD_PARTY_NOTICES.md) are complete.
