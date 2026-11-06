# OBSIDIANTI_RETARGET_CAUSAL_AUDIT_v1.3.0

Read-only, single-invocation Termux Git forensic campaign. Source-first publication through Termux, then a full on-device evaluation and exact remote Git readback of measurements. No direct ChatGPT GitHub writes, no canonical `assets/obsidianti/Obsidianti.glb` mutation, no `.blend` mutation, no animation approval or model-fix claim.

## Question

Does one shared pelvis translation scale explain the Lionheart discrepancy, or does the loss of independent original IK foot controls/rest-space FK retargeting alter the relative positions of the feet?

## Experimental design

- Evaluate the **current** canonical GLB SHA-locked read-only as well as the historical unapproved candidate; compare both without conflating them.
- Verify the actual original Lionheart `.blend` with SHA-256, original v1.1.0 sampler, historical pre-contact FK GLB from verified Git-LFS archive, historical quaternion mapper, and exact 1.2.1 GLB evaluator. Re-evaluate source at half frames, not just keys.
- Prove the translation-invariance identity: a common pelvis translation cannot change the vector between feet. For stationary original feet, any changing target separation is an irreducible target limb-relative error.
- Numerically attribute foot vertical displacement residuals to shared hip Y motion versus hip-relative leg Y movement, independently for each side and all attack clips.
- Record incremental FK stage effects from pelvis translation, pelvis rotation, upper leg, shin and foot rotations. This is an ordered ablation, not an unambiguous physical force decomposition.
- Reconstruct the original importer's per-bone quaternion mapping and compare it to actual historical target channels. Distinguish exact-key parity from midpoint interpolation differences.
- Compare actual evaluated skinned wedge-sole witnesses on source-bilateral contact candidates, without declaring toe-bone positions equivalent to contact sole. Existing untouched Ares and accepted idle remain controls.
- Report per-frame raw metrics, per-clip summary, original source SHA, original target SHA and provenance in committed Git. All files versioned; report under `diagnostics/obsidianti/retarget-causal-audit-v1.3.0`.

## Authority and failure behavior

Termux Git ONLY. One executable versioned `.sh` entrypoint with a validated embedded source packet and checksum. Uses isolated clone, preflight source and rules; commits its own immutable source first; executes real Blender/GLB sampling after source commit; publishes reports under versioned paths second; push and exact remote readback. An unhandled error leaves a persistent receipt marked BLOCKED, not a false pass. Never overwrite a dirty user checkout or canonical model. Git LFS fetch is permitted for the SHA-locked historical model. Failed source/runtime preflight must not mutate the GLB.

## Success definitions

- SOURCE_COMMITTED_REMOTE_VERIFIED: the campaign mechanism is committed and Git remote readback matches.
- RESEARCH_COMMITTED_REMOTE_VERIFIED: the analysis ran on actual source and target binary, generated and committed evidence, with exact Git remote readback. Still **not** a completed animation repair.
- Model repair: **not in scope**, requiring separate original owner authorization and visual acceptance.

Failure controls: verify input and output hashes, rules blob, unique Git paths, repo identity, stable LFS member, re-sampled Blend pose, source-executable syntax/test, independent report readback. Any missing prerequisite fails closed with durable status and original assets unchanged. Script can resume source-committed version without republishing or overwriting. No broad package installation.
