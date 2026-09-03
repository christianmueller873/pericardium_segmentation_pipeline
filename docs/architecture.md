# Architecture

## Responsibilities

### Agent 1: coarse anatomical guide

Agent 1 is a frozen 2D nnU-Net body-region model. Only label 7, pericardium, is
consumed. It proposes broad location and may recover a coherent region missed
near the superior or inferior range end. Other anatomical labels are disabled.

### Agent 2: precise boundary model

Agent 2 is a 12,861,646-parameter MONAI 3D residual U-Net. CT volumes are
resampled to 1.5 mm isotropic spacing, windowed to [-160, 240] HU, and processed
with a 224 × 224 × 192 sliding window. A fixed probability threshold of 0.5
produces its binary mask.

### Fusion

Agent 2 is the normal base prediction. Fusion proceeds conservatively:

1. Reject a fragmented Agent 2 result unless at least 90% of foreground belongs
   to one 26-connected component.
2. If Agent 2 is fragmented, use Agent 1 only when Agent 1 itself is coherent.
3. Otherwise require Agent 1/Agent 2 agreement in overlap, location, volume
   ratio, and shared nonempty slices.
4. Permit probability-supported Agent 1 recovery only near Agent 2 range ends.
5. Bound a hard recovery to the immediately adjacent slice, spatial continuity,
   and the anchor contour's area.
6. Withhold the automatic result when Agent 2 is completely empty and Agent 1
   cannot be independently verified.
7. Reduce every nonempty fused result to one filled 3D component.

All thresholds are centralized in `dual_agent_config_v1.json`. The synthetic
regression suite exercises normal preservation, partial recovery, hard
fallback, internal gaps, empty predictions, incompatible masks, fragmentation,
and grid mismatch.

## Runtime sequence

The development GPU has 6 GB of memory. To avoid contention, inference is
sequential:

1. Load and run Agent 1.
2. Resample its label-7 result to the native CT grid when needed.
3. Release Agent 1 and clear CUDA cache.
4. Load and run Agent 2.
5. Resample Agent 2 probabilities to the native grid.
6. Fuse masks and return diagnostics.

## API

- `GET /health` verifies dependencies available at runtime and model files;
  `?check_hashes=true` also hashes both checkpoints.
- `POST /segment` returns the fused mask in the original flat-slice schema.
- `POST /segment/compare` returns fused, Agent 1, and Agent 2 masks using
  per-slice foreground run-length encoding plus fusion diagnostics.

The viewer uses `/segment/compare`, defaults to Fused, and keeps edits separate
for each selected output during the browser session.
