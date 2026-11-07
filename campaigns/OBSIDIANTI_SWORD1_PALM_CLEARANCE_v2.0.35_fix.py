#!/usr/bin/env python3
"""Obsidianti Sword1 two-handed polish: anatomical palm IK plus right-arm torso clearance.

Input: exact published v2.0.33 42-clip review GLB. Output: append only a new 43rd
clip, retaining every input glTF animation, mesh, skin and binary prefix verbatim.
Does not touch the source sword attack, lead-in, shield charm, or canonical GLB.
"""
from __future__ import annotations
import copy,json,math,pathlib

V='OBSIDIANTI_SWORD1_PALM_CLEARANCE_v2.0.35'
INPUT_SHA='899aa3f7f24fb3b36e80a1c96cff7d032dcacf27f990231203ba5c08f2ee066b'
PREVIOUS='Vanguard_SwordAttack1_TwoHand_GripIK'
VARIANT='Vanguard_SwordAttack1_TwoHand_PalmIK_Clearance'
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

def make_variant(input_path,core,old):
 j,buf=core.read_glb(input_path)
 names=[a['name'] for a in j['animations']]
 if len(names)!=42 or len(set(names))!=42 or names[-1]!=PREVIOUS:raise ValueError('INPUT_MUST_BE_EXACT_V233_42_CLIP_GLB')
 ids=core.name_ids(j);pa=core.parents(j)
 required=set(RIGHT+LEFT+CENTER+tuple((WEAPON,)))
 if not required<=set(ids):raise ValueError('REQUIRED_SKELETON_BONES_MISSING_'+repr(sorted(required-set(ids))))
 act=j['animations'][-1];a,b=core.range_times(j,buf,act)
 if abs(a)>.001 or not .5<b<3.:raise ValueError('SWORD_VARIANT_TIME_RANGE_INVALID')
 first=snapshot(j,buf,act,0.,core)
 palm_local,palmeta=palm_local_offset(first,ids,pa,core)
 keycount=math.ceil(b*FPS)+1
 uniform=[b*i/(keycount-1) for i in range(keycount)]
 # Exact branch boundaries are crucial: a quaternion transition must not straddle LEAD.
 raw_times=(CUSTOM_TIMES if CUSTOM_TIMES is not None else uniform)
 ts=sorted(set(round(float(t),10) for t in [0.,b,LEAD,max(0.,LEAD-.055),*raw_times]))
 if not all(0<=t<=b+1e-8 for t in ts) or any(t2-t1<1e-7 for t1,t2 in zip(ts,ts[1:])):
  raise ValueError('ADAPTIVE_KEY_TIME_GRID_INVALID')
 poses=[];rows=[];prev=None
 for t in ts:
  pose=snapshot(j,buf,act,t,core)
  if t >= LEAD:
   rr=fix_right(pose,ids,pa,core,prev)
   ll=fix_left(pose,ids,pa,core,palm_local)
   prev={'elbow':rr['elbow']}
  else:
   # Keep the successful 0.23 sec prep unchanged except for the palm pickup,
   # which fades in smoothly by the attack boundary. The shield's authored
   # rotation/scale transition remains entirely from the source clip.
   rr=None;ll=None
  poses.append(pose)
  if rr is not None:
   rows.append({'t':round(t,6),'palmErrorM':round(ll['palmErrorM'],8),'leftStretch':round(ll['stretch'],5),
     'rightBeforeClearanceM':round(rr['beforeClearanceM'],6),
     'rightAfterClearanceM':round(rr['afterClearanceM'],6),
     'rightPenBefore':rr['oldPenetration'],'rightPenAfter':rr['newPenetration'],
     'rightElbowShiftM':round(rr['elbowShiftM'],6),'rightWristShiftM':round(rr['wristShiftM'],6),
     'shaftAngleErrorDeg':round(rr['spearRotationErrorDeg'],7),'poleDeg':rr['poleDegrees']})
 # Smooth small correction from preexisting keys over the last part of the lead-in.
 # At t==LEAD the previous clip already has full left grip; this does not change
 # the user's requested anticipation duration.
 begin=max(0.,LEAD-.055)
 for n,t in enumerate(ts):
  if begin<t<LEAD:
   pose=poses[n];prepared=copy.deepcopy(pose)
   r=fix_right(prepared,ids,pa,core,None);l=fix_left(prepared,ids,pa,core,palm_local)
   f=(t-begin)/(LEAD-begin);f=f*f*(3.-2*f)
   for bone in (RIGHT+LEFT):
    i=ids[bone]
    for key in ('rotation','translation'):
     pose[i][key]=core.qslerp(pose[i][key],prepared[i][key],f) if key=='rotation' else mix(pose[i][key],prepared[i][key],f)
 # Original animated source tracks are preserved exactly, except for the six arm bones.
 out=copy.deepcopy(j);append=core.Appender(out,buf)
 new={'name':VARIANT,'samplers':[],'channels':[]}
 emit={(ch['target']['node'],ch['target']['path']) for ch in act['channels'] if ch['target']['path'] in ('rotation','translation','scale')}
 for bn in RIGHT+LEFT:
  for path in ('rotation','translation'):emit.add((ids[bn],path))
 for node,path in sorted(emit):
  append.add(new,node,path,ts,[pose[node][path] for pose in poses])
 append.js['animations'].append(new)
 # Crucial: report improvement quantitatively but don't claim physical clearance
 # unless the actual skinned torso geometry passes subsequent owner review.
 report={'schema':V,'status':'43_CLIP_PALM_AND_RIGHT_ARM_CLEARANCE_REVIEW',
   'newVariant':VARIANT,'sourceVariant':PREVIOUS,'inputCount':42,'outputCount':43,
   'frames':len(ts),'fps':FPS,'adaptiveTimeGrid':CUSTOM_TIMES is not None,'leadSecondsPreserved':LEAD,'palm':palmeta,
   'maxPalmContactErrorM':max(x['palmErrorM'] for x in rows),
   'maxWeaponRotationErrorDeg':max(x['shaftAngleErrorDeg'] for x in rows),
   'rightArmClearanceBeforeMinM':min(x['rightBeforeClearanceM'] for x in rows),
   'rightArmClearanceAfterMinM':min(x['rightAfterClearanceM'] for x in rows),
   'averagePenetrationBefore':sum(x['rightPenBefore'] for x in rows)/len(rows),
   'averagePenetrationAfter':sum(x['rightPenAfter'] for x in rows)/len(rows),
   'maxRightHandTranslationM':max(x['rightWristShiftM'] for x in rows),
   'maxLeftStretchFactor':max(x['leftStretch'] for x in rows),
   'samples':rows,'ownerVisualAcceptance':'PENDING','realSkinnedTorsoCollisionVerified':False}
 return append.js,bytes(append.bin),report

