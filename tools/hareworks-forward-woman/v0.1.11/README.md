# Hareworks Walking_Woman world-space locomotion and true foot IK v0.1.11

## Owner's authorized deliverable

One visible character. It must translate forward through an actual 3D world, while the camera follows at a pinned offset (no camera bob), and the actual skinned soles remain fixed at persistent world coordinates through stance. During swing, each sole gets a new landing target. Leg bones are freshly solved from world-space foot targets, not copied from an animation. Source animation is allowed for STARTUP calibration of pelvis/upper body and low-foot contact phases only. Arms are deferred to independent IK.

**This specifically replaces the earlier in-place v0.1.9 proof as the active evaluation implementation.** The original approved v0.1.9 source files are not modified; the user may still use them for visual reference. No second actor is rendered. The accepted v0.2.2 backward, v0.2.7 left step, and pelvis-only v0.2.6 experiment are unmodified and NOT claimed as real locomotion IK.

## Actual driver

- Original canonical `assets/hareworks/Hareworks-nine-clips.glb`, SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, size 6,784,896, 74 bones, nine clips. Exact model checked before publication and in browser.
- Temporary hidden source clone uses the original `Walking_Woman` AnimationMixer during INITIAL calibration only: 120 samples for source-anchored periodic pelvis and spine/subtree pose curves; 240 samples to establish skinned sole low-height phases. The source clone/mixer are disposed. **Visible runtime character never plays a source animation clip.**
- The visible root moves in **world Z** by integrating `speed*dt`. Speed and cadence are linked; terrain markers and the ground grid stay fixed in world space.
- Skinned-sole patches are chosen from actual canonical mesh vertices near each foot, via `SkinnedMesh.getVertexPosition` and mesh transforms. Each stance contact stores a WORLD anchor that remains unchanged despite root movement. On liftoff, a spline travels from old anchor to a predicted world landing plus toe clearance. The next stance latches that landing.
- At 120 Hz each thigh and calf are restored to calibration rest, then independently rotated from analytic world ankle target and anatomical knee pole using a TWO-BONE IK solve. Foot WORLD orientation is resolved; measured skinned-sole residuals are iteratively corrected (up to 4 passes). Upper body follows periodic fitted curves, not source tracks. A limited pelvis reach adjustment is disclosed if a target would otherwise be outside the skeletal reach.
- Camera presets are a FIXED FOLLOW camera tied to `actor.position`, never pelvis height or yaw. The single actor stays near center while the world scrolls under it.
- Real browser three-cycle audit advances 120 Hz in one virtual timeline; measures each skinned foot patch's displacement from its fixed anchor during stance, anchor world-motion, world Z travel, penetrating sole sample, reach adjustments and follow-camera relative error. Browser writes a durable JSON evidence artifact to the phone Termux campaign state; a ZIP, build receipt or unit test is not visual or physical proof.

## Hard caveats / explicit scope

This is a gait-tuning follow-up to the first integrated world-IK implementation, to test on the real phone GLB. The stance windows come from low-sole phases (heuristic contact inference), not force sensors. Skinned vertices are sampled around the shoe, not proven full sole support polygons. The future landing position is predicted from the accepted pelvis/foot Fourier curves and world velocity. It may need parameter tuning based on the real 120 Hz measurements and the owner's visual inspection. A pre-rendered screenshot, local fixture or source checksum cannot establish successful mobile pinning.

**Success gate:** Real browser audit with both feet skinned-sole drift <=0.025 model units in stance, no anchor motion inside stance beyond numerical noise, actual world movement >0.9 model units across 3 cycles, camera follow error near zero, no reach rejections, and owner visual approval. Measurement failures are visible, not hidden. Camera never moves due to pelvis bob. The allowed travel input is 0–0.8 model units/second.

## Publication

Only Android Termux Git may install/commit/push through the user's phone, from an isolated verified checkout with fresh remote HEAD verification, a protected source list and a unique destination collision gate. Nothing touches the GLB or accepted earlier gait implementations. The packet includes test-driven pure contact and analytic IK geometry, syntax checks, browser source-hash checks, exact HTTP readback and a persistent Termux receipt. The full viewer URL (dynamic localhost port) is printed only after the phone executes the campaign.

Mandatory fresh authority: AGENTS.md Git blob `547c2af52303f4efb718bbf8f82a698110c7bfca`; Campaign Etiquette Home Center `1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI`; Top-down Etiquette Home Center `1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU`.

## v0.1.11 gait quality correction
The owner's 5424.mp4 showed a marching, knee-high presentation, despite the character's real-world movement and pinned-foot controller. A code audit found two coupled errors: previous phase cadence was `speed / (0.52 * sourceClipDuration)` (fixed only ~0.503 model units of travel per cycle), but swing clearance was fixed at 0.12 model units. That ratio made foot lift conspicuous. Worse, the landing predictor used `speed * clipDuration * remainingPhase`, which differs from actual future root travel when speed changes.

This version keeps **one actor**, **world-space persistent sole anchors**, **true 120 Hz two-bone IK**, **skinned sole verification**, **fixed-offset camera**, and every accepted reference file. At the same fixed speed of 0.52 u/s, the default travel per cycle is now 0.66 u, chosen provisionally from measured 0.66–0.70 u foot-fore-aft ranges in v0.2.3 research; additive swing clearance is 0.055 u instead of 0.12. The source motion is still the posture reference, not a live leg joint controller. These are initial tuning values, not certified gait parameters.

Cadence is `speed / strideCycle` and future landing world travel is `strideCycle * phaseToLanding`, making speed and root travel coherent. Controls independently vary stride (0.48–0.76 u) and swing clearance (0.025–0.12 u). The real-browser three-cycle audit now derives its duration from actual cadence, includes selected parameters and counts and preserves original drift, reach, penetration and camera limits. This is a change to the trial gait, not the accepted v0.1.9. Owner visual review and real 74-joint skinned audit remain pending.
