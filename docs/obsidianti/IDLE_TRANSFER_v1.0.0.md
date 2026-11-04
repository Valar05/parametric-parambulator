# Obsidianti: Lionheart Idle intake v1.0.0

**Repository:** `Valar05/parametric-parambulator`.

**Stable canonical model path:** `assets/obsidianti/Obsidianti.glb`.

This character is separate from Repl. **Do not touch** `assets/repl/Repl.glb`, Repl's mane/tail, motion, sources, or scripts. Never write `Obsidianti_v2.glb`, `Obsidianti_attackX.glb`, or other numbered model outputs into the repository. Every subsequent approved Obsidianti pose/animation edit must replace the content of **the same** `assets/obsidianti/Obsidianti.glb` path, with Git commits as rollback, after proving preservation of previous accepted clips, rig, mesh, skin and weapon/hair attachments.

## Intake packet: immutable binary sources

- `payload/Obsidianti.blend`: the user's corrected wedges, complete original 66-joint Meshy biped, six added control bones, helmet-tassel and independent left/right weapon rigs. **Blender authoring source**, never overwritten by script.
- `payload/LionheartLancer.blend`: original donor with native keyed `Idle` and independent Light/Heavy/etc attacks. **Animation authority**.
- `payload/Obsidianti.original.glb`: user-exported target with original `Running`, `Walking`; includes two unused, unskinned cloth root objects, which are intentionally **not** part of the visible character.
- `payload/Obsidianti.idle-candidate.glb`: retargeted, scene-cleaned candidate with three clips: `Running`, `Walking`, `LionheartIdle_UNREVIEWED`. Original skin, mesh, joint bindings, material and binary prefix unchanged. Left/right weapon pose animations are separate.
- `payload/Obsidianti.IdleComparison.png`: the source of the user's favorable **pose appearance** feedback, not proof of animated-rig playback.

The machine-readable SHA-256 inventory is in `manifest.json`. All inputs are checked before any Git write. The two `.blend` files are committed to `assets/obsidianti/source/` via existing Git LFS filters; the original uploaded GLB remains inside the attached ZIP, not as a second repository model. The single candidate GLB is imported **once** to the canonical model path.

## Stage, execution and review boundaries

1. Android/Termux-only one-shot launcher validates the exact ZIP SHA, extracts only allowlisted entries, then invokes the unique versioned campaign script.
2. Script reads live repo's `AGENTS.md`, reports exact current `main` SHA, confirms no destination collisions, validates source and target GLBs including all existing clips, and works in an isolated new checkout without touching owner's dirty worktree.
3. Git publish first adds/re-reads **campaign source + Blender input archives + docs + reviewer**; then installs the verified candidate once to `assets/obsidianti/Obsidianti.glb`. Uses existing Git LFS configuration and only ordinary non-forced pushes to `main`. If normal Git push authentication fails, it can retry through an already-connected `gh auth git-credential` helper; it does not bypass remote authorization. Remote SHA and LFS pointer OID must match. No alternate GitHub connector writes or Windows lane.
4. Read-only viewer: `http://127.0.0.1:8179/review/obsidianti.html` after successful phone execution, using the exact working checkout that was pushed. The viewer needs network access to load pinned Three.js modules from jsDelivr; network failure is viewer-blocked, not model/commit success.
5. Human visual appearance of initial pose was praised as perfect. Actual hosted bone-animation playback, shoe grounding, weapon and tassel motion have NOT yet been verified by the owner in the target viewer. **Do not silently promote candidate to accepted animation.**

## Next work after this intake

On the now durable canonical target, verify that selecting `LionheartIdle_UNREVIEWED` produces the same stance as the previous visual preview. If it diverges, repair **only** the action/rest-basis math and retain the owner's approved silhouette. Then turn this key into an editable shared Idle baseline. After approval, use `Ares Step*` lower-body motions with that idle upper body and `AxeKick` full-body, with entry/exit reconciliation. Ares's binary source is **not** included in this initial Idle packet: its authoritative source is the separate Gravity Fist repo, and it was not accessible for binary extraction here. Do not claim the future step/kick motions are installed.

## Reusing the canonical path

Future scripted animation updates should read `assets/obsidianti/Obsidianti.glb`, append/replace the **named animation channel** in memory after source and target hashes are checked, then atomically overwrite **that same path** only after verification. The next script gets a unique filename and does not create another canonical GLB. Keep the blend source and original material/skin intact. Verify the SHA of the one GLB after a non-forced commit/push and exact remote readback.
