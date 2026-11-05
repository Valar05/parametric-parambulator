# Obsidianti Native Motion Measurement v1.0.0

## Mission and authority

Read-only, SHA-verified measurement of the actual donor Lionheart native Blender file and the actual v1.5.6 Obsidianti candidate GLB. The donor is used **only for measurement**, never to regenerate Obsidianti animation. The canonical asset and all existing animations, `.blend` sources, weapons, rig data, Repl files, and owner-edited v1.9.3 files are locked and unmodified. Termux Git is the only authorized source and result publication lane. Owner visual evaluation is not implied.

## Inputs

- Repository `Valar05/parametric-parambulator`, branch main, live AGENTS.md blob `547c2af52303f4efb718bbf8f82a698110c7bfca`.
- `assets/obsidianti/source/LionheartLancer.blend`, Git LFS file SHA256 `81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4`.
- `assets/obsidianti/Obsidianti.glb`, SHA256 `8036ea2545cd1f32096447649eea1119aeb59769c94c929c2f63b4`, strictly unchanged.
- v1.5.6 handoff ZIP SHA256 `fc3ca580b82de074f6a2f040e8335baf1351b74a102df389bbaa5dfc85a68c3a` with `visual/Candidate_UNAPPROVED.glb`, SHA256 `261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5`.

## Method

1. Source inspected using actual native Blender evaluated pose with preexisting donor IK constraints; target inspected by importing EXACT preexisting GLB animation actions. NLA and clip identity verified. Every attack is sampled at half-source-frame intervals including terminal frames.
2. Measure thigh/shin rest lengths, effective hip-ankle reach, normalized extension, hip/pelvis/foot transforms, native controller world/local translation, knee angle, action translation F-curves, source parent hierarchy, source and target bind bases and object matrices.
3. Target mesh skin foot/toe witnesses: evaluate the actual skinned vertices at all sampling times and record their lowest Z and Y. Low vertices do not automatically establish actual sole contact; floor is a provisional percentile estimate until independently calibrated.
4. Pair donor and target frames by seconds and compare **scalar** source/target hip displacement relative to initial pose using measured anatomical ratios, and compare normalized extension. Source and target local axes may differ: directional vector differences are not automatically valid. Do not infer that feet and pelvis share a scale error.
5. Record foot snapping and potential near-floor sliding indicators from consecutive half-frame distances. Include clip-specific and full CSV/metadata outputs for all ten attacks.
6. Publish source Python and this doctrine first, then raw CSV and metadata ZIP, Markdown report and JSON summary through isolated Termux Git. Verify exact nonforced remote SHA and LFS pointer readback; also place hash-checked copies and receipts in Downloads.

## Evidence/limitations

Output is measurement, NOT repaired motion or an IK authoring rig. Never smooth over unresolved bones, insufficient LFS objects, mismatched clips, ambiguous coordinate spaces, missing skin witnesses, or physical floor uncertainty. Preserve partial results in a handoff ZIP upon failure with conspicuous BLOCKED status. Blender and its existing proot distribution required; no dependency installs or alternate processing machines. The user must not manually collect logs.

## Output paths

Repository: `diagnostics/obsidianti/motion-measurement-v1.0.0/{MEASUREMENT_REPORT.md,MEASUREMENT_SUMMARY.json,MEASUREMENT_RAW.zip}`. One unique report, JSON summary, raw ZIP, handoff ZIP and receipt in Termux Downloads. Existing asset files are not updated.
