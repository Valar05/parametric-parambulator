# Hareworks v0.2.3: `Walking` versus `Walking_Woman` research

Research mission: determine, with actual source-GLB measurements, which **time-varying motion traits** distinguish two authored forward gait clips. This is not a backward gait, a style-transfer implementation or a claim about sexes generally. Preserve the owner-approved generated forward gait (`tools/hareworks-forward-woman/v0.1.9`) and owner-accepted generated backward in-place gait (`v0.2.2`) byte-for-byte.

## Primary source and evidence

The exact Git LFS model is `assets/hareworks/Hareworks-nine-clips.glb`, SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, 6,784,896 bytes, nine source animation clips, same 74-bone skeleton. The browser verifies the **whole downloaded GLB's SHA**, instantiates two independent original source-clip mixers, samples **360 reference poses per clip**, and does not generate or play any candidate motion. The scripts, existing assets and historical proofs are immutable.

- Compare cycles at **phase-aligned** times: search a measured global phase offset that best aligns the two left/right foot paths relative to the pelvis; explain that this is kinematic alignment and not proof of force contact. Exclude the last 7% of both cycles where source/root reset artifacts can corrupt measurements. Record duration separately.
- For every single bone, report static initial pose difference, raw pose difference and **dynamic motion difference** after subtracting the two initial orientations independently. RMS/max and phase of maximum error are included. A different starting pose does not constitute a dynamic difference.
- Capture full three-dimensional hip-relative head, shoulders, forearms, hands, fingers and feet displacement in the **pelvis coordinate frame**, where model root travel and pelvis orientation are normalized out. Report motion amplitude/range for X/Y/Z and ratios. Distinguish local rotational style and world trajectory shape.
- Group per-joint findings by pelvis, torso, head/neck, shoulders, upper arms, forearms, hands, fingers, legs and feet. Preserve actual left/right asymmetries rather than manufacture symmetry.
- Original source `Walking` and `Walking_Woman` play side by side, orbit and scrub independently through synchronized normalized phases. Optional display-only root-trend subtraction does not affect source measurements. Controls include raw-phase vs measured phase alignment, JSON/CSV downloads, and sortable per-joint table.
- On successful runtime browser analysis, the local phone server **automatically saves** `research-report.json`, `research-report.csv` and `measurement-receipt.json` beneath the campaign's persistent state path. A successful packet, Git push or HTTP GET is **not** evidence of real browser analysis. Export buttons remain available if POST is blocked.

## Limits

The report describes these two source clips, not innate male or female gait. Foot event synchronization is an approximation based on observed kinematics, not a contact-force sensor. It is not evidence that copying delta quaternions onto `Walk_Backward` will produce attractive or physically sound movement. No outputs are applied to any generated motion. No automatic changes to locomotion. Any future transfer requires a separate owner-authorized, visually reviewed campaign.

## Execution

One SHA-verified Android Termux `.sh` in the authoritative `Valar05/parametric-parambulator` Git lane. Fresh, rules-verified isolated checkout, source-GLB binary verification, collision gate, pure math tests with altered-motion and no-motion negative control, HTML/JS/import/hash checks, scoped commit/push, remote readback and a unique localhost no-cache server. Source revision and entry script hash are visible in the viewer; the complete URL is emitted by the actual phone execution, not guessed.

The terminal receipt records `Git published / HTTP ready / browser research pending`. Only a validated, source-backed POST updates the separate measurement receipt. The owner's existing visual acceptance for the forward and backward motions remains in force; this research has no motion-acceptance outcome.
