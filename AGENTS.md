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
