# Obsidianti: Lionheart pelvis and weapon translations v1.2.1

**Owner-authorized scope:** Update the single existing `assets/obsidianti/Obsidianti.glb` in `Valar05/parametric-parambulator` through Termux Git only. Repl's entire model is protected. No new GLB filenames or invented rig.

## Problem, diagnosis, and surgical correction

The owner approved the first transferred Lionheart Idle pose and found most Ares actions excellent. On several Lionheart action imports the character pitches forward, her front wedge enters the floor while the rear wedge lifts. Independently, Light attack weapon-bone translation is too large and directionally wrong. The owner specifically authorizes **pelvis rotation** to reconcile support-foot contact, and **removal of all inherited Lionheart weapon-bone translation channels**. No need to salvage their authored travel; possible future independent prop motion should follow the character's own forward frame.

The GLTF solver samples **the real 3D skinned wedge sole vertices** at all source-keyed frames, and it invokes the exact original Lionheart Blender source sampler for left/right toe support classification. It searches pelvis local-X pitch in a bounded range, with ZERO pelvis translation edits; root Y is preserved exactly. Source clips containing intended foot lift are not automatically pinned. Existing good clips are left unchanged if improvement is insignificant or the floor collision becomes worse. The approved single-frame Idle, newly authored breathing Idle, all eight Ares steps, full Ares AxeKick, original Walking and Running, weapons' rotations, fingers, helmet tassel, geometry, skin, attachments, and all Repl files are unchanged. The script **never modifies foot or leg channels**.

Every moving Lionheart action loses its `mixamorig:LeftWeapon.L` and `mixamorig:RightWeapon.R` **translation** animation channels (both weapons retain their rest translation, parent/skin, rotation keys, and all weight data). No forced 2-handed IK. The solver records the chosen pitch, rootY=0 (unchanged), physical foot contact RMS and maximum penetration before/after, for every Lionheart clip. If the source evidence does not justify pelvis adjustment for a clip, that clip's pelvis stays identical. No global fixed pitch, root-Y change, or arbitrary heel correction.

## Evidence and limitations

The model's structural invariants are enforced before replacement: same scene-root references, all 23 animations, untouched existing BIN prefix, all original skin/mesh/node definitions and no changes to protected animation records. This is a candidate requiring human visual approval, not a guarantee that all motions are perfect. Some source-specific moves may still need individual refinement if pitch alone does not explain their contacts; do not add IK without new owner authorization. The verification report explicitly identifies inconclusive clips.

Full Git-authoring receipts require the versioned scripts committed first, one canonical GLB changed second, non-force push, exact remote HEAD and LFS pointer readback. The actual animated character must be opened on the phone for owner review. Never imply Git/LFS metadata proves the rendered result.

Source authority: 2026-11-04 live AGENTS.md and CAMPAIGN_ETIQUETTE, verified `main` at `806cf70cdd957312d290d3cdd3d5e0c239f1f5a6`, canonical input Git LFS SHA256 `5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0`. The exact authorized fixed output path is `assets/obsidianti/Obsidianti.glb`.

## v1.2.1 recovery from verified v1.2.0 field failure

v1.2.0 returned `RULES_READ_BLOCKED_UNEXPECTED_AGENTS` because its exact-text check
searched for lowercase `read the live Campaign Etiquette` while actual tracked
`AGENTS.md` starts the instruction with uppercase `Read`. The archive integrity
and Git clone passed; the model/source commits were never attempted. This was a
campaign code defect, not a rules violation or missing local file.

v1.2.1 preserves the exact authorized model-mutation algorithm and all locks.
Instead of exact prose, the code loads actual `AGENTS.md`, checks Git root,
compares its Git object SHA with the tracked `HEAD:AGENTS.md`, verifies the
repository identity and policy topics using case-insensitive checks, and
records both the document SHA256 and Git blob in its receipt.

The recovery includes an executable regression test with a disposable Git repo:
it must accept the actual capital-R case, reject an altered uncommitted rules
file, and reject another repository's policy header. No direct GitHub writes,
no alternative GLB path, no reweighting, no Ares changes, no replacement of
owner-approved Lionheart Idle. New source is committed through authorized
Termux Git before editing the same canonical model.
