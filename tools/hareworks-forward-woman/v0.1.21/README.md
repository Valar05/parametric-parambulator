# Hareworks v0.1.21: real terrain-contact stress test

The owner accepts v0.1.20 as a sufficient **temporary gait baseline** for testing uneven ground, not the finished catwalk. This version is a terrain harness, not a leg-style revision.

Five selectable surfaces: flat (baseline parity), uphill, downhill, cross-slope and smooth deterministic rough ground. Rough is the initial review preset at 65% intensity, with a 0–125% adjustable strength and a one-tap return to flat. Switching terrain reloads and resets the run, preventing instantaneous mutation under an already planted foot.

The terrain module defines **one physical world-space height function** for visible mesh, heel/sole/toe planted anchor Y, swing targets, pelvis ground-following and penetration metrics. No painted-only bumps and no clip playback. The physical solver still samples the original Walking_Woman nine-clip GLB, 74 bones and original source-derived knee/ankle curves; its stance anchor x/z is held in world space at the actual selected terrain elevation. Hip/root Y follows terrain continuously with bounded rate. The original distal foot heading is preserved, with terrain-normal pitch and roll applied *after* the knee solve, no yaw steering of knees.

The real 120Hz browser audit reports terrain-relative heel/sole/toe intrusion, world-anchor drift, reach conflict, knee source deviation, root speed and contact transitions. It is **not** allowed to report real terrain contact PASS if source knee preservation prevents a plant. The initial 32-step skinned-model startup smoke is distinct from full gait audit and owner visual assessment. A procedural preview remains visibly labeled unpinned on any blocking failure.

Safety: new v0.1.21 files only, immutable model SHA-256, v0.1.20 original knee-governor and v0.1.18 accepted foot heading **byte-identical**, camera OrbitControls retained, previous version directories untouched, one checked Android Documents Git worktree, Termux Git commit/push/readback, explicit cache-busted viewer URL and persistent receipt. No direct GitHub mutations.
