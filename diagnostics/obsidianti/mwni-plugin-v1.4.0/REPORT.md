# Mwni Blender Animation Retargeting: installed and tested

Termux-authorized source and evidence campaign; source branch was never written by ChatGPT GitHub connector.

- Pinned upstream revision: `8c91ff4f4d898bab835b3587f17585487056b60b` (v2.1.1 compatible with Blender 4.3.x)
- Blender: `Blender 4.3.2`
- Source `.blend` SHA-256: `81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4`
- Source canonical GLB SHA-256: `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4`
- Installed addon source: `/data/data/com.termux/files/home/.local/share/obsidianti-blender-addons/mwni-2.1.1-8c91ff4f4d89`
- Canonical model: unchanged. No owner visual approval.

| Test | Actual Blender process | Plugin mapped + IK + baked + exported | Left/right foot motion RMS (m), no IK -> IK -> baked |
|---|---:|---|---|
| Heavy1 | 0 | PLUGIN_IK_BAKE_EXPORT_TESTED_UNAPPROVED | Left: 0.099717 -> 0.094627 -> 0.09461; Right: 0.419519 -> 0.065851 -> 0.065858 |
| Light2 | 0 | PLUGIN_IK_BAKE_EXPORT_TESTED_UNAPPROVED | Left: 0.078855 -> 0.150371 -> 0.150356; Right: 0.437381 -> 0.073581 -> 0.073209 |

## Interpretation

These are third-party Mwni driver/IK retarget tests. Foot bone motion error is not a sole-contact verdict. Actual skinned wedge-sole ranges and on-device output hashes are in `RESULTS.json`.
Any missing candidate, runtime exception, failed bake parity, or foot contact deterioration is identified explicitly; do not label an installed add-on as a successful animation repair.

## Explicit protected boundary

No original Blender source, canonical GLB, model Git LFS pointer, Repl asset, or approved animation was modified. The two exported clip GLBs and experimental `.blend` remain unapproved files in Android Downloads, not new canon.
