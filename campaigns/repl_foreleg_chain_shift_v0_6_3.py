#!/usr/bin/env python3
"""Repl v0.6.3: reverse both foreleg hinge directions, KEEP joint levels.

The v0.6.2 bone level is correct, but its hinge signs were reversed.
This version constrains upper Bone_014/020 BACKWARD and lower Bone_013/019
FORWARD per owner's forehoof observation. The stance and
all hind, torso, tail, mane, root and accepted animation tracks are intact.
The full real skinned forelimb and hoof target is checked before release.
"""
from __future__ import annotations
import hashlib,json,math,struct
from fore_constraints import optimize,poles,clamp

VERSION='0.6.3'
CANON='assets/repl/Repl.glb'
SOURCE_SHA='6a519d49d21dae6048553edc0aa09b340b8ca13979750a4abc1631a48e5c019f'
SOURCE_BLOB='6078f4f74069891bf4140e7925fe3e53e66569fa'
FRAMES=97; PER_STRIDE=32; STRIDE=1.28; STEP=STRIDE/PER_STRIDE
DURATION=3*STRIDE; ROOT_TRAVEL=.96; STANCE=.62
WALK_NAMES=('REPL_WALK_01_FORWARD_FOUR_BEAT_IK',
 'REPL_WALK_02_FORWARD_BODY_WEIGHT_TRANSFER',
 'REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED')
LEGS={
 'LF':{'phase':.25,'ancestor':'Bone_016',
       'bones':('Bone_015','Bone_014','Bone_013','Bone_012'),
       'upper':'Bone_014','lower':'Bone_013','end':'Bone_011'},
 'RF':{'phase':.75,'ancestor':'Bone_022',
       'bones':('Bone_021','Bone_020','Bone_019','Bone_018'),
       'upper':'Bone_020','lower':'Bone_019','end':'Bone_017'},
}
DRIVEN=set(n for d in LEGS.values() for n in d['bones'])

