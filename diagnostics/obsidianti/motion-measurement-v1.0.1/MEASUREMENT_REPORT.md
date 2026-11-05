# Obsidianti/Lionheart native measured motion

## Scope and source protection
Read-only native Blender evaluation of Lionheart actions and exact Obsidianti v1.5.6 GLB; no animation or rig mutations.
Donor IK is evaluated in Blender. Target GLB has baked rotations; this report does **not** assume target Foot.IK controls exist.
Directional comparison needs calibration of anatomical facing. Scalar world-space displacement and normalized leg reach are measured without assuming matching rotation axes.

## Summary: distance in meters, ratios unitless

| Clip | Leg | Length ratio | Target hip travel | Scaled donor hip travel | Target extension max | Donor extension max | Witness lowest Z |
|---|---|---:|---:|---:|---:|---:|---:|
| Cast | left | 0.8725 | 0.047 | 0.113 | 0.928 | 0.949 | 0.0016291890060529113 |
| Cast | right | 0.8675 | 0.061 | 0.133 | 0.966 | 0.931 | -0.00816936232149601 |
| Heavy1 | left | 0.8725 | 0.346 | 0.357 | 0.907 | 1.000 | 0.013751565478742123 |
| Heavy1 | right | 0.8675 | 0.366 | 0.390 | 1.000 | 1.000 | -0.008156255818903446 |
| Heavy2 | left | 0.8725 | 0.801 | 0.784 | 0.893 | 0.915 | 0.013751753605902195 |
| Heavy2 | right | 0.8675 | 0.644 | 0.555 | 0.988 | 1.000 | -0.04460185393691063 |
| Heavy3 | left | 0.8725 | 0.314 | 0.375 | 0.972 | 0.987 | -0.06086818501353264 |
| Heavy3 | right | 0.8675 | 0.430 | 0.464 | 0.995 | 0.927 | -0.15258198976516724 |
| Kick | left | 0.8725 | 0.798 | 0.693 | 0.998 | 1.000 | -0.049415528774261475 |
| Kick | right | 0.8675 | 0.810 | 0.707 | 1.000 | 1.000 | -0.17268355190753937 |
| Light1 | left | 0.8725 | 0.049 | 0.170 | 0.940 | 0.991 | -0.006669751368463039 |
| Light1 | right | 0.8675 | 0.172 | 0.345 | 1.000 | 0.982 | -0.09863583743572235 |
| Light2 | left | 0.8725 | 0.397 | 0.351 | 0.922 | 0.946 | 0.0032752957195043564 |
| Light2 | right | 0.8675 | 0.400 | 0.358 | 0.999 | 0.987 | -0.13077014684677124 |
| Light3 | left | 0.8725 | 0.232 | 0.330 | 0.928 | 0.915 | -0.001908227801322937 |
| Light3 | right | 0.8675 | 0.374 | 0.497 | 0.990 | 0.863 | -0.10985611379146576 |
| SpringAttack | left | 0.8725 | 0.610 | 0.545 | 0.912 | 0.958 | -0.05601687729358673 |
| SpringAttack | right | 0.8675 | 0.922 | 0.905 | 0.949 | 0.869 | -0.1285608857870102 |
| Stomp | left | 0.8725 | 0.403 | 0.373 | 0.902 | 0.915 | -0.007708408869802952 |
| Stomp | right | 0.8675 | 0.394 | 0.359 | 0.999 | 0.970 | -0.07086008042097092 |

## Important cautions

- The maximum time-varying difference of travel magnitudes is **not** the same as a signed forward-axis translation error.
- A normalized hip-to-ankle extension is not itself a planted-foot/contact label.
- Sole witness minimum may include shoe-top vertices or nonsole vertices; visually calibrate the floor and witness selection before claiming penetration.
- Controller targets and animated raw local translation channels are in the two metadata JSON files.
- The full trajectories CSV files include every half-frame and should be used to diagnose switching, bouncing, and displacement independently.
- Original data, source SHA and remote readback are in the Termux receipt.

## Contact and snapping diagnostics
Each side/clip includes max consecutive half-frame ankle/hip displacement, candidate near-floor frames, and candidate support sliding. These are observations, not automatically labeled contact.

## Limitations
