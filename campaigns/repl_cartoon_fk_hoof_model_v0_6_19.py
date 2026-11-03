#!/usr/bin/env python3
"""Repl v0.6.19: bounded two-joint front stance repair, fail closed.

It tests *whole* gait, source and candidate, before allowing any GLB write.
No front distal/toe/hoof, hind, root, hair or nonwalk channel edits.
"""
import copy,hashlib,json,math
VERSION='0.6.19'
SOURCE_SHA='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
FRAMES=97
FRONT={'LF':('Bone_015','Bone_014','Bone_013'), 'RF':('Bone_021','Bone_020','Bone_019')}
EDITED={n for names in FRONT.values() for n in names[:2]}
class Blocked(RuntimeError):pass
def need(cond,why):
 if not cond:raise Blocked(why)
def sha(x):return hashlib.sha256(x).hexdigest()
def norm(q):
 x=math.sqrt(sum(v*v for v in q));need(x>1e-9,'ZERO_QUATERNION');return tuple(v/x for v in q)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def phase(label,frame):
 u=((frame%32)/32.-(.25 if label=='LF' else .75))%1.
 return u,u<.62

def reference_profiles():
 # Smooth amplitudes. Avoid changing any airborne-swing frame directly;
 # the full-cycle validator rejects any problematic boundary.
 return [
  ('full_stance', [1.]*20),
  ('early_extension', [0.,.33,.67,1,1,1,1,1,.90,.75,.55,.40,.25,.12,0,0,0,0,0,0]),
  ('mid_extension', [0.,.14,.3,.55,.8,1,1,1,.85,.65,.43,.25,.12,0,0,0,0,0,0,0]),
  ('small_extension', [0.,.10,.25,.4,.55,.55,.55,.55,.45,.35,.23,.1,0,0,0,0,0,0,0,0]),
 ]

def apply(source, ref, profile, base, previous):
 need(sha(source)==SOURCE_SHA,'CANONICAL_SOURCE_CHANGED__DO_NOT_EDIT')
 doc,binary=previous.parse_glb(source);names=previous.inspect_source(doc)
 need(ref['version']=='0.6.19' and set(ref['degree_offsets'])=={'1_LF','1_RF','2_LF','2_RF'},'REFERENCE_WRONG_VERSION_OR_LEG_SET')
 outbin=bytearray(binary)
 amps=profile[1]
 for stage in range(1,4):
  tr=previous.tracks(doc,binary,doc['animations'][stage+2],base)
  for leg,bones in FRONT.items():
   for bidx,bonename in enumerate(bones[:2]):
    node=names[bonename];key=(node,'rotation')
    need(key in tr,'FRONT_JOINT_TRACK_MISSING:'+bonename)
    rows=[]
    for frame in range(FRAMES):
     u,on=phase(leg,frame);f=frame%32
     if on:
      j=int(round((u*32)))
      # first stance is f8 for LF, f24 for RF; crosses wrap on RF
      j=(f-(8 if leg=='LF' else 24))%32
      need(j<20,'STANCE_WINDOW_MISMATCH')
      a=amps[j]
     else:a=0.
     deg=ref['degree_offsets'][f'{min(stage,2)}_{leg}'][str(f)][bidx]*a
     q=tuple(tr[key]['rows'][frame])
     rows.append(norm(base.qmul(q,base.axisq((1,0,0),deg))))
    acc=base.emit_accessor(doc,outbin,rows,5126,'VEC4')
    tr[key]['sampler']['output']=acc
  doc['animations'][stage+2].setdefault('extras',{})['replStanceExtensionV0618']={
   'profile':profile[0],'source_sha256':SOURCE_SHA,'humanVisualAcceptance':'PENDING'}
 doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{}).update({
  'version':VERSION,'humanVisualVerdict':'PENDING','profile':profile[0]})
 return base.glb_encode(doc,bytes(outbin))

