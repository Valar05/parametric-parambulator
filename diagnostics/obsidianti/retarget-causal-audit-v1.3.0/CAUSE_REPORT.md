# Obsidianti bilateral retarget: causal differential audit v1.3.0

**Status:** read-only diagnosis against original evaluated Lionheart and SHA-locked historical FK GLB. **No repair, no canonical mutation, no visual acceptance.**

## Source and method

- Source `.blend` SHA-256: `81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4`
- Actual Blender-evaluated source-sample SHA-256: `70ee2fbc44c2d52964e7c11f66cf145b386d50be809830613ed0ad04733a9b04`
- Historical target GLB SHA-256: `955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32`
- Evaluate original Blender constraints on original/half frames; evaluate historical GLB at same times. Recreate its original bone quaternion mapper; decompose FK ankle position by allowing hip translation, hip rotation, upper-leg rotation, shin rotation and foot rotation in sequence.
- Compare source/target leg lengths and real skinned wedge contact witnesses. Use target Y for vertical comparisons: no unverified source/target horizontal facing alignment.

## Exact pelvis-only impossibility invariant

A shared pelvis translation moves both foot positions by the same vector. It **cannot change** their separation. If the two original feet stay fixed relative to each other but their destination separation changes, no hip translation adjustment (not even an arbitrarily large 3D vector) can simultaneously restore both.

Stationary-pair contradictions: **Cast**.

| Clip | Source pair Δ max (mm) | Target pair Δ max (mm) | Source-foot Y range L/R (mm) | Target-foot Y range L/R (mm) |
|---|---:|---:|---:|---:|
| Cast | 0.0 | 104.7 | 0.0/0.0 | 14.1/90.0 |
| Heavy1 | 177.5 | 263.9 | 125.4/114.5 | 95.4/294.2 |
| Heavy2 | 1604.6 | 1395.6 | 433.2/118.4 | 400.3/213.1 |
| Heavy3 | 1175.6 | 983.3 | 11.9/122.7 | 70.0/285.1 |
| Kick | 1339.0 | 1149.6 | 1299.0/58.4 | 1140.9/181.9 |
| Light1 | 108.9 | 219.6 | 0.0/93.6 | 35.8/224.1 |
| Light2 | 261.9 | 358.4 | 194.1/97.3 | 164.0/264.3 |
| Light3 | 1812.1 | 1745.1 | 472.2/168.7 | 395.8/203.0 |
| SpringAttack | 1537.3 | 1302.0 | 200.6/168.7 | 241.5/288.2 |
| Stomp | 870.2 | 860.1 | 840.0/7.5 | 691.2/104.0 |

## Where the dynamic vertical error appears

The following terms decompose the **Y-axis foot displacement residual** exactly into (1) target hip Y motion relative to scaled source hip motion and (2) target hip-to-foot Y motion relative to scaled source leg motion. They are not arbitrary IK corrections.

| Clip | Left root residual RMS (mm) | Left limb residual RMS (mm) | Right root residual RMS (mm) | Right limb residual RMS (mm) |
|---|---:|---:|---:|---:|
| Cast | 0.0 | 3.8 | 0.0 | 55.6 |
| Heavy1 | 1.7 | 19.1 | 1.6 | 79.3 |
| Heavy2 | 1.7 | 12.9 | 1.5 | 100.5 |
| Heavy3 | 0.7 | 23.6 | 0.7 | 105.9 |
| Kick | 1.0 | 13.5 | 0.8 | 39.3 |
| Light1 | 0.0 | 4.7 | 0.0 | 58.9 |
| Light2 | 0.0 | 8.4 | 0.0 | 65.0 |
| Light3 | 0.0 | 18.3 | 0.0 | 90.9 |
| SpringAttack | 0.3 | 51.9 | 0.2 | 66.7 |
| Stomp | 1.4 | 22.1 | 1.3 | 31.7 |

## Exact rebase-rotation parity

The historical v1.1.0 import function is rerun using actual sampled source bone rotations and rest bases. Output quaternions are compared to the historical GLB channels. Midframe source evaluation can differ from interpolated target animation, so individual timestamps in `CAUSAL_AUDIT.json` must distinguish keyed samples from midpoint samples.

