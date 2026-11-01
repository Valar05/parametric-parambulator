#!/usr/bin/env python3
"""Repl v0.6.1: anatomically pole-constrained front-leg IK repair.

Operates on the exact active v0.6.0 Repl.glb. Only rewrite foreleg VEC4
animation samplers in the three existing traveling walk clips. All binary
buffers and other tracks remain intact. Hind leg, mane, corrected tail
socket, textures, root translation and old clips are locked.
"""
from __future__ import annotations
import hashlib,json,math,struct,sys
from pathlib import Path
from fore_constraints import fk,poles,optimize,clamp

VERSION='0.6.1'
CANON='assets/repl/Repl.glb'
SOURCE_SHA='edbe9c647839b3c37b627519e8a7477d7fa8720138913ed3b6524d4613212518'
SOURCE_BLOB='61166671f2512d2167429f269b756fffcefa834a'
CYCLES=3; FRAMES=97; FRAMES_PER_STRIDE=32; STEP=1.28/32; STRIDE=1.28
DURATION=3.84; ROOT_TRAVEL=.96; SPEED=.25; STANCE=.62; LIFT=.105
ORIGINAL_CLIPS=3; TOTAL_CLIPS=6
WALK_NAMES=('REPL_WALK_01_FORWARD_FOUR_BEAT_IK',
  'REPL_WALK_02_FORWARD_BODY_WEIGHT_TRANSFER',
  'REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED')
LEGS={
 'LF':{'phase':.25,'bones':('Bone_016','Bone_015','Bone_014','Bone_013'),
       'end':'Bone_012'},
 'RF':{'phase':.75,'bones':('Bone_022','Bone_021','Bone_020','Bone_019'),
       'end':'Bone_018'}
}
ALL_LEG_BONES=set(sum((list(v['bones'])+[v['end']] for v in LEGS.values()),[]))

