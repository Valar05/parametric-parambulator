# Obsidianti Mwni interactive 3D viewer v1.4.4

**HTTP server tested and real GLB bytes SHA-checked on-device. Browser visual approval is pending.**

- Browser URL on the SAME PHONE: `http://127.0.0.1:9180/index.html?run=20261106T184314Z-aadc298a&build=5c4e7f3e7df6d6b1d5a77799`
- Source commit: `2fd8e7ff03cfb6075d9d62f84f97551616c9ee04`
- Browser: orbit/pinch, play/pause, replay, seek, speed, camera presets, Heavy1/Light2 switching.
- On browser load, a fresh SHA-256 digest verifies the entire selected GLB before displaying animation.
- Optional canonical comparison: ORIGINAL_COMPARE_AVAILABLE_CACHED_SHA_VERIFIED
- This is the exact Mwni result from v1.4.0/recovered v1.4.3, not a new retarget run.
- No model files have been changed or promoted; do not equate HTTP check with browser rendering.

| Model | SHA-256 | Animations |
|---|---|---|
| candidateHeavy1 | `793ab2378e59d065308b80949d5352f5e2472d94ce93d4e63fc27aa5ed63fec1` | Animation |
| candidateLight2 | `10bdf5dcbf0a7a9f3e746620cc88bc4bdb4e94bd4a512395a03d33aa2a1bfa82` | Animation |
| canonical | `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4` | Running, Walking, LionheartIdle_UNREVIEWED, ObsidiantiIdle, Lionheart_Cast, Lionheart_Heavy1, Lionheart_Heavy2, Lionheart_Heavy3, Lionheart_Kick, Lionheart_Light1, Lionheart_Light2, Lionheart_Light3, Lionheart_SpringAttack, Lionheart_Stomp, Ares_StepForward_Lower, Ares_StepBack_Lower, Ares_StepLeft_Lower, Ares_StepRight_Lower, Ares_StepForwardLeft_Lower, Ares_StepForwardRight_Lower, Ares_StepBackLeft_Lower, Ares_StepBackRight_Lower, Ares_AxeKick_Full |
