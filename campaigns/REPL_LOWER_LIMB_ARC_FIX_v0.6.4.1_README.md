# Repl lower limb arc correction v0.6.4.1

**One ZIP, one Termux invocation, one canonical GLB.** This campaign corrects Repl's currently unapproved distal leg articulation, not the accepted tail or mane. The newest owner observation: the forehoof/fetlock and the joint immediately above it should form a rearward arc, and rear hooves must also fold rearward during swing. The previous v0.6.3 code already keyed two front hoof bones, but pointed the bend incorrectly; the previous offline test sample omitted rear hoof tracks, while production already contains at least Bone_023. This version fixes both cases. The rear cannon needs the same calibrated positive-X bending pole as the fore cannon (the earlier negative sign made the hoof geometry arc forward): all leg acceptance is based on visible skinned-hoof motion, not merely angle signs.

## Source and constraints

Source: pinned `Valar05/parametric-parambulator` commit `77148fbe2855112906fb24801df2d8ee28e8a51a`, canonical `assets/repl/Repl.glb` SHA-256 `29bc09491f8d42bd272c2a03142252323d147a8bcc90b3aa7c75ed127a31be84`. No Pose Lab writes or other model imports. The four-beat walk moves forward through space for 0.96 model units. There is **no in-place variant**.

Fore pairs: **LF 013→012, RF 019→018**. Hind pairs: **LH 024→023, RH 029→028**. Larger upstream joints can compensate by bounded IK only during swing to preserve physical hoof targets; stance tracks remain identical. Rear foot bone rotations are corrected where already present and newly keyed only if missing; existing front foot tracks are corrected, without changing skeleton hierarchy, meshes, skin weights or earlier animations.

## Use

Download the one `REPL_LOWER_LIMB_ARC_FIX_v0.6.4.1.zip` into Android Downloads and invoke its SHA-pinned one-liner from the chat. It validates, extracts, compiles, checks repository identity and source SHA, computes and verifies full model locally on the phone, then publishes a full-textured browser viewer and diagnostic report. Only after those checks does it update the single GLB path with an allowlisted Git commit, push through existing Termux Git authentication, and read back the exact remote model bytes. No manual extraction, no second diagnostic script.

If Termux cannot access GitHub, preserved local state and exact problem are reported in the same log. The output is still a candidate until a human inspects the textured gait. The viewer uses Three.js libraries over network; it embeds the actual GLB geometry and textures so the model file itself needn't be separately downloaded.

## Diagnostics

Checks: 50 joints, 53 nodes, exactly six animations, two rear hoof channels present and corrected in each walk clip, updating existing channels or creating missing ones as observed, original three clips and all accepted rest weights unchanged, all four mid-swing rearward arcs, a signed negative-Z rearward **skinned hoof** displacement gate for all four legs, bounded proximal correction, real skinned plantar witness locations, unchanged stance, exact 0.96 world root travel. Small negative swing surface readings are reported. They are not masked or called accepted. Optional Blender rendering is attempted when `blender` is present on the Termux PATH. No dependence on Blender for the numerical IK bake.

## Receipt and recovery

Stable Termux state: `~/.local/share/repl-campaigns/lower-limb-arc-v0.6.4.1/`. Public Downloads: `REPL_LOWER_LIMB_ARC_FIX_v0.6.4.1_OPERATOR.log`, `REPL_LOWER_LIMB_ARC_FIX_v0.6.4.1_TEXTURERENDER.html`, `REPL_LOWER_LIMB_ARC_FIX_v0.6.4.1_report.json`, `REPL_LOWER_LIMB_ARC_FIX_v0.6.4.1_RECEIPT.txt`. Re-running the same ZIP verifies the same packet and remotely committed result, or resumes a verified local commit if the push failed. It never force-pushes, resets, cleans, touches unrelated files, or creates additional repo GLBs. Full signed/physical acceptance requires owner viewing the resultant walk.

## 0.6.4.1 field repair
The first 0.6.4 run stopped BEFORE Git mutation because the real canonical GLB contains a pre-existing Bone_023 rotation channel. The first packet was tested only on a structural surrogate where this channel was absent. This patch version discovers per-clip rear hoof channel presence and updates existing tracks in place, preserving their exact planted pose. It still supports the absent-channel case; only genuinely missing channels are appended. Separate source fixtures test both branches.
