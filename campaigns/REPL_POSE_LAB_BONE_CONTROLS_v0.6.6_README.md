# REPL_POSE_LAB_BONE_CONTROLS v0.6.6

**Phone-first interactive skeleton and posing**, without any more speculative automatic gait edits.

Actual source: `Valar05/parametric-parambulator`, pinned main `4e5c15de287d38292e0dd7364031ef084fa55639`, canonical `assets/repl/Repl.glb` SHA256 `c3209b404b5c50842591cfa654142d2f0d84d27eb1acf7779b8d4d504d4508af`.

## Use
1. Download the exact versioned ZIP into Android Downloads.
2. Run the one SHA-checked Termux launch command supplied with the ZIP. It safely extracts and runs the single embedded Bash entrypoint, regardless of current directory.
3. The script reads the actual source and GLB, validates version/structure, builds the textured HTML from the existing project viewer, verifies public Downloads readback, commits this COMPLETE source packet (NOT the model) via Termux Git, and verifies remote main readback.
4. Open `REPL_POSE_LAB_BONE_CONTROLS_v0.6.6.html` in Downloads in a web browser with Three.js CDN connectivity.
5. Toggle **Skeleton overlay** and **Pose Mode**. Tap a bone; tap more to add. Twist two fingers to rotate selected bone(s) on the unlocked local X/Y/Z axis. Double tap empty canvas to deselect. The camera toggle allows orbiting without editing. Buttons provide Undo/Redo, reset and precision +/−; the dropdown exposes every bone by name.
6. Export a reference pose JSON and a PNG screenshot. The JSON contains model SHA, active clip/time, selected bone names, local quaternion values and deltas, plus current camera.

## Locks and safety
- The named bad toe-tip bones `Bone_012`,`Bone_018`,`Bone_023`,`Bone_028` are protected by default, and temporarily shown at GLB rest orientation in Pose Mode. The **original v0.6.5 animation is never edited**, even in the viewer. You may deliberately unprotect a tip for examination; the GLB still cannot be saved/overwritten.
- Gait correction remains unapproved. The 0.6.6 campaign is an **inspector**, not an automatic animation repair, and does not copy any trial GLB into Git.
- No Pose Lab repository mutation. No Home Center, SSH replacement, SFTP, direct ChatGPT GitHub mutation, or multi-script diagnostic loop.
- Preserve all unrelated dirty changes. Only this packet's exact allowlisted source paths are committed in a private isolated Termux clone. No force push, no resets or cleans. Production mismatch blocks.
- The initial HTML depends on existing CDN Three.js 0.170.0 exactly as the predecessor viewer did; fully offline JavaScript vendor distribution is not claimed.
- Git deployment / owner browser interaction are not claimed until an actual Termux and phone receipt establishes them.

## Acceptance gates
`PACKET_SELFTEST` and file hashes, exact pinned production GLB SHA, exactly one GLB, viewer template and gizmo blob guards, all 50 skeleton joints, user gesture source code, non-destructive rendering, HTML SHA in Downloads, authorized Termux commit, remote ref and packet readback. Owner still needs to approve the UI's actual touch experience.
