# Auto-Rig Pro and animation-library reuse: field guide (2026-11-07)

**Authority:** `Valar05/parametric-parambulator` under the live root `AGENTS.md` and live Campaign Etiquette. This is a retrospective field guide, **not** a new deployment lane, licensed software distribution, approved animation, or permission to change canonical assets. Execute changes only through a versioned SHA-verified **Termux Git** launcher, with remote readback and owner visual review. Reread live rules every campaign turn; never treat this guide as a replacement for them.

## What actually worked

- Purchased **Auto-Rig Pro 3.79.17** was run with Blender 5 in the owner's private Termux PRoot Blender environment, `obs-arp-blender50`; the proprietary add-on and license remain private and are **not** vendored into Git. See `campaigns/OBSIDIANTI_ARP_BLENDER5_ISOLATED_v2.0.12_*` and `campaigns/MUDMAN_ARES_FULL_RETARGET_v2.0.22_*` for versioned executions.
- Multiple humanoid rigs became animation-library consumers, including Obsidianti (Lionheart, Ares and Vanguard sources) and the Mudman (Ares). This is a practical accelerator, not evidence that arbitrary skeletons transfer perfectly. The owner estimated some character animation work at 200+ hours; this is a personal production estimate, not a benchmark.
- **Ares `(2).blend`** source content SHA-256: `63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a`. The original is an immutable source for the mudman campaign. The donor source and Godot project live outside this repo; do not mutate them incidentally.

## Repeatable onboarding checklist for a new Mixamo-style character

1. Obtain the exact owner-authorized source Blender/action library and rigged, textured target character; record byte hashes. Verify licensing and keep purchased proprietary files in the private runtime, not in source control.
2. Inspect actual **source bones, target skinning, rest orientation, target dimensions, and action slots**. Modern Blender actions can contain multiple slots; select by *both* action and slot identifier. Do not assume action name alone, or silently substitute a different slot. In the Ares mudman audit, 77 populated action/slot combinations exported before curation.
3. In Blender 5, use the tested native `bpy.ops.wm.fbx_import` route for the Mixamo target. The older `bpy.ops.import_scene.fbx` path failed in this runtime with `AttributeError: 'ImportFBX' object has no attribute 'files'` (mudman v2.0.21; repaired v2.0.22).
4. Map corresponding source/target chains and run the ARP retarget in the owner's tested environment. Capture source action/slot, mapped-bone counts, configuration, trial Blend SHA, exported GLB SHA, and per-clip failures. Do not treat exported as owner-approved.
5. Make **Hips Location ON/OFF** an explicit, documented retarget choice, not an implicit tweak. Obsidianti v2.0.14 used Hips Location OFF; v2.0.16 used it ON and recovered the complete 21-slot library. Neither automatically proves contact, attack quality, or source pose parity on another target.
6. Preserve originals and previously accepted clips. Export a versioned review GLB first, then inspect **actual skinned feet/soles**, hips, limbs, weapons, and intermediate frames in a hash-identified 3D viewer.
7. Verify material/UVs independently. Meshy FBX imports can lose the material connection. Mudman v2.0.23 restored the *exact original* 2048×2048 PNG to a glTF `baseColorTexture` on its UV-mapped skinned mesh. Verify the source PNG SHA, `texture`/`image` wiring, material assignment, and a visibly textured mesh; don't accept a white model merely because a texture exists on disk.
8. Measure grounding against **world-space skinned vertices**, not a bone proxy or a grid that automatically follows the model's bounding box. Mudman v2.0.23 measured 4,474 witness vertices, original minimum Y `+0.731799 m`, applied an unanimated parent translation of `-0.731799 m`, and kept the viewer floor at `y=0`. A flat floor at y=0 must not be confused with an animation contact solver.
9. Curate exported animations with real game-controller data (Godot scene and attack definitions) and a persisted **source-action-slot → final-clip** manifest. Rename only when supported by evidence, and preserve intentional *static hold* states like prone. Do not dismiss all constant tracks as accidental duplicates.
10. Use **exact animation-name equality** when selecting clips from a multi-animation GLB. Suffix selection confused `StandUp` with `ProneBackStandUp`, giving a false viewer failure in v2.0.23; fixed in v2.0.24. Guard missing and duplicate names explicitly.
11. Every viewer must show *actual* loaded GLB SHA, run/build token, Git source revision, chosen clip, and distinguish original from candidate. Use cache busting, no-store HTTP, real-model SHA verification, and user inspection. Keep status text idempotent; v2.0.23 appended `TEXTURED 1/1` repeatedly while switching clips.
12. Preserve separate gates: source exists; ARP ran; GLB exported; remote Git evidence committed/read back; viewer served the intended SHA; **owner approved the motion**. Only the last is visual acceptance.

## Retargeting lessons that should not be relearned

- **Obsidianti's anatomy matters.** Lionheart forefoot geometry was longer than Obsidianti's: source ankle-to-foremost skinned vertex approximately 22.0/21.6 cm versus Obsidianti 14.2/14.5 cm. Some trailing-foot poses did not transfer cleanly. v2.0.19 measured toe-roll corrections of only a few to ~23 mm; these were not a reliable cure for large visible pose errors. Do not promise toe-roll patches solve skeleton/proportion mismatch.
- **Vanguard.glb retarget:** the owner found feet much better than the Lionheart attempts; arm/lance grip remained imperfect. Keep as review baseline, not fully accepted finished combat motion. Its mesh is weighted to a smaller subset of its Rigify bones; do not blindly map every control/deform/helper bone. See `campaigns/OBSIDIANTI_VANGUARD_RIGIFY_ARP_v2.0.17_*`.
- **AxeKick** is a separately owner-accepted control clip; preserve its original accepted sampler data, don't regenerate while repairing other actions. Other retargeted actions need individual review and cannot inherit that approval.
- The original Mudman v2.0.22 full-library GLB is a reproducible **77-slot source review**, not the 23-clip game-ready curated subset. v2.0.23 did the curation, texture embedding, and grounding *without an ARP rerun*.
- If rotation appears 90° wrong, inspect the *actual* offending root/hip/ancestor channel and explicit signed quarter-turns. A reference-pose-fitted **62.38362°** v2.0.26 correction for `HitHeadLeft` was explicitly **rejected** by the owner. “Better alignment score” is not a substitution for requested 90°/erroneous-key correction.

## Known source and report anchors

- Obsidianti v2.0.14: `diagnostics/obsidianti/arp-full-library-v2.0.14/runs/20261107T031757Z-c7c5e4e4/REPORT.md`.
- Obsidianti v2.0.16: `diagnostics/obsidianti/arp-contact-ik-authoring-v2.0.16/runs/20261107T041249Z-40a10759/REPORT.md`.
- Mudman full source v2.0.22: `diagnostics/mudman/ares-full-retarget-v2.0.22/runs/20261107T133703Z-00546afd/REPORT.md`.
- Mudman curated v2.0.23: `diagnostics/mudman/godot-curated-v2.0.23/runs/20261107T143456Z-5a637cc3/REPORT.md` and `CURATION.json`.
- Mudman rejected v2.0.26: `diagnostics/mudman/hitheadleft-frame-v2.0.26/runs/20261107T154910Z-52c55251/HITHEADLEFT_FRAME_FORENSICS.json`.
- v2.0.27 generated **exact 90° experimental** `HitHeadLeft` candidates. Their publication is not proof that the owner chose or accepted either one. See its campaign contract and versioned evidence.

**Do not store** licensed ARP files, credentials, original proprietary add-on source, unapproved fixed binaries as canonical assets, or unsupported guesses masquerading as measurements.
