#!/usr/bin/env python3
"""Bake an uninterrupted lance-following two-bone IK grip and a shrinking shield on one new attack clip.

No Blender, ARP, or alternative animation runtime. All original GLB bytes/41 animations remain in-place.
Source accessor math is supplied by the pinned v2.0.31 composer in the same Git repo.
"""
from __future__ import annotations
import copy, json, math, pathlib, sys

V='OBSIDIANTI_SWORD1_SUSTAINED_IK_v2.0.33'
BASE_SHA='9ff2b5423b4bf5fea1bf67295b52d848803381699fede56164aca9ce65bea9b7'
ATTACK='Vanguard_SwordAttack1'
SPEAR='Lionheart_Light1'
VARIANT='Vanguard_SwordAttack1_TwoHand_GripIK'
LEAD=0.23
FPS=90
GRIP_LOCAL=(-0.018,-0.235,0.0) # RightWeapon.R coordinates; local -Y points toward butt, not blade tip.
CHARM_SIZE=0.08
CHARM_WRIST_OFFSET=0.031
NAMES={'shoulder':'mixamorig:LeftArm','elbow':'mixamorig:LeftForeArm','wrist':'mixamorig:LeftHand',
       'left_weapon':'mixamorig:LeftWeapon.L','right_weapon':'mixamorig:RightWeapon.R'}


def norm(v):return math.sqrt(sum(x*x for x in v))
def plus(a,b):return tuple(x+y for x,y in zip(a,b))
def minus(a,b):return tuple(x-y for x,y in zip(a,b))
def times(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):
 d=norm(v)
 if d<1e-10:raise ValueError('DEGENERATE_IK_VECTOR')
 return times(v,1.0/d)
def lerp(a,b,f):return tuple(x+(y-x)*f for x,y in zip(a,b))
def ease(x):
 x=max(0.,min(1.,x));return x*x*(3-2*x)
def quat_rotate(h,q,v):
 x,y,z,w=h.normq(q)
 vec=(x,y,z)
 t=times(cross(vec,v),2.)
 return plus(plus(v,times(t,w)),cross(vec,t))
def between(h,a,b):
 u=unit(a);v=unit(b);d=max(-1.,min(1.,dot(u,v)))
 if d>1-1e-9:return (0.,0.,0.,1.)
 if d<-1+1e-9:
  alt=(1.,0.,0.) if abs(u[0])<.8 else (0.,1.,0.)
  axis=unit(cross(u,alt));return (axis[0],axis[1],axis[2],0.)
 xyz=cross(u,v);return h.normq((xyz[0],xyz[1],xyz[2],1.+d))


def all_trs(js,dat,clip,t,h):
 # Capture explicit sampled local TRS for all skinned nodes; animation set has one rest skeleton.
 return {i:{p:tuple(h.at_time(js,dat,clip,i,p,t)) for p in ('translation','rotation','scale')}
         for i in range(len(js['nodes']))}

def blend_trs(a,b,f,h):
 result={}
 for i in a:
  result[i]={}
  for path in ('translation','rotation','scale'):
   result[i][path]=(h.qslerp(a[i][path],b[i][path],f) if path=='rotation'
                  else lerp(a[i][path],b[i][path],f))
 return result

def world(i,pose,pa,h,cache):
 if i in cache:return cache[i]
 a=pose[i];t=a['translation'];q=h.normq(a['rotation']);sc=a['scale']
 if i in pa:
  p,r,s=world(pa[i],pose,pa,h,cache)
  pos=plus(p,quat_rotate(h,r,tuple(t[k]*s[k] for k in range(3))))
  rot=h.qm(r,q)
  scale=tuple(s[k]*sc[k] for k in range(3))
 else:pos,rot,scale=t,q,sc
 cache[i]=(pos,rot,scale)
 return cache[i]

def pworld(i,pose,pa,h):return world(i,pose,pa,h,{})