class Blocked(RuntimeError):pass
def need(ok,why):
 if not ok:raise Blocked(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def gitblob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def parse_glb(b):
 need(len(b)>28 and b[:4]==b'glTF','BAD_GLB_MAGIC')
 _,version,declared=struct.unpack_from('<4sII',b,0)
 need(version==2 and declared==len(b),'BAD_GLB_HEADER')
 n,typ=struct.unpack_from('<I4s',b,12)
 need(typ==b'JSON','NO_JSON_CHUNK')
 p=20+n;m,typ=struct.unpack_from('<I4s',b,p)
 need(typ==b'BIN\0' and p+8+m==len(b),'NO_BIN_CHUNK')
 return json.loads(b[20:p]),b[p+8:]
def pos(w,node):return tuple(w[node][k] for k in (3,7,11))
def qnorm(q):
 n=math.sqrt(sum(x*x for x in q));need(n>1e-12,'INVALID_QUATERNION')
 return tuple(x/n for x in q)
def local_world_x(world,node):
 m=world[node];axis=(m[0],m[1],m[2]);n=math.sqrt(sum(x*x for x in axis))
 need(n>.000001,'DEGENERATE_WORLD_X_TO_LOCAL_AXIS')
 return tuple(x/n for x in axis)
def angle_of(q,reference,axis,base):
 inverse=(-reference[0],-reference[1],-reference[2],reference[3])
 relative=base.qmul(inverse,qnorm(q));
 amount=sum(a*b for a,b in zip(relative[:3],axis))
 return (math.degrees(2*math.atan2(amount,relative[3]))+180)%360-180
def blend(base,a,b,f):return base.quat_slerp(a,b,f)
def ease(x):x=clamp(x,0,1);return x*x*(3-2*x)
def event(phase,t,rest_foot):
 unwrapped=t/STRIDE-phase
 cycle=math.floor(unwrapped+1e-10)
 u=unwrapped-cycle
 touch=(cycle+phase)*STRIDE
 z0=rest_foot[2]+SPEED*touch+.5*STANCE*SPEED*STRIDE
 if u<STANCE:
  return (rest_foot[0],rest_foot[1],z0),True,u,cycle
 s=(u-STANCE)/(1-STANCE)
 moving=ease(s)
 lift=LIFT*math.sin(math.pi*s)**1.25
 return (rest_foot[0],rest_foot[1]+lift,z0+SPEED*STRIDE*moving),False,u,cycle

def tracks(doc,binary,clip,base):
 ans={}
 for ch in clip['channels']:
  sm=clip['samplers'][ch['sampler']]
  need(sm['interpolation']=='LINEAR','WALK_TRACK_NOT_LINEAR')
  key=(ch['target']['node'],ch['target']['path'])
  need(key not in ans,'DUPLICATE_ANIMATION_TRACK')
  times=base.accessor(doc,binary,sm['input'])
  values=base.accessor(doc,binary,sm['output'])
  need(len(times)==len(values)==FRAMES,'WALK_TRACK_NOT_97_FRAMES')
  for i,t in enumerate(times):
   need(abs(t[0]-i*STEP)<2e-6,'GAIT_SAMPLER_TIME_CHANGE')
  ans[key]={'values':values,'sampler':sm,'times':times}
 return ans

def measure_hinges(world,names,leg):
 p=[pos(world,names[n]) for n in [*leg['bones'],leg['end']]]
 return poles(p),p

def make_correction(source,base,progress=None):
 """Deterministic one-GLB v060->v061 conversion, standard library only."""
 need(sha(source)==SOURCE_SHA,'UNEXPECTED_CANONICAL_MODEL_HASH')
 doc,old_bin=parse_glb(source)
 need(len(doc['nodes'])==53 and len(doc['skins'][0]['joints'])==50,
      'CANONICAL_RIG_NOT_50_JOINTS')
 need(len(doc['animations'])==TOTAL_CLIPS,'WALK_CLIP_COUNT_CHANGED')
 for i,name in enumerate(WALK_NAMES):
  need(doc['animations'][i+3]['name']==name,'UNEXPECTED_WALK_CLIP_NAME')
 names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
 for leg in LEGS.values():
  for name in (*leg['bones'],leg['end']):need(name in names,'MISSING_FORELEG_JOINT:'+name)
 root=names['Bone_000'];root0=tuple(doc['nodes'][root].get('translation',(0,0,0)))
 old_skin=json.dumps(doc['skins'],sort_keys=True)
 old_nodes=json.dumps(doc['nodes'],sort_keys=True)
 old_mesh=json.dumps(doc['meshes'],sort_keys=True)
 old_clips=json.dumps(doc['animations'][:3],sort_keys=True)
 old_animation_data=json.dumps(doc['animations'][3:],sort_keys=True)
 restworld=base.world_matrices(doc,{})
 for leg in LEGS.values():leg['rest_end']=pos(restworld,names[leg['end']])
 original_tracks=[tracks(doc,old_bin,clip,base) for clip in doc['animations'][3:]]
 for s,tr in enumerate(original_tracks):
  need((root,'translation') in tr,'ROOT_FORWARD_TRACK_MISSING')
  for leg in LEGS.values():
   for node in [*leg['bones'],leg['end']]:
    need((names[node],'rotation') in tr,'FORELEG_ROTATION_TRACK_MISSING:'+node)
 # Keep the old motion for unmodified legs and all ancestor/body tracks.
 append=bytearray(old_bin)
 diagnostic=[]
 caches={}
 total_samples=0
 for stage_idx in (0,1):
  stage=stage_idx+1
  tr=original_tracks[stage_idx]
  if progress:progress('STAGE_'+str(stage)+'_ANATOMICAL_SOLVER_STARTED')
  result={}
  for label,leg in LEGS.items():
   node_ids=[names[n] for n in leg['bones']];endid=names[leg['end']]
   current=[tr[(n,'rotation')]['values'] for n in node_ids]
   foot_old=tr[(endid,'rotation')]['values']
   rows={n:[] for n in (*node_ids,endid)}
   sample_stats=[]
   for frame in range(FRAMES_PER_STRIDE):
    t=frame*STEP
    # Baseline body (including existing hindleg tracks) is immutable.
    pose={node:vals['values'][frame]
       for (node,typ),vals in tr.items() if typ=='rotation' and node not in (*node_ids,endid)}
    doc['nodes'][root]['translation']=list(tr[(root,'translation')]['values'][frame])
    actual_old=dict(pose)
    for k,n in enumerate(node_ids):actual_old[n]=current[k][frame]
    actual_old[endid]=foot_old[frame]
    world_before=base.world_matrices(doc,actual_old)
    world_rest=base.world_matrices(doc,pose)
    local_axes=[local_world_x(world_rest,n) for n in node_ids]
    rest_quats=[base.node_rotation(doc['nodes'][n]) for n in node_ids]
    oldq=[angle_of(current[k][frame],rest_quats[k],local_axes[k],base)
          for k in range(4)]
    positions=[pos(world_rest,n) for n in (*node_ids,endid)]
    linkdata=[positions[0]]+[tuple(b-a for a,b in zip(positions[i],positions[i+1]))
                     for i in range(4)]
    target,stance,u,_cycle=event(leg['phase'],t,leg['rest_end'])
    if stance:
     for k,n in enumerate(node_ids):rows[n].append(tuple(current[k][frame]))
     rows[endid].append(tuple(foot_old[frame]))
     continue
    s=(u-STANCE)/(1-STANCE)
    q,loss=optimize(linkdata,target,s,oldq)
    # Each bone rotates about sagittal WORLD X, mapped to its real local basis.
    proposal=dict(pose)
    blendfactor=ease(min(1.,s/.115,(1.-s)/.115))
    for k,n in enumerate(node_ids):
     solved=qnorm(base.qmul(rest_quats[k],base.axisq(local_axes[k],q[k])))
     proposal[n]=blend(base,current[k][frame],solved,blendfactor)
    # Preserve old hoof pitch / toe direction with independent terminal
    # compensation. The end marker's world position is unchanged by its own rotation.
    proposal[endid]=tuple(foot_old[frame])
    newworld=base.world_matrices(doc,proposal)
    ref=world_before[endid];actual=newworld[endid]
    desired=(ref[6],ref[10]);now=(actual[6],actual[10])
    delta=math.atan2(desired[1]*now[0]-desired[0]*now[1],
                     desired[0]*now[0]+desired[1]*now[1])
    need(abs(delta)<math.radians(105),'HOOF_COMPENSATION_WOULD_EXCEED_105_DEG')
    if abs(delta)>1e-6:
     proposal[endid]=qnorm(base.qmul(proposal[endid],
                base.axisq(local_world_x(newworld,endid),math.degrees(delta))))
    newworld=base.world_matrices(doc,proposal)
    (e,k),p=measure_hinges(newworld,names,leg)
    new_foot=pos(newworld,endid)
    error=math.dist(new_foot,target)
    need(error<.018,'CONSTRAINED_IK_MISSES_SWING_FOOT:'+label+':'+str(frame)+':'+str(error))
    if .25<=s<=.75:
     need(e>.005 and k<-.035,
          'FORELEG_POLE_WRONG_SIDE:'+label+':'+str(frame)+':'+str((e,k)))
    for n in (*node_ids,endid):rows[n].append(proposal[n])
    sample_stats.append({'frame':frame,'swing':round(s,3),
       'fore_elbow_forward':e,'carpus_backward':k,
       'foot_error':error,'angles':q,'blend':blendfactor})
    total_samples+=1
   for n in rows:
    # Exact pose-cycle closure. Three traversed strides; no in-place clip.
    first32=rows[n]
    rows[n]=first32*3+[first32[0]]
    need(len(rows[n])==FRAMES,'BAD_REPEATED_POSE_COUNT')
   result[label]=rows
   diagnostic.append({'stage':stage,'leg':label,'swing_samples':sample_stats})
  caches[stage]=result
  if progress:progress('STAGE_'+str(stage)+'_ANATOMICAL_SOLVER_COMPLETE')
 # Reuse the exact leg solution from stage 2 for stage 3, whose body/root
 # motion is already identical and only mane/tail secondary differs.
 caches[3]=caches[2]
 count=0
 for stage_idx,tr in enumerate(original_tracks):
  stage=stage_idx+1
  for label,rows in caches[stage].items():
   for n,quats in rows.items():
    new_index=base.emit_accessor(doc,append,quats,5126,'VEC4')
    tr[(n,'rotation')]['sampler']['output']=new_index
    count+=1
  clip=doc['animations'][stage_idx+3]
  clip.setdefault('extras',{})['anatomicalForelimbConstraints']={
    'version':VERSION,'front_elbow_pole':'+Z forward',
    'front_carpus_pole':'-Z backward',
    'hinge_sequence':'shoulder -> elbow -> carpus -> fetlock -> hoof',
    'bounds_degrees':{'shoulder':[-47,47],'elbow':[-12,75],
                      'carpus':[-80,14],'fetlock':[-45,45]},
    'locomotion':'forward only', 'hind_leg_tracks':'EXACT_UNCHANGED',
    'owner_visual_acceptance':'PENDING'}
 doc['nodes'][root]['translation']=list(root0)
 need(json.dumps(doc['nodes'],sort_keys=True)==old_nodes,'LOCKED_NODES_CHANGED')
 need(json.dumps(doc['skins'],sort_keys=True)==old_skin,'LOCKED_SKIN_CHANGED')
 need(json.dumps(doc['meshes'],sort_keys=True)==old_mesh,'LOCKED_MESH_CHANGED')
 need(json.dumps(doc['animations'][:3],sort_keys=True)==old_clips,'ACCEPTED_CLIPS_CHANGED')
 need(bytes(append[:len(old_bin)])==old_bin,'LOCKED_BINARY_PREFIX_CHANGED')
 need(count==30,'UNEXPECTED_NUMBER_OF_FORELEG_TRACK_REPLACEMENTS')
 doc['asset'].setdefault('extras',{})['replWalkCampaign']['version']=VERSION
 doc['asset']['extras']['replWalkCampaign']['forelegIK']='opposing elbow/carpus poles constrained'
 doc['asset']['extras']['replWalkCampaign']['humanVisualVerdict']='PENDING'
 out=base.glb_encode(doc,bytes(append))
 report=validate_result(source,out,base,diagnostic)
 report['solver_samples']=total_samples
 report['new_track_count']=count
 return out,report

def validate_result(old,new,base,diag):
 orig,obin=parse_glb(old);doc,bin=parse_glb(new)
 need(len(doc['animations'])==6,'WRONG_OUTPUT_CLIP_COUNT')
 need(doc['skins']==orig['skins'] and doc['meshes']==orig['meshes'] and
      doc['nodes']==orig['nodes'],'MODEL_GEOMETRY_CHANGED')
 need(doc['animations'][:3]==orig['animations'][:3],
      'OLD_MANE_TAIL_CLIPS_CHANGED')
 need(bin[:len(obin)]==obin,'ORIGINAL_BINARY_CHANGED')
 names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
 root=names['Bone_000'];root0=list(doc['nodes'][root]['translation'])
 oldrest=base.world_matrices(doc,{})
 for leg in LEGS.values():leg['rest_end']=pos(oldrest,names[leg['end']])
 before=[tracks(orig,obin,clip,base) for clip in orig['animations'][3:]]
 after=[tracks(doc,bin,clip,base) for clip in doc['animations'][3:]]
 untouched=0;changed=0
 max_swing_error=0.;min_elbow=1e5;max_carpus=-1e5
 hinge_sample_count=0
 max_quat_step_deg=0.;max_contact_delta=0.
 for stage in range(3):
  oldtr=before[stage];newtr=after[stage]
  need(set(oldtr)==set(newtr),'WALK_TRACK_SET_CHANGED')
  for key in oldtr:
   if key[1]=='rotation' and key[0] in (names[n] for n in ALL_LEG_BONES):
    changed+=1
   else:
    need(newtr[key]['values']==oldtr[key]['values'],
         'UNAUTHORIZED_HIND_ROOT_OR_BODY_TRACK_CHANGE:'+str(key))
    untouched+=1
  loc=newtr[(root,'translation')]['values']
  need(abs(loc[-1][2]-loc[0][2]-ROOT_TRAVEL)<1e-5,
       'NON_MOVING_OR_IN_PLACE_ROOT')
  for label,leg in LEGS.items():
   for f in range(FRAMES):
    t=STEP*f
    pose={node:entry['values'][f] for (node,typ),entry in newtr.items() if typ=='rotation'}
    doc['nodes'][root]['translation']=list(loc[f])
    world=base.world_matrices(doc,pose)
    target,stance,u,_=event(leg['phase'],t,leg['rest_end'])
    where=pos(world,names[leg['end']]);e=math.dist(where,target)
    if not stance:
     max_swing_error=max(max_swing_error,e)
     s=(u-STANCE)/(1-STANCE)
     (el,car),_p=measure_hinges(world,names,leg)
     if .25<=s<=.75:
      min_elbow=min(min_elbow,el);max_carpus=max(max_carpus,car)
      hinge_sample_count+=1
    else:
     oldpose={node:entry['values'][f] for (node,typ),entry in oldtr.items() if typ=='rotation'}
     old_world=base.world_matrices(doc,oldpose)
     old_p=pos(old_world,names[leg['end']])
     max_contact_delta=max(max_contact_delta,math.dist(where,old_p))
   for n in (*leg['bones'],leg['end']):
    qtrack=newtr[(names[n],'rotation')]['values']
    need(max(abs(a-b) for a,b in zip(qtrack[0],qtrack[-1]))<1e-6,
         'ANATOMICAL_CORRECTION_BREAKS_CYCLE')
    for a,b in zip(qtrack,qtrack[1:]):
     dot=abs(sum(x*y for x,y in zip(a,b)))
     angular=math.degrees(2*math.acos(clamp(dot,-1.,1.)))
     max_quat_step_deg=max(max_quat_step_deg,angular)
 doc['nodes'][root]['translation']=root0
 need(max_swing_error<.018,'CORRECTED_SWING_FOOT_ERROR:'+str(max_swing_error))
 need(max_contact_delta<1e-8,'STANCE_HOOF_MOVED_RELATIVE_TO_V060')
 need(hinge_sample_count>=24,'MISSING_HINGE_INSPECTION_FRAMES')
 need(min_elbow>.005 and max_carpus<-.035,
      'ANATOMICAL_HINGE_POLES_FAIL:'+str((min_elbow,max_carpus)))
 need(max_quat_step_deg<28,'ANATOMICAL_SWING_POSE_SNAPS:'+str(max_quat_step_deg))
 return {'campaign':'REPL_FORELEG_ANATOMICAL_IK_REPAIR','version':VERSION,
   'old_sha256':sha(old),'new_sha256':sha(new),
   'foreleg_elbow_pole':'+Z forwards','foreleg_carpus_pole':'-Z backwards',
   'min_forward_elbow_protrusion_at_mid_swing':min_elbow,
   'max_backward_carpus_protrusion_at_mid_swing':max_carpus,
   'measured_mid_swing_frames':hinge_sample_count,
   'max_swing_hoof_target_error':max_swing_error,
   'max_stance_hoof_deviation_from_v060':max_contact_delta,
   'max_foreleg_quaternion_step_degrees':max_quat_step_deg,
   'unchanged_animation_tracks':untouched,
   'replaced_foreleg_animation_tracks':changed,
   'root_travel':ROOT_TRAVEL,'walk_clips':list(WALK_NAMES),
   'old_3_mane_tail_clips':'PRESERVED','hindleg_tracks':'PRESERVED',
   'single_glb_path':CANON,'human_acceptance':'PENDING'}
