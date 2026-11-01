REPL Cartoon FK Hoof Walk 0.6.10 | targeted front swing clearance

Visual correction from owner (2026-11-01):
- Actual joint directions in v0.6.8 look correct; hind legs reasonably animated.
- Front hooves drag and rotate through the ground.
- Swing shoulder directly above front middle joint should advance 20-30 deg.
- Middle foreleg should fold backward more than before. Front curvature must be
  visually more dramatic than rear curvature while gait speed stays unchanged.

This version changes ONLY four front rotation channels, in swing frames only:
LEFT Bone_015 shoulder, Bone_014 middle; RIGHT Bone_021 shoulder, Bone_020 middle.
World +Z angle deltas are calibrated from the actual pinned rig at runtime;
no assumption that left and right local +X have the same world-space sign.

The lower front drivers, rear legs, four toe-mass orientations, skin/mesh,
hierarchy, 6 animation clips, root-travel and timing, mane and tail remain.
The old v0.6.8 protection of the two middle fore joints is intentionally
superseded only for these specific middle-joint SWING keys by owner instruction.

Self-recovery searches a bounded set of amplitude profiles (20-30 deg
shoulder and 24-60 deg signed middle). Every profile is judged against actual
skinned hoof underside elevation relative to the SAME foot's planted underside.
All three travel clips must pass; a missing/altered rig, uncertain source or
insufficient clearance blocks the update without touching the canonical GLB.

Execution contract:
- Exact parent Git commit 859a74c72cf0d8c35e54b4128119603976f8daa9
- Exact input GLB SHA-256 eff0c604ca56ba58543c7a477bffc0e22e3c23f1d5da00bdbf1ea62369f27509
- Single Termux .sh entrypoint bundled in the ZIP; output via Termux Git only.
- No direct ChatGPT GitHub mutation. No new GLB in repository.
- Numerical checks and packet selftest are not a claim of human visual approval.

Regression fix 0.6.10 (2026-11-01):
- Fix variable collision in physical verifier: the foreleg spec was overwritten
  with the swing phase fraction, causing TypeError after all three stages.
- Exercise make_candidate() AND verify() through every mid-swing branch in an
  isolated deterministic synthetic rig before performing the real-device run.
- Preserve bounded physical-clearance profile recovery. Real-world source,
  rig, skin, keyframes, feet and human approval remain separate validation.
- Write a durable blocked diagnostic for developer exceptions; no blind replay,
  no tolerance inflation, no Git mutation on unsuccessful candidates.
