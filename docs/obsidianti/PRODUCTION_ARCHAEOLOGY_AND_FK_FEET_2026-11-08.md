# Obsidianti animation production archaeology and FK-feet hand-authoring handoff

**Recorded:** 2026-11-08. **Owner:** Drew. **Execution authority:** Android Termux Git, `Valar05/parametric-parambulator`. **Status:** documentation and rig-authoring campaign proposed; owner has **not** visually accepted the new FK authoring rig. This document preserves conversational directives that had not been explicitly proven committed to the repository. It is not a claim that an absent asset was created.

## Decision: retire Sword1 from active work, preserve it as archaeology

Owner on November 8: "I think I'm going to put a pin in the two-handed stuff for now. I think she has sufficient moveset without it and I don't think I have a purpose for it. I just thought it looked cool." This is a **scope decision, not deletion authorization**. Do not continue the Sword1 contact/wrist/shield iterations by default. Do not roll experimental two-handed Sword1 into the new primary animation source. Retain its files and receipts for future research or reactivation if specifically commissioned.

Owner on November 8: the ARP workflow was a "huge unlock" whether or not the game gets made, making manual Blender animation attractive. The production priority shifts from automated retargeting polish to a stable human-editable Blender animation library. Some moves will be hand-animated; do not confuse an ARP retarget pass with owner acceptance of aesthetics, timing, or foot contact.

## Canonical primary animation source, and why

The 41-clip v2.0.32 animation reunion was published in:

`diagnostics/obsidianti/animation-reunion-v2.0.32/runs/20261107T203838Z-d49615bb/OBSIDIANTI_41_CLIP_SHIELD_LANCE_LIONHEART_ARP_REVIEW_UNAPPROVED.glb`

**SHA-256:** `9ff2b5423b4bf5fea1bf67295b52d848803381699fede56164aca9ce65bea9b7`, 18,806,184 bytes (Git LFS). Its composition proof reports 41 clips: Ares movement steps, Vanguard motions and sword actions, AxeKick, Lionheart ARP retargets; shield, lance, rig and materials were retained. The v2.0.32 proof says original 30 were preserved; approval remains pending. This is a deliberately conservative *pre-Sword1* source for a new authoring copy; it does **not** overwrite `assets/obsidianti/Obsidianti.glb`, any native `.blend`, or earlier campaign artifacts.

The 42-clip v2.0.33 and v2.0.36 43-clip and v2.0.39 44-clip Sword1 variants remain available in diagnostics for archaeology. Do not present 44 as the main accepted moveset. v2.0.39 was explicitly visually rejected for the left wrist and shield timing.

## FK vs IK, and this specific commission

Owner explicitly asked for "a version of obsidianti that has FK on the feet" and cautioned against sabotaging existing FK animations. **Literal implementation:** a separate editable Blender rig with direct local FK foot-bone rotations, a read-only retained reference rig and distinct cloned action data. Do not silently reinterpret the explicit FK request as an IK retrofit. If the owner later wants independently switchable IK foot planting, implement that as a separate permissioned operation with a constraint-influence per-action design and pose-match/bake tests; do not impose new always-on IK constraints on existing FK motions.

The repository already documents IK-authoring experiments (`IK_AUTHORING_v1.9.3.md`, `FK_AUTHORITY_IK_v1.10.3.md`) and sparse FK (`SPARSE_FK_AUTHORING_v1.10.4.md`). Those preserve different source snapshots and are not an interchangeable proof that this **41-clip** rig is editable. The new script uses native Blender GLB import; original GLB animation channels already encode FK bone transformations. It duplicates the armature and meshes for a distinct editable rig, duplicates imported Blender Actions/NLA associations and marks the left/right foot bones as direct FK controls. All source model bytes and original Actions remain unchanged. If Blender's importer semantics or actual foot-bone names fail validation, stop and report; never guess another anatomical bone or weaken preservation gates.

## Retargeting history and important owner decisions

- **Lionheart spear:** ARP improved the earlier pelvis pitch, inconsistent stance foot contact and weapon-offset problems. Overcorrecting feet from baked FK gave exaggerated foot heights, lifted rear legs in Heavy1, high legs in Heavy3, and small rear lifts in Light/Spring. Later toe-roll post ARP shifted height and was accepted as "good enough for now," not perfect physical foot locks. Root/pelvis motion should not be frozen to fake contact; feet should be planted with real world-space evidence when IK is commissioned.
- **Ares unarmed and Vanguard:** the Ares retarget was substantially useful, and Vanguard two-handed sword retarget had good feet with some arm issues. The 41-clip combination preserved Ares 8-direction lower steps and Vanguard actions together with Lionheart. Upper-body idle overlay on lower-body step actions was separately requested. Preserve original data and conventions.
- **AxeKick:** preserve as baked. Do not re-retarget it during an unrelated authoring task.
- **Sword1 v2.0.33–v2.0.39:** goal was lance contact with a left palm, right arm avoiding torso, shield shrinking to wrist charm while preserving existing attack timing. Adaptive rebake failed time-grid at v2.0.35; v2.0.36 produced 43 clips and a viewable model, but left wrist remained incorrect. v2.0.37 blocked assuming a pre-existing shield scale channel; v2.0.38 blocked assuming named shield geometry; v2.0.39 used the weapon-weighted skinned mesh but visual result moved the wrong degree of freedom. Owner identified left wrist rotated roughly 90° sideways instead of pointing downward, hand spacing removed; shield remained full size too long and shrank too late. Do not treat palm-position residual or shield monotonicity alone as anatomical/visual success. **Owner then shelved all two-handed work.** Do not start v2.0.40 absent renewed authorization.
- **Mudman:** a separate enemy, shorter/stumpier than Obsidianti, dry mud patches with wet areas. Ares motions re-targeted, persistent 90° HitHeadLeft root orientation and foot-ground/texture issues were unresolved. Mudman is a separate asset; do not slip its fixes into Obsidianti FK authoring.

