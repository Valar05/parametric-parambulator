#!/usr/bin/env python3
"""Evidence-level trajectory comparison; original data preserved, assumptions explicit."""
import csv,json,math,sys,pathlib,statistics,collections
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
META={k:json.loads((root/k/'metadata.json').read_text()) for k in ('lionheart','obsidianti')}
ROWS={k:collections.defaultdict(list) for k in META}
def fl(row,key):
 try:return float(row[key])
 except (ValueError,TypeError,KeyError):return None
def xyz(row,p):return tuple(fl(row,p+'_'+axis) for axis in 'xyz')
def norm(v):return math.sqrt(sum(a*a for a in v))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
for kind in ROWS:
 with (root/kind/'trajectories.csv').open() as fp:
  for row in csv.DictReader(fp):ROWS[kind][(row['clip'],row['side'])].append(row)
summary={'schema':'obsidianti-motion-measurement-v1','authority':'READ_ONLY_BOTH_REAL_ASSETS',
 'sources':{k:{'path':v['source'],'fps':v['fps'],'roles':v['roles'],'skinWitnessCounts':v.get('skinWitnessCounts')} for k,v in META.items()},
 'method':{'samples':'every half native Blender frame; nearest-time correspondence',
 'coordinateCaution':'Blender world axes are preserved; length and extension ratios are coordinate-rotation invariant. Direction comparisons not authoritative until anatomical facing is calibrated.',
 'soleFloor':'provisional: estimated from 10th percentile of per-frame target minimum skin witness Z; not guaranteed physical floor',
 'sourceIK':'native Blender evaluated constraints; target GLB baked FK; missing target IK is expected',
 'correction':'NONE'},'clips':{},'limitations':[]}
for clip in ['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']:
 data={};summary['clips'][clip]=data
 for side in ('left','right'):
  donor=ROWS['lionheart'][(clip,side)];target=ROWS['obsidianti'][(clip,side)]
  if not donor or not target:raise RuntimeError('MISSING_ROWS '+clip+side)
  ratio=(fl(target[0],'thighRest_m')+fl(target[0],'shinRest_m'))/(fl(donor[0],'thighRest_m')+fl(donor[0],'shinRest_m'))
  donor_start=xyz(donor[0],'hip');target_start=xyz(target[0],'hip')
  dhip=[];thip=[];scaled=[];stretch=[];footclose=[];ankle_glide=[]
  foot_start=xyz(target[0],'ankle')
  source_total=max(fl(z,'seconds') for z in donor);target_total=max(fl(z,'seconds') for z in target)
  for tr in target:
   t=fl(tr,'seconds')
   dr=min(donor,key=lambda r:abs(fl(r,'seconds')-t))
   hs=norm(sub(xyz(dr,'hip'),donor_start));ht=norm(sub(xyz(tr,'hip'),target_start))
   dhip.append(hs);thip.append(ht);scaled.append(ht-ratio*hs)
   stretch.append(fl(tr,'extensionRatio')-fl(dr,'extensionRatio'))
   footclose.append(norm(sub(xyz(tr,'ankle'),xyz(tr,'hip'))))
   ankle_glide.append(norm(sub(xyz(tr,'ankle'),foot_start)))
  soles=[fl(r,'soleMinZ') for r in target if fl(r,'soleMinZ') is not None]
  metrics={'sourceDurationSeconds':source_total,'targetDurationSeconds':target_total,
    'sourceRestLegLength_m':fl(donor[0],'thighRest_m')+fl(donor[0],'shinRest_m'),
    'targetRestLegLength_m':fl(target[0],'thighRest_m')+fl(target[0],'shinRest_m'),
    'anatomicalLengthRatio':ratio,
    'maxDonorHipDisplacementMagnitude_m':max(dhip),
    'maxTargetHipDisplacementMagnitude_m':max(thip),
    'maxScaledHipDisplacementExcess_m':max(scaled),
    'minScaledHipDisplacementExcess_m':min(scaled),
    'maxDonorExtensionRatio':max(fl(x,'extensionRatio') for x in donor),
    'maxTargetExtensionRatio':max(fl(x,'extensionRatio') for x in target),
    'maxExcessExtensionRatioOverTime':max(stretch),
    'minExcessExtensionRatioOverTime':min(stretch),
    'maxTargetAnkleDisplacementFromStart_m':max(ankle_glide),
    'maxTargetAnkleStepPerHalfFrame_m':max([norm(sub(xyz(b,'ankle'),xyz(a,'ankle'))) for a,b in zip(target,target[1:])] or [0]),
    'maxTargetHipStepPerHalfFrame_m':max([norm(sub(xyz(b,'hip'),xyz(a,'hip'))) for a,b in zip(target,target[1:])] or [0]),
    'maxTargetHipToAnkle_m':max(footclose),
    'soleWitnessCount':META['obsidianti'].get('skinWitnessCounts',{}).get(side,0),
    'soleMinZ':min(soles) if soles else None,'soleMaxZ':max(soles) if soles else None,
    'targetSampleCount':len(target),'donorSampleCount':len(donor),
    'donorFootIKAvailable':META['lionheart']['roles'][side+'_ik'] is not None,
    'donorKneePoleAvailable':META['lionheart']['roles'][side+'_pole'] is not None}
  if soles:
   ss=sorted(soles);floor=ss[max(0,int(.1*(len(ss)-1)))];metrics['provisionalFloorZ']=floor
   metrics['maxPenetrationBelowProvisionalFloor_m']=max(0,floor-min(soles))
   candidate=[(i,row) for i,row in enumerate(target) if fl(row,'soleMinZ') is not None and fl(row,'soleMinZ')<=floor+.012]
   travel=[norm(sub(xyz(target[i],'ankle'),xyz(target[i-1],'ankle'))) for i,_ in candidate if i>0]
   metrics['candidateNearFloorFrameCount']=len(candidate)
   metrics['candidateNearFloorMaxAnkleStepPerHalfFrame_m']=max(travel) if travel else None
  data[side]=metrics
