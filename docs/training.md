# Training and data lineage

## Agent 1

Agent 1 is a 2D nnU-Net v2 multi-class body-region model with 13 foreground
classes plus background. The recorded development split contained 9,204
samples: 7,386 training and 1,818 validation samples. The dual-agent application
uses only pericardium label 7.

## Agent 2 pretraining

Agent 2 learned broad anatomy from 947 pseudo-labeled CT volumes. This stage
provided the initial anatomical representation used by later gold refinement.

## Gold-standard refinement

Manual 2D contours were converted into geometry-aware 3D targets through a
versioned pipeline that included DICOM/BMP registration, orientation checks,
canonical-grid construction, connectivity repair, and visual QA.

Nineteen accepted patients were used for refinement. A patient-level 16/3 split
selected the training length. The selected epoch was 34; the final model was
then fit for 34 epochs on all 19 accepted patients using AdamW at 1e-5 learning
rate and 1e-5 weight decay.

The objective combined 75% regional loss and 25% axial boundary-weighted loss,
including a fourfold boundary-band boost. The calibration score combined 70%
whole-sac Dice and 30% boundary F1.

## Test isolation

One patient, identified publicly as `heldout-001`, was excluded from training,
calibration, checkpoint selection, and the final-fit case list. The checkpoint
was frozen before the one-time evaluation. Public results should never expose
the internal alias used in local research files.

The held-out case must not now be used to tune fusion thresholds or retrain the
model if the reported evaluation is to retain its meaning.

## Reproducibility boundaries

Training scripts and local manifests remain available for internal provenance,
but medical volumes, derived labels, checkpoints, and patient-linked manifests
are excluded from the proposed public Git history. A public release can explain
the methodology without redistributing restricted artifacts.
