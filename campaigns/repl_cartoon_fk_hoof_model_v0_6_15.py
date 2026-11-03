#!/usr/bin/env python3
"""Repl 0.6.15. Apply precomputed, measured motion to ONE pinned canonical GLB.

No speculative run-time solver; every angle in trajectory.json was selected with
actual skinned hoof vertices from SHA-pinned v0.6.10 model and independently
verified again after writing. No side projects, alternate GLB assets, toe edits,
rear-track edits or changes to forward-root displacement.
"""
from __future__ import annotations
import hashlib,json,math

VERSION='0.6.15';CANON='assets/repl/Repl.glb'
SOURCE_SHA='976d8f2b3da32a01bb99c5dfbce00bc28df2db702836a0ec8337eda1573137ab'
FRAMES=97;PERIOD=32;STANCE=.62;STEP=.04;STRIDE=1.28;TRAVEL=.96
FRONT={
 'LF':{'phase':.25,'shoulder':'Bone_015','middle':'Bone_014'},
 'RF':{'phase':.75,'shoulder':'Bone_021','middle':'Bone_020'},
}
FOUR={'LH':0.,'LF':.25,'RH':.5,'RF':.75}
EDITED={s[k] for s in FRONT.values() for k in ('shoulder','middle')}
TARGET_MIN=.245;TARGET_MAX=.335
# Ground derives from verified original rest-sole Y=0 (4.2e-6 skin error).
# This is not a freely shifting per-frame planted hoof anchor.
GROUND_Y=0.;MIN_SWING_Y=.0035;MAX_PEAK_Y=.101
MAX_STANCE_VERTEX_DISPLACEMENT=.014
MAX_ROTATION_STEP_DEG=65.
class Blocked(RuntimeError):pass
def need(test,what):
 if not test:raise Blocked(what)
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(q):
 v=math.sqrt(sum(x*x for x in q));need(v>1e-10,'INVALID_QUATERNION');return tuple(a/v for a in q)
def phase(label,frame):
 u=((frame*STEP)/STRIDE-FOUR[label])%1.
 if u>1-1e-8:u=0.
 return u,u<STANCE
def weight(label,frame):
 u,on=phase(label,frame)
 return math.sin(math.pi*u/STANCE)**2 if on else 0.
def point(world,n):return (world[n][3],world[n][7],world[n][11])
def pose(track,frame):return {n:tuple(v['rows'][frame]) for (n,path),v in track.items() if path=='rotation'}
def support_body(base,original,translation,frame,stage,settings,sign):
 r=dict(original);t=list(translation)
 if stage>1:
  lf=weight('LF',frame);rf=weight('RF',frame)
  t[1]-=settings['body_settle']*max(lf,rf)
  root=settings['_root']
  # Measured sign lowers the supporting shoulder, not an assumed local axis.
  r[root]=norm(base.qmul(r[root],base.axisq((0.,0.,1.),sign*settings['body_roll_degrees']*(lf-rf))))
 return r,tuple(t)
def actual_min(base,doc,binary,root,translation,rot,parts,detail=False):
 doc['nodes'][root]['translation']=list(translation)
 world=base.world_matrices(doc,rot);mats=base.skin_matrices(doc,binary,world)
 xyz,joints,weights,ids=parts
 vv=[base.deform_vertex(xyz[i],joints[i],weights[i],mats) for i in ids]
 return vv if detail else min(v[1] for v in vv)
def body_sign(base,doc,names,current):
 root=names['Bone_000'];fr=0;p=pose(current,fr)
 doc['nodes'][root]['translation']=list(current[(root,'translation')]['rows'][fr])
 old=base.world_matrices(doc,p)
 p[root]=norm(base.qmul(p[root],base.axisq((0.,0.,1.),.5)))
 new=base.world_matrices(doc,p)
 left=names['Bone_015'];right=names['Bone_021']
 dd=(point(new,left)[1]-point(old,left)[1])-(point(new,right)[1]-point(old,right)[1])
 need(abs(dd)>.0002,'LOADED_ROLL_EFFECT_NOT_IDENTIFIABLE')
 return 1. if dd<0 else -1.
