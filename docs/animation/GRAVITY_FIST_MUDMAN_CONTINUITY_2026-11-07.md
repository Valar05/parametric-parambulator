# Gravity Fist → Mudman: design and animation continuity (2026-11-07)

**Repository:** `Valar05/parametric-parambulator`. This is a continuity ledger, not a claim that the first enemy has been implemented in a game or that every reviewed action is accepted. The original game donor is `Valar05/gravity-fist`; it is not modified by these campaigns.

## Design identity and implementation boundary

First enemy for Obsidianti: **small, stumpy dried-mud humanoid boxer**, shorter than Obsidianti, broad thick torso, short legs/arms, oversized fists. Cracked dry clay with a few wet patches, not a giant stone golem or a fluid-slime simulation. Low-tier and initially brittle, suitable in groups. Preserve simple humanoid/Mixamo-compatible bones rather than inventing extra limbs or elaborate secondary rigs. Combat intent borrows Gravity Fist's *enemy* jab and cross timing, including their recovery/attack-window behavior where game data supports it. Attack animations are reusable sources; **AI and hitbox integration in the new game are not proven deployed**. Future wet mud and stone variants are merely proposals.

## Verifiable inputs

- Owner Ares `(2).blend` SHA-256 `63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a`.
- Original Meshy Mudstone Golem Mixamo Running ZIP SHA-256 `fbcb592ac941dbc34ecade66b044b551f5bd55bf5855be50d8af5caba0514f79`; embedded original atlas SHA-256 `f1a6089742844a6a3b0a4b7c93ce6ca80faf126adf92ec135bb7aa26a478e886`.
- Source Godot name/role evidence: `Valar05/gravity-fist/scenes/SecurityTitan.tscn` (Git blob `4f07c8c2af40038c1f672750b8a155f53f123b6d`) and `security_titan.json` (Git blob `f2a1036f75cc7c4b7821e700ffa61a6bed7980fc`). Do not reassign generic Mixamo-named motions by guesswork.

## Current review-derived animation inventory

v2.0.22 transferred **77 populated Ares action slots**. v2.0.23 retained **23 selected game-role clips**; the other 54 are archived in the original full-library review. The mapping below is from the published curated `CURATION.json`:

| Final clip | Exact source label in v2.0.22 |
| --- | --- |
| Cross-Enemy | Mudman_Cross-Enemy |
| Run | Mudman_Run |
| BackImpact | Mudman_BackImpact__OBHitHeadLeft |
| Death | Mudman_Death |
| HitHeadLeft | Mudman_HitHeadLeft |
| HitHeadRightBig | Mudman_HitHeadRightBig |
| Idle-Cross | Mudman_Idle__OBCross |
| Jab-Enemy | Mudman_Jab-Enemy__OBCross |
| KnockedBack | Mudman_KnockedBack |
| ProneBack | Mudman_ProneBack |
| ProneBackDamage | Mudman_ProneBackDamage |
| ProneBackStandUp | Mudman_ProneBackStandUp |
| ProneFrontDamage | Mudman_ProneFrontDamage__OBHitHeadLeft |
| ProneFront | Mudman_ProneFront__OBHitHeadLeft |
| StandUp | Mudman_StandUp__OBHitHeadLeft |
| StepBack | Mudman_StepBack |
| StepBackLeft | Mudman_StepBackLeft |
| StepBackRight | Mudman_StepBackRight |
| StepForward | Mudman_StepForward |
| StepForwardLeft | Mudman_StepForwardLeft |
| StepForwardRight | Mudman_StepForwardRight |
| StepLeft | Mudman_StepLeft |
| StepRight | Mudman_StepRight |

`Idle-Cross` is an **explicit alias** for the moving Ares `Idle__OBCross` slot, not an exact source-name match. `HitHeadRightBig` is kept distinct because an exact `HitHeadRight` source was not found in this particular transfer. `ProneBack` and `ProneFront` are intentional static holds, not accidental zero-motion duplicates. The originally attempted alternative Security Titan hit reactions are not needed if Ares provides usable reactions.

## Artifact hashes and status

- **v2.0.22** 77-clip raw transfer review SHA-256: `396e9cf024846ba9e8c5159a9b8660b21a296a73a6e656d4c347dc86780079d6`.
- **v2.0.23** textured, grounded, curated 23-clip review SHA-256: `19304bf8007670e36a38b354b5f8d2ea0c39982c97e2a247acdac1190fe2b7ef`.
- **v2.0.24** exact animation selector fixed the `StandUp` vs `ProneBackStandUp` suffix-match bug; no animation curve repair.
- **v2.0.25** did not find an unambiguous 90° root channel and stopped. This is a diagnosis limit, not proof the user-reported defect does not exist.
- **v2.0.26** modified `mixamorig:Hips` by a measured 62.38362°; *owner visually rejected* as still wrong. Candidate SHA-256 `3753b68c100e6af406a0a9211579227ce6702d70c13ff2f708d66fbfa6724b16`. **Never use as correction baseline.**
- **v2.0.27** generates separate *exact quarter-turn* candidates from original v2.0.23, including -90° about X and -90° about the previously measured axis. Owner selection and visual acceptance are **NOT established** by successful publication or display. Until accepted, the original v2.0.23 GLB remains the comparison baseline.

## Still to resolve

1. User's visual verdict on which, if either, v2.0.27 exact 90° candidate fixes `HitHeadLeft`. If neither, inspect source Ares Blend/track keys and parent/root transform without assuming direction; preserve the user's exact requested 90°/bad-key repair.
2. Once proven, make a **separately authorized** source-level Gravity Fist/Ares correction so future transfers do not inherit the bug. This repo's experiments do not demonstrate that the original donor was changed.
3. Import and play these character clips in the target new game's Godot runtime; wire Jab-Enemy/Cross-Enemy and reactions to actual enemy AI, timing, collisions, and death. Existing viewer playback is not a deployed enemy game.
4. Keep ongoing Obsidianti retarget review separate. Accepted AxeKick stays locked; Vanguard better-footed results remain useful baselines rather than automatically accepted completed animations.

**Important scope:** Character concept, relative scale, and animation selection are user decisions; changing the rig, substituting donor sources, expanding movement mechanics, or mutating Gravity Fist/other canonical models requires explicit user authorization. Carry current owner visual verdicts forward, not an inferred PASS from numerical metrics.
