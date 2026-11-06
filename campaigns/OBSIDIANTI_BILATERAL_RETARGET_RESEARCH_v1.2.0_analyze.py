#!/usr/bin/env python3
"""Actual source evaluated IK versus retargeted GLB on the same time grid.
Uses the historical GLB evaluator from the 1.2.1 archived campaign, read from Git.
No solvers, no writes to any source model, no foot correction inferred from height alone.
"""
from __future__ import annotations
import argparse,collections,hashlib,importlib.util,json,math,pathlib,statistics
MOVES=['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']
NAMES={'hip':'mixamorig:Hips','left':('mixamorig:LeftUpLeg','mixamorig:LeftLeg','mixamorig:LeftFoot','mixamorig:LeftToeBase'), 'right':('mixamorig:RightUpLeg','mixamorig:RightLeg','mixamorig:RightFoot','mixamorig:RightToeBase')}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def pos(m):return [m[3],m[7],m[11]]
def dist(a,b):return math.dist(a,b)
def subtract(a,b):return [a[k]-b[k] for k in range(3)]
def length_chain(p):return dist(p[0],p[1])+dist(p[1],p[2])
def rms(vals):return math.sqrt(sum(x*x for x in vals)/len(vals)) if vals else None
def summary(vals):return {'max':round(max(vals),7),'rms':round(rms(vals),7),'mean':round(statistics.mean(vals),7)} if vals else None
def vector(v):return [round(float(x),7) for x in v]
def glb_read(mod,path):
 g,b=mod.load_glb(path)
 names={x.get('name',''):i for i,x in enumerate(g['nodes'])}
 required=[NAMES['hip'],*NAMES['left'][:3],*NAMES['right'][:3]]
 absent=[n for n in required if n not in names]
 if absent:raise RuntimeError('TARGET_SKELETON_BONE_MISSING '+repr(absent))
 clips={a['name']:a for a in g.get('animations',[])}
 missing=[n for n in ('Lionheart_'+m for m in MOVES) if n not in clips]
 if missing:raise RuntimeError('HISTORICAL_GLB_CLIP_MISSING '+repr(missing))
 return g,b,names,clips

def source_row(row,side):
 bones=row['bones'];chain=NAMES[side]
 for n in (NAMES['hip'],*chain[:3]):
  if n not in bones:raise RuntimeError('SOURCE_BONE_MISSING '+n)
 p=[bones[n]['worldPosition'] for n in chain[:3]]
 toe=bones[chain[3]]['worldPosition'] if chain[3] in bones else None
 return {'hip':bones[NAMES['hip']]['worldPosition'],'chain':p,'foot':p[2],'toe':toe}

def sampled_target(mod,g,anim,names,t,side):
 tracks=mod.channels(g,BUF,anim)
 matrices=mod.global_matrices(g,tracks,t)
 chain=[pos(matrices[names[n]]) for n in NAMES[side][:3]]
 toe=pos(matrices[names[NAMES[side][3]]]) if NAMES[side][3] in names else None
 return {'hip':pos(matrices[names[NAMES['hip']]]),'chain':chain,'foot':chain[2],'toe':toe}

