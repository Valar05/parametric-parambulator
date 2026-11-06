# Obsidianti sparse FK-only authoring v1.10.4

**Authority:** Termux Git only.

**Input:** exact v1.10.1 saved Blender FK baseline SHA-256 `96e13a407a3d1746636509ddf26dbc6d15aec78458beb333cbc99dfecf320034`. Original Ares FK candidate SHA-256 `955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32`.

**Mission:** produce independent, editable, sparse FK copies of 10 Lionheart attack actions without IK. Retain every original action and the whole source rig for comparison. Only leg quaternion keyframes of copied FK actions are eligible for decimation; protect pelvis, root, weapon, nonleg curves, animation timing, geometry, other clips and original data. No automatic aesthetic corrections.

**Algorithm:** source-driven quaternion orientation RDP, progressively stricter tolerances with validation against the actual evaluated reference pose at every original source key and 1/4, 1/2, 3/4 positions between original key times; hip <=0.5 mm, knee and ankle <=3 mm, foot and leg joint orientation <=0.5 deg. Preserve Blender's original source FCurves unchanged. Require at least 5% reduction across editable leg quaternion keyframe groups. Reject any attempt not satisfying gates rather than publish misleading sparse baseline.

**Delivery:** one SHA-locked launcher; source and policy files self-published via isolated Termux Git checkout; evidence committed and exact remote readback; successful `.blend` published to Git LFS and Android shared Downloads with SHA verification. Reports and logs always available as a handoff ZIP. Do not edit the original canonical GLB. Blender execution and visual owner acceptance are separate gates.
