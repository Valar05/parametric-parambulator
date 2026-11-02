# Parametric Parambulator

A clean, independent home for Repl's procedural 3D movement, rig and animation development.

## One model, one authoritative path

The sole live Repl model belongs at `assets/repl/Repl.glb`. **The original 43-joint source baseline is committed here; later accepted mane/tail weighting is not yet integrated.** The intended original source is hash-locked in `assets/repl/CANONICAL_MODEL.json`. No campaign result is integrated until that actual GitHub file exists, can be read back and has the correct digest.

After the one-time initial import, each approved bone-weight, pivot or motion change must update **the same GLB path** in this repository. Git commits carry the history and rollback. Scripts, rendered evidence, reports and viewers may be versioned; new GLBs for each experiment may not. Temporary candidate models are not deliverables.

The owner has visually approved the mane-weighting direction and later tail results. The original source GLB is older and cannot be claimed to already contain those approved improvements. Preserve accepted work when integrating an actual successor. Do not regress to the unweighted source while reporting a current success.

**Pose Lab is historical reference only.** Do not require it as a checkout, workspace or transport for Repl. Earlier `campaigns/` scripts are historical prototypes and currently generate separate GLB outputs; they are **not** the approved canonical-asset delivery workflow. Do not run them to claim integration of the model in this repository.

## Required gates

Source identity, remote commit, same-path GitHub asset readback, actual visible textured evidence, and the owner's visual verdict are separate completion stages. Never treat a launcher, test result, GitHub link or local scratch model as the final model.

Campaign Etiquette: https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit

## Current canonical motion candidate

The single `assets/repl/Repl.glb` model is updated in place with the 3-control mane, 4-control tapering tail, preserved body/hooves, and 14-second tail straightening clip. Full-textured review includes an optional, non-mutating tail pivot gizmo, off by default. Version v0.5.1 is a candidate awaiting owner visual verdict, not automatic aesthetic acceptance. Git history preserves prior model.

## Tail attachment repair v0.5.2

The v0.5.1 root pivot was too low for the actual rump/tail attachment. The single canonical Repl.glb now uses a root at (0, 1.204, -0.889) derived from the measured body/tail intersection arc, while preserving the resting positions of the other three tail controls, unchanged original skin weights, original mane and materials. The 14-second straighten keys were recalculated against the corrected rest skeleton, reaching approximately -8 degrees across all three tail spans. No other GLB was created in the repository. The textured review includes the optional non-mutating root gizmo (off by default). The owner visual acceptance is pending. The earlier v0.5.1 commit remains available through Git history.

## Repl: moving four-beat IK walk v0.6.0

The one canonical `assets/repl/Repl.glb` now contains three additional forward-traveling four-beat horse walk review clips (legs, body, integration). Each advances the original skeletal root in world +Z. There is no in-place walk variant. Four distinct stance/swing sequences are solved using the actual foreleg/hindleg chains, with mesh-hoof groundedness tests. The earlier mane, corrected tail pivot, tail straightening and previous clips are unchanged. The owner's visual verdict is pending; Git numerical checks alone are not acceptance.

## Repl forelimb anatomical hinge correction v0.6.1

The single canonical `assets/repl/Repl.glb` retains all six clips. The three forward-traveling walking clips now constrain elbow protrusion toward the horse’s head (+Z), and carpal flexion toward the rear (-Z). Four real skinned front-leg chains have separate joint limits, a grounded hoof target, and an anatomy/pole validator. The better-performing hindlegs, existing three mane/tail clips, body/hooves stance tracks, 50-joint skeleton, original textures and approved v0.5.2 tail pivot remain unchanged. Each walk travels 0.96 model units forward; no in-place version. The full-textured viewer shows optional elbow/carpus markers and the optional, non-mutating tail pivot gizmo. Actual owner visual approval is still pending.

## Repl owner-corrected foreleg joint levels v0.6.2

Following the owner rejection of v0.6.1, the foreleg hinge constraints were moved ONE JOINT LOWER in both leg chains: Bone_014/020 are the upper forward bending points and Bone_013/019 are the lower rearward bending points. The previous mapping (015/021 upper, 014/020 lower) was rejected. The campaign preserves every contact-phase pose, hindleg, torso, mane, tail and root-travel animation track, and it updates only the current canonical `assets/repl/Repl.glb`. The existing 14-second tail and corrected attachment geometry are unchanged. The three full forward-travel walking clips each still advance 0.96 model units; no in-place clip is authored. The textured HTML review provides correctly labeled upper/lower bending markers; its export is supplementary and human visual acceptance remains pending.

