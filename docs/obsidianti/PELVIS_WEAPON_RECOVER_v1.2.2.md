# Obsidianti v1.2.2: recover previously committed pelvis + weapon fix

## Commission and precise failure

Termux v1.2.1 reached actual Lionheart source evaluation, real skinned model preflight, and committed a patched canonical model locally. Its final `git status --porcelain` check returned `DIRTY_AFTER_MODEL_COMMIT`, leaving the result **unpushed**.

Code analysis found the immediate cause: `tests/OBSIDIANTI_PELVIS_WEAPON_TEST_v1.2.1.py` dynamically imports the committed solver, so Python normally writes an untracked `.pyc` to `campaigns/__pycache__`. That untracked file survives the model-only commit. The old gate treats it as any other dirty file. This recovery **tests that hypothesis against real Git status before touching anything**; it refuses unrelated dirty changes.

## Authorization and locks

Target: `Valar05/parametric-parambulator` only, via Termux Git only. Preserve `assets/repl/Repl.glb`, original `.blend` sources, source v1.2.1 scripts, all animations, weights, materials, the approved Idle and the source pose. No direct GitHub writes, no Windows/Cloud alternate lane, no cloned replacement model, and no alteration of the committed v1.2.1 candidate.

One unique versioned Termux launcher. Requires both SHA-verified packet and actual original v1.2.1 receipt. Recover **only** the isolated checkout named by the prior receipt, after verifying its original main base, exact v1.2.1 script and model commits, canonical GLB LFS pointer, full model SHA, fitting report and original source readback. The prior receipt and previous candidate must match.

When status contains **only** `campaigns/__pycache__/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.cpython-*.pyc`, verify Python bytecode magic, length, path and Git untracked state; move it to a preserved quarantine folder **outside** Git worktree. Refuse any other dirty files. Do not run `git clean`, reset, stash, or delete a dirty user file.

Commit the new recovery runner/documentation/tests (new filenames, no collisions) to the same isolated checkout. Perform nonforced Git LFS+Git push of the **already committed** 3D result. Verify remote HEAD SHA and remote Git LFS model pointer through fresh fetch. If remote advanced independently, fail with exact conflict. Reuse existing phone viewer on a free port and report its HTTP state separately from human visual acceptance.

## End-to-end evidence

Receipts include original source receipt path, exact local model SHA, prior model commit, source release commit, quarantined cache SHA, new recovery script commit, remote head SHA and canonical Git LFS pointer. Never call pointer readback independent downloaded LFS binary verification. Owner's on-phone visual judgment remains final.

### Prior verified references

Original prior main: `806cf70cdd957312d290d3cdd3d5e0c239f1f5a6`.
Original prior canonical SHA-256: `5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0`.
Original failure receipt: `OBSIDIANTI_PELVIS_WEAPON_v1.2.1_20261104T204813Z-76d247_RECEIPT.json`.

## Status

The recovery is source-prepared and tests are off-device only until the authorized Termux Git launcher runs. Do not assert the phone has pushed the recovered model before remote readback.
