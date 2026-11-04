# Obsidianti v1.3.1: source velocity + scale-aware retargeted pelvis and target IK

Mission: Correct the user-reported Lionheart contact failures without changing Ares, original Idle, mesh, skin or weapon rotations. No new GLB path. Termux Git only.

The real v1.3.0 report (sha256 f2a399e7ec590f03251023047dcbd6b2f258cc63e27b7d6f266b6968c5f19734) showed Heavy3 23 unreachable, Light1 8.3cm penetration, Light2 19.5cm right-sole hover with 22 unreachable right leg supports, Light3 demands 0.5 to 1.06 metres shift. This was NOT a request to enlarge the IK reach.

Corrections:
- Native-source ToeBase classification combines BOTH upper/lower floor heights, world-plane speed, and 3-frame support persistence. Feet cannot be constrained to ground merely because a toe is deeply below the source floor.
- Fit the source-to-target hip translation scale relative to the preserved first pose. Try unchanged motion first; adapt root vertical scale, then horizontal only when measured actual skinned support fails. Restore exact v1.1 pelvis rotations on affected Lionheart clips; preserve current user-praised Heavy2 clip byte-for-byte.
- Use two-bone IK on the actual skinned sole witnesses; preserve yaw, hands, weapons, and authored airborne/kicking foot phases. Keep original v1.2 weapon TRANSLATION channels absent.
- Measure all 10 Lionheart actions and their half-frame support, maintain actual source-derived stance schedules, require <=12mm supported RMS, <=26mm worst support penetration, <=30mm worst supported hover, <=2 unreachable frames and zero bad support samples. These are conservative numeric preflight limits, NOT owner visual approval.
- If no adaptive profile passes, record exact per-clip metrics and STOP without updating the model. No force push; no edits to user dirty worktree.

Evidence: report from the actual user-run v1.3.0; off-device fixture tests are not a substitute for on-phone current-GLB preflight. Fresh authorized Termux source/Git/readback and owner visual acceptance remain mandatory.

## Owner review and recovery locks

- The owner specifically said the existing v1.2 **Heavy2** movement looked good. Preserve that entire animation unchanged, including its pelvis rotation, rather than silently regress a visually good result. The historical v1.1 pelvis is restored for the other nine Lionheart actions only.
- Original Ares directional and AxeKick clips and ObsidiantiIdle, LionheartIdle_UNREVIEWED, Running and Walking remain identical. Existing independent shield and lance rotation channels remain; unwanted weapon position channels stay absent.
- Reuse the native Blender donor sample from the real v1.3.0 run only if its complete SHA-256 equals the verified owner receipt SHA `7b17dd51aadc208d9b357b8cafcf4c191ae103223842e007a786e91a3556c4f2`; otherwise evaluate original .blend again.
- Retains the same single `assets/obsidianti/Obsidianti.glb` path, with Termux Git-only source commit, independent real model preflight, Git LFS model commit, nonforced remote push and exact remote-head/pointer readback. No mutation to a user's dirty project directory.
- If this exact source package is already committed but its physical preflight blocked, the same operator command may resume ONLY if the branch HEAD's direct parent is the expected original commit and every source file has exactly the original packet hash.
- Candidate root normalization is **not** motion approval. The owner must inspect the final clips and confirm foot contact, body travel, wedge silhouette, weapon positions and continuity.

## Evidence boundaries

**Real v1.3.0 diagnostic evidence:** 76,440-byte JSON, SHA `f2a399e7ec590f03251023047dcbd6b2f258cc63e27b7d6f266b6968c5f19734`, reports Heavy3, Light1, Light2 and Light3 unresolved by v1.3.0. This source-derived report grounds the new correction mechanism.

**Off-device regression:** Original target skinned shoe geometry with analytic two-bone IK; 23-animation fixture with source airborne foot; injected +0.23m Light2 root transfer reproduces 25.3cm foot hover and 26 unreachable support samples, and normalization to zero-root-translation reduces hover to less than 1mm and unreachable samples to zero in that fixture; donor toe sliding and source below-floor false contact rejected. No real 16.9MB v1.2 canonical binary or actual native JSON source sample is available off-device, so these tests are NOT acceptance of real Lionheart actions.
