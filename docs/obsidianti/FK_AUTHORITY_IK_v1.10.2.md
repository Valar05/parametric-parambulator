# Obsidianti FK-authoritative knee pole recovery v1.10.2

**Scope:** create a pose-parity-tested IK authoring project using the exact Ares-scaled FK GLB. The v1.10.1 FK baseline remains the protected reference. No canonical GLB edits.

- Both knee pole controls are unconnected children of the matching foot IK controller, ensuring they move with the foot during editing.
- Every sampled FK knee plane drives a continuous, bounded pole-position optimization using Blender's *evaluated* knee joint, not a generic angle guess. All original FK data and foot controller trajectories remain unchanged.
- Evaluate every original animation key, midpoint, and an independent quarter-interval holdout between fitted samples. Reject any editability verdict if hip >1mm, ankle >4mm, knee >4mm, or foot orientation >0.75° in either leg.
- If no parity, keep v1.10.1 FK baseline and publish only diagnostics. Do not sell/label an unverified IK rig as editable.
- Authorized source and execution: Termux Git only, isolated clean checkout, exact SHA readback; no GitHub connector write, canonical model changes, or force push.
- Output should include SHA-verified Downloads PARITY.json and REPORT.md; on parity pass also IK_EDITABLE_UNAPPROVED.blend. Print full paths and acceptance status.
- The prior v1.10.1 baseline has SHA256 `96e13a407a3d1746636509ddf26dbc6d15aec78458beb333cbc99dfecf320034` and is reused intact.
