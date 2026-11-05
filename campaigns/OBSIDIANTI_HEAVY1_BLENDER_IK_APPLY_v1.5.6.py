#!/usr/bin/env python3
"""Validate Blender evaluated IK against original glTF skin, patch ONLY Heavy1 six leg rotations.

The published GLB is never changed by this tool. --out is an isolated candidate.
A failed physical gate still writes an inspectable full diagnostic report.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, math, pathlib, struct, sys

VER='OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
MATH_SHA='dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f'
HEAVY1_SHA='a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4'
SIDES=('Left','Right')
PARTS=('UpLeg','Leg','Foot')
CLIP='Lionheart_Heavy1'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def vec(a,b):return [a[i]-b[i] for i in range(3)]
def length(v):return math.sqrt(sum(x*x for x in v))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def angle(a,b):return math.degrees(2*math.acos(min(1.,abs(sum(x*y for x,y in zip(a,b))))))
def xyz(m):return [m[3],m[7],m[11]]
def clamp(v,a,b):return min(b,max(a,v))

def main():
 p=argparse.ArgumentParser()
 for s in ('model','math-helper','native-ik-samples','source','report'):
  p.add_argument('--'+s,required=True)
 p.add_argument('--out',required=True)
 a=p.parse_args()
 if pathlib.Path(a.out).resolve()==pathlib.Path(a.model).resolve():raise RuntimeError('CANDIDATE_PATH_MUST_DIFFER_FROM_CANONICAL')
 if sha(a.model)!=MODEL_SHA:raise RuntimeError('MODEL_CHANGED_FROM_PINNED_BYTES')
 if sha(a.math_helper)!=MATH_SHA:raise RuntimeError('HELPER_CHANGED_FROM_PINNED_BYTES')
 if sha(a.source)!=HEAVY1_SHA:raise RuntimeError('NATIVE_LIONHEART_SOURCE_CHANGED')
 modspec=importlib.util.spec_from_file_location('obs_blender_ik_math',a.math_helper)
 M=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(M)
 source=json.loads(pathlib.Path(a.source).read_text())
 sample=json.loads(pathlib.Path(a.native_ik_samples).read_text())
 if (sample.get('engine','').find('Blender 4.x actual IK')<0 or sample.get('originalBadFKUsedForLegBasis') is not False
   or sample.get('trajectoryBasis')!='SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS'):
  raise RuntimeError('NATIVE_IK_SAMPLE_PROVENANCE_OR_ENGINE_MISMATCH')
 if sample['sourceActionSHA256']!=HEAVY1_SHA or sample['sourceModelSHA256']!=MODEL_SHA:
  raise RuntimeError('NATIVE_IK_SAMPLES_SOURCE_HASH_CHANGED')
 frames=sample['frames'];stimes=[float(x['timeSeconds']) for x in frames]
 if len(frames)!=61 or any(y<=x for x,y in zip(stimes,stimes[1:])) or abs(stimes[0])>.001 or abs(stimes[-1]-1)>.001:
  raise RuntimeError('NATIVE_IK_FRAME_CADENCE_WRONG')
 g,b=M.load_glb(a.model);orig_json=copy.deepcopy(g);original_bin=bytes(b)
 anim=next((x for x in g['animations'] if x['name']==CLIP),None)
 if anim is None:raise RuntimeError('EXACT_HEAVY1_CLIP_MISSING')
 ids={n.get('name'):i for i,n in enumerate(g['nodes'])};tr=M.channels(g,b,anim)
 hip=ids['mixamorig:Hips'];allowed={(ids['mixamorig:'+s+p],'rotation') for s in SIDES for p in PARTS}
 if len(allowed)!=6 or any(k not in tr for k in allowed):raise RuntimeError('HEAVY1_ROTATION_CHANNEL_MISSING')
 if (hip,'rotation') not in tr or (hip,'translation') not in tr:raise RuntimeError('LOCKED_PELVIS_TRACK_MISSING')
 # Six-only edit of named Heavy1 tracks. Non-Heavy1 animation dictionaries
 # and original glTF skin/mats/scene stay byte-identical in JSON and BIN prefix.
 def append(t,values,typ):
  sizes={'SCALAR':1,'VEC4':4};count=sizes[typ]
  flat=[float(x) for row in values for x in (row if typ!='SCALAR' else [row])]
  if any(not math.isfinite(x) for x in flat):raise RuntimeError('NONFINITE_BAKED_CHANNEL')
  while len(b)%4:b.append(0)
  offset=len(b);b.extend(struct.pack('<'+'f'*len(flat),*flat))
  view=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(flat)*4})
  access=len(g['accessors']);desc={'bufferView':view,'componentType':5126,'count':len(values),'type':typ}
  if typ=='SCALAR':desc['min']=[min(values)];desc['max']=[max(values)]
  g['accessors'].append(desc)
  return access
 inp=append(None,stimes,'SCALAR')
 for channel in anim['channels']:
  k=(channel['target']['node'],channel['target']['path'])
  if k not in allowed:continue
  n=g['nodes'][k[0]]['name'];qs=[f['joints'][n] for f in frames]
  if any(abs(math.sqrt(sum(x*x for x in q))-1)>.0001 for q in qs):raise RuntimeError('INVALID_UNIT_QUATERNIONS_'+n)
  sampler=anim['samplers'][channel['sampler']]
  sampler['input']=inp;sampler['output']=append(None,qs,'VEC4');sampler['interpolation']='LINEAR'
 newtr=M.channels(g,b,anim)
 if any(k not in newtr for k in allowed):raise RuntimeError('PATCHED_CHANNELS_MISSING')
 witnesses,skin,ibm=M.foot_witnesses(g,b)
 probes=[];scores={'maxAnkleMismatchVsBlender_m':0.,'maxNativeControllerMiss_m':0.,'maxMappedKneeGoalMiss_m':0.,
  'maxQuarterFootStep_m':0.,'maxQuarterKneeDirectionStep_deg':0.,
  'maxHalfFrameJointRotationStep_deg':0.,'maxSkinnedPenetration_m':0.,
  'maxSkinnedHoverAboveGround_m':0.,'sourceControllerTotalTravel_m':{},
  'expectedBackwardsRelativePelvisVerified':None}
 prev={};errframes=[]
 checks=sorted(set([round(t,9) for t in stimes]+[round((x+y)/2,9) for x,y in zip(stimes,stimes[1:])]))
 for t in checks:
  w=M.global_matrices(g,newtr,t)
  pts=M.skin_foot_points(witnesses,skin,ibm,w)
  iskey=min(abs(t-f['timeSeconds']) for f in frames)<1e-6
  fi=min(range(len(frames)),key=lambda i:abs(stimes[i]-t)) if iskey else None
  record={'timeSeconds':t,'sides':{}}
  for side in SIDES:
   hipP=xyz(w[hip]);up=ids['mixamorig:'+side+'UpLeg'];kn=ids['mixamorig:'+side+'Leg'];ft=ids['mixamorig:'+side+'Foot']
   ap=xyz(w[ft]);kp=xyz(w[kn]);h=xyz(w[up]);v=vec(kp,h)
   yy=[p[1] for p in pts[side]];miny=min(yy);flo=max(0,-miny)
   scores['maxSkinnedPenetration_m']=max(scores['maxSkinnedPenetration_m'],flo)
   # This isn't declared planted based merely on low toe-height. Record range.
   scores['maxSkinnedHoverAboveGround_m']=max(scores['maxSkinnedHoverAboveGround_m'],max(0,miny))
   center=[sum(pt[i] for pt in pts[side])/len(pts[side]) for i in range(3)]
   obs={'ankle_m':ap,'knee_m':kp,'hip_m':h,'soleMinY_m':miny,'soleCenter_m':center}
   if iskey:
    f=frames[fi];target=f['observed'][side]
    miss=length(vec(ap,target['ankleWorld']));goal=length(vec(ap,target['ankleGoal']))
    scores['maxAnkleMismatchVsBlender_m']=max(scores['maxAnkleMismatchVsBlender_m'],miss)
    scores['maxNativeControllerMiss_m']=max(scores['maxNativeControllerMiss_m'],goal)
    scores['maxMappedKneeGoalMiss_m']=max(scores['maxMappedKneeGoalMiss_m'],length(vec(kp,target['sourceMappedKneeGoalWorld'])))
    obs.update({'mappedKneeGoal_m':target['sourceMappedKneeGoalWorld'],'mappedKneeMiss_m':target['kneeGoalMissMetres']})
    obs.update({'nativeBlenderAnkle_m':target['ankleWorld'],'nativeTargetAnkle_m':target['ankleGoal'],
                'vsBlenderMiss_m':miss,'controllerGoalMiss_m':goal})
   if side in prev:
    prior=prev[side]
    step=max(length(vec(ap,prior['ankle'])),length(vec(center,prior['center'])))
    scores['maxQuarterFootStep_m']=max(scores['maxQuarterFootStep_m'],step)
    dd=clamp(dot(v,prior['kneeVec'])/(max(length(v),1e-9)*max(length(prior['kneeVec']),1e-9)),-1.,1.)
    scores['maxQuarterKneeDirectionStep_deg']=max(scores['maxQuarterKneeDirectionStep_deg'],math.degrees(math.acos(dd)))
    if step>.060 or flo>.015:
     errframes.append({'timeSeconds':t,'side':side,'step_m':step,'floorPen_m':flo})
   prev[side]={'ankle':ap,'center':center,'kneeVec':v}
   record['sides'][side]=obs
  probes.append(record)
 for side in SIDES:
  for part in PARTS:
   key=(ids['mixamorig:'+side+part],'rotation')
   qs=[list(f['joints']['mixamorig:'+side+part]) for f in frames]
   for q0,q1 in zip(qs,qs[1:]):
    scores['maxHalfFrameJointRotationStep_deg']=max(scores['maxHalfFrameJointRotationStep_deg'],angle(q0,q1))
 # The source returns to its starting pose, so endpoint travel is ZERO by
 # construction. Record actual cumulative travel; endpoint displacement separately.
 scores['sourceControllerNetDisplacement_m']={}
 scores['sourceControllerPeakStep_m']={}
 for side in SIDES:
  series=[x['legsRelativePelvis'][side]['footControllerRelativePelvisMetres'] for x in source['frames']]
  world=[x['bones'][side+'Foot.IK']['worldPosition'] for x in source['frames']]
  scores['sourceControllerTotalTravel_m'][side]=sum(length(vec(y,x)) for x,y in zip(world,world[1:]))
  scores['sourceControllerNetDisplacement_m'][side]=length(vec(world[-1],world[0]))
  scores['sourceControllerPeakStep_m'][side]=max(length(vec(y,x)) for x,y in zip(world,world[1:]))
 errors=[]
 if scores['maxAnkleMismatchVsBlender_m']>.004:errors.append('BLENDER_TO_GLTF_BONE_BASIS_NOT_PRESERVED')
 if scores['maxNativeControllerMiss_m']>.009:errors.append('NATIVE_TARGET_NOT_REACHED')
 if scores['maxQuarterFootStep_m']>.060:errors.append('FOOT_DISCONTINUITY')
 if scores['maxQuarterKneeDirectionStep_deg']>25:errors.append('KNEE_BRANCH_DISCONTINUITY')
 if scores['maxHalfFrameJointRotationStep_deg']>25:errors.append('JOINT_ROTATION_DISCONTINUITY')
 if scores['maxSkinnedPenetration_m']>.015:errors.append('SKINNED_WEDGE_PENETRATION')
 for p in ['nodes','skins','meshes','scenes','materials','textures','images']:
  if g.get(p)!=orig_json.get(p):errors.append('PROTECTED_GLB_FIELD_CHANGED:'+p)
 for original,modified in zip(orig_json['animations'],g['animations']):
  if original['name']!=CLIP and original!=modified:errors.append('PROTECTED_ACTION_CHANGED:'+original['name'])
  if original['name']==CLIP:
   for ca,cb in zip(original['channels'],modified['channels']):
    k=(ca['target']['node'],ca['target']['path'])
    if ca!=cb:errors.append('ACTION_CHANNEL_POINTER_CHANGED') # channels must be immutable: edit samplers only.
   for i,(sa,sb) in enumerate(zip(original['samplers'],modified['samplers'])):
    if sa!=sb and not any(c['sampler']==i and (c['target']['node'],c['target']['path']) in allowed for c in original['channels']):errors.append('NONLEG_SAMPLER_CHANGED')
 if not bytes(b).startswith(original_bin):errors.append('SOURCE_BUFFER_OVERWRITTEN')
 # Audit reference Idle and pre-existing Heavy1 without accepting them as correct.
 baselines={}
 for ref_name in ('LionheartIdle_UNREVIEWED','Lionheart_Heavy1'):
  ref_anim=next((z for z in orig_json['animations'] if z['name']==ref_name),None)
  if ref_anim is None:continue
  ref_tracks=M.channels(orig_json,original_bin,ref_anim)
  values=[]
  for tt in (0.,1/60,1/30,.10,.25,.5,.75,1.):
   ww=M.global_matrices(orig_json,ref_tracks,tt)
   pp=M.skin_foot_points(witnesses,skin,ibm,ww)
   values.append({'time':tt,'minimumSoleY':{side:min(v[1] for v in pp[side]) for side in SIDES}})
  baselines[ref_name]=values
 r={'version':VER,'status':'PHYSICAL_PREFLIGHT_FAILED_NO_MODEL_CHANGE' if errors else 'PHYSICAL_PREFLIGHT_PASSED_CANDIDATE_ONLY',
    'modelSourceSha256':MODEL_SHA,'originalSource':HEAVY1_SHA,'BlenderEngine':sample['engine'],
    'targetApprovedIdleKept':True,'originalBadHeavy1LegFKNotUsed':True,
    'lockedPelvisPreserved':True,'editedOnlySixHeavy1LegRotations':True,
    'sampleFrames':len(frames),'physicalProbeCount':len(checks),
    'nativeIKPoleCalibrations':sample['poleCalibration'],'referenceBaselineSoles':baselines,'strategy':sample.get('strategy'),'legRatio':sample.get('legRatio'),
    'metrics':scores,'offendingSamples':errframes[:70],'probes':probes,'failures':errors}
 pathlib.Path(a.report).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(a.report).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 protection_errors=[x for x in errors if x.startswith(('PROTECTED_GLB_FIELD_CHANGED','PROTECTED_ACTION_CHANGED','ACTION_CHANNEL_POINTER_CHANGED','NONLEG_SAMPLER_CHANGED','SOURCE_BUFFER_OVERWRITTEN'))]
 if protection_errors:
  print('PROTECTED_STRUCTURE_BLOCK='+','.join(protection_errors),flush=True)
  return 2
 blob=M.encode_glb(g,b)
 if sha(a.model)!=MODEL_SHA:raise RuntimeError('SOURCE_MODEL_CHANGED_DURING_CANDIDATE_EVALUATION')
 output=pathlib.Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
 if output.exists():raise RuntimeError('OUTPUT_ALREADY_EXISTS_NO_OVERWRITE')
 output.write_bytes(blob)
 r['candidateSha256']=sha(output)
 pathlib.Path(a.report).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 if errors:
  print('QUARANTINED_CANDIDATE_CREATED='+r['candidateSha256'],flush=True)
  print('PREFLIGHT_FAILED='+','.join(errors),flush=True)
  return 2
 print('PREFLIGHT_PASSED='+r['candidateSha256'],flush=True)
 return 0

if __name__=='__main__':sys.exit(main())