class Blocked(RuntimeError):pass
def need(condition,code):
 if not condition:raise Blocked(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def gitblob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def parse_glb(data):
 need(len(data)>28 and data[:4]==b'glTF','BAD_GLB_MAGIC')
 _magic,v,l=struct.unpack_from('<4sII',data,0)
 need(v==2 and l==len(data),'BAD_GLB_HEADER')
 n,t=struct.unpack_from('<I4s',data,12)
 need(t==b'JSON','BAD_JSON_CHUNK')
 p=20+n
 m,t=struct.unpack_from('<I4s',data,p)
 need(t==b'BIN\0' and p+8+m==len(data),'BAD_BIN_CHUNK')
 return json.loads(data[20:p]),data[p+8:]
def pos(world,n):return tuple(world[n][i] for i in (3,7,11))
def qnorm(q):
 z=math.sqrt(sum(x*x for x in q));need(z>1e-10,'INVALID_QUATERNION')
 return tuple(x/z for x in q)
def axis_local_world_x(world,n):
 m=world[n];a=(m[0],m[1],m[2]);z=math.sqrt(sum(v*v for v in a))
 need(z>1e-7,'BAD_WORLD_X_AXIS');return tuple(v/z for v in a)
def angle_relative(q,reference,axis,base):
 inv=(-reference[0],-reference[1],-reference[2],reference[3])
 r=base.qmul(inv,qnorm(q))
 angle=math.degrees(2*math.atan2(sum(v*w for v,w in zip(r[:3],axis)),r[3]))
 return (angle+180)%360-180
def ease(x):
 x=clamp(x,0.,1.);return x*x*(3.-2.*x)
def phase_at(offset,t):
 u=(t/STRIDE-offset)%1.
 if abs(u-1.)<1e-8:u=0.
 return u, u<STANCE

def sample_tracks(doc,binary,clip,base):
 mapping={}
 for ch in clip['channels']:
  sm=clip['samplers'][ch['sampler']]
  need(sm['interpolation']=='LINEAR','UNEXPECTED_NONLINEAR_SAMPLER')
  key=(ch['target']['node'],ch['target']['path'])
  need(key not in mapping,'DUPLICATE_ANIMATION_TRACK')
  times=base.accessor(doc,binary,sm['input'])
  val=base.accessor(doc,binary,sm['output'])
  need(len(times)==len(val)==FRAMES,'BAD_FRAME_COUNT')
  need(all(abs(t[0]-i*STEP)<2e-6 for i,t in enumerate(times)),'FRAME_TIMES_MODIFIED')
  mapping[key]={'values':val,'sampler':sm,'times':times}
 return mapping

def make_correction(source,base,progress=None):
 need(sha(source)==SOURCE_SHA,'SOURCE_NOT_EXACT_v0.6.2')
 doc,original_bin=parse_glb(source)
 need(len(doc['nodes'])==53 and len(doc['skins'][0]['joints'])==50,'RIG_COUNT_MISMATCH')
 need(len(doc['animations'])==6,'ANIMATION_COUNT_CHANGED')
 for i,name in enumerate(WALK_NAMES):
  need(doc['animations'][i+3]['name']==name,'WALK_CLIP_CHANGED')
 names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
 parents={child:i for i,n in enumerate(doc['nodes']) for child in n.get('children',[])}
 for leg in LEGS.values():
  chain=[leg['ancestor'],*leg['bones'],leg['end']]
  for item in chain:need(item in names,'MISSING_LEG_BONE:'+item)
  for a,b in zip(chain,chain[1:]):
   need(parents.get(names[b])==names[a],'FORELEG_CHAIN_NOT_ONE_LEVEL_DOWN:'+str((a,b)))
  need(chain[2]==leg['upper'] and chain[3]==leg['lower'],'SHIFTED_HINGE_MAPPING_WRONG')
 root=names['Bone_000'];root_original=tuple(doc['nodes'][root].get('translation',(0.,0.,0.)))
 old_nodes=json.dumps(doc['nodes'],sort_keys=True)
 old_skins=json.dumps(doc['skins'],sort_keys=True)
 old_mesh=json.dumps(doc['meshes'],sort_keys=True)
 old_clips=json.dumps(doc['animations'][:3],sort_keys=True)
 before=[sample_tracks(doc,original_bin,c,base) for c in doc['animations'][3:]]
 for tr in before:
  need((root,'translation') in tr,'MISSING_ROOT_TRAVEL')
  for leg in LEGS.values():
   need((names[leg['ancestor']],'rotation') in tr,'MISSING_UPPER_UNMODIFIED_BONE')
   for b in leg['bones']:
    need((names[b],'rotation') in tr,'MISSING_DRIVEN_BONE:'+b)
   need((names[leg['end']],'rotation') not in tr,
        'TERMINAL_BONE_TRACK_CHANGED__REINSPECT_BEFORE_EDIT')
 new_bin=bytearray(original_bin)
 results={};observations=[];sample_count=0
 try:
  for stage in (1,2):
   tr=before[stage-1]
   if progress:progress('STAGE_'+str(stage)+'_REVERSED_FORELEG_SOLVER_STARTED')
   stage_data={}
   for label,leg in LEGS.items():
    driven=[names[n] for n in leg['bones']]
    end=names[leg['end']]
    original_quats={n:tr[(n,'rotation')]['values'] for n in driven}
    rows={n:[] for n in driven}
    for frame in range(PER_STRIDE):
     t=frame*STEP
     doc['nodes'][root]['translation']=list(tr[(root,'translation')]['values'][frame])
     pose={node:v['values'][frame] for (node,mode),v in tr.items()
           if mode=='rotation' and node not in driven}
     original_pose=dict(pose)
     for n in driven:original_pose[n]=original_quats[n][frame]
     beforeworld=base.world_matrices(doc,original_pose)
     # Preserve the physical end-of-hoof witness, including any gait-stage
     # toe pitch. Do not guess a new target using a mislocated bone origin.
     target=pos(beforeworld,end)
     u,stance=phase_at(leg['phase'],t)
     if stance:
      for n in driven:rows[n].append(tuple(original_quats[n][frame]))
      continue
     s=(u-STANCE)/(1.-STANCE)
     restworld=base.world_matrices(doc,pose)
     points=[pos(restworld,names[name]) for name in (*leg['bones'],leg['end'])]
     links=[points[0]]+[tuple(b-a for a,b in zip(points[i],points[i+1])) for i in range(4)]
     restq=[base.node_rotation(doc['nodes'][n]) for n in driven]
     axes=[axis_local_world_x(restworld,n) for n in driven]
     oldq=[angle_relative(original_quats[n][frame],restq[k],axes[k],base)
           for k,n in enumerate(driven)]
     q,_loss=optimize(links,target,s,oldq)
     proposal=dict(pose)
     fade=ease(min(1.,s/.115,(1.-s)/.115))
     for k,n in enumerate(driven):
      solved=qnorm(base.qmul(restq[k],base.axisq(axes[k],q[k])))
      proposal[n]=base.quat_slerp(original_quats[n][frame],solved,fade)
     world=base.world_matrices(doc,proposal)
     points=[pos(world,names[name]) for name in (*leg['bones'],leg['end'])]
     upper,lower=poles(points)
     error=math.dist(points[-1],target)
     need(error<.010,'SHIFTED_FORELEG_TARGET_ERROR:'+label+':'+str((frame,error)))
     if .25<=s<=.75:
      need(upper<-.010 and lower>.040,
           'SHIFTED_POLE_SIDE_INVALID:'+label+':'+str((frame,upper,lower)))
     for n in driven:rows[n].append(proposal[n])
     observations.append({'stage':stage,'leg':label,'frame':frame,
        'swing':round(s,4),'upper_backward':upper,
        'lower_forward':lower,'toe_marker_error':error,
        'joint_angles_degrees':q})
     sample_count+=1
    for n in driven:
     rows[n]=rows[n]*3+[rows[n][0]]
     need(len(rows[n])==FRAMES,'WRONG_CLIP_LOOP_LENGTH')
    stage_data[label]=rows
   results[stage]=stage_data
   if progress:progress('STAGE_'+str(stage)+'_REVERSED_FORELEG_SOLVER_PASS')
  # Stage three has identical leg, trunk, and root tracks to stage two;
  # only mane/tail secondary tracks differ. The forward traveling root remains.
  results[3]=results[2]
  changed=0
  for stage in (1,2,3):
   tr=before[stage-1]
   for label,rows in results[stage].items():
    for n,quats in rows.items():
     newacc=base.emit_accessor(doc,new_bin,quats,5126,'VEC4')
     tr[(n,'rotation')]['sampler']['output']=newacc
     changed+=1
   doc['animations'][stage+2].setdefault('extras',{})['ownerCorrectedForelegHierarchy']={
      'version':VERSION,'upperBackward':{'LF':'Bone_014','RF':'Bone_020'},
      'lowerForward':{'LF':'Bone_013','RF':'Bone_019'},
      'previousWrongUpperPole':'FORWARD',
      'previousWrongLowerPole':'BACKWARD',
      'worldTravel':'unchanged +Z, not in-place',
      'hindlegMotion':'bitwise unchanged','humanVisualAcceptance':'PENDING'}
  doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{})['version']=VERSION
  doc['asset']['extras']['replWalkCampaign']['forelegKneePole']=(
    'v0.6.3 reverses signs, unchanged joints: upper 014/020 rear, lower 013/019 front')
  doc['asset']['extras']['replWalkCampaign']['humanVisualVerdict']='PENDING'
  doc['nodes'][root]['translation']=list(root_original)
  need(json.dumps(doc['nodes'],sort_keys=True)==old_nodes,'CANONICAL_NODES_CHANGED')
  need(json.dumps(doc['skins'],sort_keys=True)==old_skins,'CANONICAL_SKIN_CHANGED')
  need(json.dumps(doc['meshes'],sort_keys=True)==old_mesh,'CANONICAL_MESH_CHANGED')
  need(json.dumps(doc['animations'][:3],sort_keys=True)==old_clips,'ORIGINAL_CLIPS_CHANGED')
  need(bytes(new_bin[:len(original_bin)])==original_bin,'OLD_ANIMATED_BUFFER_REWRITTEN')
  need(changed==24,'UNEXPECTED_TRACK_UPDATE_COUNT')
  output=base.glb_encode(doc,bytes(new_bin))
 finally:
  doc['nodes'][root]['translation']=list(root_original)
 report=validate(source,output,base)
 report['solver_swing_samples']=sample_count
 report['track_changes_expected']=changed
 report['provenance']='pinned production owner-rejected v0.6.2 canonical model'
 return output,report