def structure(doc,previous):
 names=previous.inspect_source(doc)
 need(len(doc['nodes'])==53 and len(doc['skins'][0]['joints'])==50 and len(doc['animations'])==6,'CANONICAL_RIG_STRUCTURE_CHANGED')
 pa={child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
 for label,s in FRONT.items():
  upper=s['shoulder'];middle=s['middle'];distal='Bone_013' if label=='LF' else 'Bone_019'
  need(pa[names[middle]]==names[upper] and pa[names[distal]]==names[middle], 'MEASURED_CHAIN_CHANGED:'+label)
 return names

def check_trajectory(data,names):
 need(data.get('version')==VERSION and data.get('source_sha256')==SOURCE_SHA,'TRAJECTORY_NOT_PINNED_TO_CANONICAL_SOURCE')
 need(data.get('ground_y')==GROUND_Y and data.get('stage_3_reuse_stage_2') is True,'TRAJECTORY_CONTEXT_CHANGED')
 need(data.get('body_settle')==.0016 and data.get('body_roll_degrees')==.30,'WEIGHT_PROFILE_CHANGED')
 need(set(data['angle_offsets_degrees'])=={'1_LF','1_RF','2_LF','2_RF'},'TRAJECTORY_STAGE_MAP_INVALID')
 for stage in (1,2):
  for label in FRONT:
   rows=data['angle_offsets_degrees'][f'{stage}_{label}']
   wanted={str(f) for f in range(PERIOD) if not phase(label,f)[1]}
   need(set(rows)==wanted,'SWING_FRAME_COVERAGE_MISMATCH:'+str((stage,label)))
   for fr,v in rows.items():
    need(len(v)==2 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in v),'TRAJECTORY_VALUES_INVALID')
    need(-55.001<=v[0]<=55.001 and -32.001<=v[1]<=40.001,'MEASURED_CONTROL_BOUND_EXCEEDED')
 return data

def build(source,plan,base,previous,progress=None):
 need(sha(source)==SOURCE_SHA,'PINNED_CANONICAL_SOURCE_SHA_MISMATCH')
 doc,oldbin=previous.parse_glb(source);names=structure(doc,previous)
 plan=check_trajectory(plan,names);root=names['Bone_000']
 oldroot=list(doc['nodes'][root].get('translation',(0,0,0)))
 original=[previous.tracks(doc,oldbin,a,base) for a in doc['animations'][3:]]
 binary=bytearray(oldbin)
 data={'_root':root,**plan}
 sign=body_sign(base,doc,names,original[1])
 doc['nodes'][root]['translation']=list(oldroot)
 changed=0
 try:
  for stage,tr in enumerate(original,1):
   change={names[n]:[] for n in EDITED}
   if stage>1:change[(root,'rotation')]=[];change[(root,'translation')]=[]
   for f in range(FRAMES):
    fr=f%PERIOD
    r=pose(tr,f);t=tr[(root,'translation')]['rows'][f]
    r,t=support_body(base,r,t,fr,stage,data,sign)
    for label,s in FRONT.items():
     _,on=phase(label,fr)
     if on:continue
     angular=plan['angle_offsets_degrees'][f'{min(stage,2)}_{label}'][str(fr)]
     for name,deg in zip((s['shoulder'],s['middle']),angular):
      node=names[name]
      r[node]=norm(base.qmul(r[node],base.axisq((1.,0.,0.),deg)))
    for n in EDITED:change[names[n]].append(r[names[n]])
    if stage>1:
     change[(root,'rotation')].append(r[root]);change[(root,'translation')].append(t)
   for key,rows in change.items():
    path='rotation' if isinstance(key,int) else key[1]
    node=key if isinstance(key,int) else key[0]
    need(len(rows)==FRAMES,'WRONG_FRAME_COUNT:'+str(key))
    need((node,path) in tr,'EXPECTED_CANONICAL_TRACK_MISSING:'+str(key))
    arr=base.emit_accessor(doc,binary,rows,5126,'VEC3' if path=='translation' else 'VEC4')
    tr[(node,path)]['sampler']['output']=arr;changed+=1
   doc['animations'][stage+2].setdefault('extras',{})['ownerMeasuredLowWalk']={
    'version':VERSION,'source_sha256':SOURCE_SHA,'source':'PHYSICAL_SKIN_VERTEX_SOLVE',
    'front_control_bones':sorted(EDITED),'body_root_settle':data['body_settle'] if stage>1 else 0.,
    'body_roll_degrees':data['body_roll_degrees'] if stage>1 else 0.,
    'human_review':'PENDING'}
   if progress:progress('STAGE_'+str(stage)+'_PRECOMPUTED_REAL_RIG_TRAJECTORY_WRITTEN')
  doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{}).update({
   'version':VERSION,'mode':'MEASURED_LOW_FRONT_WALK','humanVisualVerdict':'PENDING'})
  doc['nodes'][root]['translation']=list(oldroot)
  result=base.glb_encode(doc,bytes(binary))
 finally:
  doc['nodes'][root]['translation']=list(oldroot)
 report=verify(source,result,plan,base,previous,sign)
 report.update({'version':VERSION,'source_sha256':SOURCE_SHA,'output_sha256':sha(result),
  'changed_channels':changed,'solver':'MEASURED_SOURCE_LOCKED_TRAJECTORY',
  'profile':{'body_settle':.0016,'body_roll_degrees':.30,'roll_sign':sign},
  'human_visual_acceptance':'PENDING', 'rig_audit':{'joint_count':50,'node_count':53,
  'edited_front_bones':sorted(EDITED),'ground_reference_y':GROUND_Y}})
 return result,report

