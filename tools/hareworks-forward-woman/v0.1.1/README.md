# Hareworks v0.1.1: Straight-Ahead Woman Walk Leg Proof

**Purpose**: Replicate the leg motion of the existing `Walking_Woman` reference before revisiting world-root movement, strafing or aiming. The owner rejected v0.1.0 because its leading foot never got ahead of the body, its support leg overextended, its CCD knees snapped, and dual-stick controls were reversed. Those systems are out of scope, not reported fixed.

## Measured source

Published nine-clip Hareworks GLB SHA `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`. Browser-exported `hareworks-gait-and-idle-turn-v1.0.8.json` provides 60 approximately uniform samples per gait excluding its potentially discontinuous `t=duration` endpoint. `Walking_Woman` period approximately 0.966667s. 74 skin joints. Actual hip/knee/intermediate/ankle/toe leg chains are asserted in the viewer.

A 30Hz holdout reference check fitted a continuous-velocity stance/swing trajectory, low-order swing-height and lateral components, and an anatomical knee bend pole derived from the source measurements. Summary before actual 3D skin tests: left ankle RMS 0.0149, right 0.0180 source units; left knee RMS 0.0255, right 0.0242. The target is ~0.39–0.40 units ahead of each hip; no sampled hard reach violations. These offline measurements are *not* runtime or visual proof.

## Model comparison

Left character: original `Walking_Woman` clip. Right: *same actual skinned GLB*, torso/root track subset of `Walking_Woman`, with all named leg tracks removed from its AnimationClip. A stable fixed-pole two-link IK generates the actual hip and knee bone orientations from analytically constructed ankle targets. This is not a CCD search and does not borrow reference leg angles; the knee is derived from two link lengths and a fixed pole. The intermediate and toe local joints are maintained from the seed pose. Source ankle/world orientation is borrowed deliberately for this narrow anatomical-leg validation. Both source and generated animated bodies are displayed side-by-side at 30 fps, one cycle per playback. The exported endpoint sample may be discontinuous, so this candidate does not claim a seamless loop. A real-bone residual failure blocks the comparison rather than becoming a warning.

This is **not a complete procedural walking controller**, because the root/pelvis path and ankle roll are not independent, actual sole contact patches are not grounded, and forward world traversal is not established. The viewer is intended only to establish whether we can put the skinned legs into convincing source-like shapes without popping. Once the owner visually accepts the side-by-side comparison, we can move on to independent forward root travel and foot-plant constraints.

## Campaign discipline

Android Termux Git only, isolated SHA-pinned checkout, preflight path collision check, text-only commit, exact remote readback, protected asset-hash checks, no LFS change, local exact-source GLB verification, viewer HTTP verified, owner visual acceptance pending. No direct connector code mutation.
