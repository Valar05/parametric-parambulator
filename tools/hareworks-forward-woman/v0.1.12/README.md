# Hareworks v0.1.12: source-derived biped IK gait

**Stage:** Termux-publishable candidate for owner visual review. No automatic visual approval.

## Mission

Replace v0.1.11's guessed `0.55` duty, smoothstep foot travel, additive sine lift, and fixed foot pitch with measured `Walking_Woman` skinned heel/sole/toe/ankle trajectories and quaternion foot orientation. Preserve one translating, skinned character, a stationary-world contact frame, fixed-follow camera, real two-bone 120 Hz leg IK, and source-fitted torso. The reference animation is sampled only at initialization; there is no visible-actor `AnimationMixer`, no source leg joint rotation playback, and no changes to the GLB or accepted existing versions.

## Evidence and limitations

- Original GLB expected SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6` (6,784,896 bytes, 74 bones, nine clips).
- The baseline `Walking_Woman` source is sampled at 360 gait phases, with real skinned heel, sole and toe witnesses, ankle position and foot orientation.
- Contact windows are inferred from the observed contiguous low-contact episode at adaptive measured thresholds; not force plate evidence. Ambiguity or implausible left/right separation blocks runtime calibration, not replaced by a fixed duty.
- Heel, sole and toe constitute distinct measured contact-pivot modes, each retaining a world anchor while active. During pivot transfers the anchor is captured from the most recent solved skinned position. During swing, interpolation uses the **measured source displacement residual**, not a generic sine or smoothstep. Root travel per cycle is derived from both source ankles’ measured forward excursions rather than selected with a stride slider.
- Some authored clip source resets may be smoothed only in the last 7% of the phase loop, with exact seam changes disclosed. Source pelvis and upper animation motion remain from the existing fitted system.
- **Physical gate:** skinned active-contact drift per foot <=0.025 model units, world anchor stationary while the same contact pivot is active, ground intrusion <=0.020, no IK reach errors, actual world travel and fixed camera offset. Logs include all-three pivot penetration and source ankle RMS.
- **Independent style gate:** phase-aligned source ankle RMS is an advisory metric, not proof of resemblance. Owner must judge gait character against accepted v0.1.9. No code/test output can set `ownerVisualAcceptance=true`.
- Foot witness selection is based on skinned vertices near the relevant anatomical bone. The 3D source's contact truth is inferred, and no force solver is claimed. If the source's heel/toe shape is unsuitable, report precisely instead of inventing style.

## Runtime

From a verified Android Termux launcher, the SHA-locked campaign checks repository HEAD, `AGENTS.md`, the true model hash and unique version path, then generates/tests the new viewer in the persistent user-owned Git checkout at ~/storage/documents/GodotProjects/parametric-parambulator. The r4 GodotProjects launcher keeps a persistent normal Git checkout in Android Documents. It disables all automatic LFS smudging (including the missing Repl.glb object), selectively fetches ONLY the required Hareworks model if absent, and installs it into the checkout ONCE. The r4 gate repairs the per-repository LFS clean filter and permits only the exact SHA-verified materialized binary's unstaged status; unrelated changes still block. Android shared storage does not reliably support hardlinks. It reuses a private verified LFS cache and never downloads the GLB on every run. It commits solely `tools/hareworks-forward-woman/v0.1.12/`, pushes through Termux Git (no force), readbacks exact remote commit, and starts a cache-proof local review server. The printed complete URL is the actual running server only after an HTTP check; the browser must still load and audit the physical rig. The script retains JSON receipts under `~/.local/state/hareworks-woman-source-v0.1.12-r4-documents/`.

On successful publishing the model remains unchanged, the viewer is a *candidate*, and owner gait approval remains pending. Source bibliography is in Home Center Drive: https://docs.google.com/document/d/1dbxbhHIfaJO731l5g1O7fU91xQ6ztiRkLULOmYnEZpM/edit
