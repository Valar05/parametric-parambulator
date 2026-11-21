# Hareworks forward `Walking_Woman`: verified comparison v0.1.7

## Mission

Repair a **broken measurement instrument**, not animation. The owner uploaded v0.1.6 real-rig parity reports. Both 70%/3-harmonic and 100%/4-harmonic trials reported identical measurements and 101 violations because the prior code set HTML selector `.value = String(strength)` (`"0.7"`, `"1"`) while the selectors expose `"0.70"` and `"1.0"`. The browser resolved invalid values to empty strings, causing `Number('') === 0` and frozen upper-body output. Those reports cannot certify upper-body accuracy.

This v0.1.7 comparison feeds *explicit numeric preset objects* through the real generated pose algorithm, independent of any HTML input. Before either tolerance test it evaluates multiple phases on the actual skinned rig and proves that the presets differ. Identical snapshots or identical aggregate measurements produce `VERIFIER_INSTRUMENT_BLOCKED` and prevent a misleading accepted result.

## Rollback test correction

v0.1.6 `poseMatches` compared quaternion values with `THREE.Quaternion.angleTo`, which can report a nonzero angle near floating-point precision even when all quaternion components were restored by `copy`. The new rollback auditor compares sign-invariant quaternion *components* directly (`q` and `-q` represent the same rotation), plus each original bone's local position and scale, to tolerance 1e-12. An intentionally injected unreachable leg must throw; the test snapshots all 74 generated bones, restores the pose, reports the first offending bone/property and maximum error, and only then passes. No flighty `acos(1-epsilon)` comparisons.

## Protected behavior

- **No changes to v0.1.2 pelvis, v0.1.3 foot and knee solver, v0.1.5 upper-body Fourier equations, original GLB or nine clips.**
- Only verifier parameter transport, sensitivity checks, rollback diagnostics, UI identity and evidence schema change in this new versioned viewer.
- Reference left continues playing original source; generated right evaluates source-fitted curves without original tracks during playback.

## Acceptance

At 30/60/120 Hz and half-frames on the **real skinned 74-bone model**, measure local upper rotations (RMS ≤2°, maximum ≤5°), upper and lower joint world positions (RMS ≤0.01 model units), joint identity and worst timestamp. These provisional thresholds stay fixed. A failing upper-body reconstruction is explicitly rejected and is not automatically modified by this campaign. Export both preset results and sensitivity evidence. Also report an independent 30/60/120 Hz leg continuity audit and named rollback diagnostics. Owner visual approval remains mandatory.

## Deployment

User-operated SHA-verified **Termux Git only** with isolated pinned checkout, immutable GLB SHA, unique scoped new files, no force push, exact Git readback, correct JS/JSON/model HTTP manifest, fresh no-cache URL, and persistent JSON receipt. `AGENTS.md` Git blob 547c2af52303f4efb718bbf8f82a698110c7bfca and live Campaign Etiquette / Top-down Etiquette were read 2026-11-20. Source parent pinned to 4fd719375d50a510f594119575fd3399e3e2c04b. In-chat script creation is not publication, and an HTTP test is not Android WebGL or human visual approval.