def run(input_path,output_path,report_path,core,old,expected_sha=INPUT_SHA):
 input_path=pathlib.Path(input_path);output_path=pathlib.Path(output_path);report_path=pathlib.Path(report_path)
 if core.digest(input_path)!=expected_sha:raise ValueError('EXACT_V233_INPUT_SHA_INVALID')
 if output_path.exists() or report_path.exists():raise ValueError('OUTPUT_COLLISION')
 js,bin0=core.read_glb(input_path)
 out,data,diag=make_variant(input_path,core,old)
 if js['animations']!=out['animations'][:42]:raise ValueError('ORIGINAL_42_ANIMATIONS_MODIFIED')
 for key in ('nodes','skins','meshes','materials','textures','images','scenes'):
  if js.get(key)!=out.get(key):raise ValueError('ORIGINAL_RIG_GEOMETRY_CHANGED_'+key)
 if not data.startswith(bin0):raise ValueError('ORIGINAL_BIN_CHANGED')
 if diag['maxPalmContactErrorM']>.00015:raise ValueError('PALM_CONTACT_GATE_FAILED')
 if diag['maxWeaponRotationErrorDeg']>.03:raise ValueError('LANCE_ANGLE_GATE_FAILED')
 if diag['averagePenetrationAfter']>diag['averagePenetrationBefore']+1e-8:raise ValueError('RIGHT_TORSO_CLEARANCE_REGRESSION')
 output_path.parent.mkdir(parents=True,exist_ok=True)
 core.glb_save(out,data,output_path)
 j2,b2=core.read_glb(output_path)
 if len(j2['animations'])!=43 or j2['animations'][:42]!=js['animations'] or not b2.startswith(bin0):raise ValueError('43_CLIP_REOPEN_DATA_MISMATCH')
 diag['inputSHA256']=expected_sha;diag['outputSHA256']=core.digest(output_path);diag['outputBytes']=output_path.stat().st_size
 report_path.write_text(json.dumps(diag,indent=2,sort_keys=True)+'\n')
 return diag
