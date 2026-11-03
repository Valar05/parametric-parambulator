#!/usr/bin/env python3
"""Repl v0.6.8: cartoon four-beat walk, articulated at real leg joints.

Owner reference is a diagnostic bone-motion demonstration, not a target frame.
Distal hoof-mass bones must NOT counter-rotate or pin to a world IK target.
They remain at a fixed local FK rest quaternion and inherit parent motion.
Only the existing traveling walk clips change. Joint hierarchy, mesh,
skin, approved mane/tail clips, world root travel, and footfall rhythm remain.
"""
from __future__ import annotations
import hashlib,json,math,struct

VERSION='0.6.8'
SOURCE_SHA='c3209b404b5c50842591cfa654142d2f0d84d27eb1acf7779b8d4d504d4508af'
CANON='assets/repl/Repl.glb'
FRAMES=97; PER_STRIDE=32; STEP=.04; STRIDE=1.28; STANCE=.62; TRAVEL=.96
WALK_NAMES=('REPL_WALK_01_FORWARD_FOUR_BEAT_IK','REPL_WALK_02_FORWARD_BODY_WEIGHT_TRANSFER','REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED')
# Local X signs are grounded in owner's Pose Lab diagnostic, not inferred
# from a cartoon anatomy diagram. Driver amounts are LESS than the diagnostic.
# The approved front middle hinge Bone_014/020 is intentionally UNCHANGED.
LEGS={
 'LF':{'phase':.25,'drivers':{'Bone_013':52.},'fixed':('Bone_012',),
       'distal':('Bone_013','Bone_012'),'middle':'Bone_014'},
 'RF':{'phase':.75,'drivers':{'Bone_019':52.},'fixed':('Bone_018',),
       'distal':('Bone_019','Bone_018'),'middle':'Bone_020'},
 'LH':{'phase':0.,'drivers':{'Bone_026':12.,'Bone_025':-14.,'Bone_024':38.},
       'fixed':('Bone_023',),
       'distal':('Bone_024','Bone_023'),'middle':'Bone_025'},
 'RH':{'phase':.5,'drivers':{'Bone_031':12.,'Bone_030':-14.,'Bone_029':38.},
       'fixed':('Bone_028',),
       'distal':('Bone_029','Bone_028'),'middle':'Bone_030'},
}
DRIVERS={x for leg in LEGS.values() for x in leg['drivers']}
FIXED={x for leg in LEGS.values() for x in leg['fixed']}
MODIFIED=DRIVERS|FIXED
FRONT_MIDDLE={'Bone_014','Bone_020'}
class Blocked(RuntimeError):pass
def need(condition,code):
 if not condition:raise Blocked(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def gitblob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def parse_glb(data):
 need(len(data)>28 and data[:4]==b'glTF','INVALID_GLB')
 _,v,length=struct.unpack_from('<4sII',data,0)
 need(v==2 and length==len(data),'INVALID_GLB_HEADER')
 n,typ=struct.unpack_from('<I4s',data,12);need(typ==b'JSON','BAD_JSON_CHUNK')
 p=20+n;count,typ=struct.unpack_from('<I4s',data,p)
 need(typ==b'BIN\0' and p+8+count==len(data),'BAD_BIN_CHUNK')
 return json.loads(data[20:p]),data[p+8:]
def norm(q):
 d=math.sqrt(sum(x*x for x in q));need(d>1e-9,'INVALID_QUATERNION')
 return tuple(x/d for x in q)
def angle(a,b):
 dot=max(-1.,min(1.,abs(sum(x*y for x,y in zip(norm(a),norm(b))))))
 return math.degrees(2*math.acos(dot))
def pos(world,i):return tuple(world[i][k] for k in (3,7,11))
def theta(a,b):return math.degrees(math.atan2(b[2]-a[2],a[1]-b[1]))
def phase(label,frame):
 u=((frame*STEP)/STRIDE-LEGS[label]['phase'])%1.
 if u>1-1e-8:u=0.
 return u,u<STANCE
def pulse(u):
 if u<STANCE:return 0.
 return max(0.,math.sin(math.pi*(u-STANCE)/(1.-STANCE)))**1.10

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

def inspect_source(doc):
 need(len(doc.get('nodes',[]))==53 and len(doc.get('skins',[{}])[0].get('joints',[]))==50,
      'SOURCE_RIG_OR_SKIN_COUNTS_CHANGED')
 need(len(doc.get('animations',[]))==6,'SOURCE_ANIMATION_COUNT_CHANGED')
 need([doc['animations'][3+i]['name'] for i in range(3)]==list(WALK_NAMES),
      'TRAVEL_CLIP_ORDER_CHANGED')
 names={node.get('name'):i for i,node in enumerate(doc['nodes']) if node.get('name')}
 parents={child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
 for label,leg in LEGS.items():
  for name in set(leg['drivers'])|set(leg['fixed'])|{leg['middle'],*leg['distal']}:
   need(name in names,'BONE_MISSING:'+name)
  first,second=leg['distal']
  need(parents.get(names[second])==names[first],'ANATOMICAL_CHAIN_CHANGED:'+label)
  # Hind hoof mass may branch into several NON-ANIMATED deforming chains.
  # The parent hoof is the only controlled channel; descendants must remain FK rest.
  if label=='LH':need(set(doc['nodes'][names['Bone_023']].get('children',[]))==set(names[n] for n in ('Bone_034','Bone_037')),'LH_HOOF_BRANCH_CHANGED')
  if label=='RH':need(set(doc['nodes'][names['Bone_028']].get('children',[]))==set(names[n] for n in ('Bone_039','Bone_042')),'RH_HOOF_BRANCH_CHANGED')
 expected={
  'LF':('Bone_015','Bone_014','Bone_013','Bone_012'),
  'RF':('Bone_021','Bone_020','Bone_019','Bone_018'),
  'LH':('Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'),
  'RH':('Bone_032','Bone_031','Bone_030','Bone_029','Bone_028')}
 for label,chain in expected.items():
  for parent,child in zip(chain,chain[1:]):
   need(parents.get(names[child])==names[parent],
        'WRONG_BONE_CONTROL_CHAIN:'+label+':'+parent+'>'+child)
 return names


# ---------------------------------------------------------------------------
# Verified physical-stance evaluation: compare MOVEMENT of a fixed mesh patch,
# not absolute position of differently posed geometry against the old clip.
# The prior v0.6.7 validator wrongly equated an intentional rest-orientation
# change with sliding, which is an invalid implication.
# ---------------------------------------------------------------------------
def hoof_witnesses(doc,binary,base,label):
 body=doc['meshes'][0]['primitives'][0]['attributes']
 xyz=base.accessor(doc,binary,body['POSITION'])
 joints=base.accessor(doc,binary,body['JOINTS_0'])
 weights=base.accessor(doc,binary,body['WEIGHTS_0'])
 sign=-1 if label[0]=='L' else 1
 ids=[i for i,v in enumerate(xyz) if v[1]<.13 and sign*v[0]>.05 and
      (v[2]>.14 if label[1]=='F' else v[2]<-.62)]
 need(len(ids)>90,'SKIN_HOOF_VERTEX_WITNESS_NOT_FOUND:'+label)
 return xyz,joints,weights,ids

def contact_patch(base,doc,binary,names,root,track,rows,frame,ids,source_pose=False):
 doc['nodes'][root]['translation']=list(track[(root,'translation')]['rows'][frame])
 pose={node:v['rows'][frame] for (node,path),v in track.items() if path=='rotation'}
 if not source_pose:
  pose.update({n:qs[frame%PER_STRIDE] for n,qs in rows.items()})
 world=base.world_matrices(doc,pose)
 skin=base.skin_matrices(doc,binary,world)
 # Stable vertex identities throughout a stance, never reselect the patch.
 points=[base.deform_vertex(ids['xyz'][i],ids['joints'][i],ids['weights'][i],skin)
         for i in ids['sample']]
 return tuple(sum(p[k] for p in points)/len(points) for k in range(3))

def start_frame(label):return int(round(LEGS[label]['phase']*PER_STRIDE))
def stance_frames(label):
 start=start_frame(label)
 return [f for f in range(start,start+PER_STRIDE) if phase(label,f)[1]]

def sample_contact_indices(base,doc,binary,names,root,tr,rows,label):
 xyz,joints,weights,indices=hoof_witnesses(doc,binary,base,label)
 fr=start_frame(label)
 doc['nodes'][root]['translation']=list(tr[(root,'translation')]['rows'][fr])
 pose={node:v['rows'][fr] for (node,path),v in tr.items() if path=='rotation'}
 pose.update({n:qs[fr%PER_STRIDE] for n,qs in rows.items()})
 skin=base.skin_matrices(doc,binary,base.world_matrices(doc,pose))
 heights=[(base.deform_vertex(xyz[i],joints[i],weights[i],skin)[1],i) for i in indices]
 # Only lower portion of a stable hoof patch is a credible planted witness.
 ids=[i for _,i in sorted(heights)[:min(36,max(18,len(indices)//12))]]
 return {'xyz':xyz,'joints':joints,'weights':weights,'sample':ids}

def physical_stance(base,doc,binary,names,root,tr,rows,label,limit=.019):
 sample=sample_contact_indices(base,doc,binary,names,root,tr,rows,label)
 fs=stance_frames(label)
 need(len(fs)>=12,'STANCE_PHASE_WINDOW_MISSING:'+label)
 first=fs[0]
 o0=contact_patch(base,doc,binary,names,root,tr,rows,first,sample,True)
 n0=contact_patch(base,doc,binary,names,root,tr,rows,first,sample,False)
 metrics={'source_drift':0.,'candidate_drift':0.,'added_drift':0.,
          'candidate_hoof_height_min':n0[1], 'candidate_hoof_height_max':n0[1],
          'worst_frame':first,'contact_vertex_count':len(sample['sample'])}
 for fr in fs[1:]:
  old=contact_patch(base,doc,binary,names,root,tr,rows,fr,sample,True)
  new=contact_patch(base,doc,binary,names,root,tr,rows,fr,sample,False)
  od=tuple(old[k]-o0[k] for k in range(3))
  nd=tuple(new[k]-n0[k] for k in range(3))
  original_drift=math.dist((0,0,0),od)
  proposed_drift=math.dist((0,0,0),nd)
  added=math.dist(od,nd)
  if added>metrics['added_drift']:metrics['worst_frame']=fr
  metrics['source_drift']=max(metrics['source_drift'],original_drift)
  metrics['candidate_drift']=max(metrics['candidate_drift'],proposed_drift)
  metrics['added_drift']=max(metrics['added_drift'],added)
  metrics['candidate_hoof_height_min']=min(metrics['candidate_hoof_height_min'],new[1])
  metrics['candidate_hoof_height_max']=max(metrics['candidate_hoof_height_max'],new[1])
 return metrics

def optimize_stance(base,doc,binary,names,root,tr,rows,limit,progress=None):
 # Bounded optional stance-only compensation on existing distal drivers.
 # Hoof-mass bones remain constant at local rest and front middle preserved.
 if limit<=0:return {}
 outcome={}
 for label,spec in LEGS.items():
  lower=spec['distal'][0];node=names[lower]
  frames=stance_frames(label)
  sample=sample_contact_indices(base,doc,binary,names,root,tr,rows,label)
  f0=frames[0]
  old0=contact_patch(base,doc,binary,names,root,tr,rows,f0,sample,True)
  new0=contact_patch(base,doc,binary,names,root,tr,rows,f0,sample,False)
  adjustments={f0:0.}
  for fr in frames[1:]:
   old=contact_patch(base,doc,binary,names,root,tr,rows,fr,sample,True)
   target=tuple(new0[k]+old[k]-old0[k] for k in range(3))
   idx=fr%PER_STRIDE
   original=rows[node][idx]
   def trial(degrees):
    rows[node][idx]=norm(base.qmul(original,base.axisq((1.,0.,0.),degrees)))
    try:
     p=contact_patch(base,doc,binary,names,root,tr,rows,fr,sample,False)
    finally:rows[node][idx]=original
    # Contact target is physical XYZ, with mild continuity regularization.
    return sum((p[k]-target[k])**2 for k in range(3)) + (degrees/1800.)**2
   candidates=[0.]
   n=int(limit//3)
   candidates.extend([float(i*3) for i in range(-n,n+1)])
   chosen=min(candidates,key=trial)
   for shift in (-1.5,-.75,0.,.75,1.5):
    q=max(-limit,min(limit,chosen+shift))
    if trial(q)<trial(chosen):chosen=q
   adjustments[fr]=chosen
   rows[node][idx]=norm(base.qmul(original,base.axisq((1.,0.,0.),chosen)))
  outcome[label]={'driver':lower,'max_compensation_deg':round(max(map(abs,adjustments.values())),4),
                  'stance_frames':len(frames)}
  if progress:progress('STANCE_COMPENSATION_'+label+'_MAX_DEG_'+str(outcome[label]['max_compensation_deg']))
 return outcome

def signed_local_x_delta(old,new,base):
 a=norm(old);b=norm(new)
 # Normalize the quaternion hemisphere to avoid a spurious full revolution.
 if sum(x*y for x,y in zip(a,b))<0:b=tuple(-x for x in b)
 inverse=(-a[0],-a[1],-a[2],a[3])
 d=norm(base.qmul(inverse,b))
 return math.degrees(2*math.atan2(d[0],d[3]))

def make_candidate(source,base,progress=None,require_hash=True,stance_repair_limit=0):
 if require_hash:need(sha(source)==SOURCE_SHA,'SOURCE_NOT_EXACT_v0.6.5')
 doc,bin0=parse_glb(source);names=inspect_source(doc)
 oldstruct={k:json.dumps(doc[k],sort_keys=True) for k in ('meshes','nodes','skins')}
 oldclips=json.dumps(doc['animations'][:3],sort_keys=True)
 root=names['Bone_000'];root_orig=list(doc['nodes'][root].get('translation',(0,0,0)))
 before=[tracks(doc,bin0,c,base) for c in doc['animations'][3:]]
 binout=bytearray(bin0);audit={};changed=0;contact_repair={}
 try:
  for stage,tr in enumerate(before,1):
   need((root,'translation') in tr,'ROOT_TRAVEL_MISSING')
   for name in MODIFIED:
    need((names[name],'rotation') in tr,'CANONICAL_ROTATION_TRACK_MISSING:'+name)
   for branch_name in ('Bone_034','Bone_033','Bone_037','Bone_036','Bone_035','Bone_039','Bone_038','Bone_042','Bone_041','Bone_040'):
    need((names[branch_name],'rotation') not in tr,'HOOF_DEFORMATION_BRANCH_UNEXPECTEDLY_ANIMATED:'+branch_name)
   rows={names[n]:[] for n in MODIFIED};swing_probe={}
   for frame in range(PER_STRIDE):
    doc['nodes'][root]['translation']=list(tr[(root,'translation')]['rows'][frame])
    oldpose={k:v['rows'][frame] for (k,p),v in tr.items() if p=='rotation'}
    candidate=dict(oldpose)
    for label,leg in LEGS.items():
     u,stance=phase(label,frame);amp=pulse(u)
     for name,delta in leg['drivers'].items():
      n=names[name]
      # LOCAL FK X with sign demonstrated by the owner in the interactive pose lab.
      candidate[n]=norm(base.qmul(oldpose[n],base.axisq((1.,0.,0.),delta*amp)))
     for name in leg['fixed']:
      n=names[name]
      # Local rest orientation. NO WORLD-SPACE PIN, NO COUNTER-ROTATION.
      candidate[n]=norm(base.node_rotation(doc['nodes'][n]))
     if not stance and .42<((u-STANCE)/(1.-STANCE))<.58:
      w=base.world_matrices(doc,candidate)
      a,b=leg['distal']
      swing_probe[label]={'frame':frame,'angle_world_deg':round(theta(pos(w,names[a]),pos(w,names[b])),3),
                          'main_bone':a,'toe_frozen':list(leg['fixed'])}
    for n in rows:rows[n].append(candidate[n])
   contact_repair[str(stage)]=optimize_stance(base,doc,bin0,names,root,tr,rows,stance_repair_limit,progress)
   for n,vals in rows.items():
    full=vals*3+[vals[0]]
    need(len(full)==FRAMES,'NONCYCLIC_FRAME_SERIES')
    output=base.emit_accessor(doc,binout,full,5126,'VEC4')
    tr[(n,'rotation')]['sampler']['output']=output
    changed+=1
   doc['animations'][stage+2].setdefault('extras',{})['cartoonFourBeatFKHooves']={
      'version':VERSION,'footfallTiming':'unchanged','rootTravel':'unchanged',
      'frontMiddleHinges':'preserved','distalLegJoints':'exaggerated local X swing',
      'hoofMass':'constant local rest rotation / parent-following FK',
      'visualVerdict':'PENDING'}
   audit[f'stage_{stage}_mid_swing']=swing_probe
   if progress:progress('STAGE_'+str(stage)+'_FOUR_LEG_FK_SWING_BUILT')
  doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{}).update({
   'version':VERSION,'mode':'CARTOON_FOUR_BEAT_WITH_FK_LOCKED_HOOF_MASS',
   'humanVisualVerdict':'PENDING'})
  doc['nodes'][root]['translation']=root_orig
  for key,value in oldstruct.items():need(json.dumps(doc[key],sort_keys=True)==value,'SOURCE_STRUCTURE_CHANGED:'+key)
  need(json.dumps(doc['animations'][:3],sort_keys=True)==oldclips,'APPROVED_CLIPS_CHANGED')
  need(bytes(binout[:len(bin0)])==bin0,'SOURCE_BINARY_PREFIX_CHANGED')
  new=base.glb_encode(doc,bytes(binout))
 finally:doc['nodes'][root]['translation']=root_orig
 report=verify(source,new,base,require_hash=require_hash)
 report.update({'version':VERSION,'source_sha256':sha(source),'output_sha256':sha(new),
                'changed_rotation_channels':changed,'swing_probes':audit,
                'user_reference':'repl.pose-lab-bone-controls.v1; diagnostic directions only',
                'stance_repair_limit_deg':stance_repair_limit,'stance_compensations':contact_repair,
                'visual_acceptance':'PENDING'})
 return new,report

def verify(source,result,base,require_hash=True):
 if require_hash:need(sha(source)==SOURCE_SHA,'SOURCE_MISMATCH_VERIFY')
 old,b0=parse_glb(source);new,b1=parse_glb(result)
 names=inspect_source(new)
 for k in ('nodes','skins','meshes'):need(old[k]==new[k],'UNAUTHORIZED_STRUCTURE_CHANGE:'+k)
 need(old['animations'][:3]==new['animations'][:3],'ACCEPTED_MANE_TAIL_CLIPS_CHANGED')
 need(b1[:len(b0)]==b0,'OLD_BINARY_BYTES_REWRITTEN')
 before=[tracks(old,b0,c,base) for c in old['animations'][3:]]
 after=[tracks(new,b1,c,base) for c in new['animations'][3:]]
 root=names['Bone_000'];saved=list(new['nodes'][root]['translation'])
 report={'stage':{},'protected_tip_max_local_delta_deg':0.,'driver_mid_swing_delta_deg':{},
         'min_swing_hoof_mesh_y':{},'max_stance_hoof_mesh_change':0.,
         'stance_physical_contact':{},
         'max_keyframe_rotation_step_deg':0.,'world_segment_mid_swing_angles':{},
         'original_swing_max_tip_rotation_deg':{}}
 body=old['meshes'][0]['primitives'][0]['attributes']
 xyz=base.accessor(old,b0,body['POSITION']);joints=base.accessor(old,b0,body['JOINTS_0']);weights=base.accessor(old,b0,body['WEIGHTS_0'])
 hoof_ids={}
 for label in LEGS:
  sign=-1 if label[0]=='L' else +1
  hoof_ids[label]=[i for i,v in enumerate(xyz) if v[1]<.13 and sign*v[0]>.05 and (v[2]>.14 if label[1]=='F' else v[2]<-.62)]
  need(len(hoof_ids[label])>90,'SKIN_HOOF_VERTEX_WITNESS_NOT_FOUND:'+label)
 try:
  for stage,(a,b) in enumerate(zip(before,after),1):
   need(set(a)==set(b),'TRACK_SET_CHANGED')
   for key,v in a.items():
    name=new['nodes'][key[0]].get('name')
    if key[1]=='rotation' and name in MODIFIED:continue
    need(v['rows']==b[key]['rows'],'NON_LEG_TRACK_MODIFIED:'+str(key))
   oldroot=a[(root,'translation')]['rows'];newroot=b[(root,'translation')]['rows']
   need(oldroot==newroot,'TRAVEL_ROOT_CHANGED')
   need(abs(newroot[-1][2]-newroot[0][2]-TRAVEL)<2e-5,'ROOT_STOPPED_TRAVELING')
   for nm in FRONT_MIDDLE:
    need(a[(names[nm],'rotation')]['rows']==b[(names[nm],'rotation')]['rows'],
         'APPROVED_FRONT_MIDDLE_JOINT_CHANGED:'+nm)
   for label,leg in LEGS.items():
    rest={n:base.node_rotation(new['nodes'][names[n]]) for n in leg['fixed']}
    for name in leg['fixed']:
     k=(names[name],'rotation')
     original=max(angle(q,rest[name]) for q in a[k]['rows'])
     report['original_swing_max_tip_rotation_deg'][f'{stage}_{label}_{name}']=round(original,2)
     for quat in b[k]['rows']:
      err=angle(quat,rest[name]);report['protected_tip_max_local_delta_deg']=max(report['protected_tip_max_local_delta_deg'],err)
      need(err<.04,'DEFORMATION_TOE_NOT_FK_LOCKED:'+name+':'+str(err))
    for name,delta in leg['drivers'].items():
     k=(names[name],'rotation')
     qold=a[k]['rows'];qnew=b[k]['rows'];u0,st=phase(label,0)
     for fr in range(PER_STRIDE):
      u,stance=phase(label,fr)
      amp=pulse(u)
      d=angle(qnew[fr],qold[fr])
      signed=signed_local_x_delta(qold[fr],qnew[fr],base)
      if stance:
       # Stance-only physical contact compensation is permitted, bounded and
       # separately reported. Never confuse it with the authored swing curve.
       need(abs(signed)<40.,'STANCE_COMPENSATION_UNBOUNDED:'+label+':'+name)
      else:
       need(abs(signed-delta*amp)<.065,
            'CARTOON_JOINT_SIGN_OR_DRIVE_MISMATCH:'+label+':'+name+':'+str((fr,signed,amp)))
      if stance and name!=leg['distal'][0]:
       need(d<.065,'UNAUTHORIZED_STANCE_DRIVER_CHANGED:'+label+':'+name)
     mids=[fr for fr in range(PER_STRIDE) if not phase(label,fr)[1] and .39<(phase(label,fr)[0]-STANCE)/(1-STANCE)<.61]
     need(mids,'NO_SWING_SAMPLES:'+label)
     peak=max(angle(qnew[fr],qold[fr]) for fr in mids)
     report['driver_mid_swing_delta_deg'][f'{stage}_{label}_{name}']=round(peak,2)
     need(peak>abs(delta)*.82,'CARTOON_SWING_TOO_SMALL:'+label+':'+name)
     for q1,q2 in zip(qnew,qnew[1:]):
      report['max_keyframe_rotation_step_deg']=max(report['max_keyframe_rotation_step_deg'],angle(q1,q2))
    # Actual animated contact test. A rest-pose hoof differs geometrically
    # from the old squash pose; this alone does not imply world-space sliding.
    # Evaluate a fixed lower-mesh patch across the entire true stance window,
    # including wraparound, and compare trajectory as well as absolute drift.
    candidate_rows={n:[b[(n,'rotation')]['rows'][k] for k in range(PER_STRIDE)]
                    for n in (names[x] for x in MODIFIED)}
    contact=physical_stance(base,new,b1,names,root,a,candidate_rows,label)
    report['stance_physical_contact'][f'{stage}_{label}']=contact
    report['max_stance_hoof_mesh_change']=max(report['max_stance_hoof_mesh_change'],
                                               contact['added_drift'])
    need(contact['added_drift']<.019,
         'PLANTED_HOOF_ADDED_DRIFT:'+str((stage,label,contact)))
    need(contact['candidate_drift']<max(.019,contact['source_drift']+.003),
         'PLANTED_HOOF_ABSOLUTE_DRIFT:'+str((stage,label,contact)))
    for fr in range(PER_STRIDE):
     u,stance=phase(label,fr)
     if stance:continue
     s=(u-STANCE)/(1.-STANCE)
     if not (.38<=s<=.62):continue
     new['nodes'][root]['translation']=list(newroot[fr])
     p0={node:v['rows'][fr] for (node,path),v in a.items() if path=='rotation'}
     p1={node:v['rows'][fr] for (node,path),v in b.items() if path=='rotation'}
     w0=base.world_matrices(new,p0);w1=base.world_matrices(new,p1)
     boneA,boneB=leg['distal'];oldangle=theta(pos(w0,names[boneA]),pos(w0,names[boneB]));newangle=theta(pos(w1,names[boneA]),pos(w1,names[boneB]))
     report['world_segment_mid_swing_angles'][f'{stage}_{label}_{fr}']={'before':round(oldangle,2),'after':round(newangle,2)}
     # Positive owner's local X reference moves distal cannon BACKWARD in world Z.
     need(newangle<oldangle-24.,'DISTAL_LEG_NOT_SWINGING_REARWARD:'+label+':'+str((fr,oldangle,newangle)))
     skin0=base.skin_matrices(new,b0,w0);skin1=base.skin_matrices(new,b1,w1)
     sk=[base.deform_vertex(xyz[i],joints[i],weights[i],skin1) for i in hoof_ids[label]]
     y=min(v[1] for v in sk)
     key=f'{stage}_{label}'
     report['min_swing_hoof_mesh_y'][key]=min(y,report['min_swing_hoof_mesh_y'].get(key,float('inf')))
     need(y>-.105,'SWING_HOOF_GROUND_PENETRATION_EXCESSIVE:'+label+':'+str(y))
   report['stage'][str(stage)]='PASS'
 finally:new['nodes'][root]['translation']=saved
 need(report['max_keyframe_rotation_step_deg']<62.,'JOINT_ANIMATION_FRAME_DISCONTINUITY')
 return report
