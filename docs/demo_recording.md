# Real inference recording walkthrough

The public recording may use the selected public SAROS CT. Before recording,
close notifications, messaging applications, unrelated browser tabs, and any
window that could expose personal information.

## Recommended capture

1. Start the viewer with `scripts/run_ct_viewer.ps1`.
2. Open the CT and position the browser so only the viewer is visible.
3. Start Windows Game Bar recording with `Win+Alt+R`.
4. Show the loaded CT briefly, then select Run Segmentation.
5. Cut or accelerate the waiting period during editing; do not imply that the
   shortened video is real-time inference.
6. Show Fused, Agent 1, and Agent 2 on the same slices.
7. Demonstrate slice navigation, opacity, Paint, Erase, Smooth, Undo, and Reset.
8. Stop recording with `Win+Alt+R`.
9. Trim the result to approximately 30–60 seconds.
10. Review every frame for usernames, paths, notifications, and identifiers.

Target public filename: `demo/assets/full_pipeline_demo.mp4`. Keep the final
video below 100 MiB; approximately 10–30 MiB is preferable for repository use.
The README should label it as a real local inference recording on public data.

## Published edit

The reviewed public edit is 74.6 seconds, 1600×772 H.264 at 24 fps, has no
audio, and is 1,232,200 bytes. Its SHA-256 is
`9ac53ddbfecc1b59fb3fbad543e736cf7fb03d69a198c776c79791ca0b0b60d6`.
The approximately 100-second idle inference wait was replaced by a two-second
disclosure card, and the post-inference portion is shown at 2× speed. The
original 250-second capture remains in the ignored local release-assets area.
