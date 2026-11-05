# Obsidianti sparse-key IK Blender authoring campaign v1.9.2

## Mission and authority

Generate a genuinely editable **native Blender** authoring copy with both feet controlled by native Blender IK, without permanently changing IK state on previously baked animations. The reference GLB's existing 23 clips are preserved in an isolated `OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT` rig. Build a **separate** `OBSIDIANTI_IK_EDITABLE` rig with new disconnected foot IK target and pole bones, two-bone IK on shin and foot Copy Rotation, and ten edit Actions. This is not an automatic physical correction of every animation and not a final GLB.

All source publication, model generation, new `.blend` binary commits and readback go through **Android Termux Git** only. Repository `Valar05/parametric-parambulator`. **No alteration** to original native `Obsidianti.blend`, native `LionheartLancer.blend`, canonical `Obsidianti.glb`, Repl, or previous campaign files. New versioned LFS output is `assets/obsidianti/source/Obsidianti_IK_AUTHOR_v1.9.2.blend`, with a separate copy in phone Downloads.

## Inspection gates

Read original native `.blend` files in actual Blender; inventory armatures, bone hierarchy, IK and other constraints, bone targets, all native actions, fcurve key counts and keyframe timestamps, FPS and object scales. Require actual IK in Lionheart native Blender source. If a source action lacks real keys, fail rather than invent times. Verify pinned LFS SHA256 for both original blends and current canonical GLB; verify the exact SHA of the v1.5.6 unapproved visual-candidate handoff from Downloads. Never substitute the rejected canonical GLB for the v1.5.6 authoring base.

## Editable output

For each native Lionheart attack Action (`Cast`, `Heavy1`, `Heavy2`, `Heavy3`, `Kick`, `Light1`, `Light2`, `Light3`, `SpringAttack`, `Stomp`) use the original native Action's authored key times, sampling the source-model candidate's evaluated pose at corresponding times. Reconstruct editable keyframes for non-leg bones and IK foot/pole controls at **only those donor key times**. Original donor Actions and sparse key times are inspected, not replaced with every-half-frame keys. The reconstructed interpolation is not guaranteed to reproduce every intermediate frame of the baked GLB and may need artist adjustment. Foot poles and rest axes need visual review; do not claim exact automatic retarget correctness.

Do not apply new IK constraints to the FK reference rig; it keeps the existing baked action library as an immutable visual safeguard. Preserve imported meshes and materials by duplicate independent model objects for the editable rig. Source meshes and GLB stay unchanged.

## Gates and proof

Reopen the saved `.blend` independently in Blender and assert two distinct armatures, actual two-bone IK constraints/targets, non-deforming controller bones, ten IK editable actions, preservation of baked FK reference clips, and exact sparse keyframe timestamp parity. Record source and output SHA, Git LFS pointer, remote pushed commit and readback. Keep the result labeled `VISUAL_ACCEPTANCE=PENDING`, never approved. Output a receipt and diagnostics ZIP to phone Downloads, plus the actual native `.blend` with verified SHA. On failure, do not publish a fake successful model. A campaign source commit is not proof the authoring copy exists.

## v1.9.2 field repair and action identity
Original v1.9.0 source publication succeeded on Termux, but the Blender authoring build blocked because it incorrectly assumed the Blender `Action` ID matched the GLB `animation.name`. Blender glTF importer stores glTF clip names on NLA tracks, often splitting or renaming Action datablocks. This revision resolves source clips from imported armature NLA track/strip associations, records complete identity evidence, and disables imported NLA evaluation only on the read-only FK reference to avoid mixing clips while sampling. Original imported Actions, animations, GLB, and native .blend files remain preserved. The prior v1.9.0 artifact is not overwritten, and no success is claimed before actual Termux/Blender verification.

## v1.9.2 field repair: compressed native BLEND output

The v1.9.1 native Blender build wrote its output with `compress=True`. The driver incorrectly required the uncompressed `BLENDER` file header, preventing Blender reopen. v1.9.2 accepts either native uncompressed `BLENDER` or Blender gzip-compressed files whose decompressed header is `BLENDER`. It independently reopens in native Blender and checks all sparse Actions, IK controls, isolation and original source SHA before publication.

To avoid rerunning a completed expensive build, the campaign may recover the sole matching prior v1.9.1 `~/.local/state/OBSIDIANTI_IK_AUTHORING_v1.9.1/*/work/Obsidianti_IK_AUTHOR_v1.9.1.blend` only if the corresponding build report marks all ten editable actions complete and the file container verifies. The previous output is **not trusted as success** until the new independent Blender reopen passes. If no unambiguous valid prior build exists, v1.9.2 performs a fresh native Blender build. Both outcomes are marked in receipt; source and canonical assets remain immutable.
