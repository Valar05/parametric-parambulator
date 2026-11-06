# Obsidianti Ares FK Rebase v1.0.1

Owner request: return to successful Ares-style FK retarget approach for Lionheart attack library, specifically its anatomically scaled pelvis displacement; do not run further contact-detect IK, do not recreate foot controls, and do not destroy functioning clips.

- Authorized lane: Android Termux Git, repository `Valar05/parametric-parambulator`, with source and result pushed and remotely read back by the phone campaign.
- Pins root `AGENTS.md` blob SHA `547c2af52303f4efb718bbf8f82a698110c7bfca`; live Campaign Etiquette was read 2026-11-05. If these change, reauthorize new source revision.
- The **actual pre-contact IK FK baseline** is recovered from Git history, at the initial commit that added `campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py` (historically predating v1.3 contact IK). The LFS object hash/size and 23 expected clips are independently validated. If the source can't be recovered, **stop**; no substitution of the faulty v1.5.6 IK-derived GLB.
- Scale is the average target/donor leg length ratio measured for Heavy1 in the published v1.0.1 read-only measurement summary: about 0.8700186. Both sides' ratios recorded and cross-checked, rather than silently assuming foot controllers scale equally.
- For each of ten attack clips, restore original FK rotation and all other channels exactly as in historical GLB, and replace only the Hips *translation accessor* with `idle_hip + scale * (original_hip - idle_hip)` using the precise same translation-scaling structure that the working Ares path had.
- The 13 non-Lionheart clips, weapon translations, interpolation, timing, meshes, nodes, skins, and original BIN bytes are unchanged. No IK switching, knee-pole animation, quaternion rewrite, pelvis-pitch cleanup or additional floor correction is introduced.
- This is an **unapproved candidate**, not a promise of better contact. No canonical GLB mutation. A versioned candidate ZIP containing the exact GLB is published through Termux Git LFS and verified remotely, and separate exact GLB copied to phone Downloads for visual review. SHA and receipts track actual source and candidate.
- Visual acceptance is pending. Measure true skinned shoe soles, floor and support before proposing canonical replacement. If history / LFS is unavailable, report the blocker and preserve everything.


## v1.0.1 transport correction
Fetch the historical LFS object via the exact authenticated anchor commit and canonical path filter. The unsupported `git lfs fetch --object-id` option is removed. All algorithmic and mutation boundaries remain unchanged.
