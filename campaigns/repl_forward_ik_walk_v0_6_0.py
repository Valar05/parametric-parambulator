#!/usr/bin/env python3
"""Repl forward-moving four-beat walk: honest joint-space IK gait + stages.

Runs on the sole canonical 50-joint v0.5.2 Repl.glb. Uses only Python stdlib
and the immutable original engine shipped in the Git repo. Does NOT generate
an in-place version. Every review animation advances the rig in +Z.

Stage 1: coordinated 4-legged planted/swing four-beat walk with moving root.
Stage 2: body weight transfer, coupled shoulder and pelvis responses re-solved
         with four-foot IK so planted hooves stay world-locked.
Stage 3: same grounded walk + restrained accepted tail/head follow-through.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode=True
VERSION='0.6.0'
CANONICAL_REL='assets/repl/Repl.glb'
SOURCE_SHA='55bca4c3406f46bd5c6475127158554a823f8aa36bfd7a6c969d9fb2806ccc7b'
SOURCE_BLOB='5fe7b6bdf6ffe4201e331d1db52ea0d24cad9002'
EXPECTED_JOINTS=50
EXPECTED_NODES=53
TIME_PER_STRIDE=1.28
CYCLES=3
DURATION=TIME_PER_STRIDE*CYCLES
FPS=25
FRAMES=97  # 3 * 32 + 1; exactly 25 fps for the 3.84 s travel segment
SPEED=.25
STRIDE_DISTANCE=SPEED*TIME_PER_STRIDE
STANCE_FRACTION=.62
SWING_LIFT=.105
ROOT_TRAVEL=SPEED*DURATION
CLIPS=(
 'REPL_WALK_01_FORWARD_FOUR_BEAT_IK',
 'REPL_WALK_02_FORWARD_BODY_WEIGHT_TRANSFER',
 'REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED')
# +Z is forward in the *actual* canonical Repl asset; X is left/right.
# Events are LH -> LF -> RH -> RF, separated by 1/4 stride.
LEGS={
 'LH':{'phase':0.0, 'drivers':['Bone_027','Bone_026','Bone_025','Bone_024'],
       'end':'Bone_023','xsign':-1,'type':'hind','max_deg':(32,45,55,28),
       'weights':(1.0,1.0,1.35,.75)},
 'LF':{'phase':.25, 'drivers':['Bone_016','Bone_015','Bone_014','Bone_013'],
       'end':'Bone_018','xsign':-1,'type':'fore','max_deg':(28,45,50,28),
       'weights':(.85,1.0,1.3,.80)},
 'RH':{'phase':.50,'drivers':['Bone_032','Bone_031','Bone_030','Bone_029'],
       'end':'Bone_028','xsign':1,'type':'hind','max_deg':(32,45,55,28),
       'weights':(1.0,1.0,1.35,.75)},
 'RF':{'phase':.75,'drivers':['Bone_022','Bone_021','Bone_020','Bone_019'],
       'end':'Bone_018','xsign':1,'type':'fore','max_deg':(28,45,50,28),
       'weights':(.85,1.0,1.3,.80)}
}
# Correction: RF is right-side Bone_017 descendant of Bone_018.
# LF is left-side Bone_011 descendant of Bone_012; their proximal ankle
# driver positions differ from the opposing limbs. Use the physical
# distal ankle markers Bone_012 and Bone_018, respectively, for IK.
LEGS['LF']['end']='Bone_012'
LEGS['RF']['end']='Bone_018'

class Blocked(RuntimeError):pass

def need(v,msg):
 if not v:raise Blocked(msg)

def sha(data):return hashlib.sha256(data).hexdigest()

def parse_glb(b):
 need(len(b)>=28 and b[:4]==b'glTF','INVALID_GLB_MAGIC')
 _,ver,total=struct.unpack_from('<4sII',b,0)
 need(ver==2 and total==len(b),'INVALID_GLB_SIZE_OR_VERSION')
 n,kind=struct.unpack_from('<I4s',b,12)
 need(kind==b'JSON','BAD_JSON_CHUNK')
 p=20+n
 m,kind2=struct.unpack_from('<I4s',b,p)
 need(kind2==b'BIN\0' and p+8+m==len(b),'BAD_BINARY_CHUNK')
 return json.loads(b[20:p]),b[p+8:]

def position(world,node):
 m=world[node]
 return (m[3],m[7],m[11])

def world_axis_x(world,node):
 # Local unit axis that maps to canonical world-space X.
 m=world[node]
 axis=(m[0],m[1],m[2]);n=math.sqrt(sum(x*x for x in axis))
 need(n>.00001,'DEGENERATE_LOCAL_AXIS:'+str(node))
 return tuple(x/n for x in axis)

def qnorm(q):
 n=math.sqrt(sum(x*x for x in q))
 return tuple(x/n for x in q)

def clamp(x,a,b):return min(b,max(a,x))

def ease(x):
 x=clamp(x,0.0,1.0)
 return x*x*(3-2*x)

def event(leg,t,rest_foot):
 """World-space target at time t. Stance target is fixed by touchdown."""
 phase=leg['phase'];unwrapped=t/TIME_PER_STRIDE-phase
 cycle=math.floor(unwrapped+1e-10)
 u=unwrapped-cycle
 touch=(cycle+phase)*TIME_PER_STRIDE
 # Target is ahead of the moving body at touchdown, behind at lift-off.
 ahead=.5*STANCE_FRACTION*STRIDE_DISTANCE
 z0=rest_foot[2]+SPEED*touch+ahead
 if u<STANCE_FRACTION:
  return (rest_foot[0],rest_foot[1],z0),True,u,cycle
 swing=(u-STANCE_FRACTION)/(1-STANCE_FRACTION)
 path=ease(swing)
 next_z=z0+STRIDE_DISTANCE
 lift=SWING_LIFT*math.sin(math.pi*swing)**1.25
 return (rest_foot[0],rest_foot[1]+lift,z0+(next_z-z0)*path),False,u,cycle

def world_to_local_angle(base,doc,world,node,radians):
 # Rotate around WORLD X by a delta, using current orthonormalized axis.
 return base.axisq(world_axis_x(world,node),math.degrees(radians))

def solve_leg(base,doc,root,leg,foot_target,pose):
 """Damped 2D Jacobian-transpose IK on actual sagittal bone chains.

 No false local-foot-lock claims: world-space anklebone position is compared
 to the actual fixed touchdown after every solve. Joint controls are capped.
 """
 nodes={x['name']:i for i,x in enumerate(doc['nodes']) if x.get('name')}
 driver=[nodes[n] for n in leg['drivers']]
 effector=nodes[leg['end']]
 baseline={n:base.node_rotation(doc['nodes'][n]) for n in driver}
 angles={n:0.0 for n in driver}
 best=1e9
 for iteration in range(54):
  world=base.world_matrices(doc,pose)
  p=position(world,effector)
  dy=foot_target[1]-p[1];dz=foot_target[2]-p[2]
  err=math.hypot(dy,dz)
  best=min(best,err)
  if err<.0015:break
  columns=[]
  for n,w in zip(driver,leg['weights']):
   j=position(world,n)
   # derivatives in world sagittal plane for rotation about +X
   Jy=-(p[2]-j[2]);Jz=p[1]-j[1]
   columns.append((n,Jy,Jz,w))
  damp=.0020
  A=damp+sum(w*a*a for _,a,b,w in columns)
  B=sum(w*a*b for _,a,b,w in columns)
  C=damp+sum(w*b*b for _,a,b,w in columns)
  determinant=A*C-B*B
  need(determinant>1e-10,'IK_SINGULAR_MATRIX')
  u=(C*dy-B*dz)/determinant
  v=(A*dz-B*dy)/determinant
  movement=0
  for (n,a,b,w),limit in zip(columns,leg['max_deg']):
   delta=clamp(w*(a*u+b*v),-.12,.12)
   maximum=math.radians(limit)
   updated=clamp(angles[n]+delta,-maximum,maximum)
   delta=updated-angles[n]
   if abs(delta)<1e-9:continue
   # Rebuild WORLD axes when upstream joint was changed this iteration.
   world_now=base.world_matrices(doc,pose)
   rotation=world_to_local_angle(base,doc,world_now,n,delta)
   original=pose.get(n,baseline[n])
   pose[n]=qnorm(base.qmul(original,rotation))
   angles[n]=updated
   movement+=abs(delta)
  if movement<1e-8:break
 # End-effector translation IK does not by itself stabilize the hoof's
 # orientation. Keep the actual fetlock/hoof basis level while the chain
 # articulates: a terminal rotation does NOT move that end-joint target,
 # but it prevents toe geometry from diving into the floor.
 world=base.world_matrices(doc,pose)
 foot_world=world[effector]
 foot_rest=leg['rest_basis']
 now=(foot_world[6],foot_world[10])   # bone-local Z projected into Y/Z
 orig=(foot_rest[6],foot_rest[10])
 angle=math.atan2(now[0]*orig[1]-now[1]*orig[0],
                  now[0]*orig[0]+now[1]*orig[1])
 need(abs(angle)<math.radians(100),'HOOF_LEVELING_AXIS_OUT_OF_RANGE')
 if abs(angle)>1e-7:
  foot_local_axis=world_axis_x(world,effector)
  pose[effector]=qnorm(base.qmul(base.node_rotation(doc['nodes'][effector]),
                   base.axisq(foot_local_axis,math.degrees(angle))))
 world=base.world_matrices(doc,pose)
 p=position(world,effector)
 residual=math.dist(p,foot_target)
 return residual,angles,p

def body_pose(base,doc,names,root_original,t,stage):
 q=t/TIME_PER_STRIDE
 offset=SPEED*t
 y=0.0
 if stage>=2:
  y=.0075*(math.cos(4*math.pi*q)-1) # center at 0 for clip boundaries
 root=doc['nodes'][names['Bone_000']]
 root['translation']=[root_original[0],root_original[1]+y,root_original[2]+offset]
 pose={}
 if stage>=2:
  # Body pitch is real, not purely a camera effect. Hooves re-solve to hold ground.
  pitch=.48*math.sin(2*math.pi*q)
  n=names['Bone_000']
  pose[n]=qnorm(base.qmul(base.node_rotation(root),base.axisq((1,0,0),pitch)))
  n=names['Bone_002']
  pose[n]=qnorm(base.qmul(base.node_rotation(doc['nodes'][n]),base.axisq((1,0,0),.40*math.sin(2*math.pi*q+.5))))
  n=names['Bone_004']
  pose[n]=qnorm(base.qmul(base.node_rotation(doc['nodes'][n]),base.axisq((1,0,0),-.38*math.sin(2*math.pi*q-.5))))
 if stage>=3:
  for name,amplitude,phase in [
    ('REPL_TAIL_BASE',1.1,-.55),('REPL_TAIL_TIP',1.5,-.95),
    ('REPL_TAIL_NEAR_TIP',1.2,-1.1),('REPL_TAIL_TERMINAL',.8,-1.2),
    ('Bone_010',-.42,.4)]:
   n=names[name]
   angle=amplitude*math.sin(2*math.pi*q+phase)
   # End-cycle quaternions match first-cycle quaternions.
   pose[n]=qnorm(base.qmul(base.node_rotation(doc['nodes'][n]),base.axisq((1,0,0),angle)))
 return pose

def validate_input(doc,raw):
 need(len(doc.get('nodes',[]))==EXPECTED_NODES,'NODE_COUNT_NOT_V052')
 need(len(doc.get('skins',[]))==1 and len(doc['skins'][0]['joints'])==EXPECTED_JOINTS,'NOT_V052_CANONICAL_RIG')
 need(len(doc.get('animations',[]))==3,'EXPECTED_THREE_ACCEPTED_REVIEW_CLIPS')
 names={x.get('name'):i for i,x in enumerate(doc['nodes'])}
 for n in ['Bone_000','Bone_002','Bone_004']:
  need(n in names,'REQUIRED_BODY_BONE_MISSING:'+n)
 for leg in LEGS.values():
  for n in leg['drivers']+[leg['end']]:need(n in names,'ACTUAL_LIMB_BONE_MISSING:'+n)
 for n in ['REPL_TAIL_BASE','REPL_TAIL_TIP','REPL_TAIL_NEAR_TIP','REPL_TAIL_TERMINAL','Bone_010']:
  need(n in names,'ACCEPTED_HAIR_CONTROL_MISSING:'+n)
 # No retargeting to another horse.
 return names

def make_gait(source,base,progress=None):
 b=source if isinstance(source,bytes) else Path(source).read_bytes()
 need(sha(b)==SOURCE_SHA,'CANONICAL_GLB_SHA_CHANGED__DO_NOT_OVERWRITE')
 doc,old_binary=parse_glb(b)
 names=validate_input(doc,b)
 root=names['Bone_000']
 old_root=tuple(doc['nodes'][root].get('translation',(0,0,0)))
 original_nodes=json.dumps(doc['nodes'],sort_keys=True)
 original_skin=json.dumps(doc['skins'],sort_keys=True)
 original_mesh=json.dumps(doc['meshes'],sort_keys=True)
 original_anims=json.dumps(doc['animations'],sort_keys=True)
 worlds=base.world_matrices(doc,{})
 for name,leg in LEGS.items():
  leg['phase']=float(leg['phase'])
  leg['rest_end']=position(worlds,names[leg['end']])
  leg['rest_basis']=tuple(worlds[names[leg['end']]])
  need(leg['rest_end'][0]*leg['xsign']>0.07,'LEG_SIDE_MISMATCH:'+name)
 last=doc['animations'][-1]['name']
 need('SLOW_STRAIGHTEN' in last,'TAIL_STRAIGHTEN_CLIP_MISSING')
 buf=bytearray(old_binary)
 stats={}
 phase_coverage={k:0 for k in LEGS}
 support_count=[]
 copy_pos={} # stage -> list of poses for second stage duplication
 for stage in (1,2,3):
  if progress:progress('GAIT_STAGE_'+str(stage)+'_STARTED')
  timeline=[]
  contact_rows=[]
  extrema={'max_ankle_position_error':0,'max_stance_slip':0,'max_swing_error':0,
           'max_per_joint_rotation_deg':0}
  for f in range(FRAMES):
   t=DURATION*f/(FRAMES-1)
   if stage==3:
    pose,loc=copy.deepcopy(copy_pos[2][f])
    doc['nodes'][root]['translation']=list(loc)
    q=t/TIME_PER_STRIDE
    for name,amp,phase in [('REPL_TAIL_BASE',1.1,-.55),
      ('REPL_TAIL_TIP',1.5,-.95),('REPL_TAIL_NEAR_TIP',1.2,-1.1),
      ('REPL_TAIL_TERMINAL',.8,-1.2),('Bone_010',-.42,.4)]:
     n=names[name]
     pose[n]=qnorm(base.qmul(base.node_rotation(doc['nodes'][n]),
                     base.axisq((1,0,0),amp*math.sin(2*math.pi*q+phase))))
   else:
    pose=body_pose(base,doc,names,old_root,t,stage)
    # Four-beat contacts, including the initially swinging/stance legs.
    for label,leg in LEGS.items():
     dest,stance,u,cycle=event(leg,t,leg['rest_end'])
     err,angles,p=solve_leg(base,doc,root,leg,dest,pose)
     extrema['max_ankle_position_error']=max(extrema['max_ankle_position_error'],err)
     extrema['max_per_joint_rotation_deg']=max(extrema['max_per_joint_rotation_deg'],*(abs(math.degrees(a)) for a in angles.values()))
     if stance:extrema['max_stance_slip']=max(extrema['max_stance_slip'],err)
     else:extrema['max_swing_error']=max(extrema['max_swing_error'],err)
   timeline.append((t,pose,tuple(doc['nodes'][root]['translation'])))
   contact={}
   contacts=0
   for label,leg in LEGS.items():
    dest,stance,u,cycle=event(leg,t,leg['rest_end'])
    contact[label]={
     'stance':stance,
     'target':dest,
     'u':u,'cycle':cycle,
    }
    if stance:
     contacts+=1
     if stage==1:phase_coverage[label]+=1
   if stage==1:support_count.append(contacts)
   if f%8==0 or f==FRAMES-1:
    world=base.world_matrices(doc,pose)
    for label,leg in LEGS.items():
     actual=position(world,names[leg['end']]);e=math.dist(actual,contact[label]['target'])
     extrema['max_ankle_position_error']=max(extrema['max_ankle_position_error'],e)
     if contact[label]['stance']:extrema['max_stance_slip']=max(extrema['max_stance_slip'],e)
    contact_rows.append({'time':round(t,4),'root_z':round(doc['nodes'][root]['translation'][2],5),
      'stance':''.join(label+' ' for label in LEGS if contact[label]['stance']).strip(),
      'support_count':contacts})
  # store stage2 poses to let stage3 remain EXACT same IK and root track
  if stage==2:copy_pos[2]=[(copy.deepcopy(item[1]),item[2]) for item in timeline]
  doc['nodes'][root]['translation']=list(old_root)
  # A traveling clip must tile in pose, but NOT in root translation:
  # the next traversal will continue from the traveled endpoint in-engine.
  need(abs(timeline[-1][2][2]-timeline[0][2][2]-ROOT_TRAVEL)<1e-7,
       'ROOT_TRAVEL_NOT_CONSISTENT_STAGE_'+str(stage))
  # sample accessor times; rotate driver bones + root translation, original clips untouched
  tm=base.emit_accessor(doc,buf,[(float(t),) for t,_,_ in timeline],5126,'SCALAR')
  poses={n:[] for leg in LEGS.values() for n in [names[name] for name in leg['drivers']+[leg['end']]]}
  if stage>=2:
   for n in ('Bone_000','Bone_002','Bone_004'):poses[names[n]]=[]
  if stage>=3:
   for n in ['REPL_TAIL_BASE','REPL_TAIL_TIP','REPL_TAIL_NEAR_TIP','REPL_TAIL_TERMINAL','Bone_010']:poses[names[n]]=[]
  rootloc=[]
  for t,pose,loc in timeline:
   rootloc.append(loc)
   for n in poses:
    poses[n].append(qnorm(pose.get(n,base.node_rotation(doc['nodes'][n]))))
  need(all(max(abs(x-y) for x,y in zip(track[0],track[-1]))<1e-5
           for track in poses.values()),
       'FORWARD_STRIDE_POSE_ENDS_NOT_CYCLIC')
  samplers=[];channels=[]
  def track(node,path,values,typ):
   acc=base.emit_accessor(doc,buf,values,5126,typ)
   ix=len(samplers);samplers.append({'input':tm,'output':acc,'interpolation':'LINEAR'})
   channels.append({'sampler':ix,'target':{'node':node,'path':path}})
  track(root,'translation',rootloc,'VEC3')
  for n,values in sorted(poses.items()):track(n,'rotation',values,'VEC4')
  doc['animations'].append({'name':CLIPS[stage-1],'samplers':samplers,'channels':channels,
   'extras':{'author':'Repl forward four-beat procedural IK campaign v'+VERSION,
    'forward_only':True,'in_place_version':False,'world_forward_axis':'+Z',
    'gait':'LH LF RH RF','duration_seconds':DURATION,
    'root_displacement_z':ROOT_TRAVEL,'stance_duty':STANCE_FRACTION,
    'stage':stage,'human_acceptance':'PENDING'}})
  stats[str(stage)]={**extrema,'frames':FRAMES,'clip':CLIPS[stage-1],
                     'root_travel':ROOT_TRAVEL,'contacts':contact_rows}
  if progress:progress('GAIT_STAGE_'+str(stage)+'_COMPLETE')
 # restore nodes to exact original, do not alter previous accepted clips
 doc['nodes'][root]['translation']=list(old_root)
 need(json.dumps(doc['nodes'],sort_keys=True)==original_nodes,'LOCKED_NODES_MODIFIED')
 need(json.dumps(doc['skins'],sort_keys=True)==original_skin,'LOCKED_SKIN_MODIFIED')
 need(json.dumps(doc['meshes'],sort_keys=True)==original_mesh,'LOCKED_MESH_MODIFIED')
 need(json.dumps(doc['animations'][:3],sort_keys=True)==original_anims,'LOCKED_OLD_CLIPS_MODIFIED')
 need(bytes(buf[:len(old_binary)])==old_binary,'SOURCE_BUFFER_PREFIX_CHANGED')
 assert len(doc['animations'])==6
 # Require meaningful progress, not just joint channels with tiny foot travel.
 need(ROOT_TRAVEL>.7,'WALK_NOT_TRAVELING')
 need(all(v>0 for v in phase_coverage.values()),'MISSING_TOUCHDOWN_PHASE')
 need(min(support_count)>=2 and max(support_count)<=3,
      'HORSE_WALK_MUST_HAVE_TWO_OR_THREE_CONTACTS')
 for st in ('1','2'):
  need(stats[st]['max_ankle_position_error']<.025,
       'IK_NOT_GROUNDED_STAGE_'+st+':'+str(stats[st]['max_ankle_position_error']))
 # stage3 shares IK with stage2, no leg differences
 need(stats['3']['max_ankle_position_error']<.025,
      'INTEGRATION_GROUNDEDNESS_FAILED')
 if 'asset' in doc:
  doc['asset'].setdefault('extras',{})['replWalkCampaign']={
    'version':VERSION,'mode':'world_forward_root_motion_only',
    'stages':list(CLIPS),'four_beat_order':['LH','LF','RH','RF'],
    'rootDisplacement':ROOT_TRAVEL,'acceptedTailPivotPreserved':True,
    'ownerVisualVerdict':'PENDING'}
 out=base.glb_encode(doc,bytes(buf))
 # Embedded glTF output's skin data/rig/UVs are unchanged, no new model names in git.
 return out,{
  'campaign':'REPL_FORWARD_IK_WALK','version':VERSION,
  'source_sha256':sha(b),'output_sha256':sha(out),
  'source_clips':3,'output_clips':6,'stages':stats,
  'kinematics':{'forward_axis':'+Z','duration_seconds':DURATION,
   'stride_duration':TIME_PER_STRIDE,'stride_distance':STRIDE_DISTANCE,
   'speed_units_per_second':SPEED,'travel_units':ROOT_TRAVEL,
   'stance_duty':STANCE_FRACTION,'swing_fraction':1-STANCE_FRACTION,
   'touchdown_sequence':['LH','LF','RH','RF'],
   'touchdown_fractions':[0,.25,.5,.75],
   'max_support':max(support_count),'min_support':min(support_count),
   'no_in_place_version':True},
  'preserved':['prior 3 animation clips','all body+hair skin weights',
    '50 joints and 53 nodes','corrected buried tail pivot','all materials and textures'],
  'human_gait_acceptance':'PENDING'
 }


def validate_skinned_hoof_witnesses(output,base):
 """Actual mesh witness test, NOT a claim of visual/clinical correctness.

 Evaluate full skin matrices, including progressive root motion, for surface
 points near each hoof. During a single stance the WORLD z spread must stay
 small. This catches legs that appear planted in joint space but skate when
 skinned, plus regressions from torso compensation.
 """
 doc,binary=parse_glb(output)
 names={x.get('name'):i for i,x in enumerate(doc['nodes']) if x.get('name')}
 root=names['Bone_000'];origin=tuple(doc['nodes'][root].get('translation',(0,0,0)))
 rest_world=base.world_matrices(doc,{})
 for leg in LEGS.values():leg['rest_end']=position(rest_world,names[leg['end']])
 body=doc['meshes'][0]['primitives'][0]
 pos=base.accessor(doc,binary,body['attributes']['POSITION'])
 joints=base.accessor(doc,binary,body['attributes']['JOINTS_0'])
 weights=base.accessor(doc,binary,body['attributes']['WEIGHTS_0'])
 witnesses={}
 for label,leg in LEGS.items():
  xsign=leg['xsign'];zsign=1 if leg['type']=='fore' else -1
  group=[i for i,p in enumerate(pos) if p[0]*xsign>.08 and p[2]*zsign>.05 and p[1]<.11]
  need(len(group)>=75,'INSUFFICIENT_PHYSICAL_HOOF_MESH_WITNESSES:'+label)
  witnesses[label]=group
 original_expected=base.EXPECTED_JOINTS
 base.EXPECTED_JOINTS=EXPECTED_JOINTS
 result={}
 try:
  for stage_index in (3,4,5):
   clip=doc['animations'][stage_index]
   track={}
   for ch in clip['channels']:
    sampler=clip['samplers'][ch['sampler']]
    track[(ch['target']['node'],ch['target']['path'])]=base.accessor(doc,binary,sampler['output'])
   need((root,'translation') in track,'FORWARD_ROOT_TRACK_MISSING')
   planted={name:{} for name in LEGS}
   lowest_y=1e6
   for f in range(FRAMES):
    t=f*DURATION/(FRAMES-1)
    pose={node:quats[f] for (node,path),quats in track.items() if path=='rotation'}
    doc['nodes'][root]['translation']=list(track[(root,'translation')][f])
    world=base.world_matrices(doc,pose)
    matrices=base.skin_matrices(doc,binary,world)
    for name,leg in LEGS.items():
     foot,stance,u,cycle=event(leg,t,leg['rest_end'])
     if not stance:continue
     positions=[base.deform_vertex(pos[i],joints[i],weights[i],matrices) for i in witnesses[name]]
     lowest_y=min(lowest_y,min(p[1] for p in positions))
     center=tuple(sum(p[k] for p in positions)/len(positions) for k in range(3))
     planted[name].setdefault(cycle,[]).append(center)
   maximum_z=0;maximum_y=0;maximum_x=0
   used=0
   for label,cycles in planted.items():
    for cycle,points in cycles.items():
     if len(points)<3:continue
     used+=1
     maximum_x=max(maximum_x,max(p[0] for p in points)-min(p[0] for p in points))
     maximum_y=max(maximum_y,max(p[1] for p in points)-min(p[1] for p in points))
     maximum_z=max(maximum_z,max(p[2] for p in points)-min(p[2] for p in points))
   need(used>=10,'INSUFFICIENT_COMPLETE_STANCE_INTERVALS')
   need(maximum_z<.018,'PHYSICAL_HOOF_MESH_Z_SKATING:'+str(maximum_z))
   need(maximum_y<.025,'PHYSICAL_HOOF_MESH_VERTICAL_JITTER:'+str(maximum_y))
   need(maximum_x<.013,'PHYSICAL_HOOF_MESH_LATERAL_DRIFT:'+str(maximum_x))
   need(lowest_y>-.025,'HOOF_MESH_PENETRATES_GROUND:'+str(lowest_y))
   result[CLIPS[stage_index-3]]={
     'evaluated_stance_intervals':used,
     'max_physical_hoof_mesh_z_spread':maximum_z,
     'max_physical_hoof_mesh_y_spread':maximum_y,
     'max_physical_hoof_mesh_x_spread':maximum_x,
     'lowest_contact_hoof_vertex_y':lowest_y,
     'per_hoof_mesh_witness_count':{name:len(v) for name,v in witnesses.items()}}
 finally:
  doc['nodes'][root]['translation']=list(origin)
  base.EXPECTED_JOINTS=original_expected
 return result
