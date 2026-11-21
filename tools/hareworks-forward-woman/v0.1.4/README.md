# Hareworks forward Woman upper-body continuity v0.1.4

## Commissioned result and precise boundaries

The owner's high-frame-rate recording `5366.mp4` shows much improved **lower-body** motion on v0.1.3, but jarring upper-body movement. The user said "But lower I think looks good though". This campaign must preserve all lower-body mechanics: the immutable v0.1.3 `foot-kernel.mjs`, `foot-profile.json` and its IK statements, plus the v0.1.2 pelvis motion profile and equations. No model or animation asset is modified. The forward-only, in-place `Walking_Woman` clip comparison remains the only demonstration. No turning, strafing, world-space footsteps, other gait authoring, or new character.

## Change

The reference skinned character (left) continues to play the unmodified source `Walking_Woman` animation, including upper body. The generated character (right) no longer plays *any* source animation tracks during runtime. Instead, on loading the exact GLB, it **samples the source upper-body bones once** at 120 uniformly spaced points for joint-level calibration. For each eligible local bone quaternion, it converts the relative rotation into a shortest-path rotation vector, fits a compact periodic Fourier representation, and reconstructs a smooth local quaternion at arbitrary gait phase. The local positional deltas are likewise phase-fitted. The generator does not read clip upper rotations during rendering, so this is source-calibrated procedural playback, **not** a general reactive arm or balance system. No hips, legs, feet or toes are touched by the upper-body stage. Upper-body amplitude defaults to 70%, and harmonic detail to 3; alternate selectable levels (0, 70, 85, 100%, and 2/3/4 harmonics) enable direct visual comparisons, not independent acceptance claims. Shortest quaternion arcs, t=0 anchoring, periodic curves, and seam continuity avoid abrupt wrap corrections.

## Honest gates

- Offline Node test: quaternion signs, log/exp, 120 Hz periodic seam, smooth harmonic shape, invalid input rejection.
- Exact source/model verification: 74 joints, nine clips including `Walking_Woman`, canonical GLB SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6` and 6,784,896 bytes, unchanged source and historic versions.
- Browser on actual skinned GLB: 30, 60, 120 fps gait cycles, joint continuity and reference differences, preserved leg and pelvis metrics, per-bone upper-body max quaternion steps, maximum offenders, actual fault injection and rollback diagnostics. The upper step limits (18°, 11°, 7° at 30/60/120) are **provisional review thresholds**, not accepted biomechanical rules. Exceedance remains a visible BLOCKED warning; the viewer still renders for diagnosis.
- The v0.1.3 acceptance is only the owner's "lower looks good" observation. This does not authorize changing leg paths or imply completed, realistic root locomotion.
- **No real-model viewer execution or visual acceptance is claimed until the Android browser runs.** No locally generated script, static screenshot, node test or Git readback substitutes for that evidence.

## Operator handoff

Execute the single SHA-verified `hareworks-forward-woman-proof-v0.1.4.sh` in Termux. It checks pinned Git parent and rules, validates exact original model locally or via LFS, checks unique destination paths, stages seven text files only, pushes without force, verifies remote SHA and blob parity, starts an isolated no-cache HTTP viewer and prints its actual full URL, PID, port, model hash, source revision and receipt. If publication already happened, the identical script can be rerun to recover the viewer without a new commit. A failed server check must report the exact HTTP path and `server.log`; it must never silently claim browser success.

Mandatory rules freshly read: GitHub `AGENTS.md` at parent `e7794120d5875aa1a56a4bc23bef46c4002fccfd` (Git blob `547c2af52303f4efb718bbf8f82a698110c7bfca`), Home Center Campaign Etiquette `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`, Top-Down Etiquette `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU`.
