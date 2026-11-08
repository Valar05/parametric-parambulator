#!/usr/bin/env python3
"""Obsidianti Sword1 two-handed polish: anatomical palm IK plus right-arm torso clearance.

Input: exact published v2.0.33 42-clip review GLB. Output: append only a new 43rd
clip, retaining every input glTF animation, mesh, skin and binary prefix verbatim.
Does not touch the source sword attack, lead-in, shield charm, or canonical GLB.
"""
from __future__ import annotations
import copy,json,math,pathlib,struct

V='OBSIDIANTI_SWORD1_PALM_CLEARANCE_v2.0.39'
INPUT_SHA='ed1f4f34f2f3a261e0c5096a39599980f20868223245455e2be554299d55a5a2'
PREVIOUS='Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance'
VARIANT='Vanguard_SwordAttack1_TwoHand_PalmIK_WristShield_v239'
FPS=120
CUSTOM_TIMES=None  # Adaptive time grid, set by driver for each candidate
LEAD=.23
GRIP_LOCAL=(-.018,-.235,0.)  # Immutable shaft point from the successful previous variant.
RIGHT=('mixamorig:RightArm','mixamorig:RightForeArm','mixamorig:RightHand')
LEFT=('mixamorig:LeftArm','mixamorig:LeftForeArm','mixamorig:LeftHand')
WEAPON='mixamorig:RightWeapon.R'
CENTER=('mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2')
KNUCKLES=('mixamorig:LeftHandIndex1','mixamorig:LeftHandMiddle1','mixamorig:LeftHandRing1','mixamorig:LeftHandPinky1')

