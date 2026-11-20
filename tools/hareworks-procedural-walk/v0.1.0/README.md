# Hareworks procedural walk v0.1.0: genuine IK prototype

The preserved 74-joint, nine-clip Hareworks GLB is the only mesh. This campaign publishes **text-only** runtime code. **No GLB, prior source, approved 2D Boneforge work, or Repl file is changed.**

## What runs

The viewer seeds ONE static pose from `Idle_Turn_Left` at t=0 for a grounded starting position, then stops/uncaches animation actions. All subsequent locomotion comes from explicit root velocity and yaw, world-space ankle targets, generated swing curves, and iterative bounded CCD on the **actual five-node hierarchy** (UpLeg > Leg > intermediate > Foot > ToeBase). The ankle world orientation is compensated during stance. Gait core code has deterministic Node tests; the viewer runs a short automatic real-rig smoke and can export a multi-direction real-rig check.

Controls: keyboard WASD/arrows, Q/E aiming, or phone movement and aim touch pads. The movement heading and aim heading are independent. At rest, aim twists the upper body up to a *provisional* budget; beyond it, body yaw starts moving, and a foot is repositioned as necessary.

## Boundaries and limitations

- This is a kinematic preview, **not a solved balance simulation**, validated ankle/sole force model, accepted anatomical ROM, or polished idle-turn animation.
- The foot target is the **ankle**, not a fully reconstructed contact patch. Per-foot seed sole heights come from the owner-uploaded heuristic v1.0.8 browser export; these are provisional.
- A bounded CCD solver may leave residual if a destination is unreachable. The viewer exposes that residual; it must not be hidden by weakening assertions or claiming a valid planted sole.
- Source clips, including `Walk_Backward` and `slide_right`, can have root motion; their pelvis/world translations are not direct proof of actual root motion or stance slip. They are only *reference priors*, not runtime animation.
- The yaw-path anomalies in the turn extractor are **not** used to set accepted twist thresholds. The initial budget is an experimental knob.
- This baseline is a **biped**, not a horse or six-legged crab. Reuse their phase planning/contact disciplines, not equine duty factors or hexapod footstep timing.
- Rendering depends on Three.js 0.170.0 from its CDN. Network is needed for a first browser load. HTTP success is not WebGL success.

## Verification and review

The Termux campaign verifies a pinned Git parent, actual source bytes and GLB JSON rig/clip properties, clean collision gates, scope-limited staging, Node syntax and numeric core tests, exact push/readback, and exact GLB digest over HTTP. The browser also loads/solves the real rig and can export real-rig directional-check JSON. **Human acceptance remains pending.** Review forward/back, strafe, diagonals, release, idle twist and foot repositioning at phone scale; inspect knee bends, toe/heel floor contact, ankle residuals, foot orientation, reach and silhouette. An attractive initial stance is not proof of a correct walk cycle.

On rerun, use `status` or `resume` with the same script. A complete published receipt can re-launch the viewer without a new commit. Interrupted/dirty checkout state is preserved, never silently overwritten.
