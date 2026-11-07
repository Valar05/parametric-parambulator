# Obsidianti Ares lower-body steps + recovered Lionheart guard (v2.0.29)

**Owner visual approval: PENDING.** Source was restored from original canonical content SHA `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4`. ARP step lower-body source v2.0.16 SHA `e7f60fea731fd9537380868adbb52fee63df34fdf1b6d7694bc39925b440fa1d`.

Recovered historical named animations: `LionheartIdle_UNREVIEWED` (static original guard) and `ObsidiantiIdle` (authored 3.0 second secondary-motion loop).

Eight new clips `CombatStep*` retain moving Hips, legs, knees, feet, and toes from v2.0.16. Upper Spine subtree uses exact original guard with compensating Spine rotation from the v1.1 algorithm. All 23 original ARP animations retained as-is.

The ARP v2.0.14 steps were not used: historical KEYS shows only two hip keys per step. The real v2.0.16 steps have 24–25 keys.

Input 23 clips; output 33 clips. Candidate SHA-256 `c78de9dcb7fc852d4784b36bb55daafb461e5958e8917d2e6ab330aaa72764c3`.

Viewer (Three.js, candidate/ARP/historical A/B): http://127.0.0.1:9210/index.html?run=20261107T171122Z-e8c0a300&build=ada3e4f7071ad603e87b1ffa

No canonical model writes, no vendor ARP rerun, no new Godot game. The proposed Three.js runtime is not implemented in this campaign.

Guard numerical max world-frame deviations (degrees): {'CombatStepForward': 9.7e-06, 'CombatStepForwardLeft': 1.07e-05, 'CombatStepLeft': 8e-06, 'CombatStepBackLeft': 3.4e-06, 'CombatStepBack': 8.7e-06, 'CombatStepBackRight': 1.11e-05, 'CombatStepRight': 4.5e-06, 'CombatStepForwardRight': 4.5e-06}
