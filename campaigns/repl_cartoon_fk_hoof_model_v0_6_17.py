#!/usr/bin/env python3
"""Repl 0.6.16: source-locked, ground-relative front four-beat gait.

PRECOMPUTED using actual v0.6.10 GLB mesh + v0.6.15 committed motion
formulae; re-evaluated from EXACT v0.6.15 GLB in owner-approved Termux
before any mutation. Only Bone_014/015/020/021 rotation tracks change.
All 32 stride frames are repaired, INCLUDING planted stance, unlike 0.6.15.
This version does not re-author the accepted tail, mane, rear or root sag.
"""
from __future__ import annotations
import hashlib,json,math
VERSION='0.6.16'
SOURCE_SHA='713a172ef697e04511ef1df625a67436a127e2e7dc8b5c98983a7ccb67f24a85'
REFERENCE_SHA='976d8f2b3da32a01bb99c5dfbce00bc28df2db702836a0ec8337eda1573137ab'
CANON='assets/repl/Repl.glb'
FRAMES=97;PERIOD=32;STRIDE=.32
BONES={'LF':('Bone_015','Bone_014'),'RF':('Bone_021','Bone_020')}
EDITED={n for names in BONES.values() for n in names}
FOUR={'LF':.25,'RF':.75,'LH':0.,'RH':.5}
class Blocked(RuntimeError):pass
def need(v,message):
 if not v:raise Blocked(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(q):
 length=math.sqrt(sum(x*x for x in q));need(length>1e-9,'INVALID_QUATERNION');return tuple(x/length for x in q)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def slerp(a,b,t):
 d=dot(a,b)
 if d<0:b=tuple(-x for x in b);d=-d
 d=min(1.,max(-1.,d))
 if d>.9995:return norm(tuple((1-t)*x+t*y for x,y in zip(a,b)))
 theta=math.acos(d);s=math.sin(theta)
 return norm(tuple((math.sin((1-t)*theta)*x+math.sin(t*theta)*y)/s for x,y in zip(a,b)))
def pose(tr,frame):return {n:tuple(d['rows'][frame]) for (n,p),d in tr.items() if p=='rotation'}
def phase(label,frame):
 u=((frame%32)/32.-FOUR[label])%1.
 return u,u<.62
def structure(doc,previous):
 names=previous.inspect_source(doc)
 need(len(doc.get('nodes',[]))==53 and len(doc['skins'][0]['joints'])==50 and len(doc['animations'])==6,'CANONICAL_STRUCTURE_MISMATCH')
 par={c:i for i,n in enumerate(doc['nodes']) for c in n.get('children',[])}
 for label,(shoulder,middle) in BONES.items():
  need(par[names[middle]]==names[shoulder],'ANATOMICAL_CONTROL_CHAIN_CHANGED:'+label)
 return names

def check_plan(plan):
 need(plan['version']==VERSION and plan['source_sha256']==SOURCE_SHA and plan['reference_source_sha256']==REFERENCE_SHA,'PRECOMPUTED_GAIT_SOURCE_MISMATCH')
 need(plan['edit_scope']=='FOUR_FRONT_JOINT_CHANNELS_ONLY','PLAN_SCOPE_CHANGED')
 rows=plan['degree_offsets']
 need(set(rows)=={'1_LF','1_RF','2_LF','2_RF'},'PLAN_CLIP_LEG_SET_CHANGED')
 for k,data in rows.items():
  need(set(data)==set(str(i) for i in range(32)),'PLAN_MISSING_FULL_STRIDE:'+k)
  for f,v in data.items():
   need(len(v)==2 and all(isinstance(x,(float,int)) and math.isfinite(x) and abs(x)<=85 for x in v), 'PLAN_DEGREE_OUT_OF_BOUNDS:'+k+':'+f)
 return plan

def build(source,plan,base,previous,progress=None):
 need(sha(source)==SOURCE_SHA,'SOURCE_CANONICAL_V0615_HASH_CHANGED')
 plan=check_plan(plan)
 doc,oldbin=previous.parse_glb(source);names=structure(doc,previous)
 originals=[previous.tracks(doc,oldbin,a,base) for a in doc['animations'][3:]]
 binary=bytearray(oldbin)
 for stage,tr in enumerate(originals,1):
  for label,bones in BONES.items():
   for name in bones:
    node=names[name];key=(node,'rotation')
    need(key in tr and len(tr[key]['rows'])==FRAMES,'MISSING_FRONT_ANIMATION_TRACK:'+name)
    rows=[]
    for f in range(FRAMES):
     deg=plan['degree_offsets'][f'{min(stage,2)}_{label}'][str(f%32)][bones.index(name)]
     q=tr[key]['rows'][f]
     rows.append(norm(base.qmul(q,base.axisq((1.,0.,0.),deg))))
    accessor=base.emit_accessor(doc,binary,rows,5126,'VEC4')
    tr[key]['sampler']['output']=accessor
  doc['animations'][stage+2].setdefault('extras',{})['replGroundRelativeV0616']={
   'source_sha256':SOURCE_SHA,'reference_sha256':REFERENCE_SHA,
   'controlled_bones':sorted(EDITED),
   'full_stance_and_swing':True,'physical_revalidation':'REQUIRED_BEFORE_GIT_COMMIT',
   'human_visual_verdict':'PENDING'}
  if progress:progress('STAGE_'+str(stage)+'_GROUND_RELATIVE_FOUR_BEAT_WRITTEN')
 doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{}).update({
  'version':VERSION,'mode':'FULL_GROUND_RELATIVE_FOREHOOF_TRAJECTORY',
  'source_visual_status':'V0615_REJECTED_KICKING','humanVisualVerdict':'PENDING'})
 output=base.glb_encode(doc,bytes(binary))
 report=verify(source,output,plan,base,previous)
 report.update({'version':VERSION,'source_sha256':SOURCE_SHA,'output_sha256':sha(output),
   'trajectory_sha256':sha(json.dumps(plan,sort_keys=True).encode()),
   'controlled_bones':sorted(EDITED),
   'profile':{'body_roll_degrees':.3,'body_settle':.0016,'motion':'UNCHANGED_FROM_V0615'},
   'loaded_shoulder_drop':{'2':'PRESERVED_V0615','3':'PRESERVED_V0615'},
   'rig_audit':{'joint_count':50,'node_count':53,'only_edited_bones':sorted(EDITED)},
   'human_visual_acceptance':'PENDING'})
 return output,report

