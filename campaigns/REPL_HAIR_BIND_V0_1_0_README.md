# Repl hair-only axial binding campaign v0.1.0

## A very polite statement of intent

Repl is already a magnificent, wide-chested unicorn. His existing body mesh, custom
43-joint rig, materials, mane and tail are accepted source material. This campaign
does not attempt to improve, repair, replace, or reinterpret any of them.

The only production task is to **automatically generate skin influences on the
separate mane and tail**, using **existing axial bones**, then animate a small
neck-and-head gesture to check that the new hair follows without tearing,
exploding, detaching or being pulled by leg bones.

No new bones. No manual weight painting. No walking. No moving hooves.
No wind shader yet. No cloth solver. No changes to the original source asset.

This is deliberately an engineering candidate, not an automatically approved
visual result.

## Authority

- Current Campaign Etiquette:
  https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit
- Pose Lab 3D rules:
  https://docs.google.com/document/d/1BNXVfowZWQSSA0Nk0OK4jP7_K-ysHnM5vTPV_EB8EWU/edit
- Original Repl asset folder:
  https://drive.google.com/drive/folders/1opV8L2iTpcbKtpXKtUqDQUYt63A2t6qT
- Machine-readable version contract:
  campaigns/REPL_HAIR_BIND_V0_1_0_CONTRACT.json
- Exact owner-uploaded input:
  Repl.glb SHA-256
  d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f

The source GLB is deliberately NOT checked into this public repository.
Do not fetch a similarly named or regenerated model and call it the original.

## What the script actually does

1. Prints its own filename, version and SHA-256 before any work.
2. Finds **only** the hash-approved Repl.glb from bounded known paths or
   the explicitly supplied --source path.
3. Inspects exact glTF structure: 6,082 skinned body vertices, 1,819 separate
   hair vertices, 1,207 hair triangles, 43 existing joints and no source clips.
4. Joins duplicated hair positions **only in its analysis graph**, never
   welding or changing source geometry, UVs or topology.
5. Classifies mane and tail by the observed source geometry, with
   independent anatomically constrained bone whitelists.
6. Samples source-body axial weights at nearby trusted roots and propagates
   those weights across hair surfaces. Long tips inherit influence from
   their original attached region, not the nearest unrelated body or leg bone.
7. Restricts each hair vertex to four existing skin influences, normalizes
   weights, and verifies every hair vertex receives only allowed bones.
8. Adds JOINTS_0 and WEIGHTS_0 to the **derived** hair primitive and a
   skin reference to its existing mesh node. Original glTF buffer bytes and
   original body primitive properties remain intact.
9. Adds one small three-second neck/head-only animation on
   Bone_010, Bone_009, Bone_008 and Bone_007, and on nothing else.
10. Samples 25 frames of the true skinned body and hair, explicitly checking
    the unchanged rest silhouette, finite hair geometry, movement of the mane,
    fixed hoof-node positions and near-zero hoof-surface drift.
11. Produces a versioned derived GLB, JSON report, a fully offline HTML
    point-sample moving preview, and a checked SHA-256 receipt.
12. On Termux, attempts the existing exact-file media scanner and requests
    an offline preview open if those commands exist. Neither request is
    described as confirmed Gallery visibility or human acceptance.

## Operating modes

- run: generate once, then verify every output hash on repeat invocation.
- doctor: check Python, exact input identity and basic glTF source structure,
  without producing outputs.
- status: check existing generated receipt and every listed artifact hash.
- resume: same safe idempotent run; never silently overwrite partial work.
- rollback: reports that the original was never changed; does NOT delete any
  candidate, input, or unrelated user data.

Python 3.10+ standard library only. No package installation, accounts,
GPU, shader compilation, Blender dependency, Git operation, or new CLI
transport is required by the runner.

## Intended operator lane

Author and audit this code in GitHub first. Pin one exact commit. On the
actual phone, use a verified isolated checkout of that commit and run:

    python3 campaigns/repl_hair_bind_v0_1_0.py run

If the locked asset is not already at a known on-device location, give the
script its actual path with --source. It never requests SFTP and will not
silently select a different model. The script itself cannot retrieve private
Google Drive bytes without the account's explicit, supported transport.

The generated outputs normally go under:

    ~/storage/downloads/Repl_HairBind_v0.1.0/

If shared storage is unavailable, they go to ~/Downloads/Repl_HairBind_v0.1.0/
or an explicit --output directory. An output folder from a different run
or an incomplete publication is BLOCKED rather than overwritten.

### Delivery

- Repl_HairBind_v0.1.0.glb
  The original body and new hair skin, with the no-hoof-motion review clip.
- Repl_HairBind_v0.1.0_preview.html
  Offline HTML point-sample visualizer with side, front and three-quarter
  views. This is NOT a substitute for textured glTF review in Blender or
  the actual game runtime.
- Repl_HairBind_v0.1.0_report.json
  Weight coverage, root-seed counts, per-bone contribution, body/hoof drift
  and hair displacement calculations.
- RECEIPT_v0.1.0.json
  Exact input hash, output hashes, source revision when known and pending
  human acceptance.

## Non-negotiable review criteria

No visually mangled pointy silhouette. No loose seams. No root separation
from head/neck or tail dock. No tail weighted to either hind leg. No body
reweighting. No hoof shift or gait invention. The head and neck visibly
gesture, and the mane follows multiple existing axial bones rather than
remaining rigidly parked in world space. The first test contains no wind
simulation. If the bone-only result is convincing, that is sufficient.

The runner can prove a numerical candidate and its artifact identity. It
cannot prove the user's actual Blender or game-viewer result. A human verdict
is required, and a later shader-only secondary-motion campaign is separately
scoped and not automatically authorized.

## Expected status before physical execution

GIT SCRIPT: committed and available after remote readback.
EXACT SOURCE: uploaded Repl.glb identified by SHA, not included in Git.
PHYSICAL RUN: not attempted by creating this repository code.
DERIVED GLB: not claimed until on-device or authorized remote receipt.
VISUAL ACCEPTANCE: pending the owner's review.

This separation is intentional. A convincing horse is a visible result,
not merely a triumphant JSON file.
