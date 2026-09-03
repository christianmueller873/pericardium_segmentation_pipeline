# Agent 1 model card

## Summary

Agent 1 is a frozen 2D nnU-Net v2 multi-class body-region model. The dual-agent
system consumes only label 7, pericardium, as a coarse anatomical guide and
range-end safety net.

## Recorded training context

- 13 foreground classes plus background.
- 9,204 total 2D samples.
- 7,386 training and 1,818 validation samples.
- Frozen checkpoint: `checkpoint_best.pth`.
- SHA-256: `c893c5d8f54cb8113e43db361c9382cf3dceb693402049f67902d43d912ea95a`.

## Use in fusion

Agent 1 cannot modify a coherent Agent 2 prediction unless agreement and
connectedness gates pass. It can be displayed independently for review.

## Limitations

The label-7 output was strongly out of domain on `heldout-001` and failed the
agreement gate. It must not be described as a validated whole-sac model for all
scan domains. The frozen checkpoint is distributed in the `v0.1.0` GitHub
Release, subject to the repository license and this model card.