def ik(pose,ids,pa,h,weight,ref_offset=None):
 """Analytic 2-bone shoulder/elbow/wrist IK with adaptive arm-length stretch.

 IK is 100% locked for every frame in the attack, following an offset fixed in the RightWeapon bone.
 Stretch is represented as lengthened arm-bone child translations, so wrist contact is exact and
 the parent rig, skinned mesh and unrelated nodes are unaltered. Left arm scales are not changed.
 """
 A,B,H,W,R=[ids[NAMES[key]] for key in ('shoulder','elbow','wrist','left_weapon','right_weapon')]
 cache={};P=world(A,pose,pa,h,cache)[0];E0=world(B,pose,pa,h,cache)[0]
 W0=world(H,pose,pa,h,cache)[0]
 rw,rq,_=world(R,pose,pa,h,cache)
 target=plus(rw,quat_rotate(h,rq,GRIP_LOCAL))
 a=norm(pose[B]['translation']);b=norm(pose[H]['translation'])
 d=norm(minus(target,P));
 if d<.01:raise ValueError('IK_TARGET_TOO_CLOSE_TO_SHOULDER')
 # Solve shoulder-elbow-hand from the current natural elbow bend pole.
 direction=unit(minus(target,P));projection=plus(P,times(direction,dot(minus(E0,P),direction)))
 pole=minus(E0,projection)
 if norm(pole)<.01:
  qc=world(A,pose,pa,h,cache)[1]
  pole=cross(direction,quat_rotate(h,qc,(1.,0.,0.)))
  if norm(pole)<.01:pole=cross(direction,(0.,0.,1.))
 pole=unit(pole)
 # Adaptive required stretch, no hidden reach clamp and no false contact report.
 stretch=max(1.0,d/(a+b-1e-5))
 la=a*stretch;lb=b*stretch
 x=(la*la-lb*lb+d*d)/(2*d)
 height=math.sqrt(max(0.,la*la-x*x))
 elbow=plus(plus(P,times(direction,x)),times(pole,height))
 # Source bone +Y axis points to child bone; source q gives joint's natural bend/twist.
 parent_rot=world(pa[A],pose,pa,h,cache)[1]
 arm0=world(A,pose,pa,h,cache)[1]
 arm_to_elbow=quat_rotate(h,arm0,pose[B]['translation'])
 arm_world=h.qm(between(h,arm_to_elbow,minus(elbow,P)),arm0)
 fore0=world(B,pose,pa,h,cache)[1]
 fore_to_hand=quat_rotate(h,fore0,pose[H]['translation'])
 fore_world=h.qm(between(h,fore_to_hand,minus(target,elbow)),fore0)
 if ref_offset is None:
  wrist_orig=world(H,pose,pa,h,cache)[1]
  ref_offset=h.qm(h.qi(rq),wrist_orig)
 wrist_world=h.qm(rq,ref_offset)
 # Blend whole IK result during short preparatory transition only. After prep it is full strength.
 source_arm=pose[A]['rotation'];source_fore=pose[B]['rotation'];source_hand=pose[H]['rotation']
 arm_local=h.qm(h.qi(parent_rot),arm_world)
 fore_local=h.qm(h.qi(arm_world),fore_world)
 hand_local=h.qm(h.qi(fore_world),wrist_world)
 pose[A]['rotation']=h.qslerp(source_arm,arm_local,weight)
 pose[B]['rotation']=h.qslerp(source_fore,fore_local,weight)
 pose[H]['rotation']=h.qslerp(source_hand,hand_local,weight)
 pose[B]['translation']=lerp(pose[B]['translation'],times(pose[B]['translation'],stretch),weight)
 pose[H]['translation']=lerp(pose[H]['translation'],times(pose[H]['translation'],stretch),weight)
 actual=world(H,pose,pa,h,{})[0]
 # At full weight, wrist must reach the moving lance exactly (within numerical tolerance).
 if weight>=1.-1e-7 and norm(minus(actual,target))>.0001:
  raise ValueError('IK_FULL_WEIGHT_FAILED_TO_REACH_LANCE_'+str(norm(minus(actual,target))))
 return {'target':target,'wrist':actual,'error':norm(minus(actual,target)),
         'stretch':stretch,'pole':pole,'elbow':elbow,'referenceOffset':ref_offset}


