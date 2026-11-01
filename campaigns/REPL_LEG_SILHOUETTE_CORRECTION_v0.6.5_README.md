# REPL_LEG_SILHOUETTE_CORRECTION v0.6.5

One ZIP, one user invocation in **Termux**, one canonical `assets/repl/Repl.glb`.

## Owner rejection addressed
v0.6.4.1 puts the front legs on the wrong visible side of their bend,
with stiff forefeet and much too subtle rear fetlock articulation. Its
existing test used a median hoof-vertex translation instead of the true
visual bending directions. The new source checks actual fore-knee and two
lower-chain segment orientations, toe lift, rear distal folded silhouette,
real skinned hoof surface clearance, stance invariance, and moving-root
identity. It also stops pinning the exact front toe position throughout
swing, which concealed its animation. The old four-beat timing, world travel,
body, mane and approved tail socket remain unchanged.

## Mechanics
- Fore mid-swing desired signed segment directions from vertical downward:
  knee +12°, cannon -20°, pastern -23°, toe tip up +145°.
- Rear distal cannon -10°, lower fetlock -16°, terminal hoof bounded 42° roll.
- Smooth swing-only phase pulse that goes to zero at both contact boundaries.
- This is a constrained swing pose projection on top of the existing traveling
  contact IK, **not a new physics engine or an in-place walk**.
- Exact live model on GitHub must match pinned v0.6.4.1 SHA, 50 joints, 53 nodes.
- One canonical GLB updated in same path through Termux Git, remote binary readback.
- Textured HTML viewer in shared Downloads; optional Blender review when on PATH.
- Human visual acceptance **PENDING**, regardless of test PASS.

## Regression
The predecessor reversed the appearance of the forelegs while passing a
vertex-translation sign test, and suppressed true hoof motion by solving the
swung toe marker rigidly. Explicit sagittal skeleton checks catch that error.

## Source/transport
Source authority: `Valar05/parametric-parambulator`, prior main
`bd0528afaf2640dcf3272b61b000f42442c6bc47`, current GLB SHA-256
`b6b5df58df8eeee79ffc2f3beabd1de15af6186988dd97e98610c4badaa48604`.
Campaign Etiquette: https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit

No direct GitHub connector writes, additional model names or Pose Lab workspace.