## Character and authoring constraints worth retaining

Obsidianti is an adult armored athletic woman with substance; do not flatten her silhouette or replace her wedge-soled shoes with separate high heels. Earlier visual design sessions explicitly rejected boob-plate, holsters and chain adornments. Keep the helmet, do not protrude hair through it. Remove cape, tabard and other cloth from the base mesh; hair/cape/tabard were separately composed as **reference images** for possible later rigs, not as permission to add cloth to all animation exports. The exact lance and shield were treated as distinct reference assets. Preserve originals and provenance rather than regenerating these textures or silhouettes during animation work.

The user estimated ARP saved approximately **80 hours** of retargeting work. That is a subjective owner estimate, not a time-study measurement. The important production lesson is that repeated hand cleanup of two or three bad poses now competes favorably with building another fragile solver. Manual authoring should be available even when exact retarget parity isn't. Two additional sword-and-shield animation sources were mentioned as existing on a laptop but were not verified as committed; don't infer they are accessible from this repository. Owner decided to shelve the two-handed work regardless.

Ares steps should remain eight-directional with a single forward-facing run animation; startup run follows steps after a fixed interval, and an upper-body idle layer may overlay the lower-body step clips. This is a gameplay-controller intent, **not** proof the controls have been implemented or accepted in Godot. Avoid rewriting the Godot gameplay controller during FK authoring.

Separate historical owner preference: during the ARP two-bone leg retarget experiments, the user asked for IK feet to stay enabled and for natural pelvis movement. That applied to **those retarget experiments**. It does not override the current explicit **FK feet** native Blender copy request. Do not collapse separate dated authoring instructions into one global switch.

## Animation engineering lessons (facts and proposed guardrails)

1. A numeric IK proximity result does not demonstrate that the hand is anatomically rotated correctly. Test wrist local rotation, hand forward/down axis, forearm continuity, grip clearance and visual orientation separately.
2. Distinguish **when** a shield shrink begins and completes from **how smooth** it is. An interpolated curve stretched until the last frame is too slow even if monotonic. For the shelved fast Sword1 move, owner preferred a rapid shrink slightly slower than the previous flicker, not delayed to end of 0.86-second attack.
3. Real source joint/bone names, skin weights and action identities must be measured on the **actual binary**, not assumed from names. glTF-to-Blender Action identity may live in NLA strips rather than action.name, and Blender can store Zstandard-compressed `.blend` files.
4. Test complete multi-attempt adaptive paths and midframes, not just a single successful pose. Float32 sampler grids can introduce duplicate or invalid timestamp spacing. The v2.0.35 failure was procedural and not proof of insoluble IK.
5. Protect source Actions and canonical models; publish derivatives to new versioned paths, verify SHA and exact Git LFS readback, and keep owner visual approval separate from automated metrics.
6. A Blender authoring file's value is actual editable controls and all original Actions. An impressive Three.js GLB viewer is not interchangeable with a native `.blend` and cannot by itself meet this task.

## FK feet authoring acceptance gates

- Input is the exact 41-clip SHA above, hydrated through Git LFS in the authorized Termux lane. Reject a pointer masquerading as binary or any hash mismatch.
- Output is a **new versioned `.blend`** with independent reference and editable armatures, independently copied mesh objects and Action datablocks. Retain imported NLA strip associations and motion count; identify one left and one right foot bone from the real armature. No IK constraint inserted into the feet. Preserve root/hips/leg/source animation data without retiming.
- Reopen the resulting `.blend` in a distinct Blender process, verify both rigs, marked FK foot bones, original versus editable Action separation and output hash. Real animation appearance needs human Blender review, not assumed approval.
- Publish campaign sources and (if it passes) `.blend` through Termux Git and Git LFS only. Place SHA-verified `.blend`, report and receipts in Android Downloads; exact remote commit and LFS readback before reporting publication. One operator invocation, collision-safe staging, no force-push, no resets of the owner's checkout.

## Future manual Blender workflow

Open the versioned FK editable `.blend`. Select `OBSIDIANTI_FK_FEET_EDITABLE`, go to Pose Mode and use the original named LeftFoot/RightFoot bones. Their rotations are FK (the existing imported GLB movements were baked to rotations). To make an original move into a new, hand-authored one, **duplicate the editable Action first**, rename the copy, and key only that copy. Keep `OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT` untouched for side-by-side comparisons. Make contact correction and hand edits on dedicated Actions; don't blanket-enable IK on pre-existing FK clips. An IK/FK switch could be a separately approved later rigging feature, not a silent replacement of the FK commission.

## Scope and evidence status

This handoff records user intent and campaign archaeology. It does not certify that source verification, native Blender build, device execution, asset upload or visual approval has occurred. The associated launcher records these gates when run and stops on failures without touching originals. **No resurrection of shelved two-handed Sword1 work without owner request.**
