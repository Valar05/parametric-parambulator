# Hareworks Walk_Backward: full-body in-place parity v0.2.2

## Owner decision

The owner **rejected v0.2.0's three-way feminine style transfer** as visually bad and explicitly reported that the backward animation's baked root travel remained. A change to wrist amplitude or a few upper-body channels is not the task. The new, narrowly scoped mission is to reproduce the source `Walk_Backward` **as accurately as practical across all 74 joints**, but **in place**. A later style transfer is out of scope until the base gait receives its own visual acceptance.

The owner has visually **accepted v0.1.9 `Walking_Woman` forward gait as a perfect match**. That viewer, v0.1.2 pelvis/v0.1.3 legs/v0.1.8 upper source-anchored equations, prior source clips and canonical model are unchanged.

## Exact source and repair

Canonical source GLB: `assets/hareworks/Hareworks-nine-clips.glb`, SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, 6,784,896 bytes, 74 joints, 9 source clips. Only `Walk_Backward` is calibrated. The original user-generated source extraction v1.0.8 confirms the hips travel from roughly `+0.1065` Z at t=0 to `-0.953415` Z at t≈0.852222s, before the **source clip's terminal reset key** returns them to +0.089648 at t=0.866667s. The reset is not physical locomotion.

1. Read the real GLB in the Android browser, SHA-256 verify bytes, and sample the source `Walk_Backward` clip at 720 poses across one cycle. Record ALL 74 local bone quaternions, positions, and scales, not just wrists or feet. These samples are only **one-time calibration evidence**.
2. Build a deterministic independent continuous phase→pose evaluator for every bone using local quaternion slerp and local position/scale interpolation. At runtime the generated rig does **not** have an AnimationMixer or any source animation tracks. This is source-calibrated kinematic reconstruction, not a dynamic physics simulator or a novel generalized motion controller.
3. Detect the genuine late `mixamorigHips` Z teleport from an outlier in its forward-time derivative. Fit the unwrapped horizontal cycle travel from the clean pre-reset section. Subtract that **X/Z trend only**, retaining pelvis Y bobbing, all 74 joint rotations and all joint articulation. Keep an isolated original reference on the left, source-posed for comparison and with the same horizontal detrend.
4. Adaptively choose a source-faithful terminal repair region (starting at 93%, extending as needed for 30/60/120Hz joint continuity) and repair the final region with a periodic C1 quaternion-vector and translation/scale Hermite bridge derived from the source's terminal *clean* joint poses and the source's first poses/velocities. Do not interpolate through the source's bogus reset key, which would produce a roughly 1 m hitch. Every repaired frame is marked as the terminal seam region and is excluded from the normal-source parity score.
5. Audit ALL 74 skinned bones at matching 30/60/120 Hz plus half-frames before the seam, comparing local quaternion, translation, scale, and resulting world-space joint positions. Report per-joint RMS, maximum and worst timestamp; verify generated seam closure and 30/60/120Hz step continuity. Parity warnings are visible rather than hiding the character.

**Critical physical distinction:** an in-place animation will move feet against a motionless display grid; game movement applies external world travel. This campaign does not promise stationary world foot contacts while preventing the model from translating. The intended acceptance is a fixed-origin, source-faithful backward cycle with a smooth seam.

## Delivery and limits

The Android Termux Git campaign has one versioned shell entrypoint. It verifies remote parent, pinned `AGENTS.md`, exact GLB LFS pointer and binary hash, collision-free new paths, preserved approved forward viewer blob, JS/kernel negative tests and real-extraction witness, per-file hashes, scoped Git commit/push, remote file byte readback, no-cache HTTP availability and a dynamically assigned local viewer URL. Only `tools/hareworks-forward-woman/v0.2.2/**` and the corresponding new campaign script are allowed Git mutations. It does not write a new GLB or edit a historical version.

Browser source calibration, actual skinned parity, device rendering, and owner visual approval remain distinct gates. A synthetic or source-extraction fixture pass is **not** proof the actual runtime gait matches. Source parity cannot legitimately be claimed for the intentionally rewritten last seam interval. Future feminine interpretation must be a separate authorized campaign after the backward source baseline is visually accepted.

## v0.2.2 startup repair (owner Android screenshot 5408.png)

The real browser v0.2.1 stopped with `SOURCE_TERMINAL_ROOT_RESET_NOT_DETECTED`, leaving the source first frame and the generated rig unposed in its bind/rest configuration. The GLB terminal reset can occur exactly at clip.duration, while the 720 source calibration samples intentionally omit that key. The old mandatory sampled-jump gate was invalid. This revision makes the sampled jump optional, records raw root track terminal-key evidence separately, and computes backward travel from a clean mid-cycle window. The continuous terminal seam still covers the end of the cycle.

The viewer first loads the actual GLB and lets the original reference run independently even if procedural calibration fails. It hides the uninitialized generated bind pose. Successful startup MUST compare all 74 bones at phase zero for local rotation, translation, scale and world positions, rejecting mismatches rather than showing a false gait. Generated uses no source mixer; no feminine style delta. Real phone proof remains pending.
