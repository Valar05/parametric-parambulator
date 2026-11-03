# Repl v0.6.20: adaptive grounded-support repair

**Single Termux Git campaign.** Inputs: latest canonical Repl v0.6.17 on `Valar05/parametric-parambulator` commit `af576184ab956cc3b07de2e49f9db9eebeb4049b`, GLB SHA `c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1`.

Unlike v0.6.19, the new `model.py` uses a bounded beam-search trajectory optimizer. It searches actual measured joint/sole geometry, varies the stance anchor, knee and smoothing priorities, retains stable motion hypotheses, retries after feedback, and only then executes the complete published physical verifier on promising motion cycles. No protected bones are edited; no new rig or model variants are committed. Search is checkpointed as JSON.

The corresponding additive AGENTS rules demand predictive failure recovery in *all* future repo campaigns. The script publishes its source and additive policy via the authorized Termux Git lane with source and remote readback. It publishes the canonical GLB only if independent whole-clip skinning verification passes and the measured extension/reach improves significantly. Visual acceptance remains yours.

This packet is authored outside the repository pending the approved Termux Git publication. Tests outside Termux do not constitute model deployment.

## Evidence / status

- Source model and human-reviewed baseline: v0.6.17, not finally approved.
- Git owner/authorized mutation: Termux ONLY. Never direct ChatGPT GitHub write.
- Solver: constrained to four existing front rotation tracks.
- Runtime search: inspect exact v0.6.17 canonical GLB, adaptively re-plan, independent verifier, scope compare.
- Numeric verification and remote readback: device dependent, evidence generated at execution.
- Human visual acceptance: always pending after numeric passes.
