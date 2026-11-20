# Hareworks Forward Woman: reach / knee / foot continuity proof v0.1.3

**Mission boundary:** Repair the user's rejected v0.1.2 foot and knee motion on the actual 74-joint, nine-clip Hareworks skinned GLB. Forward `Walking_Woman` in-place reference versus generated motion **only**. Preserve v0.1.2 independent pelvis/hip equations and upper-body reference treatment exactly. No turning, walking backward, strafing, world-root locomotion, foot-plant controller, asset replacement, or alteration of the old campaigns.

**Owner's evidence:** high-frame-rate recording `5361.mp4` revealed foot popping; the v0.1.2 viewer reported `BLOCKED_REAL_RIG_UNREACHABLE_KNEE` at hip-to-ankle distances about 0.736–0.740. The precise skinned behavior of this release still needs the user's review.

## Changes and why

1. The old v0.1.1 ankle path used a simplified stance/swing forward interpolation and independent vertical/lateral harmonics. It occasionally requested geometry outside the actual physical reach in v0.1.2. New **six-harmonic ankle trajectory** is fitted in pelvis-yaw-relative, hip-relative coordinates from the exact `Walking_Woman` 60 Hz joint extraction, using 30 even-index training samples and 30 odd-index held-out samples. It has C-infinity periodic position continuity. Forward reach is ~0.394 left and ~0.402 right, close to source measurements.
2. The moving **knee-bend pole** is fitted from measured reference knee-plane normals instead of using a fixed pole, preserving the bend side throughout the cycle. Each frame still solves knee position using actual upper and lower anatomical lengths. There is **no silent target clamp**; an unreachable leg remains a hard diagnostic error.
3. The old foot twist used five Newton iterations against a world-yaw target and could produce discontinuities or singularities. New foot orientation uses one deterministic swing-to-toe alignment followed by one analytical twist around the toe axis. The generated foot does not read original clip ankle rotations at runtime. Rotation continuity and mismatch from the original are measured against the live GLB.
4. A failing frame now **rolls back all generated bone positions/quaternions/scales** atomically, rather than leaving half a pose on screen. A deliberate injected unreachable-right-leg test must fail and verify the previous real-skinned pose is restored.
5. Playback defaults to **60 fps**, selectable 30, 60 or 120 fps, with loop and the original orbit/zoom camera. The actual-rig gate samples full **30/60/120 Hz** cycles plus wraparound, measures hip/knee/ankle/toe errors and every successive leg joint quaternion step, and checks the injected failure. It runs automatically on load and can export a full JSON receipt from the viewer.

## Offline source fit (not runtime acceptance)

The source is the user's browser-exported `hareworks-nine-clip-gait-and-idle-turn-v1.0.8.json`, hash-labelled canonical GLB `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`. The new profile retains 6 sine/cosine pairs per component rather than samples/keyframes. Node/Python tests evaluate held-out source poses and check the actual fitted ankle and knee targets at 30, 60, 120 and 240 Hz.

| Offline held-out sample RMS | Left | Right |
|---|---:|---:|
| Ankle position | 0.001629 | 0.001751 |
| Anatomical knee position | 0.003043 | 0.003575 |
| Minimum geometry reach margin | 0.002317 | 0.001025 |

These are **mathematical fit results**, not proof that the skinned mesh is good or that its feet plant. The actual skinned pose uses the existing nonuniform 5-node Hareworks leg chains; failure to meet numerical gates is reported, not dismissed.

## Acceptance gates and limitations

- Real 74-joint GLB is pinned by exact LFS SHA/size; original `Walking_Woman` clip is compared with generated motion from multiple viewing angles. Source model is read-only and copied only to an isolated HTTP viewer snapshot.
- The generated side must have no original hip, root, or leg animation tracks. The original `Walking_Woman` serves only the reference and unchanged upper-body subtree on generated side.
- Automated real-model diagnostics: 29 frames at 30 fps, 58 at 60 fps, 116 at 120 fps; all expected frames must evaluate; both feet move ahead of the hips; no unreachable knee; ankle residual <= 0.008 model units; 3D knee and ankle reference discrepancies <= 0.05 and <= 0.04 respectively; maximum per-sample joint quaternion changes at 30/60/120 fps <= 30/18/11 degrees; no injected-fault pose corruption. These limits are explicit provisional tests, **not visually accepted thresholds**.
- No claim of fully independent world locomotion, planted outsole or friction, accepted physics, validated heel-ground force, or polished gait. The fitted pelvis, toe vectors and ankle yaw remain phase-based and source-calibrated. A real video or owner's review is required for quality approval.
- If a physical test fails, preserve the viewer and export the exact failure, then refine within this original forward-leg-only scope. Do not retroactively call the experiment successful.

## Authority, provenance and transport

- Repo: `Valar05/parametric-parambulator`, `main`. Parent commit is pinned at campaign generation.
- Rules: root `AGENTS.md`, Home Center Campaign Etiquette ID `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`, Top-Down Etiquette ID `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU` reread on 2026-11-20.
- Publication: **Termux Git only**, fresh isolated snapshot, unique paths, hash-pinned embedded files, scope-only staging, exact remote commit/tree readback. Original GLB, source clips, v0.1.1/v0.1.2, Repl, and Boneforge are immutable.
- Results: Termux launch verifies Git + local HTTP byte serving; Android WebGL and true skinned gait gate execute separately inside the viewer; owner visual approval is last. No local host test can stand in for Termux execution or browser evidence.
