# SwordAttack1 two-handed, sustained offhand IK and wrist charm v2.0.33

Owner approval: **PENDING**. Canonical and all previous 41 animations preserved untouched.

Appended only `Vanguard_SwordAttack1_TwoHand_GripIK`. Starts from the **first frame** of `Lionheart_Light1`; 0.23 seconds of transitional hand reach and shield shrink/rotation before the unchanged original Vanguard sword attack plays.

The left hand follows a point down the lance hilt (`RightWeapon.R` local (-0.018, -0.235, 0.0)) with explicit 2-bone IK **for the full attack**. Stretch is measured and adjusted across every sample.

Maximum arm stretch factor: 1.806775; maximal full-attack keyed grip error 3.1e-07 m; sampled and half-frame error 0.007584763683408621 m.

The original left-wrist shield is rotated tip-to-elbow, scaled to 8% and positioned as a charm. Mesh, skin, weapon, and material are not edited.

The entire first 41 clips and binary payload prefix are byte-for-byte preserved. This is a **new review GLB**, not a canonical model change.

Viewer: http://127.0.0.1:9213/index.html?run=20261107T213143Z-f1187b82&build=7394fdfd241c9cebc44421ba

Output SHA-256: 899aa3f7f24fb3b36e80a1c96cff7d032dcacf27f990231203ba5c08f2ee066b
