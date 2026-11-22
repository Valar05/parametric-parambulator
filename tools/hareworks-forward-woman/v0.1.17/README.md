# Hareworks v0.1.17: anatomical reach + measured world footfall stride

User rejected v0.1.17: knee flexion became much larger, while the visible stride did not behave dynamically. User specifically approved the v0.1.17 foot direction. Preserve it.

**Root cause:** v0.1.17 multiplied the source ankle's hip-relative forward position by `0.42 + 0.58*(speed/1.26677)`, producing a 0.658 stretch at the default `0.52` viewer speed. Inverse kinematics collapsed the knees. The apparent stride metric changed but source leg reach was destroyed.

**Correction:** Speed now controls target WORLD footfall separation and physical left+right cycle cadence, not the length of the thigh/shin geometry. At the default speed (`0.52 u/s`) the original v0.1.9 hip-to-ankle Y and Z are retained exactly, with gentle lateral runway crossover. At slower/faster speed the plan varies root travel per complete gait cycle, then cadence solves `speed = cadence * worldCycleDistance`. Planted skinned foot anchors remain unchanged when speed varies. Upper body, source knee pole and foot orientation from v0.1.17 are retained. The achievable speed range is bounded by measured anatomical reach; no extra limb straightening beyond physical length is implied.

Tests: compare original archived 60 source frames against speed-adjusted hip/ankle flexion in both legs. At each speed, verify foot-target Y/Z preserved and heel/sole/toe longitudinal rocker intact. Run nominal world-root and contact-step tests plus real 120Hz skinned browser audit for multiple speeds. Real-world visual verdict is the owner's, not numerical tests.

Authorized execution: verified single Android Termux Git entry, existing persistent `Documents/GodotProjects/parametric-parambulator`, versioned new v0.1.17 source only. No model edit, no historical gait edits, no reset, no force push. Exact remote Git readback is required.
