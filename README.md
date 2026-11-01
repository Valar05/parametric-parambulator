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