def validate(old,new,base):
 before,b0=parse_glb(old);after,b1=parse_glb(new)
 need(len(after['animations'])==6,'ANIMATION_COUNT_LOST')
 need(after['nodes']==before['nodes'] and after['skins']==before['skins']
       and after['meshes']==before['meshes'],'MODEL_STRUCTURE_CHANGED')
 need(after['animations'][:3]==before['animations'][:3],'PREVIOUS_CLIPS_CHANGED')
 need(b1[:len(b0)]==b0,'CANONICAL_BUFFER_CHANGED')
 names={n.get('name'):i for i,n in enumerate(after['nodes'])}
 oldtracks=[sample_tracks(before,b0,c,base) for c in before['animations'][3:]]
 newtracks=[sample_tracks(after,b1,c,base) for c in after['animations'][3:]]
 root=names['Bone_000'];saved=tuple(after['nodes'][root]['translation'])
 unchanged=changed=0
 max_toe_error=0.;max_stance_error=0.;max_step=0.
 max_upper=-1e9;min_lower=1e9;middle=0
 for stage in range(3):
  a=oldtracks[stage];b=newtracks[stage]
  need(set(a)==set(b),'ANIMATION_TRACK_SET_CHANGED')
  for key in a:
   if key[1]=='rotation' and after['nodes'][key[0]].get('name') in DRIVEN:
    changed+=1
   else:
    need(a[key]['values']==b[key]['values'],
         'UNAUTHORIZED_ROOT_HIND_SHOULDER_OR_SECONDARY_CHANGE:'+str(key))
    unchanged+=1
  rt=b[(root,'translation')]['values']
  need(abs(rt[-1][2]-rt[0][2]-ROOT_TRAVEL)<1e-5,
       'FORWARD_TRAVEL_REGRESSED_TO_IN_PLACE')
  for leg in LEGS.values():
   node_ids=[names[n] for n in leg['bones']]
   end=names[leg['end']]
   for frame in range(FRAMES):
    t=frame*STEP
    after['nodes'][root]['translation']=list(rt[frame])
    oldpose={n:v['values'][frame] for (n,mode),v in a.items() if mode=='rotation'}
    newpose={n:v['values'][frame] for (n,mode),v in b.items() if mode=='rotation'}
    w0=base.world_matrices(after,oldpose)
    w1=base.world_matrices(after,newpose)
    footdelta=math.dist(pos(w0,end),pos(w1,end))
    u,stance=phase_at(leg['phase'],t)
    if stance:max_stance_error=max(max_stance_error,footdelta)
    else:
     max_toe_error=max(max_toe_error,footdelta)
     s=(u-STANCE)/(1-STANCE)
     if .25<=s<=.75:
      p=[pos(w1,names[n]) for n in (*leg['bones'],leg['end'])]
      upper,lower=poles(p)
      max_upper=max(max_upper,upper);min_lower=min(min_lower,lower)
      middle+=1
   for n in node_ids:
    q=b[(n,'rotation')]['values']
    need(max(abs(x-y) for x,y in zip(q[0],q[-1]))<1e-6,
         'CYCLIC_POSE_TRACK_CHANGED')
    for x,y in zip(q,q[1:]):
     dot=abs(sum(i*j for i,j in zip(x,y)))
     ang=math.degrees(2*math.acos(clamp(dot,-1.,1.)))
     max_step=max(max_step,ang)
 after['nodes'][root]['translation']=list(saved)
 need(changed==24 and unchanged>25,'WRONG_MUTATED_TRACKS')
 need(max_stance_error<1e-8,'STANCE_HOOF_CHANGED')
 need(max_toe_error<.010,'SWING_HOOF_TARGET_DRIFT')
 need(middle>=90,'NOT_ENOUGH_MID_SWING_WITNESSES')
 need(max_upper<-.010 and min_lower>.040,
      'REVERSED_KNEE_AND_FETLOCK_POLE_SIDE_WRONG')
 need(max_step<35.,'JOINT_ROTATION_JUMP')
 # Skin-space regression check: real hoof geometry, not just bones.
 # The original body mesh's low fore-hoof vertices are selected at rest;
 # their exact deformation must be unchanged during every planted sample.
 body=before['meshes'][0]['primitives'][0]
 xyz=base.accessor(before,b0,body['attributes']['POSITION'])
 joints=base.accessor(before,b0,body['attributes']['JOINTS_0'])
 weights=base.accessor(before,b0,body['attributes']['WEIGHTS_0'])
 hoof_mesh_ids={}
 for label,sign in (('LF',-1),('RF',1)):
  hoof_mesh_ids[label]=[i for i,p in enumerate(xyz)
    if sign*p[0]>.06 and p[1]<.12 and .15<p[2]<.50]
  need(len(hoof_mesh_ids[label])>=120,
       'MISSING_REAL_SKINNED_HOOF_WITNESSES:'+label)
 max_stance_hoof_mesh_delta=0.
 swing_hoof_mesh_min_y={'LF':float('inf'),'RF':float('inf')}
 sample_frames=(0,2,5,6,8,12,15,16,18,22,25,30,31,32,34,38,54,70,86,95,96)
 for stage in range(3):
  a=oldtracks[stage];b=newtracks[stage]
  rt=b[(root,'translation')]['values']
  for frame in sample_frames:
   after['nodes'][root]['translation']=list(rt[frame])
   oldpose={n:v['values'][frame] for (n,mode),v in a.items() if mode=='rotation'}
   newpose={n:v['values'][frame] for (n,mode),v in b.items() if mode=='rotation'}
   old_mats=base.skin_matrices(after,b0,base.world_matrices(after,oldpose))
   new_mats=base.skin_matrices(after,b1,base.world_matrices(after,newpose))
   for label,leg in LEGS.items():
    u,stance=phase_at(leg['phase'],frame*STEP)
    for i in hoof_mesh_ids[label]:
     old_p=base.deform_vertex(xyz[i],joints[i],weights[i],old_mats)
     new_p=base.deform_vertex(xyz[i],joints[i],weights[i],new_mats)
     if stance:
      max_stance_hoof_mesh_delta=max(max_stance_hoof_mesh_delta,
                                     math.dist(old_p,new_p))
     else:
      swing_hoof_mesh_min_y[label]=min(swing_hoof_mesh_min_y[label],new_p[1])
 after['nodes'][root]['translation']=list(saved)
 need(max_stance_hoof_mesh_delta<1e-8,'REAL_SKINNED_STANCE_HOOF_CHANGED')
 return {'campaign' :'REPL_FORELEG_BEND_REVERSAL','version':VERSION,
   'source_sha256':sha(old),'new_sha256':sha(new),
   'foreleg_upper_backward':{'LF':'Bone_014','RF':'Bone_020'},
   'foreleg_lower_forward':{'LF':'Bone_013','RF':'Bone_019'},
   'meanings':'reverse bending directions at owner-designated foreleg joints; body and hooves grounded',
   'max_swing_toe_marker_deviation':max_toe_error,
   'max_stance_toe_marker_deviation':max_stance_error,
   'max_real_skinned_stance_hoof_vertex_delta':max_stance_hoof_mesh_delta,
   'min_swing_skin_hoof_y':swing_hoof_mesh_min_y,
   'swing_ground_intersection_review':'NEEDS_VISUAL_REVIEW_NOT_APPROVED',
   'max_upper_backward_pole_mid_swing':max_upper,
   'min_lower_forward_pole_mid_swing':min_lower,
   'mid_swing_witness_count':middle,
   'max_joint_quaternion_step_degrees':max_step,
   'changed_foreleg_tracks':changed,'other_tracks_bitwise_unchanged':unchanged,
   'world_root_forward_travel':ROOT_TRAVEL,
   'all_three_prior_mane_tail_clips':'EXACT_UNCHANGED',
   'three_traveling_walk_clips':'PRESERVED','hindleg':'EXACT_UNCHANGED',
   'human_visual_acceptance':'PENDING'}
