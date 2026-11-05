# Obsidianti Heavy1: true Blender constraint IK transfer, v1.5.6

## Commission and authority

Owner requested a **Heavy1-only** replacement for the failed v1.5.0 IK campaign. The failed solver independently rotated bones starting from the rejected Heavy1 FK pose, mis-anchored source Knee.IK pole controls at the target physical knees, and guessed ±8° yaw without establishing anatomical alignment. Those mistakes are **forbidden** in this version. Full native source movement archive v1.4.0 and approved Obsidianti combat Idle are the authority. Do not regenerate or approximate the donor action.

**Authorized execution and mutation lane: Android Termux Git only**, `Valar05/parametric-parambulator`. One SHA-verified and self-contained `.sh` launcher operates on an isolated verified checkout. No ChatGPT connector, Windows, Pose Lab or local scratch publication. Original model input `assets/obsidianti/Obsidianti.glb` LFS SHA256 `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4`. Original source archive `diagnostics/obsidianti/lionheart-ik-all-v1.4.0/actions/Heavy1.json`, SHA256 `a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4`, all 61 half-frame samples. Calibration SHA256 `b6d23f49c67df7816124362f4b1ee540db5c16a672fbc8c435a7f503ca123336`. Source sampler was actual Blender 4.3.2 with original native Lionheart IK constraints evaluated. Pinned glTF math helper `campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py`, SHA256 `dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f`.

## Exact allowed edits

**Only** six `rotation` channels in `Lionheart_Heavy1` for `mixamorig:LeftUpLeg`, `LeftLeg`, `LeftFoot`, `RightUpLeg`, `RightLeg`, `RightFoot`. Heavy1 Hips translation AND rotation, all other Heavy1 tracks, ALL other animations (including accepted Heavy2, Ares footwork, source Walking/Running, approved LionheartIdle and ObsidiantiIdle), nodes, bind transforms, skins, meshes, materials, weapons, wedges, helmet, tassels, clothes, Repl, scene and geometry are immutable. No other canonical GLB path is created. Original BIN payload must remain an unchanged prefix. A new model in the same canonical path is permitted only after actual physical proof; Git history provides rollback. The new clip is an **unapproved visual-review candidate**, not a completed accepted repair.

## Actual Blender IK authoring

1. Verify the exact full native source data, imported model, rules, git LFS and hashes. Build a **temporary Blender armature**, not another exported model, from the actual glTF bind matrices of Obsidianti's pelvis, thigh, shin and foot bones, preserving their bone axes and lengths. Initialize its leg transforms exclusively from the user-approved combat Idle, transformed underneath the existing locked Heavy1 pelvis. Do not read any rejected Heavy1 leg rotation for solving.
2. Drive actual Blender `IK` constraints (2-bone chain, full influence, no stretch) on each `Leg` using actual foot-controller target objects; drive knee-pole objects using the **source Knee.IK control relative to Foot.IK**, preserving their full measured separation (54.1cm left, 36.9cm right at original source frame zero), not the target physical knee position. Use foot `COPY_ROTATION` from the native evaluated source Foot bone relative to source hip. Only the source IK controls and approved target Idle define leg pose.
3. Convert Blender Z-up and glTF Y-up exactly, and determine source-to-target anatomical facing from evaluated source pelvis/left-right thigh positions and the actual target approved Idle left-right thigh positions. **No arbitrary ±8° guessed yaw.** Sample actual source controls and native foot rotations at all 61 half frames. Preserve the existing unchanged target pelvis track, report reach or continuity failures rather than editing hips without approval.
4. Calibrate Blender's `pole_angle` by minimizing distance between the target's approved Idle knee and actual Blender-evaluated IK knee at the first frame. Use temporal IK continuity by advancing one frame at a time without independently resetting leg pose to rejected FK. Export only six actual evaluated deform joint **local rotations**, converted back to original glTF node basis. No extra controller bones or scene objects are exported.
5. Independent Python/glTF validator replaces only those six named Heavy1 sampler outputs in a quarantined binary, checks Blender-vs-glTF ankle reconstruction at all keys, controller goal alignment, sampled knee motion, quarter-frame leg/joint continuity, and **actual skinned wedge sole vertices** at all 121 quarterframe points. Reject >4mm Blender/glTF bone reconstruction error, >9mm ankle-to-native IK target error, >6cm quarter-frame sole/ankle jump, >25° quarter-frame knee bend-direction or >25° half-frame joint rotation, or >15mm actual wedge penetration. No validation threshold is simply dropped or reclassified as a success. The broken published FK animation is a before/after reference only.
6. If a genuine native-source amplitude of 1.0 fails, try a bounded narrow sequence `0.95, 1.05, 0.9, 0.85, 0.8` with the SAME real Blender constraint solver. Preserve each rejected profile's actual numerical failure reason, and select the first full physical pass. If none passes, **publish no model**. A diagnostic Git report and phone archive still explain the exact failure.
7. Candidate commit/readback only through Termux Git, immutable source ZIP preverified, source scripts committed and pushed first, model candidate written only into isolated temporary path until checks pass, original model LFS pushed/verified, remote main and Repl Git blob independently read back, phone viewer selects Heavy1. Owner visual verdict remains required.

