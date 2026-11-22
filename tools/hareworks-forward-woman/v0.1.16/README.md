# Hareworks v0.1.16: dynamic runway gait with actual world contacts

Owner request: preserve working v0.1.9 source-derived procedural gait and v0.1.15 visible character, while restoring runway crossover, foot-to-knee orientation and a physically coherent speed control. Do not regress orbit camera, skinned 74-joint model, other clips or source math.

**Confirmed startup exception in v0.1.15**: `cadenceFor()` rejected a measured full-cycle stride near 1.2245 because it allowed 0.3...1.0. v0.1.16 accepts the physically measured 1.2245 and can run the existing real-glb 32-step startup test instead of entering the unpinned fallback. That startup still needs phone browser evidence.

**Dynamic control**: `speed-gait.mjs` computes stride length, cadence and lateral placement from travel speed (not simply animation-time speed). Physical phase advances by cadence*dt. Root advances by the original phase-integrated support-root curve scaled to the current stride; the existing world contact anchor is held fixed through stance. At speed changes geometry parameters change smoothly over about 0.22s, rather than reseeding an anchor. Zero speed produces no root or phase motion. The accepted original source curve remains the 1.267u/s reference.

**Runway character**: the original fitted hip-relative ankle path, knee pole and pelvis continue to supply the motion. Front-leading foot shifts modestly toward centerline, more at fast speed; the procedural toe-vector plus ankle-yaw solver from v0.1.9 contributes 52% to foot orientation against the preserved real-source pose. The computed foot direction also reacts moderately to the measured knee-to-foot lateral offset. This is a style candidate, NOT owner approval.

**Honest gates**: unsupported animation source / GLB hash fails; real physical initialization must complete 32 skinned 120Hz solver steps before marking world IK ready. The old unpinned preview still has an unmistakable warning. Browser physical contact audit and owner visual verdict are independent. Passing JS tests alone does not prove heel/toe geometry, gait beauty, or phone performance.

Single authorized Android Termux entrypoint, verified one-time Hareworks model, persistent Documents/GodotProjects checkout, no new clone, no destructive Git commands, no model writes. Only new versioned v0.1.16 files are eligible for commit/push through Termux. Read AGENTS.md and Campaign Etiquette for authoritative execution constraints.
