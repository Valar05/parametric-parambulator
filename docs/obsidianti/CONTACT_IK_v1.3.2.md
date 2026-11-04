# v1.3.2: source-grounded IK with reachable stance anchors and owner priorities

Source is pinned `Valar05/parametric-parambulator` on `e2ebd90038b201c9ac7923b851557a1eb13dc224`, existing model LFS `f9fc5cef...e4629e6`, historical pre-pitch model `5fa87737...70d04c0`, user native source SHA `7b17dd51...e91a3556c4f2`. This revision does not originate an alternative GLB.

## Owner scope and verdict

* **Light1 and Light2**: primary fixes for source-confirmed foot hover around 10 cm. Restore exact pre-pitch Hips rotation. Preserve source foot-contact intent; compute stance anchors that remain reachable for the real target two-bone leg chains throughout each contact interval. Existing bounds stay strict.
* **Heavy1**: minor 14–17 mm reach shortfall is accepted up to a scoped 22 mm cap, subject to support-RMS <=6 mm, penetration <=18 mm, hover <=15 mm, bad support frames=0, <=5 IK failures. This is a **known imperfection**, not an IK pass.
* **Kick**: low-priority disposable. Byte-identically preserve current motion. Do not demand the airborne kick generate grounded support.
* **Heavy2**: byte-identically preserve owner's preferred v1.2 clip.
* **Heavy3, Light3, Cast, SpringAttack, Stomp**: retain physical gates and verified v1.3.1 source-contact semantics.
* Original Idle/Ares/Meshy clips, rig, weights, scene, materials, and Repl unchanged; unwanted weapon translation channels remain removed on all moving Lionheart clips.

## Anchor fitting

Legacy seeded target world XZ directly from the target shoe at the **start** of an episode, even when that sole was misplaced or anatomically unreachable. This is the known problem. v1.3.2 computes a weighted intersection of per-frame ankle-reach discs, using the actual skinned sole-to-ankle offset and source donor ToeBase horizontal motion. It shifts only the contact target, not skin/leg length, and caps any correction at 22 cm. Prefer source preserved relative travel and original global root; bounded root projection remains an optional fallback. Requires actual skinned preflight on all action frames and half-frames.

## Deployment and evidence

Single SHA-locked Android Termux launcher. Fresh root AGENTS read in checkout, collision gate, exact full LFS blob hashes, verified native Blender world-foot samples reused only with matching SHA, source-first Git commit and nonforced push. Only if all **non-exempt** real skinned preflights pass: mutate same canonical `assets/obsidianti/Obsidianti.glb`, LFS push, Git push, remote HEAD & pointer readback; reviewer viewer URL returned. Preserve prior source commits; never force-push. Failure outputs original full report plus **short picker-friendly `IK_DATA_<runid>.json` and `IK_RCPT_<runid>.json`**. A green test or HTTP 200 viewer is not human approval.

Independent non-device tests are off-device evidence only, not a substitute for the real Termux model SHA and human motion review. If Light1/2 remain above physical limits, stop with exact diagnostic evidence rather than publish them broken.
