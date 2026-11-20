# Hareworks Forward Woman Proof v0.1.2 | Independent pelvis and foot orientation

## Owner objective

Demonstrate that the actual skinned Hareworks woman's **forward walk** can be reconstructed with procedural leg trajectories and IK **without copying source pelvis and ankle orientation tracks** on the generated character. Allow camera orbiting to judge its motion. Do **not** add turning, strafing, aiming, root traveling, or a full locomotion system yet. The rejected v0.1.0 walker remains rejected; this is a separate proof.

## Exact sources and authority

- Repository: `Valar05/parametric-parambulator`, audited base `f322307c46e561443c3e0177ef309332fb51834d`.
- Original nine-clip Hareworks source preserved, SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, 6,784,896 bytes.
- Existing v0.1.1 `gait-kernel.mjs` and `profile.json` remain authoritative for the **previously reviewed** forward ankle trajectory / analytic knee IK. Do not edit them.
- `hareworks-gait-and-idle-turn-v1.0.8.json`, extracted from that source, supplies 61 samples of `Walking_Woman`. The last sample at `t=duration` resets to a different pose. The new pelvis/foot harmonic fit is trained on **30 alternating samples of the 60 continuous frames**, with **30 held-out samples**. This is documented rather than smoothing across a false continuous endpoint.
- Read live `AGENTS.md`, Campaign Etiquette, Top-Down Etiquette; honor Termux Git-only publication, exact remote readback, and owner's visual acceptance.

## Generated motion

Left model plays original `Walking_Woman`. Right model retains the model's unchanged mesh, 74-joint skin, and nonleg upper-body source animation only. Source clip tracks for the hips, their ancestors, and **all leg bones** are excluded from its AnimationMixer. The generated pelvis position/yaw are computed from `motion-profile.json` Fourier phase curves and applied to the hips in their parent's local space. The ankle trajectories and analytically determined knee bends continue to use the unchanged v0.1.1 phase kernel. The ankles are rotated from procedural toe-direction and world-yaw curves, **not reference ankle quaternions**. The remaining toe joint's *local* seed rotation is unchanged; the completed skinned boot, ankle and toe must be visually inspected.

The new `pose-kernel-test.mjs` compares source-fit curves with the **30 measured holdout samples** at ~60Hz spacing and enumerates 30 FPS generated frames. It does not claim physical acceptance. The viewer offers side/front/top/three-quarter camera presets, touch-drag orbit, pinch zoom, a frame scrubber, 30 FPS step review, and exported real-bone traces. It rejects unreachable knee geometry, >0.012 ankle target residual, 60° or greater joint rotation per 30fps frame, and insufficient forward ankle travel as **mechanical gates**. Real-rig discrepancies otherwise remain visible and subject to owner review.

## Explicit limitations

This is still **in-place** source-style motion: upper torso/arms/head remain reference animated; it does **not** create independently traveling root motion, verified planted sole contacts, foot support dynamics, or a ready gameplay controller. New pelvis/foot orientation curves are a **reference-calibrated parametric reconstruction**, not generic human locomotion or learned dynamics. Positive fit results and HTTP checks do not establish believable skinned walking until the owner accepts the orbitable comparison.

## Execution evidence boundary

One SHA-checked downloadable Termux `.sh` authoring entrypoint, one isolated clone, exact new destination collisions checked before writes, text-only commit, no GLB mutation, no force push, remote SHA and blob readback, original LFS source verified and served over HTTP, JSON receipt and logs. Rerunning the same packet recovers the exact already-published candidate rather than creating a competing commit. Publication and browser HTTP availability are distinct from 30 FPS rig check and visual approval.
