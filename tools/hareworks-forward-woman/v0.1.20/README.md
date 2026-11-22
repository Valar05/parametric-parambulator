# Hareworks v0.1.20: stationary forward knee poles, no history-dependent knee corrections

Owner's 120-fps v0.1.19 review is REJECTED: the knees remain unstable and the leg silhouette is noticeably worse. The previous 10-rad/s knee-pole filter and hard side-of-pelvis projection were inventions, not a faithful restoration of the accepted v0.1.9 motion. Remove both.

## Correction

- Use STATIONARY anterior (+Z) poles in character-local space, calibrated against the original 60-frame knee witnesses. No side-to-side pole animation. The solver is a pure function of phase and current hip/ankle, not previous frame, browser FPS or prior knee. The source knee shape is an independently enforced deviation envelope.
- Choose a world-contact ankle target by bounded binary search: accept the most planted-foot correction that keeps the solved knee within 0.025 units of the original source-knee shape and at least 0.012 units on its anatomical side. Do not iterate skin-patch residuals through the knee solver. When the source-style and ideal ground contact cannot both be met, keep the knee and mark the physical contact as a warning; NEVER call that a grounded success.
- Preserve the exact approved left/right `foot-heading.mjs` from v0.1.18, v0.1.19 source speed, OrbitControls and the canonical nine-clip GLB. No new animated source mixer on the visible actor.
- Instrument source-knee error, contact conflict, frame-to-frame knee movement and sole penetration. The actual phone browser 120Hz audit and owner review remain distinct gates. The 120-fps owner video is rejection evidence, not a source of inferred root metrics.

Only `tools/hareworks-forward-woman/v0.1.20/` is new. Do not edit assets, older iterations or another project. The authorized mutation lane is the checked existing Android Documents repository using Termux Git, with exact remote readback and no force push.