def main(args):
 spec=importlib.util.spec_from_file_location('obs_original_glb_evaluator',args.evaluator)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 global BUF
 g,BUF,names,clips=glb_read(mod,args.model)
 donor=json.loads(pathlib.Path(args.donor).read_text())
 expected=set(MOVES)
 if not expected.issubset(donor.get('actions',{})):raise RuntimeError('SOURCE_ACTION_SET_INCOMPLETE')
 output={'schema':'obsidianti-bilateral-transfer-archaeology-v1.2.0','status':'READ_ONLY_MEASURED_NOT_CAUSAL_PROOF','originalDonorSHA256':args.blend_sha,'sourceEvaluatedSampleSHA256':sha(args.donor),'historicalTargetGLBSHA256':sha(args.model),'historicalEvaluatorPath':'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py','rig':{'targetNodeCount':len(g['nodes']),'targetClipCount':len(g['animations']),'sourceClipCount':len(donor['actions'])},'clips':{},'warnings':[],'restAxes':{},'bilateralGroundContacts':{},'soleContact':{}}
 # Provenance-rich per-side rest orientations; this checks geometry before attributing anything to quaternion interpolation.
 rest=mod.ref_quats(g) if hasattr(mod,'ref_quats') else None
 # Historical evaluator has global_matrices, not ref_quats. Compute cumulative node quaternions here.
 parents={child:i for i,node in enumerate(g['nodes']) for child in node.get('children',[])}
 def qmul(a,b):
  x,y,z,w=a;X,Y,Z,W=b
  return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
 def normalize(q):
  n=math.sqrt(sum(v*v for v in q));return [v/n for v in q]
 def worldq(i):
  q=normalize(g['nodes'][i].get('rotation',[0,0,0,1]))
  return normalize(qmul(worldq(parents[i]),q)) if i in parents else q
 for side in ('left','right'):
  original=donor['actions']['Heavy1']['frames'][0]['bones']
  output['restAxes'][side]={n:{'sourceRestWorldQuat':original[n]['restWorldQuat'],'targetRestWorldQuat':vector(worldq(names[n])),'targetLocalRestQuat':g['nodes'][names[n]].get('rotation',[0,0,0,1])} for n in NAMES[side][:3]}
 try:
  source_floor=min(donor['actions']['Idle']['frames'][0]['bones'][NAMES[s][3]]['worldPosition'][1] for s in ('left','right'))
  witnesses,skin,ibm=mod.foot_witnesses(g,BUF)
  output['soleContact']['sourceToeFloor_m']=source_floor
 except Exception as ex:
  witnesses=None;source_floor=None
  output['warnings'].append('SOLE_WITNESS_UNAVAILABLE '+str(ex))
 for action in MOVES:
  anim=clips['Lionheart_'+action];records=donor['actions'][action]['frames'];duration=records[-1]['time']
  srcbase={s:source_row(records[0],s) for s in ('left','right')}
  tracks=mod.channels(g,BUF,anim)
  first_world=mod.global_matrices(g,tracks,0.)
  tarbase={s:{'hip':pos(first_world[names[NAMES['hip']]]),'chain':[pos(first_world[names[x]]) for x in NAMES[s][:3]],'foot':pos(first_world[names[NAMES[s][2]]])} for s in ('left','right')}
  byside={}
  max_t=max((float(t[-1]) for (idx,p),(t,vals) in tracks.items()),default=0.)
  if max_t<duration-0.05:output['warnings'].append('DURATION_DIFFERENCE '+action+' source='+str(duration)+' target='+str(max_t))
  sole_records=[]
  for side in ('left','right'):
   donor_length=length_chain(srcbase[side]['chain']);target_length=length_chain(tarbase[side]['chain'])
   if donor_length<0.01 or target_length<0.01:raise RuntimeError('UNEXPECTED_CHAIN_LENGTH '+action+'/'+side)
   ratio=target_length/donor_length
   observed=[];expected_delta=[];srcsteps=[];tarsteps=[];feet_height=[];src_height=[];heel_toe=[];toe_height=[];anchor_vectors=[];samples=[]
   prev_src=None;prev_tar=None
   for row in records:
    t=float(row['time']);src=source_row(row,side)
    mat=mod.global_matrices(g,tracks,t)
    tar={'hip':pos(mat[names[NAMES['hip']]]),'foot':pos(mat[names[NAMES[side][2]]])}
    if NAMES[side][3] in names:tar['toe']=pos(mat[names[NAMES[side][3]]])
    # This compares motion relative to the hip from the first pose; source and target have different proportions.
    srel=subtract(src['foot'],src['hip']);trel=subtract(tar['foot'],tar['hip'])
    srel0=subtract(srcbase[side]['foot'],srcbase[side]['hip']);trel0=subtract(tarbase[side]['foot'],tarbase[side]['hip'])
    pred=[trel0[i]+ratio*(srel[i]-srel0[i]) for i in range(3)]
    err=dist(trel,pred)
    # World-space foot displacement compared to source motion, separately anchored at first pose.
    sdiff=subtract(src['foot'],srcbase[side]['foot']);tdiff=subtract(tar['foot'],tarbase[side]['foot']);werr=dist(tdiff,[ratio*x for x in sdiff])
    observed.append(err);expected_delta.append(werr)
    feet_height.append(tar['foot'][1]);src_height.append(src['foot'][1])
    if prev_src is not None:srcsteps.append(dist(src['foot'],prev_src));tarsteps.append(dist(tar['foot'],prev_tar))
    prev_src=list(src['foot']);prev_tar=list(tar['foot'])
    if src['toe'] and tar.get('toe'):
     so=subtract(src['toe'],src['foot']);to=subtract(tar['toe'],tar['foot'])
     # normalized toe baseline vertical: a relative orientation witness without assuming local bone roll
     toe_height.append(tar['toe'][1]);heel_toe.append(to[1] - ratio*so[1])
    samples.append({'t_s':round(t,5),'sourceFoot':vector(src['foot']),'targetFoot':vector(tar['foot']),'sourceHip':vector(src['hip']),'targetHip':vector(tar['hip']),'hipRelativeMotionError_m':round(err,6),'worldDisplacementError_m':round(werr,6),'sourceFootY_m':round(src['foot'][1],6),'targetFootY_m':round(tar['foot'][1],6)})
   byside[side]={'sourceLegLength_m':round(donor_length,7),'targetLegLength_m':round(target_length,7),'measuredLengthRatio':round(ratio,7),'hipRelativeTrajectoryError_m':summary(observed),'worldDisplacementError_m':summary(expected_delta),'sourceInterSampleFootMovement_m':summary(srcsteps),'targetInterSampleFootMovement_m':summary(tarsteps),'sourceFootYRange_m':round(max(src_height)-min(src_height),7),'targetFootYRange_m':round(max(feet_height)-min(feet_height),7),'heelToeYResidual_m':summary([abs(x) for x in heel_toe]),'samples':samples}
  if witnesses is not None:
   support=[]
   for row in records:
    sides=[side for side in ('left','right') if NAMES[side][3] in row['bones'] and abs(row['bones'][NAMES[side][3]]['worldPosition'][1]-source_floor)<0.06]
    if len(sides)==2:
     t=float(row['time']);world=mod.global_matrices(g,tracks,t)
     shoes=mod.skin_foot_points(witnesses,skin,ibm,world)
     y={side:mod.floor_height(shoes['Left' if side=='left' else 'Right']) for side in ('left','right')}
     support.append({'t_s':round(t,5),'soleHeightLeft_m':round(y['left'],6),'soleHeightRight_m':round(y['right'],6),'absoluteLeftRightSoleDifference_m':round(abs(y['left']-y['right']),6)})
   output['bilateralGroundContacts'][action]={'bothSourceFeetNearFloorSampleCount':len(support),'soleHeightDifference':summary([x['absoluteLeftRightSoleDifference_m'] for x in support]),'samples':support}
  la=byside['left']['hipRelativeTrajectoryError_m']['rms'];ra=byside['right']['hipRelativeTrajectoryError_m']['rms']
  output['clips'][action]={'sourceDuration_s':duration,'targetDuration_s':max_t,'sourceSampleCount':len(records),'left':byside['left'],'right':byside['right'],'rightMinusLeftRmsHipRelativeError_m':round(ra-la,7),'largerHipRelativeErrorSide':('right' if ra>la else 'left' if la>ra else 'tie')}
 # For every clip, report both sides. Never infer a rig bug just from one scalar asymmetry.
 output['overall']={'clipsRightLargerError':sum(v['largerHipRelativeErrorSide']=='right' for v in output['clips'].values()),'clipsLeftLargerError':sum(v['largerHipRelativeErrorSide']=='left' for v in output['clips'].values()),'maxRightError_m':max(v['right']['hipRelativeTrajectoryError_m']['max'] for v in output['clips'].values()),'maxLeftError_m':max(v['left']['hipRelativeTrajectoryError_m']['max'] for v in output['clips'].values())}
 pathlib.Path(args.output).write_text(json.dumps(output,indent=2)+'\n')
 print('CLIPS_MEASURED='+str(len(output['clips']))+' RIGHT_GREATER='+str(output['overall']['clipsRightLargerError'])+' LEFT_GREATER='+str(output['overall']['clipsLeftLargerError']))
 print('RIGHT_MAX_HIP_RELATIVE_ERROR_M='+str(output['overall']['maxRightError_m']))
 print('LEFT_MAX_HIP_RELATIVE_ERROR_M='+str(output['overall']['maxLeftError_m']))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--evaluator',required=True);p.add_argument('--model',required=True);p.add_argument('--donor',required=True);p.add_argument('--blend-sha',required=True);p.add_argument('--output',required=True);main(p.parse_args())
