# Hareworks Woman Forward upper source-anchor repair v0.1.8

## Defect and repair

Owner's v0.1.7 JSON reports 101 parity violations for both distinct 70%/3 and 100%/4 curves. Left upper arm local rotation error approximately 68 degrees, neck approximately 24 degrees. The rig and injection gate ran correctly. Source inspection found that `seedMixer.stopAllAction()` can restore generated joints to their rest/bind pose after sampling time zero, while the old `fitVectorSeries` applies a periodic delta constrained to zero at gait phase zero. Those two baselines are not necessarily equal.

v0.1.8 samples **the original `Walking_Woman` source local quaternion and local translation at phase zero**, stores that as the absolute upper-body baseline, and fits a continuous 12-harmonic-capable periodic rotation/translation delta **relative to the source's actual first pose**. The generation loop evaluates fitted functions only. It never plays source upper tracks on generated. Previous comparison presets 70%/3 and 100%/4 remain for direct measurement; new 100%/12 tests whether remaining error is due to harmonic underfitting.

This is a **targeted upper-body correction**, not a claim of novel balancing, true physical walk, world root travel or full procedural locomotion.

## Hard gates

- Exact source 74-joint original GLB SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, `Walking_Woman`, all nine clips unchanged.
- **Actual skinned rig time-zero local upper rotations** <0.001 degrees; local translations <1e-6 and world joint origins <0.0001 model units, after known side-by-side offset removed. Failure stops parity certification but leaves viewer rendered.
- Real reference vs generated parity at 30/60/120Hz with midframes: ≤2 degrees RMS, ≤5 degrees maximum per upper local rotation; ≤0.01 model unit RMS for upper and lower world joint origin positions. Any above threshold remains REJECTED, no silent relaxation.
- Stable distinct preset sensitivity: 70%/3 vs 100%/4. Three independently measured presets 70%/3, 100%/4, 100%/12.
- Real-rig injected unreachable-knee fault must leave all 74 generated bones restored (position, quaternion, scale). Snapshot comparison is sign-invariant and component-based.
- Node regression: known 81-degree source-zero/bind mismatch, exact phase-zero pose for all amplitudes and 3/4/8/12 harmonics, cycle seam, Fourier reconstruction and deliberate invalid inputs.

## Immutable constraints and authority

**Leg and pelvis behavior is locked:** v0.1.3 `foot-kernel.mjs` and `foot-profile.json`, v0.1.2 `pose-kernel.mjs` and `motion-profile.json`. No GLB, weights, mesh, reference animation, source clips, `AGENTS.md`, or existing versioned files are modified. Full visual approval remains pending. New source/verification files only at `tools/hareworks-forward-woman/v0.1.8/` and `campaigns/hareworks-forward-woman-upper-anchor-v0.1.8.sh`.

Campaign source is built against Git main commit `2735267ab41a199949f83af26e1db2b6a529ab05`. Mandatory live `AGENTS.md` Git blob `547c2af52303f4efb718bbf8f82a698110c7bfca` and Home Center Campaign Etiquette `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI` and Top-down Etiquette `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU` were freshly read for this authoring. Execution/publication occurs only through the owner's pinned SHA-checked Android Termux Git script. Remote readback and physical browser review remain separately required.
