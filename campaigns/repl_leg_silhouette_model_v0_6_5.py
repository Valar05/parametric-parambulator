#!/usr/bin/env python3
"""Repl v0.6.5: anatomically signed, observable four-hoof swing arcs.

This is an owner-corrected candidate, NOT owner-accepted locomotion. All old
skin/mesh/rest data and all stance frames are left identical. Motion is forward
travel only. A separately verified Termux runner controls canonical Git writes.

The critical regression from v0.6.4.1: measuring median body-vertex rearward
translation does NOT certify joint silhouette and the forehoof toe was used as
an exact swing target, suppressing much of the visible ankle articulation.
This solver controls sagittal segment directions directly, with the true rig
bone hierarchy and true world-space transforms, then confirms the physical
skinned mesh and all 3 traveling walk clips.
"""
from __future__ import annotations
import hashlib,json,math,struct,statistics
VERSION='0.6.5'
CANON='assets/repl/Repl.glb'
SOURCE_SHA='b6b5df58df8eeee79ffc2f3beabd1de15af6186988dd97e98610c4badaa48604'
SOURCE_BLOB='c59179a61f742838e124cc4e21b846f878e3150c'
FRAMES=97;PER_STRIDE=32;STEP=.04;STRIDE=1.28;STANCE=.62;TRAVEL=.96
WALK_NAMES=('REPL_WALK_01_FORWARD_FOUR_BEAT_IK','REPL_WALK_02_FORWARD_BODY_WEIGHT_TRANSFER','REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED')
LEGS={
 'LF':{'phase':.25,'segment_targets':(('Bone_015','Bone_014',12.),('Bone_014','Bone_013',-20.),('Bone_013','Bone_012',-23.),('Bone_012','Bone_011',145.))},
 'RF':{'phase':.75,'segment_targets':(('Bone_021','Bone_020',12.),('Bone_020','Bone_019',-20.),('Bone_019','Bone_018',-23.),('Bone_018','Bone_017',145.))},
 'LH':{'phase':0.,'segment_targets':(('Bone_025','Bone_024',-10.),('Bone_024','Bone_023',-16.)),'hoof':'Bone_023'},
 'RH':{'phase':.5,'segment_targets':(('Bone_030','Bone_029',-10.),('Bone_029','Bone_028',-16.)),'hoof':'Bone_028'},
}
CHANGED_NAMES={a for l in LEGS.values() for a,b,target in l['segment_targets']}|{'Bone_023','Bone_028'}
class Blocked(RuntimeError):pass
def need(ok,c):
 if not ok:raise Blocked(c)
def sha(x):return hashlib.sha256(x).hexdigest()
def gitblob(x):return hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()
def parse_glb(data):
 need(len(data)>28 and data[:4]==b'glTF','INVALID_GLB')
 _,v,length=struct.unpack_from('<4sII',data)
 need(v==2 and length==len(data),'INVALID_GLB_HEADER')
 n,typ=struct.unpack_from('<I4s',data,12);need(typ==b'JSON','BAD_JSON_CHUNK')
 p=20+n;length,typ=struct.unpack_from('<I4s',data,p)
 need(typ==b'BIN\0' and p+8+length==len(data),'BAD_BIN_CHUNK')
 return json.loads(data[20:p]),data[p+8:]
def pos(world,i):return tuple(world[i][k] for k in (3,7,11))
def axis(world,i):
 # World +X represented in the bone's LOCAL coordinates (world R^T e_x).
 # A hoof joint's local +X can point opposite world +X: never guess sign.
 r=(world[i][0],world[i][1],world[i][2]);d=math.sqrt(sum(v*v for v in r))
 need(d>1e-8,'BAD_LOCAL_WORLD_X_CONVERSION')
 return tuple(v/d for v in r)
def norm(q):
 d=math.sqrt(sum(v*v for v in q));need(d>1e-10,'BAD_QUATERNION')
 return tuple(v/d for v in q)
def theta(a,b):
 # Signed sagittal inclination from DOWN; + toward head (+Z), - to rear.
 return math.degrees(math.atan2(b[2]-a[2],a[1]-b[1]))
def phase(label,t):
 u=(t/STRIDE-LEGS[label]['phase'])%1.
 if u>.9999999:u=0.
 return u,u<STANCE
def pulse(u):
 if u<STANCE:return 0.
 s=(u-STANCE)/(1.-STANCE)
 return max(0.,math.sin(math.pi*s))**1.1

