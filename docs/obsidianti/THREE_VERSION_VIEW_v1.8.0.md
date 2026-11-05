# Obsidianti three-version comparison viewer v1.8.0

## Commission

Read-only phone viewer, side-by-side Lionheart and Obsidianti. Toggle hides Lionheart including its animation dropdown and controls. Target version selector offers **exactly three distinct** Obsidianti GLBs: canonical rejected baseline, v1.5.6 Heavy1 improved review candidate, and v1.7.0 multi-action unapproved review candidate. Preserve independent animation selection and synchronized proportional timeline. The v1.5.6 target is default; canonical is selectable but never default.

## Evidence and authority

All output is from **one SHA-verified Termux Git launcher**. No ChatGPT connector writes, desktop execution, model mutations or silent substitutes. Actual completed v1.7.0 Termux receipt and surviving review GLB/source Lionheart GLB must exist on the phone. The v1.5.6 ZIP is selected only by its exact SHA-256, and its GLB by its expected hash. Canonical LFS binary must match pinned SHA. If v1.7.0 is missing, fail honestly rather than calling an older model v1.7.0.

Before publishing versioned viewer source, the campaign checks 23 matching animation names, identical topology/mesh/skin across all three versions, preservation of Heavy1 in the v1.7.0 candidate, and action-specific GLB sampler differences. Saves measurements.json, model hashes, artifact receipt and a live no-cache HTML viewer URL. Only new runner/viewer/docs source files are committed and pushed through Termux Git with remote SHA readback. Canonical model remains unchanged; visual acceptance pending.

## UI and regression requirements

Lionheart visibility toggle removes its canvas/pane and animation dropdown. Obsidianti menu switches exact model binary without changing animation selection if present. Camera positions and zoom persist between clip and model changes; no animation-pose-dependent bounding-box scale. Character framing is based on rig landmark height, independent of weapons. An optional Reframe button is explicit. All file hashes checked on load; missing animation names never silently fall back to first animation. Runtime status identifies model version/hash and selected clips.