def verify(source,output,plan,base,previous,sign):
 old,oldbin=previous.parse_glb(source);new,newbin=previous.parse_glb(output)
 names=structure(new,previous);root=names['Bone_000'];structure(old,previous)
 for k in ('nodes','meshes','skins','materials','textures','images'):
  need(old.get(k)==new.get(k),'LOCKED_SOURCE_COMPONENT_CHANGED:'+k)
 need(old['animations'][:3]==new['animations'][:3],'LOCKED_NONWALK_CLIPS_CHANGED')
 need(newbin[:len(oldbin)]==oldbin,'ORIGINAL_BINARY_PREFIX_CHANGED')
 a=[previous.tracks(old,oldbin,clip,base) for clip in old['animations'][3:]]
 b=[previous.tracks(new,newbin,clip,base) for clip in new['animations'][3:]]
 patches={label:previous.hoof_witnesses(new,newbin,base,label) for label in FOUR}
 for label,part in patches.items():need(len(part[3])>=100,'SKIN_PATCH_TOO_SMALL:'+label)
 saved=list(new['nodes'][root].get('translation',(0,0,0)))
 report={'front_hoof_clearance':{},'frame_clearance':{},'loaded_shoulder_drop':{},
  'tested_physical_frames':0,'max_stance_vertex_delta':0.,'max_joint_step_deg':0.,'stages':{}}
 try:
  for stage,(oldtr,newtr) in enumerate(zip(a,b),1):
   need(set(oldtr)==set(newtr),'CANONICAL_TRACK_KEYS_CHANGED')
   for key,t0 in oldtr.items():
    n,path=key;name=new['nodes'][n].get('name')
    mutable=(path=='rotation' and name in EDITED) or (stage>1 and n==root and path in ('rotation','translation'))
    if not mutable:need(t0['rows']==newtr[key]['rows'],'PROTECTED_ANIM_TRACK_EDIT:'+str((stage,name,path)))
   rr0=oldtr[(root,'translation')]['rows'];rr1=newtr[(root,'translation')]['rows']
   need(len(rr1)==FRAMES,'ROOT_LENGTH_NOT_97')
   need(abs(rr1[-1][2]-rr1[0][2]-TRAVEL)<1e-5,'ROOT_TRAVEL_NOT_0_96')
   need(all(abs(x[2]-y[2])<1e-7 and abs(x[0]-y[0])<1e-7 for x,y in zip(rr0,rr1)),
    'WORLD_ROOT_FORWARD_OR_LATERAL_PATH_CHANGED')
   for name in EDITED:
    t0=oldtr[(names[name],'rotation')]['rows'];t1=newtr[(names[name],'rotation')]['rows']
    for f in range(PERIOD):
     label='LF' if name in ('Bone_015','Bone_014') else 'RF'
     if phase(label,f)[1]:need(max(abs(a-b) for a,b in zip(t0[f],t1[f]))<2e-6,'FRONT_STANCE_LOCAL_ROTATION_CHANGED')
    for f in range(FRAMES-1):
     q=t1[f];p=t1[f+1];dot=min(1.,abs(sum(x*y for x,y in zip(q,p))))
     report['max_joint_step_deg']=max(report['max_joint_step_deg'],2*math.degrees(math.acos(dot)))
   for label in FOUR:
    peak=-1e9; low=1e9;oldpeak=-1e9
    for f in range(FRAMES):
     fr=f%PERIOD;_,on=phase(label,fr)
     pp0=pose(oldtr,f);pp1=pose(newtr,f)
     h0=actual_min(base,new,newbin,root,rr0[f],pp0,patches[label])
     h1=actual_min(base,new,newbin,root,rr1[f],pp1,patches[label])
     report['tested_physical_frames']+=1
     if on:
      if stage==1:need(abs(h1-h0)<3e-5,'STAGE1_STANCE_CHANGED:'+label)
      else:
       p0=actual_min(base,new,newbin,root,rr0[f],pp0,patches[label],detail=True)
       p1=actual_min(base,new,newbin,root,rr1[f],pp1,patches[label],detail=True)
       maxdelta=max(math.dist(x,y) for x,y in zip(p0,p1))
       report['max_stance_vertex_delta']=max(report['max_stance_vertex_delta'],maxdelta)
       need(maxdelta<MAX_STANCE_VERTEX_DISPLACEMENT,'BODY_SAG_MOVED_PLANTED_HOOF:'+str((stage,label,fr,round(maxdelta,5))))
      continue
     if label in FRONT:
      peak=max(peak,h1);low=min(low,h1);oldpeak=max(oldpeak,h0)
      need(h1>=MIN_SWING_Y-1e-4,'SWING_REAL_MESH_BELOW_GROUND:'+str((stage,label,f,round(h1,6))))
      need(h1<=MAX_PEAK_Y+1e-4,'SWING_NEW_PRANCE_TOO_HIGH:'+str((stage,label,f,round(h1,6))))
      if f<32:report['frame_clearance'][f'{stage}_{label}_{fr}']=round(h1,6)
    if label in FRONT:
     ratio=peak/oldpeak
     need(TARGET_MIN<=ratio<=TARGET_MAX,'FULL_CYCLE_PEAK_RATIO_FAILED:'+str((stage,label,ratio)))
     report['front_hoof_clearance'][f'{stage}_{label}']={'baseline_peak':round(oldpeak,6),
      'verified_peak':round(peak,6),'verified_ratio':round(ratio,6),'min_swing':round(low,6)}
   if stage>1:
    strongest=None
    for f in range(PERIOD):
     lf=weight('LF',f);rf=weight('RF',f)
     if abs(lf-rf)<.45:continue
     new['nodes'][root]['translation']=list(rr0[f]);before=base.world_matrices(new,pose(oldtr,f))
     new['nodes'][root]['translation']=list(rr1[f]);after=base.world_matrices(new,pose(newtr,f))
     left=names['Bone_015'];right=names['Bone_021']
     dleft=point(after,left)[1]-point(before,left)[1]
     dright=point(after,right)[1]-point(before,right)[1]
     differential=(dright-dleft) if lf>rf else (dleft-dright)
     loaded=-dleft if lf>rf else -dright
     if strongest is None or differential>strongest[0]:strongest=(differential,loaded,f)
    need(strongest is not None and strongest[0]>.0003 and strongest[1]>.0005,
      'NO_MEASURED_LOADED_CORNER_SETTLE:'+str((stage,strongest)))
    report['loaded_shoulder_drop'][str(stage)]={'differential_y':round(strongest[0],6),
       'supported_side_drop_y':round(strongest[1],6),'frame':strongest[2]}
   report['stages'][str(stage)]='PASS'
 finally:new['nodes'][root]['translation']=saved
 need(report['max_joint_step_deg']<MAX_ROTATION_STEP_DEG,'FORELEG_QUATERNION_DISCONTINUITY:'+str(report['max_joint_step_deg']))
 return report