def tracks(doc,binary,clip,base):
 out={}
 for ch in clip['channels']:
  sm=clip['samplers'][ch['sampler']];key=(ch['target']['node'],ch['target']['path'])
  need(key not in out and sm.get('interpolation')=='LINEAR','DUPLICATE_OR_NONLINEAR_TRACK')
  vals=base.accessor(doc,binary,sm['output']);ts=base.accessor(doc,binary,sm['input'])
  need(len(vals)==len(ts)==FRAMES,'BAD_FRAME_COUNT')
  need(max(abs(v[0]-i*STEP) for i,v in enumerate(ts))<5e-6,'BAD_FRAME_TIMING')
  out[key]={'rows':vals,'sampler':sm,'times':ts}
 return out

def animate_frame(doc,base,name_map,leg,pose,frame,original_world):
 u,stance=phase(leg,frame*STEP)
 if stance:return pose,{}
 amp=pulse(u);spec=LEGS[leg]['segment_targets'];newpose=dict(pose)
 # Record the previous pose's visible segments once. Target those segment
 # directions, not fabricated local Euler angles or a misleading mesh centroid.
 origins={a:theta(pos(original_world,name_map[a]),pos(original_world,name_map[b]))
          for a,b,_ in spec}
 for a,b,target in spec:
  world=base.world_matrices(doc,newpose)
  actual=theta(pos(world,name_map[a]),pos(world,name_map[b]))
  want=origins[a]+amp*(target-origins[a])
  correction=actual-want
  need(abs(correction)<130.,'EXCESSIVE_PHYSICAL_HINGE_CORRECTION:'+leg+':'+a+':'+str(correction))
  n=name_map[a];q=newpose.get(n,base.node_rotation(doc['nodes'][n]))
  newpose[n]=norm(base.qmul(q,base.axisq(axis(world,n),correction)))
 if leg in ('LH','RH'):
  # The actual hind terminal hoof bone is weighted only lightly, so preserve
  # existing rotation and add a noticeable but bounded separate toe roll.
  world=base.world_matrices(doc,newpose);n=name_map[LEGS[leg]['hoof']]
  q=newpose.get(n,base.node_rotation(doc['nodes'][n]))
  newpose[n]=norm(base.qmul(q,base.axisq(axis(world,n),-42.*amp)))
 after=base.world_matrices(doc,newpose)
 return newpose,{a:theta(pos(after,name_map[a]),pos(after,name_map[b])) for a,b,_ in spec}

