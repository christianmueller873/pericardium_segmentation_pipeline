# Limitations and intended use

## Intended use

This repository is an engineering and research demonstration of CT
segmentation, model comparison, and safety-gated fusion. It is intended for
software review, reproducibility work, and controlled research experiments.

## Known limitations

- Final accuracy was measured on only one held-out patient.
- Agent 1 and Agent 2 do not always share a compatible label definition or scan
  domain.
- Fusion has not been evaluated on a multi-patient external reference set.
- The held-out reference contains unannotated slices and is not an independent
  multi-rater clinical consensus.
- Extreme superior and inferior range ends remain difficult.
- Sequential inference is optimized for a 6 GB GPU and may be slow.
- Browser edits exist only in the current session and are not exported.
- An empty or incoherent automatic prediction may be withheld by design.
- No uncertainty calibration, expert-reader study, regulatory review, or
  prospective clinical evaluation has been completed.

## Prohibited interpretation

Do not use this software for diagnosis, treatment planning, clinical triage, or
any patient-care decision. Do not describe the reported metrics as population
performance or clinical effectiveness.
