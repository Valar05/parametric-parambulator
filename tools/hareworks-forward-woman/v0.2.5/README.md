# Hareworks v0.2.5 · Backward style laboratory

> **v0.2.5 recovery:** supersedes the non-published v0.2.4 packet that stopped at `PY_PRESERVE_EXACT_RESEARCH_JSON` because of a malformed Python newline literal. The style controller and approved reference gaits are unchanged. Adds preflight AST validation of all embedded Python sections before network, GLB work, or publication.

## Owner instructions and authorization

The owner accepted the in-place procedural `Walk_Backward` v0.2.2, and accepted forward `Walking_Woman` v0.1.9. BOTH accepted implementations remain byte-for-byte unchanged. The owner requested a **controlled experiment** transferring the measurable characteristics of `Walking_Woman` vs `Walking` to the backward gait, layer by layer, only when baseline preservation gates allow it.

- Three **source** clips: `Walk_Backward`, `Walking`, `Walking_Woman` from `assets/hareworks/Hareworks-nine-clips.glb` SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6` (6,784,896 bytes), exactly 74 bones and nine source clips.
- The approved backward pose is reconstructed using an **unchanged byte copy** of v0.2.2 `inplace-kernel.mjs` and its real-source witness tests. Both visible models are driven by mathematical procedural pose evaluators; no source AnimationMixer drives either. Animation mixers operate only on separate hidden clones, once, to calibrate the original clips.
- Previous source research: the owner-exported JSON is embedded byte-for-byte as `research-priors.json` with SHA-256 `f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe`, and the browser verifies it before allowing experimental motion; 360 original poses per forward clip; 218 matched phases and 74 bones; measured Woman-vs-Walking offset `0.9777777777777777` with caveat (terminal window excluded). This experiment is NOT a claim about biological sexes.

## Correct transfer

For bone `j`, remove its *starting* source orientation from each forward source clip before comparing phase-dependent motion:

`N_j(p) = inverse(Q_normal_j(0)) * Q_normal_j(p)`;
`W_j(p) = inverse(Q_woman_j(offset)) * Q_woman_j(p+offset)`;
`D_j(p) = inverse(N_j(p)) * W_j(p)`;
`Q_trial_j(p) = Q_accepted_backward_j(p) * slerp(identity, D_j(p), layer_gain)`.

This ensures phase-zero parity and excludes fixed initial arm/hand orientations that wrecked v0.2.0. The style overlay is **not** an absolute clip pose and does not reverse the forward animation. Hips can receive dynamically measured local X/Y sway and bounce difference, but accepted backward pelvis Z remains identical; other bone translations and all scales remain approved. The terminal source keyframe is filtered by a short smooth blend in the source sampling window, not transposed as runtime locomotion.

## Four independent layers

1. Pelvis: local hips orientation and X/Y movement only, never Z travel.
2. Legs: thigh/shin/foot/toe local rotations, plus *real-skinned* low-foot position safeguards. This pilot does NOT yet solve target foot-path IK; the safety gate attenuates or rejects candidates that violate contact tolerances. Do not interpret rejected leg transfer as a finished female backward step path.
3. Torso/head: spine, neck, and head joint motion, without static offsets.
4. Arms/hands: shoulders, upper arms, forearms, hands, and fingers, independently from the legs and pelvis.

All start **OFF**. The operator enables specific layers and requests strengths, then presses **Test and apply requested layers**. The browser performs bounded tests against the left approved procedural baseline. Each layer is individually attenuated or rejected; the final combination is tested at 30/60/120 fps with half-frames and full 74-bone continuity. Only a passing combination is rendered. The viewer reports *requested vs applied* gains and rejected gates rather than silently accepting a bad result. Reset restores v0.2.2 exactly.

Foot support witnesses are inferred from the lowest existing foot positions, **not** physical force/contact sensors. Gates cover contact-ankle/toe displacement, swing-ankle displacement, root X/Z changes, head displacement, downward foot penetration relative to approved baseline, full-body temporal joint steps, and seam rotation/position. Full JSON and a CSV gain summary are stored in Termux campaign state by a local-only HTTP evidence receiver and may be downloaded from the page. Browser measurements are NOT certified at packaging time, only after running on the owner's Android browser and verified original GLB.

## Pipeline

One uniquely named checksum-verified `.sh` campaign runs through the owner's **Termux Git** lane only. It checks fresh remote `main` and canonical LFS SHA, creates an isolated checkout, enforces immutable old blobs, checks all new path collisions, SHA-verifies every embedded file, executes Node and Python tests including injected invalid reports, commits only new text outputs, pushes without force, performs exact remote Git object readback, opens a fresh no-cache local HTTP viewer, and prints its full URL, PID, port, hashes and persistent receipt. It never modifies the canonical model, original clips, or earlier accepted demo files. Owner visual acceptance remains pending.