# Separate explicit mismatch facts from hypotheses
source_roles=META['lionheart']['roles'];target_roles=META['obsidianti']['roles']
if any(source_roles.get(s+'_ik') is None for s in ('left','right')):
 summary['limitations'].append('Native donor foot IK labels unresolved; report retains entire bone inventory/constraints for inspection.')
if all(x.get('soleWitnessCount',0)==0 for c in summary['clips'].values() for x in c.values()):
 summary['limitations'].append('No weighted foot/toe skin witnesses resolved; cannot infer actual sole penetration.')
if any(abs(m['sourceDurationSeconds']-m['targetDurationSeconds'])>.05 for c in summary['clips'].values() for m in c.values()):
 summary['limitations'].append('Some donor/target durations differ; nearest-seconds correspondence should be interpreted cautiously.')
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Obsidianti/Lionheart native measured motion','',
 '## Scope and source protection','Read-only native Blender evaluation of Lionheart actions and exact Obsidianti v1.5.6 GLB; no animation or rig mutations.',
 'Donor IK is evaluated in Blender. Target GLB has baked rotations; this report does **not** assume target Foot.IK controls exist.',
 'Directional comparison needs calibration of anatomical facing. Scalar world-space displacement and normalized leg reach are measured without assuming matching rotation axes.','',
 '## Summary: distance in meters, ratios unitless','',
 '| Clip | Leg | Length ratio | Target hip travel | Scaled donor hip travel | Target extension max | Donor extension max | Witness lowest Z |','|---|---|---:|---:|---:|---:|---:|---:|']
for clip, sides in summary['clips'].items():
 for side,m in sides.items():
  lines.append(f"| {clip} | {side} | {m['anatomicalLengthRatio']:.4f} | {m['maxTargetHipDisplacementMagnitude_m']:.3f} | {m['maxDonorHipDisplacementMagnitude_m']*m['anatomicalLengthRatio']:.3f} | {m['maxTargetExtensionRatio']:.3f} | {m['maxDonorExtensionRatio']:.3f} | {m['soleMinZ'] if m['soleMinZ'] is not None else 'unavailable'} |")
lines+=['','## Important cautions','',
 '- The maximum time-varying difference of travel magnitudes is **not** the same as a signed forward-axis translation error.',
 '- A normalized hip-to-ankle extension is not itself a planted-foot/contact label.',
 '- Sole witness minimum may include shoe-top vertices or nonsole vertices; visually calibrate the floor and witness selection before claiming penetration.',
 '- Controller targets and animated raw local translation channels are in the two metadata JSON files.',
 '- The full trajectories CSV files include every half-frame and should be used to diagnose switching, bouncing, and displacement independently.',
 '- Original data, source SHA and remote readback are in the Termux receipt.','',
 '## Contact and snapping diagnostics',
 'Each side/clip includes max consecutive half-frame ankle/hip displacement, candidate near-floor frames, and candidate support sliding. These are observations, not automatically labeled contact.',
 '', '## Limitations',*[f'- {x}' for x in summary['limitations']]]
(out/'REPORT.md').write_text('\n'.join(lines)+'\n')
print('ANALYSIS_COMPLETE clips='+str(len(summary['clips']))+' half_frame_rows='+str(sum(len(v) for g in ROWS.values() for v in g.values())),flush=True)
