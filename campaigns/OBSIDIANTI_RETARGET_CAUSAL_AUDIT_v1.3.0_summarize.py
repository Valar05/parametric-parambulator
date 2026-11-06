#!/usr/bin/env python3
"""Generate bounded, evidence-specific diagnosis; does not claim a repaired model."""
import json,pathlib,sys
src=json.loads(pathlib.Path(sys.argv[1]).read_text());out=pathlib.Path(sys.argv[2]);o=src['clips']
canonical=json.loads(pathlib.Path(sys.argv[3]).read_text()) if len(sys.argv)>3 else None
mm=lambda x:f'{1000*x:.1f}' if x is not None else 'n/a'
lines=['# Obsidianti bilateral retarget: causal differential audit v1.3.0','',
 '**Status:** read-only diagnosis against original evaluated Lionheart and SHA-locked historical FK GLB. **No repair, no canonical mutation, no visual acceptance.**','',
 '## Source and method','',
 f"- Source `.blend` SHA-256: `{src['originalBlendSHA256']}`",
 f"- Actual Blender-evaluated source-sample SHA-256: `{src['sourceSamplesSHA256']}`",
 f"- Historical target GLB SHA-256: `{src['historicalGLBSHA256']}`",
 '- Evaluate original Blender constraints on original/half frames; evaluate historical GLB at same times. Recreate its original bone quaternion mapper; decompose FK ankle position by allowing hip translation, hip rotation, upper-leg rotation, shin rotation and foot rotation in sequence.','- Compare source/target leg lengths and real skinned wedge contact witnesses. Use target Y for vertical comparisons: no unverified source/target horizontal facing alignment.','',
 '## Exact pelvis-only impossibility invariant','',
 'A shared pelvis translation moves both foot positions by the same vector. It **cannot change** their separation. If the two original feet stay fixed relative to each other but their destination separation changes, no hip translation adjustment (not even an arbitrarily large 3D vector) can simultaneously restore both.','']
contr=src['invariants']['stationarySourcePairContradictions']
lines.append('Stationary-pair contradictions: **'+(', '.join(contr) if contr else 'none established from whole-clip samples')+'**.')
lines.extend(['','| Clip | Source pair Δ max (mm) | Target pair Δ max (mm) | Source-foot Y range L/R (mm) | Target-foot Y range L/R (mm) |','|---|---:|---:|---:|---:|'])
for name,cl in o.items():
 L,R=cl['legs']['Left'],cl['legs']['Right']
 lines.append('| '+name+' | '+mm(cl['sourceFootSeparationVariation_m']['max'])+' | '+mm(cl['targetFootSeparationVariation_m']['max'])+' | '+mm(L['sourceFootYRange_m'])+'/'+mm(R['sourceFootYRange_m'])+' | '+mm(L['targetFootYRange_m'])+'/'+mm(R['targetFootYRange_m'])+' |')
lines.extend(['','## Where the dynamic vertical error appears','',
 'The following terms decompose the **Y-axis foot displacement residual** exactly into (1) target hip Y motion relative to scaled source hip motion and (2) target hip-to-foot Y motion relative to scaled source leg motion. They are not arbitrary IK corrections.','',
 '| Clip | Left root residual RMS (mm) | Left limb residual RMS (mm) | Right root residual RMS (mm) | Right limb residual RMS (mm) |','|---|---:|---:|---:|---:|'])
for name,cl in o.items():
 L,R=cl['legs']['Left'],cl['legs']['Right']
 lines.append('| '+name+' | '+mm(L['rootVerticalMismatch_m']['rms'])+' | '+mm(L['limbVerticalMismatch_m']['rms'])+' | '+mm(R['rootVerticalMismatch_m']['rms'])+' | '+mm(R['limbVerticalMismatch_m']['rms'])+' |')
lines.extend(['','## Exact rebase-rotation parity','',
 'The historical v1.1.0 import function is rerun using actual sampled source bone rotations and rest bases. Output quaternions are compared to the historical GLB channels. Midframe source evaluation can differ from interpolated target animation, so individual timestamps in `CAUSAL_AUDIT.json` must distinguish keyed samples from midpoint samples.','',
 '| Clip | Max disagreement at source frame (degrees) | Max disagreement at true source midpoint (degrees) |','|---|---:|---:|'])
for name,c in o.items():lines.append(f'| {name} | {c["originalImporterQuatToHistoricalGLBMaxAngularErrorAtKeysDeg"]:.5f} | {c["originalImporterQuatToHistoricalGLBMaxAngularErrorDeg"]:.5f} |')
lines.extend(['','## Root-Y-only counterfactual','',
 'When both source toe pivots are near source ground, solve the best single hip-Y translation multiplier (bounded to 0–2) against both target foot bones, keeping leg FK unchanged. This is an analytic diagnostic and is **not** equivalent to fixing the true wedge sole.','',
 '| Clip | Samples | Best multiplier | Recorded RMS vertical foot residual (mm) | Best achievable (mm) |','|---|---:|---:|---:|---:|'])
for name,c in o.items():
 a=c['bestPossibleSharedHipYScaleOnBilateralContact']
 if a: lines.append(f'| {name} | {a["sampleCount"]} | {a["fitWithin0to2"]:.4f} | {mm(a["rmsRecorded_m"])} | {mm(a["rmsOptimal_m"])} |')
 else: lines.append(f'| {name} | insufficient bilateral-source-near-floor samples | n/a | n/a | n/a |')
lines.extend(['','## FK stage contributions and source rest-space diagnostics','',
 'For every sampled time, the JSON includes incremental world-Y displacements from: Hips.translation, Hips.rotation, UpLeg.rotation, Leg.rotation, Foot.rotation. This is an ordered ablation, so contributions depend on the chosen sequence and are **not** unique physical causal forces. Compare right/left and source rest bases before editing any angle.','',
 '## Limitations and next decision','',
 '- A separate foot-rotation basis bug is not established unless orientation and full skinned wedge surface are independently validated.','- The source-foot contact label uses the original source ToeBase height; the target contact witness is a heuristic weighted-shoe patch and requires visual confirmation.','- Only the original Lionheart transfer is tested here. Ares and approved Idle are protected controls, not targets for modification.','- No canonical GLB, original `.blend`, animation channel, or rig was modified. Inspect the time-stamped error and stage matrices to select the smallest repair, then test actual skinned wedge contact on an isolated candidate.','',
 '**Deployment status:** no repaired animation published, owner review required.',''])
if canonical:
 lines.extend(['','## Current canonical GLB: independent real-binary comparison','',
   f"- Current canonical GLB SHA-256: `{canonical['historicalGLBSHA256']}`",
   '- This evaluates the *currently committed model* against the same actual source Blender half-frame positions, instead of equating a historical unapproved candidate with the live canonical asset.','',
   '| Clip | Historical target separation Δ max (mm) | Current canonical separation Δ max (mm) | Current left foot Y range (mm) | Current right foot Y range (mm) |','|---|---:|---:|---:|---:|'])
 for name,c in o.items():
  now=canonical['clips'][name]
  lines.append('| '+name+' | '+mm(c['targetFootSeparationVariation_m']['max'])+' | '+mm(now['targetFootSeparationVariation_m']['max'])+' | '+mm(now['legs']['Left']['targetFootYRange_m'])+' | '+mm(now['legs']['Right']['targetFootYRange_m'])+' |')
 lines.extend(['','Any differences between these two columns establish whether subsequent historical changes improved or worsened the same exact foot-separation invariant. The current model is read and SHA-checked, never rewritten.',''])
out.write_text('\n'.join(lines)+'\n')
print('REPORT_GENERATED='+str(out))
