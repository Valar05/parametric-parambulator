# v0.1.30 left gait contact continuity

Based exactly on published v0.1.28. Change only the procedural viewer and UI, plus this new pure mathematical helper, its test and campaign. Original source reconstruction core, all GLB files, prior viewers, camera functions and original source animation untouched.

The former IK implementation applied full correction instantly during a stance window, then removed it at lift-off, and refused large corrections at thresholds. This patch fades both stance contact and correction envelopes using continuous smoothstep curves, preserving source knee plane and original foot orientation. Added a generated-without-IK diagnostic for isolating source seam behavior. No claim of proven mesh-space contact physics or human acceptance. Source parity before IK remains unchanged.
