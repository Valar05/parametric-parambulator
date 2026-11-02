# AGENTS.md — Mandatory repository boot gate

**Applies to EVERY agent turn that concerns this repository, including failures, explanations, follow-ups, and script production.** This file must be fetched/read from the actual pinned repository revision anew before proposing changes, declaring a state, running an operation, or writing any new campaign. Never assume its content is already in conversation context.

**Read the live Campaign Etiquette document for EVERY Git-owned campaign turn:**
https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit

If either required read cannot be performed, disclose `RULES_READ_BLOCKED`; never claim compliance. The rules-read tool result, source commit, and canonical model SHA must appear in the execution receipt. A script may enforce a read gate for its invocations; this document is not proof ChatGPT automatically loads files in future unrelated chats.

## Authority, safety, deliverables

- Target repo: `Valar05/parametric-parambulator` ONLY. Canonical Repl file: `assets/repl/Repl.glb`, **exactly one**. Git history is rollback, not additional versioned GLBs.
- Authorized mutation/execution: **Termux Git only**. No direct ChatGPT GitHub connector writes, Windows substitution, Pose Lab as workspace, or multiple little manual helper commands.
- Every campaign uses one uniquely versioned Android Termux `.sh` entrypoint; a directly downloadable, SHA-checked attachment; a safe isolated verified checkout; persistent JSON diagnostics; and exact remote Git readback. Do not rely on the operator's current directory or dirty checkout.
- Never rewrite an existing campaign source filename. Check ALL would-be destination paths and their Git states **before** modifying the canonical GLB or README. File collisions are preflight failures. No silent overwrite/reset/stash/force-push.
- Inspect actual binary and animate against the actual skeleton/skin/ground contact before solver changes. Check per-frame and midframe world-space hooves, **Z advance, support lock, pitch/roll, joint continuity**, and not just the height of the tip.
- Preserve approved mane/tail, meshes, weights, other clips, hind-leg tracks, front distal/toe/hoof channels and root travel unless explicitly reauthorized. Protect by compare and hashes.
- Tests must exercise complete success path, realistic GLB, and deliberately injected failure paths before release. A green synthetic test or correct ZIP SHA is not production success.
- Distinguish: script created, downloaded, Termux run, canonical file changed, Git commit/push/readback, rendered viewer, **owner visual acceptance**. Numeric success NEVER implies visual approval.
- Updates to `AGENTS.md` must preserve earlier requirements. This root file is checked and installed by the committed versioned AGENTS helper as part of the Termux publication step. The template is immutable within the SHA-locked packet.

## Repl incident ledger: do not regress

- **v0.6.7:** conflated old/new hoof pose difference with physical stance sliding. Use fixed skinned witnesses and ground-relative motion.
- **v0.6.9:** `float`/dictionary name shadowing escaped tests. Run the complete production success path and compile-check scripts.
- **v0.6.11–13:** peak clearance calibration missed toe-off, negative floor values, and late contact; joint search was underconstrained. Evaluate the entire gait and source geometry, not proxy markers.
- **v0.6.13–14:** unconditional remote full clone timed out; prefer verified Git cache, safe shallow fetch/recovery.
- **v0.6.15:** the hoof teleported/kicked forward at swing boundaries despite acceptable clearance. Check world-space forward motion and planted support.
- **v0.6.16:** all numerical geometry tests passed in Termux, but publication failed because seven campaign destination filenames were still `v0.6.15`. Mandatory prepublication destination collision gate BEFORE asset writes.

## Mandatory per-turn checklist

Read root AGENTS and live Campaign Etiquette; determine requested goal/owner/lane; inspect exact remote main HEAD and canonical hash; review existing owner visual verdict and failure ledger; ensure unique destination names; prove source and physical tests; ensure execution receipts and remote readback; request final visual acceptance. On any missing evidence, block at that boundary. No invented completion claims.

## 2026-11-02 — Repl stance and breakover: owner correction and mandatory physical gates

Owner visual verdict: v0.6.17 is the BEST YET and ALMOST ACCEPTABLE, **NOT APPROVED**. Preserve its low airborne hoof arc, four-beat cadence, traveling root, existing secondary body motion, rear tracks, mane/tail, mesh and all original assets. Current commissioned issues: front knees never appear straight during support, and hooves need to travel farther underneath the forequarters before lift-off.

Read and measure the EXACT current canonical GLB, not just its geometric replay, script parameters, or an earlier version. Distinguish source hash, published binary, and derivative. For each front foot measure at all 97 frames AND half-frames: true skinned sole Y; lowest toe and heel vertices; stable patch world Z; shoulder-to-hoof relative Z at touch-down and last support frame; upper-to-lower segment knee flexion (0 degrees straight); source-to-candidate changes; joint quaternion step; and toe-off/swing/touchdown continuity. Add per-leg and per-clip receipts. Screen captures and angle offsets alone are not motion evidence.

A stance-only straightening solution is NOT VALID if the return to swing causes hoof penetration, a jump, premature heel roll, prancing, or implausible late swing. Test the connected cyclic trajectory under the ground plane, not separately acceptable poses. Stance hoof must remain supported without world-space sliding while Repl advances over it; forward swing remains smooth and natural. Numeric passes are not human visual acceptance.

Only the four existing approved front shoulder/middle rotation channels (Bone_015, Bone_014, Bone_021, Bone_020) may be modified without new owner consent. Front distal/hoof/toe joints, root and body, rear channels, timing, skeleton and weights stay locked. Do not quietly 'fix' degrees-of-freedom limitations by changing locked channels or shortening stance. If constrained geometry is infeasible, publish the EXACT identified boundary and propose a separately approved distal-joint pilot; do NOT weaken physical gates or commit an invalid GLB.

Source and policy must be committed by the user's authorized Termux Git lane with exact remote readback, not direct ChatGPT Git writes; preserve all previous policy text. A new campaign script may commit itself and this additive doctrine without changing the model if the physics gate blocks, but must report MODEL_UNCHANGED and never label the requested animation completed. One invocation, verified hashes, no repeated manual diagnostic commands, no stale destination filenames, no force push, no dirty-tree overwrite.

## 2026-11-02 — Repl v0.6.18 Python shadow import regression and owner-run cost

FIELD FAILURE: v0.6.18 terminated during verified Git checkout because `main()` contained `import os,tempfile` AFTER a use of `os`. Python marks a name imported inside a function as local for the function's entire scope, so the earlier `os.chdir` raised `UnboundLocalError`. The campaign's static AST-parse self-test did not exercise `main()`. This was a code defect, not a rig or network failure.

MANDATORY: No nested imports in campaign entrypoint `main()` for globals already imported at module scope. Run an AST/symbol-table scope regression AND exercise the actual driver through checkout, first source/AGENTS publication, blocked physical gate, and successful physical gate with disposable test Git fixtures; do not rely on `py_compile` or source greps alone. A mock success-path pass is not physical GLB evidence; pin and independently recheck the actual canonical model on Termux.

When a requested gait repair is already known to fail the available numerical profiles, report that boundary before sending the owner another campaign. Publishing the source/policy may be valuable but is not the same as achieving a visibly improved walk. Preserve all original v0.6.17 locks and prior addendum; avoid repeated phone invocations just to discover pretestable Python errors.
