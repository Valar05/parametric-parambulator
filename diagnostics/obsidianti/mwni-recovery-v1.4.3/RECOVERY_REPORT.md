# Obsidianti Mwni v1.4.3: recovery of real Blender review files

**Status:** 4 previous Blender exports recovered and SHA-verified in shared Android Downloads; source and canonical model unchanged.

- Source prior evidence commit: `8f3485133c8ce5f616e396aab2fbf83636412334`
- Original run: `20261106T172615Z-6d53cfaf`
- Failures repaired: v1.4.0 used proot-only virtual paths; v1.4.1 rejected compressed Blender files; v1.4.2 recognized raw/gzip but not the real Zstd bytes.
- Correction: resolve the pinned proot bind path, verify exact Git-recorded SHA and size, recognize raw/gzip/Zstd Blender signatures and optionally test the entire Zstd frame when the decoder is already installed.
- Retarget tests were completed previously: Heavy1 and Light2, both with plugin IK enabled; they remain UNAPPROVED.
- Heavy1 right-foot discrepancy RMS: 0.419519 m baseline to 0.065851 m with IK.
- Light2 right-foot discrepancy RMS: 0.437381 m baseline to 0.073581 m with IK.
- Light2 left-foot discrepancy RMS WORSENED: 0.078855 m baseline to 0.150371 m with IK.
- This recovery does not rerun the solver, change the plugin, modify source or canonical rig, or assert sole contact/visual approval.

## Published candidate files

| Clip | Type | SHA-256 | Android Downloads file |
|---|---|---|---|
| Heavy1 | candidateGLB | `793ab2378e59d065308b80949d5352f5e2472d94ce93d4e63fc27aa5ed63fec1` | `OBSIDIANTI_MWNI_REVIEW_RECOVERY_v1.4.3_20261106T172615Z-6d53cfaf_MWNI_Heavy1_UNAPPROVED.glb` |
| Heavy1 | editableBlend | `cb4ce023b885072ecbc5e58cb0a255bdbf20bcef56cf0bb787314778cb87514d` | `OBSIDIANTI_MWNI_REVIEW_RECOVERY_v1.4.3_20261106T172615Z-6d53cfaf_MWNI_Heavy1_UNAPPROVED.blend` |
| Light2 | candidateGLB | `10bdf5dcbf0a7a9f3e746620cc88bc4bdb4e94bd4a512395a03d33aa2a1bfa82` | `OBSIDIANTI_MWNI_REVIEW_RECOVERY_v1.4.3_20261106T172615Z-6d53cfaf_MWNI_Light2_UNAPPROVED.glb` |
| Light2 | editableBlend | `c31f7b8d11385b73d94c97fd24424279bfe37e926bb6a7e48646f23a5dbad54c` | `OBSIDIANTI_MWNI_REVIEW_RECOVERY_v1.4.3_20261106T172615Z-6d53cfaf_MWNI_Light2_UNAPPROVED.blend` |

## Publication boundaries

Source files and evidence committed through Termux Git; exact remote revision verified. No new canonical or alternate deployed GLB. These are diagnostic review artifacts outside the repo, pending owner inspection.