## Owner-corrected foreleg bend polarity v0.6.3

The owner rejected v0.6.2 because the forehoof bends FORWARD, not backward. The upper mapped foreleg joints LF Bone_014/RF Bone_020 now bend BACKWARD, and the lower mapped joints LF Bone_013/RF Bone_019 bend FORWARD. Joint-chain levels remain unchanged from v0.6.2; no additional bones are added. Only swing foreleg rotations in the same three forward-travel walk animations are corrected. Stance legs, hind legs, root translation, body, mane, tail, approved socket, skin weights and earlier three animation clips remain intact. The canonical assets/repl/Repl.glb is the only model file in the repository. A textured viewer highlights both bend positions and displays forward travel. Visual acceptance remains pending until the owner reviews v0.6.3.

## Four-leg distal hoof arc correction v0.6.4.1

The owner rejected the v0.6.3 forefoot shape: both the hoof joint and the joint immediately above it must create a backward-bending distal arc. The same distal correction applies to the rear hooves. This campaign corrects existing FRONT hoof tracks Bone_012 and Bone_018 and corrects existing REAR hoof tracks Bone_023 and Bone_028 when present, or creates them only when missing, alongside lower cannon joints Bone_013, Bone_019, Bone_024 and Bone_029. Each stage preserves exact prior root travel and four-beat gait contact timing, and the three older mane/tail clips remain unchanged. A textured review viewer labels all eight distal joints and reports honest hoof ground warnings. Only assets/repl/Repl.glb is a canonical model, and numerical validation does not establish artistic acceptance.

## Four-leg visual swing-shape correction v0.6.5

Owner rejected v0.6.4.1: both front legs appear to bend the wrong direction, the forefoot barely flexes, and the rear fetlocks bend too subtly. The new candidate enforces the actual sagittal segment directions of both front knees, lower cannon/pastern, and toe lift, plus increased rear fetlock swing. It preserves stance frames, original 4-beat timing, all previous clips, body geometry and weights, mane/tail, approved socket, and the existing 0.96 world-unit forward travel. No in-place walk, no extra GLB. World-space segment and skinned-vertex tests pass before Git commit, but final naturalness remains the owner's visual decision.

## Cartoon horse walk with FK-protected hoof mass v0.6.8

Owner rejected the v0.6.5 ankle/toe animation as stiff, wrongly rotated, and squashing the hoof mass. A v0.6.6 Pose Lab demonstration identified the functioning lower hinges and confirmed the hind hoof mass contains two independent toe-deformation branches per hoof. v0.6.8 leaves those deformation branches as FK followers, fixes all four hoof-mass parent rotations at local rest, preserves approved front middle joint motion, and adds 52-degree cartoon front lower swing plus 38-degree rear lower swing through the owner-demonstrated local X axes. It preserves existing contact rhythm, all prior clips, root travel 0.96, mane/approved tail, single GLB. The textured HTML includes the existing Pose Lab tools; visual acceptance remains PENDING until owner review.

## Front swing clearance and shoulder-middle articulation v0.6.10

Owner reviewed v0.6.8: joint directions look correct and rear-leg motion is reasonable, but front hooves drag and rotate through the ground. This front-only campaign adds 20–30 degrees of world-forward shoulder segment lead at Bone_015/Bone_021 and stronger world-backward middle segment folding at Bone_014/Bone_020, with runtime signed axis calibration and bounded physical-clearance profiles. The whole skinned underside must clear the same hoof planted ground reference. The 0.6.8 rear legs, front lower drivers, hoof masses and deformation branches, all stance frames, world forward travel, timing, mane, tail, geometry, weights and the single canonical GLB path are preserved. Source is strictly pinned to 0.6.8 and the final textured visual review remains pending.

## Repl measured low front walk v0.6.15

The v0.6.10 canonical model was decoded and its skinned hoof vertices measured directly. The signed, source-locked trajectory in campaigns/ was optimized against those physical geometry measurements before the packet was built. Termux re-measures every hoof through all 97 frames in the three forward walk clips before allowing Git mutation. Front peak swing lift is targeted at 25-33% of v0.6.10, with toe-off clearance greater than 0.0035 model units in the actual deformed mesh and restrained load-side body settle. Only four front shoulder/middle rotation channels and stage 2/3 root Y/roll can change. Rear joints, distal hoof and toe joints, skin, geometry, hair, earlier clips, root X/Z and forward travel remain unchanged. One canonical GLB path. Human visual acceptance required.
