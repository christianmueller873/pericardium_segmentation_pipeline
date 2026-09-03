# Training and data lineage

## Agent 1

Agent 1 is a 2D nnU-Net v2 multi-class body-region model with 13 foreground
classes plus background. The recorded development split contained 9,204
samples: 7,386 training and 1,818 validation samples. The dual-agent application
uses only pericardium label 7. Local provenance identifies SAROS Version 1 as
the training source. SAROS annotations are CC BY 4.0; the underlying TCIA CT
collections retain separate terms.

## Agent 2 pretraining

Agent 2 learned broad anatomy from 947 CT volumes selected from the
TotalSegmentator dataset Version 2.0.1. The manifests contain 805 training and
142 validation cases. Pseudolabels came from the TotalSegmentator
`trunk_cavities` task's `pericardium` output, with 10% trimmed from each end of
the positive axial support. This stage provided the initial anatomical
representation used by later gold refinement.

The generation log did not capture the exact TotalSegmentator package version.
Version 2.18.0 was installed when provenance was audited on 2026-09-03 and is
recorded only as a current reproduction baseline.

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
the methodology without redistributing restricted artifacts. Dataset and tool
citations and release conditions are in the
[third party notices](../citations/THIRD_PARTY_NOTICES.md).