| Clip | Max disagreement at source frame (degrees) | Max disagreement at true source midpoint (degrees) |
|---|---:|---:|
| Cast | 0.00001 | 2.55765 |
| Heavy1 | 0.00003 | 20.89214 |
| Heavy2 | 0.00004 | 34.09280 |
| Heavy3 | 0.00004 | 47.28918 |
| Kick | 0.00001 | 59.25245 |
| Light1 | 0.00001 | 20.88743 |
| Light2 | 0.00001 | 32.11954 |
| Light3 | 0.00003 | 25.55229 |
| SpringAttack | 0.00002 | 47.23694 |
| Stomp | 0.00004 | 15.08117 |

## Root-Y-only counterfactual

When both source toe pivots are near source ground, solve the best single hip-Y translation multiplier (bounded to 0–2) against both target foot bones, keeping leg FK unchanged. This is an analytic diagnostic and is **not** equivalent to fixing the true wedge sole.

| Clip | Samples | Best multiplier | Recorded RMS vertical foot residual (mm) | Best achievable (mm) |
|---|---:|---:|---:|---:|
| Cast | insufficient bilateral-source-near-floor samples | n/a | n/a | n/a |
| Heavy1 | 46 | 0.5948 | 27.3 | 24.2 |
| Heavy2 | 82 | 1.8087 | 41.6 | 35.5 |
| Heavy3 | 122 | 0.9889 | 76.7 | 76.7 |
| Kick | 58 | 0.9449 | 11.8 | 9.3 |
| Light1 | insufficient bilateral-source-near-floor samples | n/a | n/a | n/a |
| Light2 | insufficient bilateral-source-near-floor samples | n/a | n/a | n/a |
| Light3 | insufficient bilateral-source-near-floor samples | n/a | n/a | n/a |
| SpringAttack | 84 | 0.4346 | 55.1 | 20.8 |
| Stomp | 84 | 1.2818 | 17.9 | 12.6 |

## FK stage contributions and source rest-space diagnostics

For every sampled time, the JSON includes incremental world-Y displacements from: Hips.translation, Hips.rotation, UpLeg.rotation, Leg.rotation, Foot.rotation. This is an ordered ablation, so contributions depend on the chosen sequence and are **not** unique physical causal forces. Compare right/left and source rest bases before editing any angle.

## Limitations and next decision

- A separate foot-rotation basis bug is not established unless orientation and full skinned wedge surface are independently validated.
- The source-foot contact label uses the original source ToeBase height; the target contact witness is a heuristic weighted-shoe patch and requires visual confirmation.
- Only the original Lionheart transfer is tested here. Ares and approved Idle are protected controls, not targets for modification.
- No canonical GLB, original `.blend`, animation channel, or rig was modified. Inspect the time-stamped error and stage matrices to select the smallest repair, then test actual skinned wedge contact on an isolated candidate.

**Deployment status:** no repaired animation published, owner review required.


## Current canonical GLB: independent real-binary comparison

- Current canonical GLB SHA-256: `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4`
- This evaluates the *currently committed model* against the same actual source Blender half-frame positions, instead of equating a historical unapproved candidate with the live canonical asset.

| Clip | Historical target separation Δ max (mm) | Current canonical separation Δ max (mm) | Current left foot Y range (mm) | Current right foot Y range (mm) |
|---|---:|---:|---:|---:|
| Cast | 104.7 | 46.7 | 11.1 | 18.3 |
| Heavy1 | 263.9 | 263.9 | 97.0 | 305.4 |
| Heavy2 | 1395.6 | 1339.4 | 398.4 | 113.6 |
| Heavy3 | 983.3 | 995.2 | 72.6 | 285.1 |
| Kick | 1149.6 | 1149.6 | 1164.9 | 181.9 |
| Light1 | 219.6 | 204.6 | 17.1 | 224.1 |
| Light2 | 358.4 | 358.4 | 172.6 | 263.0 |
| Light3 | 1745.1 | 1736.1 | 397.9 | 203.0 |
| SpringAttack | 1302.0 | 1302.0 | 246.7 | 292.6 |
| Stomp | 860.1 | 860.1 | 727.6 | 60.5 |

Any differences between these two columns establish whether subsequent historical changes improved or worsened the same exact foot-separation invariant. The current model is read and SHA-checked, never rewritten.

