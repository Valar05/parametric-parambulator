# Obsidianti multi-action native Blender IK visual candidate, v1.7.0

## User commission

Replace the remaining rejected Lionheart action leg motion, excluding preserved Heavy1 v1.5.6 and previously accepted Heavy2, with the approach that materially improved Heavy1. Deliver **one non-canonical review GLB** with the full 23-animation library and a two-model viewer showing original Lionheart beside Obsidianti. Both sides have independent dropdowns, synchronized proportional timeline, and frame-step controls.

## Authority

Android Termux Git alone publishes campaign source. The authoritative model path `assets/obsidianti/Obsidianti.glb` must **not** be rewritten by this review campaign. No unrelated meshes, textures, joints, hip, torso, weapons, other animation tracks, or Repl are editable.

## Inputs

- Exact canonical Obsidianti source SHA256 `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4`, used only to solve Blender temporary IK and run physical checks.
- Exact original Lionheart blend SHA256 `81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4` for native source full-animation GLB.
- Existing `OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6_20261105T115742Z-a190493_HANDOFF.zip` SHA256 `fc3ca580b82de074f6a2f040e8335baf1351b74a102df389bbaa5dfc85a68c3a` under Termux Downloads; its `visual/Candidate_UNAPPROVED.glb` SHA256 `261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5` forms the review GLB base.
- Native donor `diagnostics/obsidianti/lionheart-ik-all-v1.4.0/actions/{Cast,Heavy3,Kick,Light1,Light2,Light3,SpringAttack,Stomp}.json`; original samples are action-specific and can last other than 1 second.

## Implementation and review boundaries

1. Read the actual AGENTS and Campaign Etiquette before publishing; use an isolated SHA-locked, Git-LFS-backed Termux checkout, no force push and no dirty-worktree rewrite.
2. Derive versioned copies of pinned `OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.6.py` and `...APPLY_v1.5.6.py`. The derivation changes only the hardcoded source-action name, source SHA validation and action frame count/duration. Keep native Blender IK, knee pole, calibration, source-space controls and physical reporting intact. The original scripts are not edited.
3. Attempt a bounded set of real Blender IK profiles per action. Preserve reports and a best inspectable candidate if numerical preflight fails. Do not label failed physical gates as passed.
4. Replace only six joint-rotation samplers for the eight authorized actions, preserving every other animation dictionary and the complete pre-existing binary data from the actual v1.5.6 review candidate.
5. Serve source Lionheart GLB and the merged candidate with **independent animation dropdowns**. Viewer must show exact selected clip identities and SHA-verified assets; no arbitrary first-clip playback fallback.
6. Keep all evidence in Termux private state and public operator handoff in Downloads. Print a verified live viewer URL, hashes, and the original canonical model's unchanged state. **Owner visual acceptance is pending**, even if automated checks pass.

The method does not infer universally correct contact behavior from the source controller. Heavy3 and other clips are visual candidates for owner correction, not approved animation repairs. Original Heavy1 v1.5.6 remains its current near-correct version. This campaign does not alter or claim to have corrected hip/torso tracks.
