# Hareworks Forward Woman v0.1.9: measured pelvis-orientation hitch repair

The owner found v0.1.8 an improvement but visually rejected a recurring leftward upper-body lean/hitch (video `5387.mp4`). The specific hypothesis is that v0.1.2's generated pelvis reconstructs XYZ translation and yaw, but omits source pitch/roll. It is a **hypothesis**, not an assumed cause.

## Precise change and locks

- Read the complete 3D source pelvis quaternion from exact `Walking_Woman` (74 joint, 9 clip GLB) at 120 points once at browser startup. Remove source heading to isolate relative pitch/roll and fit a phase-periodic quaternion residual.
- Reconstruct `original predicted yaw × source-fitted residual pitch/roll` in world coordinates (quaternion composition order verified by synthetic tests). Preserve the v0.1.2 pelvis translation and yaw path, and ALL v0.1.3 IK leg joint/foot formulas. The source animation does not drive the generated character during runtime.
- Provide A/B controls: v0.1.8 baseline/off, tilt4, tilt12-half, tilt12, and automatically selected mode. Auto chooses a correction only if its real-skinned pelvis quaternion mismatch improves and the prior leg, torso, head, IK residuals remain within explicitly stated non-regression deltas. Otherwise it defaults to **v0.1.8 baseline**, without claiming a fix.
- Measure at 30/60/120 Hz with half frames, source/generator signed sideways and forward lean, per-frame timestamps, pelvis quaternion RMS, chest and head world positions, ankle and knee world positions, IK residual and cycle endpoint.
- Preserve v0.1.8 source t=0 upper anchor and 70%/3, 100%/4, 100%/12 parity comparisons; no change to original model, source clips, weights, earlier versions, Repl or root motion. Existing strict parity limits remain. Visual approval by owner still required.

## Regression gates

- Real GLB canonical SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6` and 6,784,896 bytes, `Walking_Woman`, skin count 74, clips count 9.
- Pure Node tests: arbitrary normalized quat decomposition (world yaw and yaw-neutral tilt) exact reproduction, sign, source t0, seam and negative invalid inputs.
- Baseline vs corrected real-skinned comparison: pelvis RMS improvement by >0.2° and at least 15%, no more than +0.003 model-unit increase in worst leg RMS, +0.006 increase in max joint error, +0.004 in chest/head world-RMS, IK residual <=0.008, cycle-seam step <= baseline+1.5°, side-lean step <= source+2°, no frame exceptions. Report all values even if no candidate passes. DO NOT bypass the gates to force appearance improvement.
- Existing foot, pelvis, upper, source-zero anchor, rollback, reference parity regression suites are unchanged and continue to run.
- Source publication only through owner Android Termux Git, all new versioned text files, isolated checkout, pinned source HEAD `95ca01f38e2f68cd10185fa54b7228e3f8053d6a`, AGENTS blob `547c2af52303f4efb718bbf8f82a698110c7bfca`, exact blob and model SHA, no force push, exact remote readback, fresh no-cache viewer and dynamic local port/PID/URL.

## Honest stages

Source packet prepared ≠ user script downloaded ≠ Termux installed/pushed ≠ actual skinned browser run ≠ numerically passes ≠ owner visually accepts. When no safe correction is identified, the new viewer deliberately keeps the previous pelvis and reports `PELVIS_TILT_NOT_YET_SAFE_OR_NOT_CAUSAL`. No alternative lanes.

Mandatory latest rules read: live `AGENTS.md`, Home Center Campaign Etiquette `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`, Top-down Etiquette `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU`.
