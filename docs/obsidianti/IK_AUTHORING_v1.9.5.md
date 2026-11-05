# Obsidianti native FK-to-IK edit conversion v1.9.5

## Commission and authority
Read live `AGENTS.md` (blob `547c2af52303f4efb718bbf8f82a698110c7bfca`) and Campaign Etiquette, both from the real linked sources on 2026-11-05. This is the successor to visually rejected v1.9.3 and maintains its original deliverable: a native Blender project with editable foot IK, preserving all original animation playback. **The motion source is only the exact Obsidianti v1.5.6 review GLB**, SHA256 `261f10786dd0eb0e80667173e4a893f6822356da628a5907efd6d0bbc2a74ff5`, recovered from the SHA-checked v1.5.6 handoff ZIP. **Do not use Lionheart to retarget or reconstruct any animation.**

Only Android Termux Git can publish campaign source and a Blender authoring project through normal commits and exact remote pointer readback. The canonical `assets/obsidianti/Obsidianti.glb`, original `.blend`, Repl and preexisting campaign versions are immutable. Neither original GLB nor any source .blend is overwritten. A failed preflight may publish campaign source, but does not publish an authoring `.blend` as successful.

## Native authoring construction
- Import the exact GLB and keep its 23 imported animation clips/curve data on `OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT`.
- Copy the exact imported attack Action data into ten `EDITABLE_IK_*` Actions. Existing channels and keyframes remain unchanged **byte-for-byte at FCurve value/interpolation level**. Do not resample original FK curves, rebake pelvis or attempt to retrieve donor key times.
- Duplicate the skeleton and mesh to `OBSIDIANTI_IK_EDITABLE`. Build nondeforming controller bones in the existing foot bind orientation, with no parent to inherit unintended pelvis motion. Add real two-bone Blender shin IK and direct foot-orientation constraints. Retain original FK curves as reference and fallback.
- Derive ankle targets and pole trajectories from **Obsidianti's own evaluated skinned-armature foot and knee pose** at existing key and midpoint times. Calibrate each pole angle once across all ten motions, not per Action.
- Insert **controller-only** keys at existing GLB source key times selected by adaptive curve reduction. Because the GLB is already baked/dense, its existing FK keys remain dense; do not misrepresent them as the original Lionheart authoring keys.
- Check every attack and both feet at all existing keyframes plus midpoints, comparing IK-evaluated true foot joint matrix position/orientation and knee joint position to FK reference. The gates are ankle <= 12mm, knee <= 18mm, foot orientation <= 5deg. Full constraint influence=1.0; no fake pass by muting IK. Save explicit per-action per-side discrepancy metrics even on failure. Failed visual parity is quarantined, not published as a usable editor.
- After writing `.blend`, reopen it using native Blender and verify 10 Action associations, exact original FK Action FCurves unchanged, all controller key times from source GLB keys, both IK chains enabled, original reference rig untouched, and report contains a full 10x2 physical comparison. This gate precedes canonical Git LFS authoring-project publication.

## Output
Versioned `assets/obsidianti/source/Obsidianti_IK_AUTHOR_v1.9.5.blend` **only after** full numerical and persistence preflights. A checksum-verified Download copy, receipt and handoff ZIP are generated on Android by the one SHA-checked Termux launcher. Git commits are non-forced; original canonical model and originals retain pinned SHA. Numeric checks never mean human visual acceptance.

## v1.9.5 owner fixes

Pole controls are parented to their corresponding ankle IK controls (no bone connection), with unmodified FK curves, and constrained evaluation turned off while controller curves are being written. Full original GLB key times are initially preserved to avoid destructive premature reduction; numeric FK/IK parity remains a hard blocker. A full device Blender run and owner visual acceptance are still required.
