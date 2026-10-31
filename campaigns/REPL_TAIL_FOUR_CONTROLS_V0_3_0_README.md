# Repl 3D tapered four-bone tail, campaign v0.3.0

Status: Git-authored engineering candidate; actual Repl GLB run and owner visual acceptance remain separate gates.

Owner direction, October 31 2026:
The three-mane-bone auto-weight result is GOOD ENOUGH TO KEEP. Lock it for this campaign. Do not reweight, rename, smooth, redesign or replace the mane while extending the tail. The two v0.2.0 tail controls remain at exactly their original joint indices, parent links and rest transforms; append two descendants instead.

Tail controls and source coordinate pivots:
1. REPL_TAIL_BASE; parent Bone_004; (0, 1.05, -0.93)
2. REPL_TAIL_TIP; parent REPL_TAIL_BASE; (0, 0.80, -1.27)
3. REPL_TAIL_NEAR_TIP; parent REPL_TAIL_TIP; (0, 0.62, -1.43)
4. REPL_TAIL_TERMINAL; parent REPL_TAIL_NEAR_TIP; (0, 0.51, -1.54)
The historical name TAIL_TIP remains on the existing second joint for backwards compatibility. Three spans decrease strictly toward the point.

Actual runner: campaigns/repl_tail_four_controls_v0_3_0.py
Predecessor engine: campaigns/repl_hair_five_controls_v0_2_0.py
Input: original Repl.glb SHA256 d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f

Scope:
* Generate exactly two new tail-only descendants with correct inverse-bind matrices.
* Preserve original 43-body-joint geometry, all body weights, source textures, hair mesh geometry, original neck/mane review, and every accepted mane vertex joint/weight tuple.
* Assign new tail weights between neighboring tail controls, smoothing transitions and holding the root attached.
* Add a separate, restrained four-second tail-only review clip. No root movement, hoof movement, body animation, mane action, wind shader, cloth or physics.
* Verify actual skinning numerically at 33 times; enforce static hoof/body/mane, finite tail, bounded tip motion, progressive segment lengths, and source and output SHA.
* Publish immutable versioned outputs in Downloads and request media registration/open only if those tools exist. Do not claim that a scan or viewer request proves a human saw it.

Primary visual review is FULL TEXTURED GLB playback, not the predecessor's untextured dot cloud. A real interactive textured HTML preview embeds the derived GLB and shows all original GLB triangles and materials. It offers cameras and a Save PNG frame button. The HTML renderer uses pinned Three.js modules from a CDN and requires network to load those modules. The GLB can also be opened separately in compatible local viewers. An offline/cached HTML source without Three.js does not prove actual visual inspection.

Outputs inside Repl_TailFourControls_v0.3.0:
Repl_TailFourControls_v0.3.0.glb
Repl_TailFourControls_v0.3.0_TEXTURERENDER.html
Repl_TailFourControls_v0.3.0_report.json
RECEIPT_v0.3.0.json

Owner handoff is a direct, versioned, checksum-verified .sh attachment and a single exact launch instruction. A GitHub page URL is provenance only and NOT a valid owner-ready download link.

Accept visually only when: four tail controls, tapering spans, graceful tail sway, no noodle-like collapse, unchanged original hairstyle, no seam splits or flying strips, no body/hoof motion, proper original textures/materials and an explicit owner verdict. GitHub CI validates code and synthetic matrices only; it cannot assert the actual GLB's visual success.

Related laws:
Campaign Etiquette: https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit
Pose Lab 3D doctrine: https://docs.google.com/document/d/1BNXVfowZWQSSA0Nk0OK4jP7_K-ysHnM5vTPV_EB8EWU/edit
Machine contract: campaigns/REPL_TAIL_FOUR_CONTROLS_V0_3_0_CONTRACT.json
