# Privacy, medical data, and publication policy

No medical image, DICOM object, NIfTI volume, patient-derived mask, patient-linked
manifest, or review gallery is approved for public Git history by default.

## Public repository policy

- Use synthetic data for the GitHub Pages demonstration.
- Publish only aggregate or neutralized evaluation results.
- Replace internal patient aliases with identifiers such as `heldout-001`.
- Do not expose filenames, DICOM headers, accession numbers, dates, local paths,
  screenshots, terminal history, or browser notifications.
- Keep model checkpoints out of ordinary Git history. Publish only the two
  frozen, hash-verified packages documented in `models/README.md` as GitHub
  Release assets.
- Never use `git add -f` on ignored medical/model paths.

## Local protections

`.gitignore` excludes data directories, gold-standard labels, nnU-Net working
directories, checkpoints, generated diagnostics, review runs, local rollback
folders, and common medical/model binary extensions.

Ignore rules are a safety layer, not proof of deidentification. Every staged
file must still be reviewed before the first push.

## Real demonstration recording

A real local inference recording may use the selected public SAROS CT after
frame-by-frame review. It must not show patient aliases, personal paths, hidden
notifications, or restricted image content. See `docs/demo_recording.md`.