def knee_and_reach(source,output,base,previous):
 d,bin=previous.parse_glb(output);old,obin=previous.parse_glb(source)
 names=previous.inspect_source(d);root=names['Bone_000']
 saved=tuple(d['nodes'][root].get('translation',(0,0,0)))
 sourcepose=[previous.tracks(old,obin,c,base) for c in old['animations'][3:]]
 dstpose=[previous.tracks(d,bin,c,base) for c in d['animations'][3:]]
 patches={leg:previous.hoof_witnesses(d,bin,base,leg) for leg in FRONT}
 def state(tr,leg,f):
  pose={i:tuple(v['rows'][f]) for (i,path),v in tr.items() if path=='rotation'}
  d['nodes'][root]['translation']=list(tr[(root,'translation')]['rows'][f])
  worlds=base.world_matrices(d,pose)
  mats=base.skin_matrices(d,bin,worlds)
  xyz,js,ws,ids=patches[leg]
  hoof=[base.deform_vertex(xyz[i],js[i],ws[i],mats) for i in ids]
  sh,knee,low=[tuple(worlds[names[n]][k] for k in (3,7,11)) for n in FRONT[leg]]
  v=[sh[i]-knee[i] for i in range(3)];w=[low[i]-knee[i] for i in range(3)]
  cos=dot(v,w)/(math.sqrt(dot(v,v))*math.sqrt(dot(w,w)))
  bend=180.-math.degrees(math.acos(max(-1.,min(1.,cos))))
  return {'bend':bend,'hoof_center_z':sum(p[2] for p in hoof)/len(hoof),
          'relative_z':sum(p[2] for p in hoof)/len(hoof)-sh[2],
          'sole_y':min(p[1] for p in hoof)}
 report={'kinematic_details':{},'min_middle_stance_bend':{},'trailing_reach_gain':{}}
 try:
  for stage in range(1,4):
   for leg in FRONT:
    start=8 if leg=='LF' else 24
    farr=[(start+j)%32 for j in range(20)]
    a=[state(sourcepose[stage-1],leg,f) for f in farr]
    b=[state(dstpose[stage-1],leg,f) for f in farr]
    # At least one measured straight support pose and more trailing reach.
    middle=min(z['bend'] for z in b[4:14])
    gain=a[-1]['relative_z']-b[-1]['relative_z']
    report['min_middle_stance_bend'][f'{stage}_{leg}']=round(middle,4)
    report['trailing_reach_gain'][f'{stage}_{leg}']=round(gain,5)
    report['kinematic_details'][f'{stage}_{leg}']={
     'stance_knee_min':round(min(z['bend'] for z in b),4),
     'stance_knee_max':round(max(z['bend'] for z in b),4),
     'stance_sole_min_y':round(min(z['sole_y'] for z in b),6),
     'prior_last_hoof_relative_shoulder_z':round(a[-1]['relative_z'],6),
     'new_last_hoof_relative_shoulder_z':round(b[-1]['relative_z'],6)}
 finally:d['nodes'][root]['translation']=list(saved)
 return report

def evaluate(source,ref,base,previous,validator):
 failures=[]
 for profile in reference_profiles():
  try:
   output=apply(source,ref,profile,base,previous)
   # Existing full production verifier: 1164 frame & 576 half-frame
   # contact, source locks, forward kick, pitch/roll, hoof clearance.
   physical=validator.verify(source,output,ref,base,previous)
   extra=knee_and_reach(source,output,base,previous)
   for leg in FRONT:
    for stage in range(1,4):
     tag=f'{stage}_{leg}'
     need(extra['min_middle_stance_bend'][tag]<=18.0,
          'STILL_NOT_STRAIGHT_DURING_SUPPORT:'+tag)
     need(extra['trailing_reach_gain'][tag]>=(.010 if leg=='LF' else .020),
          'NOT_ENOUGH_TRAILING_REACH:'+tag)
   physical.update(extra)
   physical['candidate_profile']=profile[0]
   physical['output_sha256']=sha(output)
   return output,physical,failures
  except Exception as exc:
   failures.append({'profile':profile[0], 'failure':str(exc)[:500]})
 raise Blocked('NO_VALID_TWO_JOINT_FULL_CYCLE_PATH__PROTECTED_DISTAL_JOINTS_NOT_AUTHORIZED:'+json.dumps(failures))
