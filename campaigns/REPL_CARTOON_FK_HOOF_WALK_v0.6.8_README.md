# Repl v0.6.8 anatomy-locked contact recovery

Corrects v0.6.7's invalid assumption that moving the planted hoof **shape**
relative to its old squash animation necessarily implies foot **sliding**.
Retains owner's exact unusual Meshy hoof hierarchy and approved front middle
joints. The four hoof-mass rotations remain at the same local FK rest quaternion
in every frame. All four physical lower-leg drivers remain anatomically signed.

New physical stance tests track the same lower hoof-mesh vertices across the
complete stance interval (including stride boundaries), and compare both actual
world movement and additional drift versus the source. `0.019` added drift is
unchanged. No numerical threshold is relaxed and no blind source mutation.

The same single Termux invocation automatically tries strict FK, then bounded
12°, 24°, and 36° compensation using **existing distal leg driver joints only**.
It never reanimates the hoof mass, front middle hinge, arbitrary bones, or
other clips. Each candidate is rebuilt and fully validated; if none works it
publishes a diagnostic JSON and leaves Git canonical untouched.

Source provenance: owner-supplied exact original v0.6.7 ZIP SHA256
`a0755237101affbef4efb74cf693befda5d1b2353299966142ab50f050765232`.
The real canonical GLB is only available on Termux Git execution lane; this
packet's code can be syntax and structural checked offline but the real
walk is **NOT YET VERIFIED OR OWNER-ACCEPTED**.

Do not claim a successful walk until Termux real-model mesh checks, one-GLB
remote commit and binary readback, and owner's visual approval.
