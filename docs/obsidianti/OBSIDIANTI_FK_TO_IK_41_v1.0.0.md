# Obsidianti: 41-action native Blender IK authoring v1.0.0

## Owner requirement (2026-11-08)

**All 41 currently preserved FK animations must remain pose-identical at all existing keys and intermediate evaluations while two foot IK targets and two knee poles actually drive the editable legs, with separately keyframed controls for each action.** Do not misread this as adding FK controls or a new GLB. This is native Blender authoring work. The previous FK-only authoring export was visually confirmed to contain all animations but lacked IK.

## Sources and immutability

- Repository: `Valar05/parametric-parambulator`.
- Authoritative native input: `assets/obsidianti/source/OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0_UNAPPROVED.blend`, SHA-256 `30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27`.
- Lineage: 41-clip `animation-reunion-v2.0.32` GLB SHA-256 `9ff2b5423b4bf5fea1bf67295b52d848803381699fede56164aca9ce65bea9b7`.
- Preserve this source `.blend`, source `.glb`, all original animation data, deform topology, textures, original FK actions, and unrelated assets. **Do not resume shelved Sword1 two-handed animations.**
- Output: `assets/obsidianti/source/OBSIDIANTI_IK41_EDITABLE_v1.0.0_UNAPPROVED.blend`, a new *separate* file. Native Blender controls are not exported as runtime GLB geometry.

## Mechanism

On the existing FK-editable armature, create four disconnected nondeforming pose controls: `CTRL_Left_ANKLE_IK`, `CTRL_Right_ANKLE_IK`, `CTRL_Left_KNEE_POLE`, `CTRL_Right_KNEE_POLE`. Install two actual two-bone, nonstretch Blender IK constraints and two copy-rotation foot constraints. For each of 41 source NLA clip identities, create a unique `IK41_EDIT__...` action copied from its corresponding original FK action. Sample reference ankle matrices and knee positions at original keys, whole frames and half-frames. Key each control **in its own action**; calibrate a fixed pole angle per side, verify the resulting evaluated ankle, knee and orientation across the entire sample grid. The original data remain unchanged. Keep NLA tracks for clip discovery; open one IK action in the Action Editor for editing.

Strict pose parity: max ankle 12 mm, knee 25 mm, foot orientation 3 degrees across the sampled keys/half-frames, plus an independent Blender native reopen check. This is a numerical guard, not a promise of visual acceptance. On failure, stop without publishing a falsely green native `.blend`. Save detailed diagnostics for subsequent repair.

## Delivery authority

One SHA-verified directly downloadable Termux `.sh` launcher; **only Termux Git** may commit/publish. Fresh isolated checkout, pinned source LFS SHA, mandatory `AGENTS.md` SHA and live Campaign Etiquette read, no dirty worktree, no overwrite or force push, source commit readback, native Blender generation, independent Blender reopen, versioned `.blend` in Android Downloads **before** expensive LFS push, controlled transfer concurrency and memory, LFS pointer and remote head readback, persistent receipt and diagnostics ZIP. User Blender visual inspection/approval remains pending.
