# Hareworks Walking_Woman v0.1.13: accepted procedural walk + inverse support-root

**State at script authoring:** v0.1.12 published but visually REJECTED. This version is a mathematical integration candidate. Physical GLB browser audit and owner gait approval are separate, pending gates.

## What is retained

- v0.1.9 accepted six-harmonic, hip-relative ankle and knee-pole curves (unchanged), four-harmonic pelvis position/yaw and the existing source-calibrated upper-body motion.
- A single traveling visible character with genuine world-coordinate stance anchors and two-bone leg IK. Original 74-joint Hareworks nine-clip GLB is immutable (SHA256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`). No new GLB added; no other version edited.
- Three.js OrbitControls restored: drag/touch rotate, pinch/scroll zoom, presets and reset; camera target translates with actor but user angle and zoom are not reset each frame.

## Mathematical repair

The original in-place fitted gait is already accurate to the archived `Walking_Woman` witnesses (60 samples): left ankle RMS 0.00154, right RMS 0.00155 units, pelvis RMS 0.00178. v0.1.12's ~0.68 units travel **per entire two-foot cycle** was around half the required travel. Let q be full gait phase and A_s(q) the already-accepted hip-relative fitted ankle. Build the per-phase world-root curve with dR_z/dq ≈ −dA_{support,z}/dq, blending the support ankles in double support; R(q+1)=R(q)+D. The archived-fit proxy yields approximately D=1.22 units/full cycle. Preserve v0.1.9 pelvis and knee pole; avoid arbitrary pelvis vertical reach shifts.

Derive candidate support episodes from negative source ankle forward velocity instead of thresholding height alone. Earlier exact source witness math gave left ~58% duty and right ~60%; these windows are kinematic hypotheses and MUST be validated against actually skinned heel/sole/toe heights and ground velocities. Distinct heel/midsole/toe witness vertex sets are partitioned from the shoe mesh, with a hard guard if they cannot be distinguished. Stance uses immutable world contact targets; swing uses the existing accepted ankle curve plus a decaying correction to preserve the last physically solved ankle at liftoff. No generic swing sine or live source leg clip on the character. A contact pivot transition captures the current skinned witness without forcibly teleporting it to Y=0; the height offset is measured and gated.

A two-support constraint is not guaranteed to be perfectly compatible with source poses. Do not hide conflicts; record actual skinned drift, floor penetration, reach warnings, and late-stance trailing extension deficit. Physical contact PASS requires a real 120 Hz browser three-cycle audit and cannot grant owner gait acceptance.

## Delivery / regression standard

One SHA-guarded Android Termux entrypoint operating on the user's NORMAL persistent checkout `~/storage/documents/GodotProjects/parametric-parambulator`. No new clones or unrelated LFS downloads. No reset, stash, forced checkout or force push. Never overwrite a pre-existing target. Stage only the brand-new `tools/hareworks-forward-woman/v0.1.13/` directory; test and read back the exact Git remote commit and actual served JS bytes. Preserve source `AGENTS.md`, existing v0.1.9, v0.1.11, v0.1.12, Repl and Hareworks model hashes. Explicit owner review remains pending even if local/static tests pass.

Measured source repository basis at `fa927379890b111220b368595c6e2f27725a9d1a`. Mathematical audit and bibliography saved to Home Center: https://docs.google.com/document/d/1dbxbhHIfaJO731l5g1O7fU91xQ6ztiRkLULOmYnEZpM/edit
