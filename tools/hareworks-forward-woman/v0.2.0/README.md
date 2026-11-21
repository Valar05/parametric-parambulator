# Hareworks three-clip backward Woman transfer v0.2.0

## Owner commission

The owner explicitly visually accepted **v0.1.9 generated forward `Walking_Woman`**, calling it a perfect match. Preserve it exactly, including the earlier v0.1.3 lower-body controller, v0.1.2 pelvis motion and v0.1.9 pelvis tilt improvement. This experiment creates **backward walking with a woman's style**, not an ordinary reproduction of the source `Walk_Backward` clip.

## Three-way construction

Verified actual source GLB `assets/hareworks/Hareworks-nine-clips.glb` (SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`) contains exactly nine animation clips. Relevant clips: `Walking` (1.033333 s), `Walking_Woman` (0.966667 s), `Walk_Backward` (0.866667 s). Same 74-bone skeleton.

1. Sample all 74 joint local transforms in `Walking`, `Walking_Woman`, and `Walk_Backward` at 240 evenly spaced periodic phases per clip using the real GLB and Three.js AnimationMixers in the browser. The generated fourth character **has no mixer** and runs no source animation clip tracks after the one-time calibration.
2. For each backward phase, phase-align to forward-normal and woman-forward using piecewise affine warps between the **left/right ground-near contact candidates** identified in the exact-GLB v1.0.8 skinned witness extraction. These are heuristics, not measured forces. Raw timestamps or a simple reverse-phase assumption would not align stance between the different-length animations.
3. Calculate each joint's local rotation delta `inverse(Q_Walking) * Q_Walking_Woman`, and the local position delta `P_Walking_Woman - P_Walking` at the contact-aligned normalized phase.
4. Compose the new backward joint rotation as `Q_Walk_Backward * slerp(identity, delta, strength)`, and position as `P_Walk_Backward + strength * deltaPosition`. The **backward pelvis's local Z component is invariant**: no forward root travel is imported. Its hip X sway, hip Y bounce, and all 74 local rotations remain eligible for transferred style.
5. Use the generated model for backward comparison, with original `Walk_Backward` beside it. A source-pair toggle shows `Walking` alongside `Walking_Woman`, proving the upstream style relationship. A link returns to the immutable v0.1.9 forward viewer.

This is a true three-clip **source-calibrated local-bone delta transfer** in the same skeletal space, not an authored blend clip, a reversed woman's forward animation, or a general physics locomotion controller. It does not modify the original GLB or add another GLB. The generated pose is composed mathematically from sampled source data.

## Acceptance and safety

- First owner acceptance is the **v0.1.9 forward gait only**. A successful v0.2.0 Git commit or smooth numerical curve does NOT mean backward gait acceptance.
- Visual A/B original backward against generated transfer, plus source forward pair. Default style = 100%; 0% is explicitly a negative-control baseline, never a purported female backward gait.
- Retain original backward foot orientation and pelvis backward Z, measure joint-position deviations from the source and continuity at 30/60/120 Hz with half-frame samples and near-cycle seam. Identify possible foot-contact distortion as review warnings, not a silent switch to the unstyled clip.
- Source clips have different periods, and near-ground witness windows are heuristic. The phased style delta may not satisfy new barefoot contact constraints until the owner reviews the result. Do not claim contact dynamics proven by a hip/channel test.
- Abort source load on a missing clip, unexpected 74-joint topology, wrong source GLB hash, corrupt calibration, wrong source-pair identity, or no measurable woman-vs-normal style difference.
- Do not overwrite any historical path. The uniquely versioned Termux campaign publishes only seven text files, verifies the Git remote commit and blob readback, hosts a no-cache viewer with a fresh port, and prints its complete localhost URL and persistent receipt. The actual Android browser is the real-rig execution authority; host tests are not that evidence.

## User control and next iteration

Use side, front, overhead and oblique orbit views, `Backward` and `Forward sources` modes, motion strength slider and per-timestamp scrubber. Run audit and export the JSON. Judge foot planting, backwards travel, feminine weight transfer, arms/torso integration, and smooth cycle boundary before approving. If a style candidate produces an implausible foot movement, revise the style-transfer contact weights or phase mapping, **not** the accepted v0.1.9 forward gait.