## Evidence and limitations

The author's offline Python parser, syntax checks and Git fixtures do NOT validate Blender's native pose result for the exact published model. The authoritative test occurs in the user's native/proot Debian Blender installed in Termux against the full real LFS asset. On failure, do not tell the owner the repair was completed. The output receipt, full skin validation and handoff ZIP are in Termux Downloads; machine-readable success/failure evidence is saved at the new `diagnostics/obsidianti/heavy1-blender-ik-v1.5.6` Git path when the authorized Termux run reaches publication. Numeric success does not equal owner visual acceptance.


## v1.5.6 source-world trajectory correction
The donor Heavy1 pelvis moves sharply in the middle of the action. Its foot IK
controllers move more smoothly in WORLD space. The previous evaluator imported
pelvis-relative displacement onto the target's locked pelvis, causing excessive
foot displacement, knee branch flips, and discontinuity. This version maps the
donor's SOURCE WORLD controller displacement and evaluated ankle residual to the
target idle foot, retaining the target's original Heavy1 pelvis tracks untouched.
Pole positions use the actual source pole-to-controller lever arm. Foot rotation
uses the donor's world rotation delta in the anatomical aligned frame.
Cyclic source travel is integrated along the controller path, not inferred
from identical first and last positions. All failures remain fail-closed.

Only Heavy1 six leg rotation channels are mutable. The evaluated Blender rig
remains real IK, with actual full-skinned wedge validation required before any
canonical GLB commit. Human visual acceptance remains pending until supplied.


## v1.5.6 Combined diagnostics and physical preview
Audit object/rest/bone ratio and foot rotations independently. Run actual Blender IK
under native, idle-orientation and hip-local foot-rotation transfers, using
combined/thigh/shin anatomical ratios. Each result is physically checked against
actual skinned wedges and locked canonical bones. Failed physically safe candidate
GLBs are preserved in isolated private/public evidence, NOT published as canonical.
The least-invalid candidate is automatically displayed as UNAPPROVED even if no
profile passes, alongside physical metrics, source-Idle baseline and exact SHA.
Real owner visual approval remains a separate human gate.


## v1.5.6 source-driven hip-independent IK targets
Based on owner video feedback: opening frame acceptable; forward foot mainly anchored,
rear foot mostly translates backward as stance widens; both feet rotate. These
are source-motion expectations, not manually scripted front/rear trajectories.
Actual Lionheart Foot.IK/Knee.IK/controller bone positions and rotations are
retargeted into fixed world anchors calibrated from approved initial target Idle.
Neither animated target hips nor rejected target Heavy1 FK leg tracks create
world-space foot targets. Source knee-plane lever and moving knee are retained.
Six-channel Only: Heavy1 bilateral UpLeg/Leg/Foot rotations, preserve root,
pelvis, skin, all other actions including Repl. Native Blender IK evaluation,
skinned footwear physical guards, source-space and knee diagnostics, immutable
versioned packet, Termux Git remote readback, always-on failed-candidate visual
review with HTTP identity and copyable URL. Numeric validation and owner visual
approval remain distinct and both mandatory for accepted animation.


## v1.5.6 metadata contract correction
The actual v1.5.6 Blender constraints evaluated every sample, but physical APPLY rejected
them before skin checks because the evaluator emitted trajectoryBasis=
SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS while APPLY expected
the old v1.5.4 identifier. Correct only the validator contract and add a
regression test. Preserve source-driven Blender controls, world target invariance,
knee pole tracking, six-channel edits, 121 skinned probes, and quarantined visual
output even when the numeric physical preflight fails. This is a source interface
repair, NOT evidence the motion is valid or visually approved.
