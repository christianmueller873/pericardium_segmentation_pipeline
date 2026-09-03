# Evaluation

## One-time held-out Agent 2 test

The final checkpoint was evaluated on 39 annotated slices from one patient,
published as `heldout-001`. Nine unannotated slices were excluded instead of
being treated as negative ground truth.

| Metric | Pretrained | Gold-refined | Change |
|---|---:|---:|---:|
| Dice | 0.868395 | 0.927257 | +0.058862 |
| Voxel precision | 0.944999 | 0.940547 | -0.004452 |
| Voxel recall | 0.803279 | 0.914337 | +0.111058 |
| Boundary F1, 1.5 mm | 0.579443 | 0.666637 | +0.087194 |
| Mean symmetric surface distance | 3.0349 mm | 1.9719 mm | -1.0630 mm |
| HD95 | 13.7142 mm | 9.4102 mm | -4.3040 mm |

The largest remaining errors occur near the extreme annotated axial range ends.

## Fusion behavior on the held-out case

Agent 1 was not compatible with the desired whole-sac definition on this scan.
Its hard label-7 Dice was approximately 0.006 and its relative volume and
overlap failed the agreement gate. The system therefore preserved Agent 2
exactly; the fused output changed zero voxels. This is evidence that the gate
prevented a regression, not evidence of a fusion accuracy improvement.

## Operational fragmentation case

On a separate public-domain operational scan, raw Agent 2 output contained
225,277 foreground voxels across 579 components; the largest component held
22.8% of foreground. Agent 1 supplied one coherent 62,429-voxel component. The
fragmentation gate selected the coherent fallback on slices 86–93. No reference
mask was available, so this is a behavior check rather than an accuracy result.

## Interpretation

The held-out metrics are promising but limited to one patient. They must not be
described as clinical validation, external validation, or performance across 20
independent test patients. The 19 refinement patients are training data.