def charm(pose,ids,pa,h,weight):
 L=ids[NAMES['left_weapon']];H=ids[NAMES['wrist']];B=ids[NAMES['elbow']]
 cache={};wpos,wrot,_=world(H,pose,pa,h,cache);epos=world(B,pose,pa,h,cache)[0]
 weapon_original=world(L,pose,pa,h,cache)[1]
 tip_before=quat_rotate(h,weapon_original,(0.,-1.,0.))
 tip_after=unit(minus(epos,wpos))
 target_world=h.qm(between(h,tip_before,tip_after),weapon_original)
 target_local=h.qm(h.qi(wrot),target_world)
 pose[L]['rotation']=h.qslerp(pose[L]['rotation'],target_local,weight)
 pose[L]['scale']=lerp(pose[L]['scale'],(CHARM_SIZE,)*3,weight)
 # Retain wrist-local weapon attachment, shortening the offset as the charm shrinks.
 pose[L]['translation']=lerp(pose[L]['translation'],(0.,CHARM_WRIST_OFFSET,0.),weight)
 if weight>=1.-1e-7:
  new=world(L,pose,pa,h,{})[1]
  err=math.degrees(math.acos(max(-1.,min(1.,dot(unit(quat_rotate(h,new,(0.,-1.,0.))),tip_after)))))
  if err>.001:raise ValueError('WRIST_CHARM_TIP_ORIENTATION_FAILED_'+str(err))
 return weight