def make_candidate(source,base,progress=None,require_hash=True):
 if require_hash:need(sha(source)==SOURCE_SHA,'SOURCE_NOT_EXACT_v0.6.4.1')
 doc,bin0=parse_glb(source)
 need(len(doc['nodes'])==53 and len(doc['skins'][0]['joints'])==50 and len(doc['animations'])==6,'CANONICAL_RIG_OR_CLIPS_CHANGED')
 for i,name in enumerate(WALK_NAMES):need(doc['animations'][i+3]['name']==name,'TRAVELING_WALK_ORDER_CHANGED')
 names={n.get('name'):i for i,n in enumerate(doc['nodes']) if n.get('name')}
 root=names['Bone_000'];origroot=list(doc['nodes'][root].get('translation',(0,0,0)))
 parents={child:i for i,n in enumerate(doc['nodes']) for child in n.get('children',[])}
 for leg,d in LEGS.items():
  for a,b,_ in d['segment_targets']:
   need(a in names and b in names and parents.get(names[b])==names[a],
       'REAL_BONE_CHAIN_CHANGED:'+leg+':'+a+'>'+b)
  if leg[1]=='H':need(d['hoof'] in names,'HIND_HOOF_MISSING')
 oldstruct={k:json.dumps(doc[k],sort_keys=True) for k in ('meshes','nodes','skins')}
 oldclips=json.dumps(doc['animations'][:3],sort_keys=True)
 binout=bytearray(bin0);before=[tracks(doc,bin0,c,base) for c in doc['animations'][3:]]
 monitor={};changed=0
 try:
  for stage,tr in enumerate(before,1):
   need((root,'translation') in tr,'FORWARD_TRAVEL_TRACK_MISSING')
   for name in CHANGED_NAMES:need((names[name],'rotation') in tr,'EXISTING_TRACK_MISSING:'+name)
   rows={names[name]:[] for name in CHANGED_NAMES}
   report={}
   for fr in range(PER_STRIDE):
    doc['nodes'][root]['translation']=list(tr[(root,'translation')]['rows'][fr])
    original={k:v['rows'][fr] for (k,path),v in tr.items() if path=='rotation'}
    oldworld=base.world_matrices(doc,original)
    for leg,d in LEGS.items():
     proposed,angles=animate_frame(doc,base,names,leg,original,fr,oldworld)
     u,stance=phase(leg,fr*STEP)
     if (not stance) and .40<((u-STANCE)/(1-STANCE))<.60:
      report[leg]=angles
     for a,b,_ in d['segment_targets']:
      rows[names[a]].append(tuple(proposed[names[a]]))
     if leg in ('LH','RH'):rows[names[d['hoof']]].append(tuple(proposed[names[d['hoof']]]))
   need(set(rows)=={names[n] for n in CHANGED_NAMES},'INCOMPLETE_FOUR_LEG_CONTROL_SET')
   for n,v in rows.items():
    full=v*3+[v[0]]
    need(len(full)==FRAMES,'INCOMPLETE_REPEATING_STRIDES')
    acc=base.emit_accessor(doc,binout,full,5126,'VEC4')
    tr[(n,'rotation')]['sampler']['output']=acc
    changed+=1
   doc['animations'][stage+2].setdefault('extras',{})['ownerCorrectedDistalSilhouette']={
    'version':VERSION,'foreCarpus':'forward-leading fold','foreCannonAndPastern':'backward-arc',
    'foreToe':'visible toe lift','hindDistal':'backward-arc with stronger toe roll',
    'contactTiming':'identical','rootTravel':'identical','humanVisualAcceptance':'PENDING'}
   monitor[f'stage_{stage}_mid_swing_angles']=report
   if progress:progress(f'STAGE_{stage}_ALL_FOUR_VISUAL_JOINTS_PROJECTED')
  doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{}).update({
   'version':VERSION,'lowerLimbs':'FOUR_HOOF_SILHOUETTE_PROJECTED_IN_WORLD_SPACE',
   'humanVisualVerdict':'PENDING'})
  doc['nodes'][root]['translation']=origroot
  for name,serial in oldstruct.items():need(json.dumps(doc[name],sort_keys=True)==serial,'CANONICAL_STRUCTURE_CHANGED:'+name)
  need(json.dumps(doc['animations'][:3],sort_keys=True)==oldclips,'PREVIOUS_MANETAIL_CLIPS_CHANGED')
  need(bytes(binout[:len(bin0)])==bin0,'PREVIOUS_MODEL_BUFFER_REWRITTEN')
  result=base.glb_encode(doc,bytes(binout))
 finally:doc['nodes'][root]['translation']=origroot
 summary=verify(source,result,base,require_hash=require_hash)
 summary.update({'source_sha256':sha(source),'output_sha256':sha(result),
                 'changed_existing_animation_channels':changed,'stage_angles':monitor,
                 'source_provenance':'exact v0.6.4.1 on device; structural surrogate host only',
                 'human_visual_acceptance':'PENDING'})
 return result,summary

