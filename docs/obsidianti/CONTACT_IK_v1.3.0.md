# Obsidianti Lionheart Contact-IK Recovery, v1.3.0

## Owner mandate and authoritative lane

Repository: `Valar05/parametric-parambulator`, only. The **single** model remains `assets/obsidianti/Obsidianti.glb`, updated at this same pathname via Termux Git. Repo instructions and live Campaign Etiquette are mandatory. This script neither writes GitHub via a ChatGPT connector nor changes Repl or Pose Lab. It does not re-rig/retexture/rebuild the character.

The v1.2.1 pelvis pitch search is **rejected by owner visual review**. It made Heavy1 and Heavy3 worse despite good Heavy2 contact. Source pre-pitch reference: historical main commit `806cf70cdd957312d290d3cdd3d5e0c239f1f5a6`, original 23-clip model LFS SHA `5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0`. Input latest rejected v1.2 model: commit `904acd8e1b0d55b60ff230c0eccd4a516efddc55`, LFS SHA `f9fc5cef4d2f0b08f2a74e350d3251bc993a861ecbb6a22eda5267a09e4629e6`. The original Lionheart Blender source remains `assets/obsidianti/source/LionheartLancer.blend` SHA `81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4`.

## Actual transform changes, exactly

1. **Undo only rejected pelvis pitch.** For each of the ten moving `Lionheart_` Actions, replace `mixamorig:Hips` rotation sampler output accessor with the **exact** historic v1.1 accessor. Do not approximate the inverse pitch, redefine the rest rig, or change the source animation file. Source and current raw GLB BIN prefix and 23 existing clips are checked before changes.
2. **Preserve weapon translation removal.** Both independent weapon bones keep their rest transforms, parent, rotation tracks, skin and attachments. The unwanted inherited animated weapon position channels remain ABSENT. No new weapon slides are authored.
3. **Infer grounded versus airborne foot** from Blender-evaluated source `LeftToeBase` and `RightToeBase` world-height sequences, with ground level measured from original native Lionheart Idle, not inferred from what the broken target happens to do. Write continuous source contact spans per clip to receipt. If a source leg is airborne, never pin it to ground in target.
4. **Two-bone IK while supported.** Use actual target `UpLeg → Leg → Foot` bone lengths and **skinned wedge sole patch** geometry. Aim the original ankle at the donor's world-projected foot-contact trajectory. Solve hip/knee joint orientations analytically using the original bend pole and compensate foot local orientation to preserve world-facing weapon/foot aesthetic. Fade correction at start/end of source support and at authored Idle entry/exit. Do not mutate toe-end deformers or source rotations outside these six leg bones.
5. **Conservative source contact horizontal path.** Scale/anchor source foot X/Z displacement during grounded episodes, test scales 100%, 50%, and 0% (no forced horizontal correction). Do not just clamp height to floor; do not remove intentional footwork.
6. **Adaptive rare vertical root offset.** Keep exact authored pelvis translation by default. Only when no unshifted 2-leg IK fit passes the source-contact gates, consider a per-contact smoothly faded Y offset from `±0.02`, `±0.04`, `±0.07 m`. Horizontal pelvis translation, yaw, roll, pitch, and root-motion timing stay authored. All such offsets are individually recorded in receipt.

## Protected, verification and deployment gates

Protected by exact GLB structural equality: model nodes, skins, meshes, scene, materials, image references, **all original BIN bytes**, `Running`, `Walking`, `LionheartIdle_UNREVIEWED`, authored moving `ObsidiantiIdle`, **all nine Ares clips**. All 23 animation names stay. No GLB proliferation; no newly versioned model file.

The code runs from a clean, isolated Termux Git clone and SHA-verifies both current GLB and historic GLB and original `.blend` source. It commits and pushes unique versioned script source first. It then evaluates original IK constraints in actual Blender from the exact original .blend; the `sourceToe` world position samples are authoritative donor signals. It evaluates real target skinned soles at animation frames and half-frames. Candidate IK metrics and contact spans for **all ten** Actions, including Heavy1, Heavy2 and Heavy3, are saved to JSON in a private campaign workdir and summarized in the public Downloads receipt. If supporting feet fail the gates, **no new model GLB is committed or pushed**. An invalid preflight is evidence, not proof of successful correction.

Successful preflight then updates only `assets/obsidianti/Obsidianti.glb`, commits via Git LFS, pushes without force, checks remote HEAD and remote LFS pointer, and serves a read-only phone viewer at the printed `REVIEW_URL`. Source-published-only and model-published are distinct states. Human review is final authority, and specifically should inspect Heavy1, Heavy2, Heavy3, Light1–3, Kick and Stomp. The owner previously found Ares acceptable; Ares must remain byte-for-byte unchanged.

## Known scope limits and stop boundaries

This is a physically grounded **candidate**, not mathematically guaranteed pleasing choreography. Source ToeBase height is a good but imperfect proxy for exact polygonal contact in the unexported donor mesh. Target body geometry and true per-frame sole patches are checked. We do not claim runtime or user approval until phone receipt, remote binary pointer and real owner review. Any unsupported donor foot action, missing Blender/old LFS object, nonfastforward remote, collision, altered canonical hash, or uncorrectable leg reach is an explicit blocked stage, not permission to overwrite or move the script to another repo/machine.

## Off-device regression fixture

For repeatable development tests, point `OBSIDIANTI_TEST_SOURCE_GLB` at the original owner-approved **three-clip skinned Idle candidate**, never at the current 23-clip canonical model. The test builds separate synthetic 23-clip fixtures only in disposable temporary storage, then verifies real skinned 2-bone ankle IK, intentional airborne kick preservation, donor backward motion, 23-clip protection, original BIN prefix, model SHA rejection and dry-run nonmutation. It does **not** model the actual Heavy1–3 recordings and does not prove deployment.
