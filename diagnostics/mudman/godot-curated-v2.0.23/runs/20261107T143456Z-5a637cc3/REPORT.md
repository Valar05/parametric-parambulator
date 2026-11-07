# Mudman v2.0.23 | Godot curated / original texture / grounded origin

**Owner visual acceptance: PENDING.** This is a review derivative, not a canonical asset update.

Input v2.0.22 77-clip GLB SHA256 `396e9cf024846ba9e8c5159a9b8660b21a296a73a6e656d4c347dc86780079d6`. Output 23-clip GLB SHA256 `19304bf8007670e36a38b354b5f8d2ea0c39982c97e2a247acdac1190fe2b7ef`.

Actual 2048x2048 Meshy RGB texture embedded as baseColorTexture for every UV-mapped mesh primitive (texture SHA256 `f1a6089742844a6a3b0a4b7c93ce6ca80faf126adf92ec135bb7aa26a478e886`).

Ground calculated from 4474 skinned geometry witnesses: original min Y 0.731799 m, constant root correction Y -0.731799 m, after correction min Y -0.0 m. The floor is y=0 in viewer.

Original animation samplers, mesh vertex buffer, skins, and per-bone motion are byte-for-byte retained for kept clips. 54 irrelevant/static/duplicate-looking candidates excluded, though prone holds retained. No vendor ARP rerun.

Godot references: `Valar05/gravity-fist/scenes/SecurityTitan.tscn` and `security_titan.json`, pinned blob SHAs in CURATION.json. Idle-Cross is an explicit alias for the moving Idle OBCross slot, not an exact action from the Ares source. Godot HitHeadRight has no exact matching motion from this Ares export, so HitHeadRightBig is retained without falsely renaming it.

## Kept clips

- `Cross-Enemy` ← `Mudman_Cross-Enemy`
- `Run` ← `Mudman_Run`
- `BackImpact` ← `Mudman_BackImpact__OBHitHeadLeft`
- `Death` ← `Mudman_Death`
- `HitHeadLeft` ← `Mudman_HitHeadLeft`
- `HitHeadRightBig` ← `Mudman_HitHeadRightBig`
- `Idle-Cross` ← `Mudman_Idle__OBCross`
- `Jab-Enemy` ← `Mudman_Jab-Enemy__OBCross`
- `KnockedBack` ← `Mudman_KnockedBack`
- `ProneBack` ← `Mudman_ProneBack`
- `ProneBackDamage` ← `Mudman_ProneBackDamage`
- `ProneBackStandUp` ← `Mudman_ProneBackStandUp`
- `ProneFrontDamage` ← `Mudman_ProneFrontDamage__OBHitHeadLeft`
- `ProneFront` ← `Mudman_ProneFront__OBHitHeadLeft`
- `StandUp` ← `Mudman_StandUp__OBHitHeadLeft`
- `StepBack` ← `Mudman_StepBack`
- `StepBackLeft` ← `Mudman_StepBackLeft`
- `StepBackRight` ← `Mudman_StepBackRight`
- `StepForward` ← `Mudman_StepForward`
- `StepForwardLeft` ← `Mudman_StepForwardLeft`
- `StepForwardRight` ← `Mudman_StepForwardRight`
- `StepLeft` ← `Mudman_StepLeft`
- `StepRight` ← `Mudman_StepRight`

Viewer: http://127.0.0.1:9206/index.html?run=20261107T143456Z-5a637cc3&build=3d27648e23b701e5670b1566
