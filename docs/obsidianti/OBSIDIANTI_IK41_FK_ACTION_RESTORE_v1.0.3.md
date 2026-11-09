# Obsidianti IK41 FK Action Retention Recovery v1.0.3

**Intent:** Recover the already authored 41-clip IK Blender file without regenerating the IK curves or changing the original source. This is not an approval, runtime GLB change, or two-handed work resumption.

The v1.0.1 real Blender IK authoring succeeded (41 actions; pose parity worst ankle 0.0113 mm, knee 4.0 mm), but a fresh reopen found `FK_EDITABLE__` source actions missing, probably orphan datablocks stripped on save. The v1.0.2 strict recovery diagnosed MISSING, not changed keyframes, across 24 reported names (its report capped the list).

This campaign imports only missing `FK_EDITABLE__` Actions from exact SHA-pinned original v1.0.0 FK .blend into an independent copy of the exact SHA-pinned v1.0.1 IK candidate. It sets fake-user on all 82 original actions and writes a **new** v1.0.3 native Blender file. It does not touch existing IK Actions, pose channels, skeleton constraints, or original files. A fresh native reopen compares every original FK Action's paths, key values, times, handles and interpolation; verifies all 41 IK action identities, active constraints, control curves, and sampled evaluated foot/knee poses. Any failure blocks delivery/publication; no relaxed parity thresholds or unjustified precision loopholes.

**Execution authority:** isolated Android Termux Git only. Campaign source and contracts commit first to `Valar05/parametric-parambulator`, main. Successful binary only publishes with LFS plus exact remote HEAD and pointer readback. An existing candidate is recovered from Termux previous-run state with its exact hash and original author report. If missing, block rather than substituting another file. Original GLB and previous .blend stay unchanged; visual owner acceptance remains pending.
