# Repl hair-only bone controls v0.2.0

This is a deliberate, additive successor to the preserved v0.1.0 axial auto-weighting campaign. Its purpose is **five hair-only controls, automatic hair weights, and a gentle stationary-hoof movement review**. No walk cycle, physics or wind is part of this commission.

## Owner-protected inputs
- Exact source GLB: `Repl.glb`, SHA-256 `d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f`.
- `Repl.blend` stays completely untouched.
- Body primitive, original 43 joints, body weights, UVs, textures and materials stay untouched.
- Predecessor `repl_hair_bind_v0_1_0.py` stays byte-for-byte untouched and is pinned by blob SHA in the new code.

## Exact addition
Three new mane bones: REPL_MANE_REAR (child of Bone_003), REPL_MANE_MIDDLE (Bone_010), REPL_MANE_FRONT (Bone_008).
Two new tail bones: REPL_TAIL_BASE (child of Bone_004), REPL_TAIL_TIP (child of new REPL_TAIL_BASE).
All five are appended to the derived asset's existing skin joint list; indices of the original 43 are preserved. Their world-space bind pivots are declarative candidates and must be examined visually, not treated as anatomical measurements. Skin bind matrices are constructed so the initial pose is preserved. No new child bone is animated in this experiment.

The original root-derived hair skin weights are assigned to these five controls. Mane axial zones blend between rear, mid and front. Tail weight increases toward the outer mass. No leg bone is permitted to contribute to the new hair weights. Coincident seam vertices must agree.

The **review animation intentionally moves only Bone_010, Bone_009, Bone_008 and Bone_007** in a restrained head/neck gesture. Original legs, hooves and root have no new animation channels. The added hair bones remain at REST to demonstrate inheritance before secondary wind is introduced.

## Single-command launch
Use the versioned `REPL_HAIR_FIVE_CONTROLS_v0.2.0.sh` **attached directly to the ChatGPT handoff**; do not attempt to download the implementation by opening a GitHub blob page in the Android GitHub app. The short launcher fetches one pinned Git revision in an isolated directory and executes the versioned Python runner. The exact source Repl.glb must already be present in supported Downloads locations or passed with an explicit path. The runner will not improvise an account login or fetch a similarly named GLB.

The runner supports run, doctor, status, resume and rollback. An immutable output directory is used. A partial/colliding directory is a visible BLOCKED state, not permission to overwrite it. Outputs include a derived GLB, JSON evidence report, offline moving-mesh preview, and SHA-256 receipt.

## Review / noncompletion boundary
Numerical checks include unchanged body primitive attributes and original buffer prefix, 48 total joints, proper rest-pose skin, 1,819 assigned hair vertices, fixed hooves, bounded hair movement, and no independent animation on the five added bones. Visual checks remain a HUMAN acceptance step. The HTML preview is a diagnostic dot/vertex visualization, not a substitute for a textured GLB review in Blender or the game.

Code compilation/CI source success **does not mean** this runner executed on the owner's actual model or appeared in Android Files. A ChatGPT download link **is** a real file attachment; it still does not prove phone Downloads placement. A GitHub link is source provenance only.

Sources: [Campaign Etiquette](https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit), [Repl assets folder](https://drive.google.com/drive/folders/1opV8L2iTpcbKtpXKtUqDQUYt63A2t6qT).
