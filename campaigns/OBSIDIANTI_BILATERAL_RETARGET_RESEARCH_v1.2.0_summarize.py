#!/usr/bin/env python3
"""Evidence-scoped Markdown report from actual on-device source samples and GLB evaluations."""
import json,pathlib,sys,statistics
metrics=json.loads(pathlib.Path(sys.argv[1]).read_text());a=json.loads(pathlib.Path(sys.argv[2]).read_text());destination=pathlib.Path(sys.argv[3])
rows=[]
for name,c in metrics['clips'].items():
 l=c['left'];r=c['right']
 rows.append((name,l['measuredLengthRatio'],r['measuredLengthRatio'],l['hipRelativeTrajectoryError_m']['rms'],r['hipRelativeTrajectoryError_m']['rms'],l['hipRelativeTrajectoryError_m']['max'],r['hipRelativeTrajectoryError_m']['max'],c['largerHipRelativeErrorSide']))
lines=['# Obsidianti bilateral FK transfer: source-level investigation','',
'**Status:** Measured research evidence, not a completed repair or owner-approved animation. All canonical GLBs and original Blender projects unchanged.','',
'## Provenance','',
'- Original Lionheart `.blend` SHA-256: `'+metrics['originalDonorSHA256']+'`',
'- Evaluated source action samples SHA-256: `'+metrics['sourceEvaluatedSampleSHA256']+'`',
'- Historical pre-contact candidate GLB SHA-256: `'+metrics['historicalTargetGLBSHA256']+'`',
'- Historical GLB world transform evaluator: `'+metrics['historicalEvaluatorPath']+'`',
'- Git source revision: `'+a['gitHead']+'`',
'- Prior relevant files indexed: **'+str(a['numberOfRelevantTrackedFiles'])+'**',
'', '## Established source import architecture','',
'- Historical v1.1.0 imports **Lionheart `.blend` directly**, and **Ares from GLB**.',
'- It reads *evaluated* Blender pose matrices (`pb.matrix`), not merely raw FK f-curves; therefore it does sample IK results from Lionheart.',
'- Both donors are passed through the same quaternion rest-space `rebase_source_pose()` conversion.',
'- The transfer adjusts the hips separately via **one shared root translation**, but does **not** preserve individually grounded ankle/toe trajectories after mapping to the destination skeleton.',
'- Exporting Lionheart to GLB before importing it was visually reported by the owner to look identical. This does not establish numerical equality.',
'', '## Actual source vs historical target measurement','',
'Per-leg hip-relative motion error is computed as follows: anchor each leg to its first source and target poses, scale subsequent source foot-to-hip vector changes by that side’s measured bone-chain length ratio, then compare with the historical target foot-to-hip trajectory. Thus this measures departure from a proportional-source-motion reference, **not** a proof of a mathematical retargeting bug, optimal foot position, or IK correctness. All lengths are meters.','',
'| Attack | Left ratio | Right ratio | Left RMS | Right RMS | Left max | Right max | Larger |','|---|---:|---:|---:|---:|---:|---:|---|']
for x in rows:lines.append('| '+x[0]+' | '+' | '.join((f'{v:.4f}' if isinstance(v,float) else str(v)) for v in x[1:])+' |')
lines+=['','Right larger in **'+str(metrics['overall']['clipsRightLargerError'])+'** clips; left larger in **'+str(metrics['overall']['clipsLeftLargerError'])+'** clips. Compare these with the owner’s pose-specific review; a whole-clip RMS can conceal an isolated bad foot pose.','',
'## Diagnostic interpretation rules','',
'1. If right-leg measured rest/chain ratios or hip-relative errors are substantially different, inspect **rest bone axes, side-specific hip/ankle basis and knee bend**, not just foot quaternion signs.',
'2. A left/right asymmetry is **not** necessarily a global quaternion bug: symmetrical bones may have mirrored local bases and different authored pose paths.',
'3. If source foot positions are nearly fixed during an interval but target foot positions drift, this supports a lost world-space support constraint after retargeting. The method here reports per-sample positions and inter-sample movement for that comparison.',
'4. If the foot bone local rotation is smooth while world-space heel/toe geometry tilts, error can originate in the thigh/shin parent chain or in the rest-pose world mapping.',
'5. If both sides show comparable normalized error but only right looks wrong, compare *artistically desired* right-foot stance, outer lateral reach, and toe orientation. Matched heights alone do not validate the motion.',
'6. GLB rotation samplers in this historical importer use LINEAR interpolation; large motion between sampled keys can create a visually sharp beat without any actual discontinuity.',
'', '## Remaining unanswered, measurable questions','',
'- Which exact frames does the owner mean by the bad right-foot poses? The present report measures all ten attacks and makes per-time data available for locating them.',
'- Are the two leg chains symmetric in *rest matrices and local axis handedness*? This report quantifies length and trajectories but does not establish that every mirrored rest matrix has the correct rotation basis.',
'- Are skinned shoe soles at identical floor contact heights? Bone-head position and toe position are not equivalent to the actual deforming wedge sole. A skinned contact-patch comparison remains necessary.',
'- Did the historical source clip produce an intermediate-frame interpolation difference? The measurements sample at the Blender source frame times; half-frame examination is a separate follow-up.',
'', '## Earlier work: provenance, not reinvention','',
'Use `ARCHAEOLOGY_INDEX.json` for relevant original scripts, docs, report hashes, and commit titles. Evidence that has already been gathered should be cited and reused, not treated as an unresolved mystery. The current campaign has added an exact bilateral trajectory test against the historical pre-contact source.','',
'## Hard boundary','',
'**No canonical model, editable Blender project, or animation has been changed. No corrective FK/IK has been attempted.** This is research through the authorized Termux Git lane; publication is verified by the launcher receipt after push and remote readback.','']
if metrics['warnings']:
 lines.extend(['## Sampling warnings','']+['- '+w for w in metrics['warnings']])
destination.write_text('\n'.join(lines)+'\n')
print('RESEARCH_MD_WRITTEN='+str(destination))