def verify(before,after,base,require_hash=True):
 if require_hash:need(sha(before)==SOURCE_SHA,'BAD_SOURCE_SHA')
 old,ob=parse_glb(before);new,nb=parse_glb(after)
 for field in ('nodes','skins','meshes'):
  need(old[field]==new[field],'UNAUTHORIZED_'+field.upper()+'_CHANGE')
 need(old['animations'][:3]==new['animations'][:3],'APPROVED_HAIR_TAIL_ANIMATIONS_CHANGED')
 need(nb[:len(ob)]==ob,'OLD_MODEL_BUFFER_PREFIX_CHANGED')
 need(len(new['animations'])==6,'WALK_ORIGINAL_CLIP_COUNT_CHANGED')
 names={v.get('name'):i for i,v in enumerate(new['nodes'])}
 root=names['Bone_000'];saved=list(new['nodes'][root].get('translation',(0,0,0)))
 beforetracks=[tracks(old,ob,c,base) for c in old['animations'][3:]]
 aftertracks=[tracks(new,nb,c,base) for c in new['animations'][3:]]
 info={'stage':{},'stance_max_joint_displacement':0.,'measured_swing_angles':{},
       'peak_swing_toe_delta':{},'max_step_rotation_degrees':0.,
       'max_root_travel_deviation':0.,'minimum_swing_surface_height':{}}
 body=new['meshes'][0]['primitives'][0];a=body['attributes']
 xyz=base.accessor(new,nb,a['POSITION']);joints=base.accessor(new,nb,a['JOINTS_0']);wts=base.accessor(new,nb,a['WEIGHTS_0'])
 ids={}
 for leg in LEGS:
  sign=-1 if leg[0]=='L' else 1
  indices=[i for i,p in enumerate(xyz) if p[1]<.13 and p[0]*sign>.05 and (p[2]>.14 if leg[1]=='F' else p[2]<-.62)]
  need(len(indices)>90,'HOOF_SKIN_WITNESSES_MISSING:'+leg)
  ids[leg]=indices
 maxstance=0.;maxstep=0.;maxheight=0.
 try:
  for stage,(prev,curr) in enumerate(zip(beforetracks,aftertracks),1):
   need(set(prev)==set(curr),'EXTRA_OR_MISSING_GAIT_TRACKS')
   for key,v in prev.items():
    if key[1]=='rotation' and new['nodes'][key[0]].get('name') in CHANGED_NAMES:continue
    need(v['rows']==curr[key]['rows'],'OUTSIDE_OF_FOUR_LEG_SWING_CHANGED:'+str(key))
   oldroot=prev[(root,'translation')]['rows'];newroot=curr[(root,'translation')]['rows']
   need(oldroot==newroot,'MOVING_ROOT_OR_BODY_TRAVEL_CHANGED')
   need(abs(newroot[-1][2]-newroot[0][2]-TRAVEL)<.00001,'NO_FORWARD_TRAVEL')
   for leg,d in LEGS.items():
    base_swing=[];candidate_swing=[];miny=math.inf;test_segment_names=[a for a,b,_ in d['segment_targets']]
    for fr in range(PER_STRIDE):
     docroot=new['nodes'][root];docroot['translation']=list(newroot[fr]);u,stance=phase(leg,fr*STEP)
     pose0={k:v['rows'][fr] for (k,p),v in prev.items() if p=='rotation'}
     pose1={k:v['rows'][fr] for (k,p),v in curr.items() if p=='rotation'}
     if stance:
      for name in test_segment_names+([d['hoof']] if 'hoof' in d else []):
       n=names[name]
       need(prev[(n,'rotation')]['rows'][fr]==curr[(n,'rotation')]['rows'][fr],
            'PLANTED_BONE_CHANGED:'+leg+':'+name)
      continue
     oldworld=base.world_matrices(new,pose0);newworld=base.world_matrices(new,pose1)
     oldskin=base.skin_matrices(new,ob,oldworld);newskin=base.skin_matrices(new,nb,newworld)
     skin_old=[base.deform_vertex(xyz[i],joints[i],wts[i],oldskin) for i in ids[leg]]
     skin_new=[base.deform_vertex(xyz[i],joints[i],wts[i],newskin) for i in ids[leg]]
     miny=min(miny,min(p[1] for p in skin_new))
     swing=(u-STANCE)/(1.-STANCE)
     if .39<swing<.61:
      angles={a:theta(pos(newworld,names[a]),pos(newworld,names[b])) for a,b,_ in d['segment_targets']}
      for a,b,target in d['segment_targets']:
       original_angle=theta(pos(oldworld,names[a]),pos(oldworld,names[b]))
       expected=original_angle+pulse(u)*(target-original_angle)
       need(abs(angles[a]-expected)<1.5,'ACTUAL_SAGITTAL_BEND_IN_WRONG_DIRECTION:'+leg+':'+a+':'+str((angles[a],expected)))
       need(abs(angles[a]-target)<9.,'NO_VISIBLE_MID_SWING_CORRECTION:'+leg+':'+a)
      info['measured_swing_angles'][f'{stage}_{leg}_{fr}']={k:round(v,3) for k,v in angles.items()}
      base_swing.append(max(math.dist(a,b) for a,b in zip(skin_old,skin_new)))
      candidate_swing.append(math.dist(pos(newworld,names[d['segment_targets'][-1][1]]),pos(oldworld,names[d['segment_targets'][-1][1]])))
    need(len(candidate_swing)>=1,'MISSING_MID_SWING_WITNESS:'+leg)
    info['peak_swing_toe_delta'][f'{stage}_{leg}']=max(candidate_swing)
    need(max(candidate_swing)>.045,'VISIBLE_ARTICULATION_TOO_SUBTLE:'+leg)
    need(miny>-.075,'HOOF_INTERSECTS_GROUND_EXCESSIVELY:'+leg+':'+str(miny))
    info['minimum_swing_surface_height'][f'{stage}_{leg}']=miny
    for a,b,_ in d['segment_targets']:
     arr=curr[(names[a],'rotation')]['rows']
     need(tuple(arr[0])==tuple(arr[-1]),'STRIDE_LOOP_JOINT_MISMATCH:'+a)
     for x,y in zip(arr,arr[1:]):
      dot=min(1,abs(sum(i*j for i,j in zip(x,y))))
      deg=math.degrees(2*math.acos(dot))
      maxstep=max(maxstep,deg)
   info['stage'][str(stage)]='PASS'
 finally:new['nodes'][root]['translation']=saved
 info['max_step_rotation_degrees']=maxstep
 need(maxstep<52.,'DISCONTINUITY_TOO_LARGE:'+str(maxstep))
 return info