def verify(source,output,plan,base,previous):
 original,oldbin=previous.parse_glb(source)
 doc,binary=previous.parse_glb(output);names=structure(doc,previous)
 root=names['Bone_000'];structure(original,previous)
 for k in ('nodes','meshes','skins','materials','textures','images','scenes'):
  need(original.get(k)==doc.get(k),'PROTECTED_GLTF_COMPONENT_CHANGED:'+k)
 need(original['animations'][:3]==doc['animations'][:3],'NON_WALK_CLIP_CHANGED')
 need(binary[:len(oldbin)]==oldbin,'ORIGINAL_BINARY_CONTENT_CHANGED')
 a=[previous.tracks(original,oldbin,c,base) for c in original['animations'][3:]]
 b=[previous.tracks(doc,binary,c,base) for c in doc['animations'][3:]]
 witnesses={lab:previous.hoof_witnesses(doc,binary,base,lab) for lab in ('LF','RF','LH','RH')}
 report={'front_hoof_clearance':{},'ground_contact':{},'max_stance_vertex_delta':0.,
   'tested_physical_frames':0,'tested_physical_half_frames':0,'maximum_front_joint_step_degrees':0.,
   'maximum_swing_forward_step':0.,'maximum_backward_swing_step':0.,
   'clip':'FULL_GROUND_RELATIVE_97_FRAME_VERTEX_CHECK',
   'support_roll_and_vertical_sag':'PRESERVED_V0615'}
 original_root=tuple(doc['nodes'][root].get('translation',(0.,0.,0.)))
 def points(tr,lab,frame):
  doc['nodes'][root]['translation']=list(tr[(root,'translation')]['rows'][frame])
  world=base.world_matrices(doc,pose(tr,frame))
  mats=base.skin_matrices(doc,binary,world)
  xyz,joints,weights,ids=witnesses[lab]
  return [base.deform_vertex(xyz[i],joints[i],weights[i],mats) for i in ids]
 def fstate(pts):
  return {'bottom':min(p[1] for p in pts),'z':sum(p[2] for p in pts)/len(pts)}
 try:
  for stage,(oldtr,newtr) in enumerate(zip(a,b),1):
   need(set(oldtr)==set(newtr),'ANIMATION_CHANNEL_SET_CHANGED')
   for key,old in oldtr.items():
    bone=doc['nodes'][key[0]].get('name')
    if not (key[1]=='rotation' and bone in EDITED):
     need(old['rows']==newtr[key]['rows'],'PROTECTED_ANIMATION_TRACK_CHANGED:'+str((stage,bone,key[1])))
   rt=newtr[(root,'translation')]['rows'];need(len(rt)==FRAMES,'ROOT_FRAME_COUNT_CHANGED')
   need(abs(rt[-1][2]-rt[0][2]-.96)<1e-6,'WORLD_FORWARD_TRAVEL_CHANGED')
   for lab in ('LF','RF'):
    qrows=[newtr[(names[n],'rotation')]['rows'] for n in BONES[lab]]
    for f in range(FRAMES-1):
     for rows in qrows:
      d=min(1.,abs(dot(rows[f],rows[f+1])))
      delta=2*math.degrees(math.acos(d))
      report['maximum_front_joint_step_degrees']=max(report['maximum_front_joint_step_degrees'],delta)
      need(delta<=18.25,'FRONT_JOINT_FRAME_KICK:'+str((stage,lab,f,round(delta,4))))
    states=[]
    for f in range(FRAMES):
     pts=points(newtr,lab,f);s=fstate(pts);states.append(s)
     report['tested_physical_frames']+=1
     _,on=phase(lab,f)
     if on:
      need(-.006<=s['bottom']<=.023,'FOOT_NOT_AT_PLANTED_GROUND:'+str((stage,lab,f,round(s['bottom'],5))))
     else:
      need(.0012<=s['bottom']<=.105,'AIRBORNE_HOOF_CLIPS_OR_PRANCES:'+str((stage,lab,f,round(s['bottom'],5))))
    # glTF LINEAR rotations interpolate by slerp. Validating integer keyframes
    # alone allowed prior frame-to-frame kinks to hide in the renderer.
    for f in range(FRAMES-1):
     midrot={}
     for (node,path),data in newtr.items():
      if path=='rotation':midrot[node]=slerp(data['rows'][f],data['rows'][f+1],.5)
     ta=newtr[(root,'translation')]['rows'][f]
     tb=newtr[(root,'translation')]['rows'][f+1]
     doc['nodes'][root]['translation']=[(x+y)*.5 for x,y in zip(ta,tb)]
     wm=base.world_matrices(doc,midrot)
     skin=base.skin_matrices(doc,binary,wm)
     xyz,joints,weights,ids=witnesses[lab]
     vm=[base.deform_vertex(xyz[i],joints[i],weights[i],skin) for i in ids]
     state=fstate(vm)
     _,on=phase(lab,f+.5)
     if on:
      need(-.0065<=state['bottom']<=.024,
       'MIDFRAME_PLANTED_HOOF_NOT_ON_GROUND:'+str((stage,lab,f,round(state['bottom'],6))))
     else:
      need(.0005<=state['bottom']<=.106,
       'MIDFRAME_AIRBORNE_HOOF_CLIPS:'+str((stage,lab,f,round(state['bottom'],6))))
     za,zb=states[f]['z'],states[f+1]['z']
     need(min(za,zb)-.007<=state['z']<=max(za,zb)+.007,
      'MIDFRAME_HOOF_KICK_OVERSHOOT:'+str((stage,lab,f,round(state['z'],6))))
     report['tested_physical_half_frames']+=1
    for k in range(3):
     # Each stance contact patch must remain anchored in world space.
     windows=([list(range(8+k*32,28+k*32))] if lab=='LF' else
       [list(range(k*32,min(k*32+12,97))),list(range(24+k*32,min(32+k*32,97)))])
     for fs in windows:
      fs=[f for f in fs if f<FRAMES]
      if len(fs)<2:continue
      slip=max(s['z'] for s in (states[f] for f in fs))-min(s['z'] for s in (states[f] for f in fs))
      need(slip<=.014,'STANCE_WORLD_Z_SLIP:'+str((stage,lab,k,round(slip,5))))
      report['max_stance_vertex_delta']=max(report['max_stance_vertex_delta'],slip)
    for k in range(3):
     # Test the actual world-space toe-off, flight, touchdown path, not just peak Y.
     if lab=='LF':
      fs=list(range(27+k*32,min(8+(k+1)*32+1,FRAMES)))
     else:fs=list(range(11+k*32,min(25+k*32,FRAMES)))
     for i,j in zip(fs,fs[1:]):
      dz=states[j]['z']-states[i]['z']
      report['maximum_swing_forward_step']=max(report['maximum_swing_forward_step'],dz)
      report['maximum_backward_swing_step']=min(report['maximum_backward_swing_step'],dz)
      need(-.006<=dz<=.060,'UNNATURAL_KICK_OR_REVERSE:'+str((stage,lab,i,j,round(dz,6))))
    flying=[states[f]['bottom'] for f in range(32) if not phase(lab,f)[1]]
    peak=max(flying);lowest=min(flying)
    need(.056<=peak<=.101,'FRONT_HOOF_LIFT_NOT_LOW_WALK:'+str((stage,lab,peak)))
    report['front_hoof_clearance'][f'{stage}_{lab}']={
      'verified_peak':round(peak,6),'min_swing':round(lowest,6),
      'forward_reversal_limit':-.006,'max_step_limit':.060}
    report['ground_contact'][f'{stage}_{lab}']={
      'first_stride_planted_y_min':round(min(states[f]['bottom'] for f in range(32) if phase(lab,f)[1]),6),
      'first_stride_planted_y_max':round(max(states[f]['bottom'] for f in range(32) if phase(lab,f)[1]),6)}
   for lab in ('LH','RH'):
    # Rear hooves are a hard preservation lock; no hidden retargeting.
    for f in range(FRAMES):
     before=points(oldtr,lab,f);after=points(newtr,lab,f)
     need(len(before)==len(after),'REAR_WITNESS_SET_CHANGED')
     delta=max(math.dist(p,q) for p,q in zip(before,after))
     need(delta<.00004,'REAR_PHYSICAL_MOTION_CHANGED:'+str((stage,lab,f,delta)))
     report['tested_physical_frames']+=1
 finally:
  doc['nodes'][root]['translation']=list(original_root)
 need(report['tested_physical_frames']==1164 and report['tested_physical_half_frames']==576,'PHYSICAL_FRAME_COVERAGE_NOT_COMPLETE')
 return report