def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,s):return tuple(s*x for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(a):return math.sqrt(dot(a,a))
def unit(a):
 v=length(a)
 if v<1e-10:raise ValueError('DEGENERATE_IK_AXIS')
 return mul(a,1/v)
def mix(a,b,t):return tuple(x*(1-t)+y*t for x,y in zip(a,b))
def rotate(h,q,v):
 x,y,z,w=h.normq(q);p=(x,y,z);t=mul(cross(p,v),2)
 return add(add(v,mul(t,w)),cross(p,t))
def between(h,a,b):
 u=unit(a);v=unit(b);d=max(-1.,min(1.,dot(u,v)))
 if d>1-1e-9:return (0.,0.,0.,1.)
 if d < -1+1e-9:
  s=(1.,0.,0.) if abs(u[0])<.8 else (0.,1.,0.)
  ax=unit(cross(u,s));return (*ax,0.)
 ax=cross(u,v);return h.normq((*ax,1+d))
def rotate_axis(v,axis,angle):
 q=unit(axis);return add(add(mul(v,math.cos(angle)),mul(cross(q,v),math.sin(angle))),mul(q,dot(q,v)*(1-math.cos(angle))))
def world(i,pose,parents,h,cache=None):
 if cache is None:cache={}
 if i in cache:return cache[i]
 tr=pose[i];p=tr['translation'];q=h.normq(tr['rotation']);sc=tr['scale']
 if i in parents:
  pp,pq,ps=world(parents[i],pose,parents,h,cache)
  pos=add(pp,rotate(h,pq,tuple(p[k]*ps[k] for k in range(3))))
  rot=h.qm(pq,q);scl=tuple(ps[k]*sc[k] for k in range(3))
 else:pos,rot,scl=p,q,sc
 cache[i]=(pos,rot,scl)
 return cache[i]
def snapshot(js,dat,clip,t,h):
 return {i:{p:tuple(h.at_time(js,dat,clip,i,p,t)) for p in ('translation','rotation','scale')} for i in range(len(js['nodes']))}
def position(i,pose,pa,h):return world(i,pose,pa,h)[0]

def line_point_distance(x,a,b):
 v=sub(b,a);d=dot(v,v)
 t=max(0.,min(1.,dot(sub(x,a),v)/d)) if d>1e-10 else 0.
 return length(sub(x,add(a,mul(v,t))))

def torso_proxy(pose,ids,pa,h):
 spine0=position(ids[CENTER[0]],pose,pa,h)
 spine1=position(ids[CENTER[1]],pose,pa,h)
 spine2=position(ids[CENTER[2]],pose,pa,h)
 shoulder=position(ids[RIGHT[0]],pose,pa,h)
 mid=mix(spine1,spine2,.47)
 axis=unit(sub(spine2,spine0))
 radial=sub(shoulder,add(mid,mul(axis,dot(sub(shoulder,mid),axis))))
 side=unit(radial)
 span=length(radial)
 # Body proxy scales with this rig's actual shoulder-to-spine distance,
 # rather than assuming a human-height or arbitrary unit scale.
 radius=.75*span
 safety=max(.012,span*.08)
 return {'lower':spine0,'upper':spine2,'center':mid,'axis':axis,'side':side,'radius':radius,'safety':safety,'shoulderSpan':span}

def capsule_clearance(p,body):
 return line_point_distance(p,body['lower'],body['upper'])-body['radius']

def arm_clearance(P,E,W,body):
 # Exclude immediate shoulder entry and finger grip. Sample the actual two arm segments.
 samples=[mix(P,E,f) for f in (.22,.35,.5,.65,.8,.94)] + [mix(E,W,f) for f in (.06,.2,.38,.56,.74)]
 clear=[capsule_clearance(p,body) for p in samples]
 return min(clear),sum(max(0.,body['safety']-c)**2 for c in clear)/len(clear)

def solve_chain(pose,ids,pa,h,which,wrist_goal,elbow_goal,keep_hand_world=None):
 A,B,H=(ids[n] for n in which)
 cache={};P=world(A,pose,pa,h,cache)[0]
 arm_parent=h.normq(world(pa[A],pose,pa,h,cache)[1])
 armrot=world(A,pose,pa,h,cache)[1]
 fore_rot=world(B,pose,pa,h,cache)[1]
 handrot=world(H,pose,pa,h,cache)[1] if keep_hand_world is None else keep_hand_world
 av=rotate(h,armrot,pose[B]['translation'])
 bv=rotate(h,fore_rot,pose[H]['translation'])
 # Shoulder and forearm rotate in the world frame, then are converted to the
 # native bone-local quaternions. Wrist world orientation is separately held.
 anew=h.qm(between(h,av,sub(elbow_goal,P)),armrot)
 bnew=h.qm(between(h,bv,sub(wrist_goal,elbow_goal)),fore_rot)
 pose[A]['rotation']=h.qm(h.qi(arm_parent),anew)
 pose[B]['rotation']=h.qm(h.qi(anew),bnew)
 pose[H]['rotation']=h.qm(h.qi(bnew),handrot)
 actual=world(H,pose,pa,h)[0]
 return length(sub(actual,wrist_goal))

def elbow_at(P,W,E0,a,b,angle,h):
 axis=unit(sub(W,P));d=length(sub(W,P))
 if d>=a+b-1e-5 or d<=abs(a-b)+1e-6:return None
 x=(a*a-b*b+d*d)/(2*d);ht=math.sqrt(max(0.,a*a-x*x))
 side=sub(sub(E0,P),mul(axis,dot(sub(E0,P),axis)))
 if length(side)<1e-7:
  fallback=(0,1,0) if abs(axis[1])<.9 else (0,0,1)
  side=cross(axis,fallback)
 pole=rotate_axis(unit(side),axis,angle)
 return add(add(P,mul(axis,x)),mul(pole,ht))

def fix_right(pose,ids,pa,h,previous=None):
 A,B,H=[ids[n] for n in RIGHT];R=ids[WEAPON]
 cache={};P=world(A,pose,pa,h,cache)[0];E=world(B,pose,pa,h,cache)[0]
 W,oldhand,_=world(H,pose,pa,h,cache)
 oldshaft=world(R,pose,pa,h,cache)[1]
 body=torso_proxy(pose,ids,pa,h)
 before,oldpen=arm_clearance(P,E,W,body)
 side=body['side'];span=body['shoulderSpan']
 a=length(pose[B]['translation']);b=length(pose[H]['translation'])
 result={'cost':oldpen/(span*span+1e-9)*200.,'elbow':E,'wrist':W,
         'clearance':before,'penetration':oldpen,'wristShiftM':0.,
         'elbowShiftM':0.,'poleDegrees':0.,'unchanged':True}
 # Bounded search: no iterative use of guessed world-space endpoints.
 # If changing just the elbow pole is sufficient, it beats moving the wrist.
 shifts=(0.,.045,.085,.125,.18,.24,.31,.4)
 turns=(0.,-12,12,-24,24,-40,40,-60,60,-85,85,-115,115,-155,155,180)
 for shift in shifts:
  wtarget=add(W,mul(side,span*shift))
  d=length(sub(wtarget,P))
  if d>=a+b-.00001 or d<=abs(a-b)+.00001:continue
  for degrees in turns:
   elbow=elbow_at(P,wtarget,E,a,b,math.radians(degrees),h)
   if elbow is None:continue
   clearance,pen=arm_clearance(P,elbow,wtarget,body)
   delta=length(sub(elbow,E));wd=length(sub(wtarget,W))
   # Strongly prefer clearing the actual body proxy while preserving the
   # recognizable original attack and minimizing grip displacement.
   movement=(delta/(span+.0001))**2*.001+(wd/(span+.0001))**2*.012
   if previous is not None:
    movement+=(length(sub(elbow,previous['elbow']))/(span+.0001))**2*.0007
   cost=pen/(span*span+1e-9)*200. + movement
   if cost<result['cost']:
    result={'cost':cost,'elbow':elbow,'wrist':wtarget,'clearance':clearance,'penetration':pen,
            'wristShiftM':wd,'elbowShiftM':delta,'poleDegrees':degrees}
 # Refuse a regression. Leave the right arm exactly as it was if every available
 # option is worse. The diagnostic remains an honest witness of unfinished clearance.
 if result['penetration']>oldpen+1e-10:
  result={'elbow':E,'wrist':W,'clearance':before,'penetration':oldpen,
          'wristShiftM':0.,'elbowShiftM':0.,'poleDegrees':0.,'cost':0.,'unchanged':True}
 if not result.get('unchanged'):
  error=solve_chain(pose,ids,pa,h,RIGHT,result['wrist'],result['elbow'],oldhand)
  if error>.0002:raise ValueError('RIGHT_IK_RECONSTRUCTION_ERROR_'+str(error))
 shaft=world(R,pose,pa,h)[1]
 error_deg=h.qdeg(oldshaft,shaft)
 if error_deg>.02:raise ValueError('RIGHT_LANCE_DIRECTION_DRIFT_'+str(error_deg))
 P2=position(A,pose,pa,h);E2=position(B,pose,pa,h);W2=position(H,pose,pa,h)
 after,actualpen=arm_clearance(P2,E2,W2,body)
 if actualpen>oldpen+1e-8:raise ValueError('RIGHT_ARM_TORSO_CLEARANCE_REGRESSED')
 return {'beforeClearanceM':before,'afterClearanceM':after,'oldPenetration':oldpen,
    'newPenetration':actualpen,'spearRotationErrorDeg':error_deg,'wristShiftM':result['wristShiftM'],
    'elbowShiftM':result['elbowShiftM'],'elbow':E2,'poleDegrees':result['poleDegrees'],
    'bodyRadiusM':body['radius'],'bodyMarginM':body['safety'],'shoulderSpanM':span}

def palm_local_offset(first_pose,ids,pa,h):
 H=ids[LEFT[2]]
 wp,wrot,_=world(H,first_pose,pa,h)
 fingers=[]
 for name in KNUCKLES:
  if name in ids:
   finger=world(ids[name],first_pose,pa,h)[0]
   fingers.append(finger)
 if len(fingers)<2:
  # Anatomical fallback: use the first proximal finger joints actually parented
  # under the hand, not an arbitrary world-axis wrist adjustment.
  for name,j in ids.items():
   if name.startswith('mixamorig:LeftHand') and name not in KNUCKLES and name!=LEFT[2]:
    if pa.get(j)==H:fingers.append(world(j,first_pose,pa,h)[0])
 if len(fingers)<2:raise ValueError('NO_MEASURABLE_PALM_FROM_FINGER_BASE_JOINTS')
 mean=tuple(sum(p[k] for p in fingers)/len(fingers) for k in range(3))
 local=rotate(h,h.qi(wrot),mul(sub(mean,wp),.58))
 if not .004<length(local)<.18:raise ValueError('PALM_MEASURED_OFFSET_OUTSIDE_ANATOMICAL_RANGE_'+str(length(local)))
 return local,{'knuckleCount':len(fingers),'palmLocalM':local,'palmOffsetM':length(local)}

def fix_left(pose,ids,pa,h,palm_local):
 A,B,H=[ids[n] for n in LEFT];R=ids[WEAPON]
 cache={};P=world(A,pose,pa,h,cache)[0]
 E=world(B,pose,pa,h,cache)[0]
 wp,wq,_=world(H,pose,pa,h,cache)
 rp,rq,_=world(R,pose,pa,h,cache)
 grip=add(rp,rotate(h,rq,GRIP_LOCAL))
 # The *palm*, measured toward the finger bases, contacts the shaft. Not the wrist.
 wrist_goal=sub(grip,rotate(h,wq,palm_local))
 basea=length(pose[B]['translation']);baseb=length(pose[H]['translation'])
 d=length(sub(wrist_goal,P))
 stretch=max(1.,d/max(basea+baseb-1e-5,1e-5))
 a=basea*stretch;b=baseb*stretch
 # Reuse the previous attack's elbow pole. It already looks good in motion.
 axis=unit(sub(wrist_goal,P))
 perp=sub(sub(E,P),mul(axis,dot(sub(E,P),axis)))
 if length(perp)<1e-7:
  perp=cross(axis,rotate(h,world(A,pose,pa,h)[1],(1.,0.,0.)))
 if length(perp)<1e-7:perp=cross(axis,(0.,1.,0.))
 pole=unit(perp)
 x=(a*a-b*b+d*d)/(2*d)
 hei=math.sqrt(max(0.,a*a-x*x))
 elbow=add(add(P,mul(axis,x)),mul(pole,hei))
 pose[B]['translation']=mul(pose[B]['translation'],stretch)
 pose[H]['translation']=mul(pose[H]['translation'],stretch)
 solve_chain(pose,ids,pa,h,LEFT,wrist_goal,elbow,wq)
 newpos,newrot,_=world(H,pose,pa,h)
 palm=add(newpos,rotate(h,newrot,palm_local))
 error=length(sub(palm,grip))
 if error>.00012:raise ValueError('PALM_IK_AFTER_SOLUTION_ERROR_'+str(error))
 return {'palmErrorM':error,'target':grip,'stretch':stretch,'palmWorld':palm,
         'wristOffsetCorrectedM':length(palm_local)}

def f32_time(value):
 """Return the exact finite IEEE-754 float32 timestamp stored by glTF."""
 v=float(value)
 if not math.isfinite(v):raise ValueError('ADAPTIVE_TIME_NONFINITE')
 try:return struct.unpack('<f',struct.pack('<f',v))[0]
 except (OverflowError,struct.error) as e:raise ValueError('ADAPTIVE_TIME_UNREPRESENTABLE') from e

def adaptive_key_grid(raw_times,end,lead=LEAD,min_gap=1e-6):
 """Normalize sampled and refined times while preserving branch boundaries.

 A glTF sampler stores IEEE float32, not rounded decimal floats. The v2.0.35
 second attempt reinserted float32 keys alongside decimal 0.23/0.175 anchors,
 producing timestamps separated by ~5e-9 seconds. Use one representable grid,
 coalescing near collisions in favor of mandatory anchors.
 """
 end=float(end)
 if not math.isfinite(end) or end<=lead or min_gap<=0:
  raise ValueError('ADAPTIVE_ATTACK_DURATION_INVALID')
 anchors=sorted(set(f32_time(t) for t in (0.,max(0.,lead-.055),lead,end)))
 if any(y-x<=min_gap for x,y in zip(anchors,anchors[1:])):
  raise ValueError('ADAPTIVE_ANCHOR_COLLISION')
 # Protected boundaries win over every candidate within min_gap, including
 # floats from a previously baked sampler or refinement near an anchor.
 samples=[]
 for raw in raw_times:
  t=float(raw)
  if not math.isfinite(t):raise ValueError('ADAPTIVE_TIME_NONFINITE')
  if t < -min_gap or t>end+min_gap:
   raise ValueError('ADAPTIVE_TIME_OUT_OF_RANGE_'+repr(t))
  t=f32_time(max(0.,min(end,t)))
  if t < anchors[0] or t>anchors[-1]:raise ValueError('ADAPTIVE_TIME_ROUNDING_OVERFLOW')
  samples.append(t)
 kept=list(anchors)
 # Sorted insertion with neighboring collision checks prevents duplicate keys
 # after on-disk float32 conversion, without moving any protected boundary.
 import bisect
 for t in sorted(set(samples)):
  i=bisect.bisect_left(kept,t)
  if i>0 and t-kept[i-1]<=min_gap:continue
  if i<len(kept) and kept[i]-t<=min_gap:continue
  kept.insert(i,t)
 if any(y-x<=min_gap for x,y in zip(kept,kept[1:])):
  raise ValueError('ADAPTIVE_KEY_TIME_GRID_INVALID')
 if not all(a in kept for a in anchors):raise ValueError('ADAPTIVE_MISSING_BRANCH_ANCHOR')
 if any(f32_time(t)!=t for t in kept):raise ValueError('ADAPTIVE_FLOAT32_ROUNDTRIP_DRIFT')
 return kept


# v2.0.39: only left chain and shield scale are authored in the added clip.
# The entire previous 43rd clip, including all right-arm channels, remains
# untouched. Pose-phase timestamps and animation duration are not moved.
SHRINK_END_FRACTION=.76
WRIST_MAX_DEGREES=34.

def knuckle_axis_local(pose,ids,pa,h):
 names=[n for n in KNUCKLES if n in ids]
 if len(names)<4:raise ValueError('LEFT_FINGER_KNUCKLE_BASIS_INCOMPLETE')
 H=ids[LEFT[2]];hq=world(H,pose,pa,h)[1]
 a=position(ids[names[0]],pose,pa,h);b=position(ids[names[-1]],pose,pa,h)
 return unit(rotate(h,h.qi(hq),sub(a,b)))

def corrected_wrist_world(pose,ids,pa,h,knuckle_local,t):
 W=ids[LEFT[2]];R=ids[WEAPON]
 old=world(W,pose,pa,h)[1];rq=world(R,pose,pa,h)[1]
 across=unit(rotate(h,old,knuckle_local))
 shaft=unit(rotate(h,rq,(0.,1.,0.)))
 if dot(across,shaft)<0:shaft=mul(shaft,-1.)
 direction=h.normq(between(h,across,shaft))
 angle=2.*math.degrees(math.acos(min(1.,abs(direction[3]))))
 factor=min(1.,WRIST_MAX_DEGREES/max(angle,1e-7))
 # Keep anticipation exactly as published; fade wrist correction in during
 # the original pickup phase, not by shifting any attack pose time.
 if t<=LEAD:return old
 fade=min(1.,max(0.,(t-LEAD)/.12));fade=fade*fade*(3-2*fade)
 return h.qslerp(old,h.qm(direction,old),factor*fade)

def solve_left_wrist(pose,ids,pa,h,palm_local,desired):
 A,B,H=[ids[n] for n in LEFT];R=ids[WEAPON]
 P=position(A,pose,pa,h);E=position(B,pose,pa,h)
 rp,rq,_=world(R,pose,pa,h);grip=add(rp,rotate(h,rq,GRIP_LOCAL))
 goal=sub(grip,rotate(h,desired,palm_local))
 a=length(pose[B]['translation']);b=length(pose[H]['translation']);d=length(sub(goal,P))
 stretch=max(1.,d/max(a+b-1e-5,1e-6))
 if stretch>1.065:raise ValueError('LEFT_ARM_STRETCH_EXCEEDS_SIX_POINT_FIVE_PERCENT')
 a*=stretch;b*=stretch
 axis=unit(sub(goal,P));perp=sub(sub(E,P),mul(axis,dot(sub(E,P),axis)))
 if length(perp)<1e-7:perp=cross(axis,(0.,1.,0.) if abs(axis[1])<.9 else (1.,0.,0.))
 x=(a*a-b*b+d*d)/(2*d);height=math.sqrt(max(0.,a*a-x*x))
 elbow=add(add(P,mul(axis,x)),mul(unit(perp),height))
 pose[B]['translation']=mul(pose[B]['translation'],stretch)
 pose[H]['translation']=mul(pose[H]['translation'],stretch)
 err=solve_chain(pose,ids,pa,h,LEFT,goal,elbow,desired)
 handpos,handrot,_=world(H,pose,pa,h)
 palm=add(handpos,rotate(h,handrot,palm_local))
 error=length(sub(palm,grip))
 if err>.0005 or error>.0005:raise ValueError('LEFT_WRIST_SOLVE_CONTACT_FAILED_'+str((err,error)))
 return {'errorM':error,'stretch':stretch,'wristRotationDeltaDeg':h.qdeg(desired,handrot)}

def identify_shield(js,buf,clip,h,end):
 """Identify shield by actual skin weights, matching the published viewer.

 The model does not name the shield mesh. The viewer identifies its skinned
 geometry by the dominant influence of mixamorig:LeftWeapon.L. Before
 authoring its scale, prove that this joint's skin-weight contribution is
 overwhelmingly confined to that mesh. Never scale an arbitrary node.
 """
 ids=h.name_ids(js)
 name='mixamorig:LeftWeapon.L'
 if name not in ids:raise ValueError('SHIELD_SKIN_BONE_MISSING_'+name)
 bone=ids[name];nodes=js['nodes'];skins=js.get('skins',[]);meshes=js.get('meshes',[])
 metrics=[];total_contribution=0.;candidate_contribution=0.;seen=0
 for ni,node in enumerate(nodes):
  if 'mesh' not in node or 'skin' not in node:continue
  skin=skins[node['skin']];joint_indices=skin.get('joints',[])
  if bone not in joint_indices:continue
  joint_idx=joint_indices.index(bone)
  mesh=meshes[node['mesh']]
  for pi,prim in enumerate(mesh['primitives']):
   at=prim.get('attributes',{})
   if 'JOINTS_0' not in at or 'WEIGHTS_0' not in at:
    raise ValueError('SHIELD_GEOMETRY_WITHOUT_SKIN_ATTRIBUTES_'+str((ni,pi)))
   joints=h.raw_accessor(js,buf,at['JOINTS_0'])
   weights=h.raw_accessor(js,buf,at['WEIGHTS_0'])
   if len(joints)!=len(weights):raise ValueError('SHIELD_SKIN_ACCESSOR_COUNT_MISMATCH')
   count=len(joints); influence=[]
   for js4,ws4 in zip(joints,weights):
    influence.append(sum(float(w) for j,w in zip(js4,ws4) if int(j)==joint_idx))
   amount=sum(influence);mean=amount/max(1,count)
   total_contribution+=amount
   selected=bool(count and mean>.55)
   if selected:candidate_contribution+=amount;seen+=1
   metrics.append({'node':ni,'primitive':pi,'vertices':count,'averageShieldBoneWeight':round(mean,6),'selected':selected})
 if seen!=1 or total_contribution<=0:
  raise ValueError('SHIELD_SKIN_WEIGHT_TARGET_NOT_UNIQUE_'+repr(metrics))
 purity=candidate_contribution/total_contribution
 if purity<.98:raise ValueError('SHIELD_SKIN_WEIGHT_SPILLS_ON_OTHER_MESHES_'+repr((purity,metrics)))
 if bone not in {i for sk in skins for i in sk.get('joints',[])}:
  raise ValueError('SHIELD_JOINT_NOT_IN_SKIN')
 # Require no other mesh to be dominated by the shield joint. The actual
 # scale animation is on this joint, not on its skinned mesh container.
 return bone,{'strategy':'verified_skin_weight_joint','node':bone,
  'shieldPrimitive':[(x['node'],x['primitive']) for x in metrics if x['selected']][0],
  'purity':purity,'metrics':metrics}

def shield_scale_track(js,buf,clip,idx,h,times,end,reason):
 """Preserve onset, extend shrink, and ensure monotonic positive scale.

 For a shield with no authored scale animation, the clip must explicitly
 author a scale channel rather than interpreting the absence as no shield.
 Start after the unchanged 0.23-second anticipation; smoothly reduce to a
 wrist-size charm by the end of the existing clip without retiming poses.
 """
 start=tuple(h.at_time(js,buf,clip,idx,'scale',0.))
 if min(start)<=0:raise ValueError('SHIELD_NONPOSITIVE_INITIAL_SCALE')
 has_channel=any(c['target']['path']=='scale' and c['target']['node']==idx for c in clip['channels'])
 probes=[end*i/300 for i in range(301)]
 delta=lambda v:max(abs(v[k]-start[k])/(abs(start[k])+1e-8) for k in range(3))
 detected=next((t for t in probes if delta(h.at_time(js,buf,clip,idx,'scale',t))>.015),None) if has_channel else None
 onset=max(LEAD,detected) if detected is not None else LEAD
 if onset>=end-.18:raise ValueError('SHIELD_SHRINK_WINDOW_INVALID_'+repr((onset,end)))
 original_final=tuple(h.at_time(js,buf,clip,idx,'scale',end))
 ratios=[original_final[k]/start[k] for k in range(3)]
 # If the source scale was not actually shrinking, create the intended charm
 # target explicitly. Use uniform scaling to avoid distorting the shield.
 shrinking=has_channel and max(ratios)<.8 and min(ratios)>0
 ratio=max(.12,min(.35,sum(ratios)/3)) if shrinking else .22
 final=tuple(v*ratio for v in start)
 finish=end
 # Critical: a continuous smooth easing rather than a shrinking/flickering
 # step or a 0.1 second snap. Keep exact original attack duration.
 out=[]
 for t in times:
  x=min(1.,max(0.,(t-onset)/(finish-onset)))
  q=x*x*(3-2*x)
  out.append(tuple(start[k]*(1-q)+final[k]*q for k in range(3)))
 if any(out[i+1][k]>out[i][k]+1e-7 for i in range(len(out)-1) for k in range(3)):
  raise ValueError('SHIELD_SCALE_FLICKER_MONOTONICITY_FAILED')
 return out,{'node':idx,'resolution':reason,'existingScaleChannel':has_channel,
   'onsetSeconds':onset,'newEndSeconds':finish,'originalEndSeconds':detected,
   'initialScale':start,'finalScale':final,'targetRatio':ratio,
   'sourceHadShrinkingScale':shrinking}

def make_variant(input_path,core):
 js,buf=core.read_glb(input_path);names=[a.get('name') for a in js['animations']]
 if len(names)!=43 or len(set(names))!=43 or names[-1]!=PREVIOUS:raise ValueError('INPUT_MUST_BE_EXACT_APPROVED_FOR_REVISION_V236_43_CLIP_GLB')
 clip=js['animations'][-1];start,end=core.range_times(js,buf,clip)
 if abs(start)>.001 or not .5<end<2.:raise ValueError('UNCHANGED_ATTACK_TIMING_MISMATCH')
 ids=core.name_ids(js);pa=core.parents(js)
 if not set(LEFT+(WEAPON,)+KNUCKLES)<=set(ids):raise ValueError('LEFT_WRIST_FINGER_BONES_MISSING')
 first=snapshot(js,buf,clip,0.,core)
 palm,palmmeta=palm_local_offset(first,ids,pa,core)
 knuckle=knuckle_axis_local(first,ids,pa,core)
 shield,shield_reason=identify_shield(js,buf,clip,core,end)
 old_keys=[]
 for sampler in clip['samplers']:
  old_keys.extend(x[0] for x in core.raw_accessor(js,buf,sampler['input']))
 # Original key times retained and supplemented with fixed-density samples;
 # the clip duration, original pose events and all old clips remain unchanged.
 times=adaptive_key_grid([*old_keys,*[end*i/240 for i in range(241)]],end)
 scales,shieldmeta=shield_scale_track(js,buf,clip,shield,core,times,end,shield_reason)
 rows=[];poses=[]
 for t in times:
  pose=snapshot(js,buf,clip,t,core)
  if t>LEAD:
   desired=corrected_wrist_world(pose,ids,pa,core,knuckle,t)
   result=solve_left_wrist(pose,ids,pa,core,palm,desired)
   rows.append({'time':t,**result})
  poses.append(pose)
 # Preserve previous v236 clip's right arm, body, shaft and pose-event tracks
 # byte-for-byte via original sampler references. Replace only left chain and
 # shield scale within the appended new clip.
 out=copy.deepcopy(js);app=core.Appender(out,buf)
 new=copy.deepcopy(clip);new['name']=VARIANT
 allowed={(ids[n],p) for n in LEFT for p in ('rotation','translation')}
 allowed.add((shield,'scale'))
 new['channels']=[ch for ch in new['channels'] if (ch['target']['node'],ch['target']['path']) not in allowed]
 for n in LEFT:
  for path in ('rotation','translation'):
   app.add(new,ids[n],path,times,[pose[ids[n]][path] for pose in poses])
 app.add(new,shield,'scale',times,scales)
 app.js['animations'].append(new)
 return app.js,bytes(app.bin),{'schema':V,'inputCount':43,'outputCount':44,'originalClipName':PREVIOUS,
  'newVariant':VARIANT,'frames':len(times),'leadSecondsPreserved':LEAD,'durationSecondsPreserved':end,
  'palm':palmmeta,'shield':shieldmeta,'leftWrist':{'maxSampleContactErrorM':max(r['errorM'] for r in rows),
  'maxArmStretchFactor':max(r['stretch'] for r in rows)},'rightArmSourceSamplersReusedExactly':True,
  'poseTimingUnchanged':True,'ownerVisualAcceptance':'PENDING'}

def run(input_path,output_path,report_path,core,expected_sha=INPUT_SHA):
 input_path=pathlib.Path(input_path);output_path=pathlib.Path(output_path);report_path=pathlib.Path(report_path)
 if core.digest(input_path)!=expected_sha:raise ValueError('EXACT_V236_SOURCE_SHA_INVALID')
 if output_path.exists() or report_path.exists():raise ValueError('OUTPUT_COLLISION')
 old,oldbin=core.read_glb(input_path)
 output,data,diag=make_variant(input_path,core)
 if output['animations'][:43]!=old['animations'] or not data.startswith(oldbin):raise ValueError('SOURCE_43_CLIPS_NOT_PRESERVED')
 for k in ('nodes','meshes','skins','materials','textures','images','scenes'):
  if output.get(k)!=old.get(k):raise ValueError('SOURCE_GEOMETRY_CHANGED_'+k)
 output_path.parent.mkdir(parents=True,exist_ok=True);core.glb_save(output,data,output_path)
 actual,actualbin=core.read_glb(output_path)
 if len(actual['animations'])!=44 or actual['animations'][:43]!=old['animations'] or not actualbin.startswith(oldbin):
  raise ValueError('REOPEN_44_CLIP_PRESERVATION_FAILED')
 diag['inputSHA256']=expected_sha;diag['outputSHA256']=core.digest(output_path)
 report_path.write_text(json.dumps(diag,indent=2,sort_keys=True)+'\n')
 return diag
