# Demonstrations

Open `index.html` directly or publish this directory with GitHub Pages.

The interactive static demonstration contains only deterministic, anatomy-like
pixels and illustrative masks generated from simple geometric functions. It
contains no medical images, patient-derived labels, model checkpoint, or live
inference.

Its purpose is to demonstrate:

- Fused, Agent 1, and Agent 2 selection.
- Slice navigation and CT-style window controls.
- Overlay visibility and opacity.
- Browser-session paint, erase, smooth, and reset behavior.
- Clear separation between a static interface demonstration and the local
  Python inference system.

The shapes must not be interpreted as model predictions or accuracy evidence.

## Real local inference recording

`assets/full_pipeline_demo.mp4` is a separate, reviewed recording of actual
local inference on an approved public SAROS CT. The long idle inference wait was
removed, the results portion is shown at 2× speed, and audio was removed. The
recording demonstrates operation of the research prototype; it is not clinical
validation or a performance benchmark.
