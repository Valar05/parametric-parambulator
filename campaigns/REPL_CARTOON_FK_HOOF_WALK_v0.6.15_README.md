# REPL_CARTOON_FK_HOOF_WALK v0.6.15 | Measured low walk

This is a complete one-ZIP, one-entrypoint Termux Git campaign. It is not a GLB
replacement file and not a second canonical model. It modifies the repository's
sole `assets/repl/Repl.glb` only after full physical validation on the device.

## Why this version is different

The actual 7,021,016-byte v0.6.10 GLB was inspected and skinned with its real
inverse bind matrices and six animation clips. The solver measured and optimized
all swing frames before this ZIP was authored. Its solution is frozen in
`campaign/trajectory.json` with exact version, source hash, and per-frame
shoulder/middle offsets. It contains **no guessed runtime joint solution** and
requires no historical v0.6.8 GLB to calculate the update.

The candidate was **applied to the real uploaded GLB** and validated in the
local development runtime: 1,164 patch/frame combinations, all three stages,
forehoof peak ratios ~28.2-29.4%, front-swing min clearance above 0.0055 model
units, support-side shoulder dip 0.002304 units, planted-vertex change below
0.0073 units, and bounded joint steps below 24.8 degrees. This test is not
proof of Termux execution, remote Git publication or human acceptance.

## Protected data

Sole canonical model path, all geometries/materials/skins/rest structure, three
existing non-walk clips, all rear controls, front distal and hoof/toe channels,
front-stance local rotations, hair and tail, forward +Z root displacement 0.96
model units, all three 97-frame four-beat walk clips.

Mutated channels: foreleg shoulder/middle rotations only during front swing;
stage 2/3 Bone_000 root Y and slight local Z roll only. No toe edits.

## Operator protocol

Download the exact ZIP via the conversation attachment. Run the one SHA-locked
Termux launcher provided alongside it from any directory. The campaign locates
or creates an isolated repo checkout, verifies Git provenance and exact source
binary before any edits, runs its physical verifier, publishes the report and
textured review HTML to Android Downloads, then stages, commits and pushes the
single canonical GLB with exact remote readback. Human visual verdict remains
PENDING after all automated checks. A failed gate blocks Git mutation.

Canonical Campaign Etiquette: https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit
