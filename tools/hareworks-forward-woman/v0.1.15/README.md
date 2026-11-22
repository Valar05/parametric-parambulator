# Hareworks v0.1.15: startup motion recovery

This is a recovery from v0.1.14, where a calibrated model could be visible but a gait-calibration or first IK-step exception froze it with no movement. The status line was insufficient and the Play button could claim RUNNING despite no controller. The exact error is not known from the owner's report, so this version diagnoses actual runtime failures without asserting a guess.

- Keep the source SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, original model, original v0.1.9 six-harmonic ankle and knee-pole equations, four-harmonic pelvis, all art, and OrbitControls.
- Build the full-cycle root and contacts from the archived 60 original v0.1.9 source witness frames, not the unstable 360-frame seam. Verify the 60-frame measured fit against the current real GLB before use. This corrects calibration fragility without changing the accepted math.
- Do 32 actual 120-Hz world-IK physics steps BEFORE declaring the physics controller started. Real skinning and real foot anchors must run; any exception records its stage and switches to a separately labeled procedural-motion preview, never a false PHYSICAL PASS.
- The preview contains the accepted source-fitted procedural hip, ankle and knee-pole gait solved through IK, traveling root, one visible actor and orbitable camera. It is **NOT ground pinned** and is not a substitute for the requested physical gait. Source clip mixer runs ONLY on the invisible calibration reference.
- The viewer's explicit status, Play control and saved diagnostic evidence distinguish a moving unpinned preview from a running physical controller. If the underlying reference fit itself fails, report that actual blocker rather than silently claim motion.

Read `AGENTS.md` and Campaign Etiquette first. Termux Git only. Persistent Android Documents checkout, new version path only, no GLB writes, no previous version writes, no force push. Real-device browser/motion success is not claimed by author-side tests. Human visual approval is independent.
