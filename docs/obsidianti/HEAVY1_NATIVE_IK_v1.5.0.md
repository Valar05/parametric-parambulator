# Obsidianti Heavy1: native Lionheart Foot.IK retarget candidate v1.5.0

## Commission and exact mutation lane

Owner request 2026-11-04: **make the next repair campaign for Heavy1 only**. Use original Lionheart evaluated Foot.IK/Knee.IK target trajectories, not toe-height contact inference, to drive Obsidianti's own shorter leg chains and bake the correct deforming bone rotations. Restore backward-moving foot motion, preserve natural knee bend, avoid world-floor penetration, foot tapping and snapping.

**ONLY** `Valar05/parametric-parambulator` and **ONLY** Android Termux Git may commit/push. One SHA-checked launcher, safe isolated Git checkout, Git LFS source checks, final remote readback. Repo source is never directly written by ChatGPT GitHub connector, desktop, or an alternative renderer lane. Source work is a packet: not a deployed model. No script may claim owner visual approval.

## Pinned real inputs

- Exact live canonical `assets/obsidianti/Obsidianti.glb`, input Git LFS SHA-256 `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4`, 16,978,732 bytes.
- Verified v1.4.0 archive commit `9c7d3774d945cc00bac1e4bfc621e50e3df7ba71` and **actual** constraint-evaluated `actions/Heavy1.json` SHA-256 `a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4` (61 full and half frames).
- `diagnostics/obsidianti/lionheart-ik-all-v1.4.0/calibration.json` SHA-256 `b6d23f49c67df7816124362f4b1ee540db5c16a672fbc8c435a7f503ca123336`.
- Immutable previously committed `campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py` helper SHA-256 `dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f` for GLB, skin, FK and quaternion routines.
- Fresh `AGENTS.md` Git blob `547c2af52303f4efb718bbf8f82a698110c7bfca` at authoring, plus live Campaign Etiquette Home Center document `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`. Runner validates its actual Git-tracked AGENTS content. Both have been read in this ChatGPT turn.

If the actual canonical or diagnostic archives have changed, do not assume a replacement or silently retarget a different model. Fail with a precise receipt. The original Blender source and native controller frames are **not reauthored** here.

## Permitted and forbidden edits

**Only six rotation channels within `Lionheart_Heavy1`:**
`mixamorig:LeftUpLeg`, `LeftLeg`, `LeftFoot`, `RightUpLeg`, `RightLeg`, `RightFoot`.

All their `rotation` curves may be resampled at 61 half-frame keys and appended as new glTF accessors. **No** Hips rotation or translation, `ToeBase`, leg rest/bind transforms, mesh, skin weights, scene, geometry, hair, helmet, weapon rig, weapon motion, materials or unrelated animation channel may change. Preserve exactly the accepted `Lionheart_Heavy2`, all Ares Step/AxeKick, original Running/Walking, the visually approved combat Idle, Kick, all other Lionheart actions, and Repl. Keep the one canonical GLB path; no second model in repo. Git history preserves previous model.

## Method

1. Read all 61 source Heavy1 native whole/half-frame samples and real target skinned skeleton. Validate pinned binary, source and calibration hashes.
2. Take source evaluated pelvis-relative foot-controller translation, preserve the native evaluated ankle-to-controller residual, and transfer knee-pole translation, aligned against Heavy1's source Idle entry and the target's **actual accepted combat Idle**. Maintain correct actor-local basis through source and target pelvis quaternions; native Blender units are already transformed to Y-up metres in v1.4.0.
3. Multiply source-relative movement by per-side target/source leg-chain ratios (left `0.87253927`, right `0.86749764`). Fit small bounded amplitude/yaw variations *only when physically justified*, and log every explored profile. Use target actual thigh/shin lengths and anatomical knee pole to construct an explicit two-bone solution. Transfer the native constraint-evaluated foot rotation (driven by Foot.IK Copy Rotation) relative to pelvis and Idle into target foot orientation.
4. Bake all 61 half-frame samples to six original target deform bone rotations. **No** contact confidence thresholds, 0.1-second boundary fade, sudden fallback into old FK poses, foot clamping to floor or source ToeBase height as ground authority.
5. Test the complete 121 point quarter-frame sequence on the target's real skinned shoe vertices and exact model FK. Reject reach misses, ankle-goal errors, floor penetration, excessive foot jumps/knee flips, or discontinuous quaternion motion. A failure remains a physical failure; do not relax a gate to fake success.
6. Write a candidate only to an isolated file, re-open and independently compare against pinned input: original BIN bytes must remain an exact prefix, all protected animation JSON must be identical, and exactly six Heavy1 rotation tracks changed.
7. **Only if** the physical and source immutability gates pass, atomically update the sole canonical model in the Termux isolated checkout, commit using Git LFS, push without force, and verify fetched remote Git head, new LFS pointer and protected Repl tree. A phone review page opens at `/review/obsidianti-heavy1-native-ik-v1.5.0.html` with Heavy1 selected and play/replay/pause/orbit. Save full preflight and SVG foot-path diagnostic as versioned Git evidence, with receipt/ZIP in phone Downloads.
8. Mark result `PUBLISHED_HEAVY1_NATIVE_IK_CANDIDATE_VISUAL_REVIEW_REQUIRED`, **never** owner-approved. If no candidate passes, status is `BLOCKED_HEAVY1_PHYSICAL_PREFLIGHT_MODEL_UNCHANGED`, with tested profiles, diagnostics and locked model.

## Acceptance observations

- Heavy1 right and left feet follow native controller's correct direction relative to the advancing pelvis, rather than lifting upward instead of traveling backward.
- No tap-tap oscillator, underground toe, unnatural heel roll, ankle snap, knee inversion or abrupt source-Idle/clip transition. Real feet and wedges remain plausible in fixed-camera full clip playback at 0.5× and 1×.
- Protect every existing accepted clip exactly, with no change to model rig/meshes/weights, Repl, or weapon ownership.
- Geometric preflight and phone reviewer evidence are distinct from owner acceptance. No output from the current authoring machine is proof of remote Termux deployment or acceptance.

## Blockers and explicit limits

This repair is still an **experimental candidate**. v1.4.0 did not evaluate original donor sole skin, and cannot prove exact source shoe-floor contact. The script uses the source rig's controller motion and target's skinned feet; it does not pretend toe bones define the source ground. The user requested Heavy1 alone; future Heavy3 or Light1/Light2 repairs require separate authorization. The finite parameter search is bounded, not a proof that an ideal solution is impossible. If every physically valid path would require edits outside these six channels (e.g., pelvis translation, foot geometry, spine or mesh), stop and report that concrete scope boundary.