def make_variant(glb,h,proof):
 js,buf=h.read_glb(glb)
 names=h.name_ids(js);pa=h.parents(js)
 expected=[a['name'] for a in js['animations']]
 if len(expected)!=41 or len(set(expected))!=41 or ATTACK not in expected or SPEAR not in expected:
  raise ValueError('EXPECTED_EXACT_41_CLIP_SOURCE_LIBRARY')
 for n in NAMES.values():
  if n not in names:raise ValueError('RIG_IK_BONE_MISSING_'+n)
 sources={a['name']:a for a in js['animations']}
 att=sources[ATTACK];spr=sources[SPEAR]
 at0,at1=h.range_times(js,buf,att);st0,_=h.range_times(js,buf,spr)
 attack_duration=at1-at0
 if not(.4<=attack_duration<=5.):raise ValueError('SWORD_ATTACK1_DURATION_UNEXPECTED')
 nframes=math.ceil((attack_duration+LEAD)*FPS)+1
 ts=[(attack_duration+LEAD)*k/(nframes-1) for k in range(nframes)]
 # Reference hand orientation relative to the moving lance is calibrated from the original attack first frame.
 initial=all_trs(js,buf,att,at0,h)
 lw=world(names[NAMES['wrist']],initial,pa,h,{})[1]
 rw=world(names[NAMES['right_weapon']],initial,pa,h,{})[1]
 ref=h.qm(h.qi(rw),lw)
 initial_spear=all_trs(js,buf,spr,st0,h)
 # Use entire pose blend into attack0 during preparation; original animation starts after 0.23 sec.
 sample_poses=[];diagnostics=[]
 for t in ts:
  if t<LEAD:
   f=ease(t/LEAD);pose=blend_trs(initial_spear,initial,f,h)
  else:
   pose=all_trs(js,buf,att,at0+min(attack_duration,t-LEAD),h)
  w=ease(t/LEAD)
  ikr=ik(pose,names,pa,h,w,ref_offset=ref)
  charm(pose,names,pa,h,w)
  sample_poses.append(pose)
  diagnostics.append({'time':round(t,6),'phase':'PREP' if t<LEAD else 'ATTACK',
       'gripErrorM':round(ikr['error'],8),'stretchFactor':round(ikr['stretch'],6),
       'weaponGripWorld':[round(v,6) for v in ikr['target']]})
 # Only export original changed/animated paths + additional IK/shield channels.
 emit=set()
 for src in (spr,att):
  emit.update((ch['target']['node'],ch['target']['path']) for ch in src['channels']
             if ch['target']['path'] in ('translation','rotation','scale'))
 for n in ('shoulder','elbow','wrist','left_weapon'):
  i=names[NAMES[n]]
  for p in ('translation','rotation','scale'):emit.add((i,p))
 # Save only the 42nd clip; old 41 GLTF animations, original BIN prefix, meshes, skins and material remain identical.
 out=copy.deepcopy(js);app=h.Appender(out,buf)
 new={'name':VARIANT,'samplers':[],'channels':[]}
 for node,path in sorted(emit):
  vals=[frame[node][path] for frame in sample_poses]
  app.add(new,node,path,ts,vals)
 app.js['animations'].append(new)
 return app.js,bytes(app.bin),{
  'schema':V,'status':'BAKED_42_CLIPS_SUSTAINED_TWO_HAND_IK_REVIEW','sourceClipCount':41,
  'outputClipCount':42,'sourceSwordAttack':ATTACK,'initialSpearPose':SPEAR,
  'generatedVariant':VARIANT,'leadSeconds':LEAD,'sourceAttackDurationSeconds':attack_duration,
  'variantDurationSeconds':attack_duration+LEAD,'keyCount':len(ts),'bakeHz':FPS,
  'leftHandIK':'BLENDED_IN_DURING_PREP__LOCKED_AT_EVERY_ATTACK_SAMPLE',
  'gripLocalOnMovingLance':GRIP_LOCAL,'stretchMode':'EXPLICIT_LENGTHENED_LEFT_ARM_CHAIN_TRANSLATIONS',
  'maxStretchFactor':max(x['stretchFactor'] for x in diagnostics),
  'maxGripErrorAfterPrepM':max(x['gripErrorM'] for x in diagnostics if x['phase']=='ATTACK'),
  'shieldScaleAtAttack':CHARM_SIZE,'shieldTipDirection':'TOWARD_LEFT_ELBOW',
  'canonicalModified':False,'ownerVisualAcceptance':'PENDING',
  'frameDiagnostics':diagnostics}


def bake(input_path,output_path,proof_path,h,expected_sha=BASE_SHA):
 input_path=pathlib.Path(input_path);output_path=pathlib.Path(output_path);proof_path=pathlib.Path(proof_path)
 if h.digest(input_path)!=expected_sha:raise ValueError('SOURCE_41_CLIP_SHA_DRIFT')
 if output_path.exists() or proof_path.exists():raise ValueError('VERSIONED_OUTPUT_COLLISION')
 out,data,diag=make_variant(input_path,h,proof_path)
 original,bin0=h.read_glb(input_path)
 if out['animations'][:41]!=original['animations']:raise ValueError('OLD_41_ANIMATIONS_MUTATED')
 for k in ('nodes','skins','meshes','materials','textures','images','scenes','accessors'):
  if out.get(k,'__MISSING__')!=original.get(k,'__MISSING__') and k!='accessors':
   raise ValueError('ORIGINAL_ASSET_CHANGED_'+k)
 if not data.startswith(bin0):raise ValueError('SOURCE_BINARY_PAYLOAD_CHANGED')
 output_path.parent.mkdir(parents=True,exist_ok=True)
 h.glb_save(out,data,output_path)
 reopened,rebin=h.read_glb(output_path)
 if len(reopened['animations'])!=42 or not rebin.startswith(bin0):raise ValueError('OUTPUT_REOPEN_FAILED')
 diag['baseSHA256']=expected_sha;diag['outputSHA256']=h.digest(output_path)
 diag['outputBytes']=output_path.stat().st_size
 proof_path.write_text(json.dumps(diag,indent=2,sort_keys=True)+'\n')
 return diag
