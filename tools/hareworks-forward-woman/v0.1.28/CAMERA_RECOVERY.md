# Hareworks v0.1.28 camera-only recovery

Source: v0.1.26 on main commit 0b0c2ee6df4d697844e231247d0c6c25550a1293.
The viewer is derived from unchanged v0.1.26. No gait math, source calibration, IK, model, protected older version, or animation tracks changed.
The prior camera disabled pan, fixed an undersized/poorly framed orthographic viewport, and reset orientation when the gait reset. This revision derives bounds from the actual posed SkinnedMesh vertices, fits orthographic extents, points the camera outside the character and restores pan/orbit/zoom with explicit Fit/Follow controls.
Actual phone rendering and owner acceptance remain pending until the Termux campaign publishes and the owner sees the viewer.
