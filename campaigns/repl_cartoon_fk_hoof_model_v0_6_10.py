#!/usr/bin/env python3
"""Repl 0.6.10: FRONT-ONLY shoulder lead, middle fold, physical swing clearance.

Source is the real, owner-reviewed v0.6.8 canonical GLB. No rest, mesh,
skin, hooves, hind legs, other clips, timing, or world root edits.
The former front middle-joint preservation lock is intentionally superseded
by the owner's Nov 1 instruction to increase front middle folding.
Drive actual joints using measured signed world-space segment directions,
not a guessed local-X polarity, and verify the actual skinned hoof underside.
"""
from __future__ import annotations
import hashlib, math, json

VERSION='0.6.10'
CANON='assets/repl/Repl.glb'
SOURCE_SHA='eff0c604ca56ba58543c7a477bffc0e22e3c23f1d5da00bdbf1ea62369f27509'
FRAMES=97; PERIOD=32; STANCE=.62; STEP=.04; STRIDE=1.28; TRAVEL=.96
# Primary shoulder is the direct parent of the middle joint in the real hierarchy.
FRONT={
 'LF':dict(phase=.25,shoulder='Bone_015',middle='Bone_014',distal='Bone_013',hoof='Bone_012'),
 'RF':dict(phase=.75,shoulder='Bone_021',middle='Bone_020',distal='Bone_019',hoof='Bone_018'),
}
EDITED={n for spec in FRONT.values() for n in (spec['shoulder'],spec['middle'])}
PROTECTED_HIND={'Bone_027','Bone_026','Bone_025','Bone_024','Bone_023','Bone_032','Bone_031','Bone_030','Bone_029','Bone_028'}
PROTECTED_TOES={'Bone_012','Bone_018','Bone_023','Bone_028'}
# Bounded recoverable geometry profiles. No timing or threshold relaxation.
PROFILES=((24,36),(26,42),(28,48),(30,54),(20,36),(24,50),(30,60))
# In model units; measured relative to the SAME hoof's planted underside.
MID_CLEARANCE=.025
EARLY_CLEARANCE=-.006
class Blocked(RuntimeError): pass
def need(test,reason):
 if not test:raise Blocked(reason)
def sha(v):return hashlib.sha256(v).hexdigest()
def norm(q):
 s=math.sqrt(sum(x*x for x in q));need(s>1e-10,'INVALID_QUATERNION')
 return tuple(x/s for x in q)
def phase(label,frame):
 u=((frame*STEP)/STRIDE-FRONT[label]['phase'])%1.
 if u>1-1e-8:u=0.
 return u,u<STANCE
def pulse(u):
 if u<STANCE:return 0.
 return max(0,math.sin(math.pi*(u-STANCE)/(1-STANCE)))**1.1
def delta_deg(a,b):return (a-b+180)%360-180
def pose_track(track,frame):
 return {n:v['rows'][frame] for (n,path),v in track.items() if path=='rotation'}
def segment_angle(base,doc,pose,names,a,b):
 w=base.world_matrices(doc,pose)
 p=tuple(w[names[a]][k] for k in (3,7,11))
 q=tuple(w[names[b]][k] for k in (3,7,11))
 return math.degrees(math.atan2(q[2]-p[2],p[1]-q[1]))
def drive_joint(base,doc,pose,names,joint,a,b,target,maximum):
 """Numerically invert actual world-angle response for THIS joint and pose.

 A measured signed target avoids confusion between local X and world +Z,
 as well as the false assumption that every Meshy hinge has the same sign.
 """
 node=names[joint];original=tuple(pose[node]);local=(1.,0.,0.)
 def evaluate(deg):
  pose[node]=norm(base.qmul(original,base.axisq(local,deg)))
  return segment_angle(base,doc,pose,names,a,b)
 starting=evaluate(0.)
 plus=evaluate(4.)
 minus=evaluate(-4.)
 slope=delta_deg(plus,minus)/8.
 need(abs(slope)>.17,'ANATOMICAL_PROFILE_AXIS_INEFFECTIVE:'+joint+':'+str(slope))
 target_delta=delta_deg(target,starting)
 value=max(-maximum,min(maximum,target_delta/slope))
 for _ in range(5):
  observed=evaluate(value)
  err=delta_deg(target,observed)
  need(math.isfinite(err),'ANATOMICAL_PROFILE_NONFINITE_ERROR:'+joint)
  if abs(err)<.22:break
  proposal=max(-maximum,min(maximum,value+err/slope))
  if abs(proposal-value)<.0001:break
  value=proposal
 final=evaluate(value)
 need(abs(delta_deg(final,target))<1.2,
      'ANATOMICAL_PROFILE_TARGET_UNREACHABLE:'+joint+':'+str((round(target,2),round(final,2),round(value,2))))
 return value,starting,final

def inspect(doc,previous):
 names=previous.inspect_source(doc)
 parents={child:i for i,n in enumerate(doc['nodes']) for child in n.get('children',[])}
 for label,s in FRONT.items():
  for pa,ch in ((s['shoulder'],s['middle']),(s['middle'],s['distal']),(s['distal'],s['hoof'])):
   need(parents.get(names[ch])==names[pa],'FRONT_CHAIN_MAPPING_CHANGED:'+label+':'+pa+'>'+ch)
  need(len({names[n] for n in (s['shoulder'],s['middle'],s['distal'],s['hoof'])})==4,'DUPLICATED_FRONT_BONE_ROLE')
 return names

def make_candidate(source,base,previous,profile,progress=None):
 need(sha(source)==SOURCE_SHA,'PINNED_SOURCE_GLB_SHA_CHANGED')
 shoulder,target_middle=profile
 need(20<=shoulder<=30 and 20<=target_middle<=60,'PROFILE_OUT_OF_OWNER_BOUNDS')
 doc,bin0=previous.parse_glb(source);names=inspect(doc,previous)
 oldparts={k:json.dumps(doc[k],sort_keys=True) for k in ('meshes','nodes','skins')}
 oldclips=json.dumps(doc['animations'][:3],sort_keys=True)
 root=names['Bone_000'];saved_translation=list(doc['nodes'][root].get('translation',(0,0,0)))
 original=[previous.tracks(doc,bin0,c,base) for c in doc['animations'][3:]]
 binary=bytearray(bin0);change_count=0;mid_probe={};profile_details={}
 try:
  for stage,tr in enumerate(original,1):
   for label,s in FRONT.items():
    for nm in (s['shoulder'],s['middle'],s['distal'],s['hoof']):
     need((names[nm],'rotation') in tr,'PINNED_V068_ROTATION_TRACK_MISSING:'+nm)
   need((root,'translation') in tr,'PINNED_ROOT_TRACK_MISSING')
   rows={names[n]:[] for n in EDITED};probes={};local_report={}
   for frame in range(PERIOD):
    doc['nodes'][root]['translation']=list(tr[(root,'translation')]['rows'][frame])
    current=pose_track(tr,frame)
    corrected=dict(current)
    for label,s in FRONT.items():
     u,stance=phase(label,frame)
     if stance:continue
     amp=pulse(u)
     if amp<1e-10:continue
     # Desired upper segment lead: +Z is forward in Repl's sagittal frame.
     orig_upper=segment_angle(base,doc,current,names,s['shoulder'],s['middle'])
     orig_mid=segment_angle(base,doc,current,names,s['middle'],s['distal'])
     a,_,out_upper=drive_joint(base,doc,corrected,names,s['shoulder'],
                       s['shoulder'],s['middle'],orig_upper+shoulder*amp,38.)
     # Middle fold is a BACKWARD absolute segment change from v0.6.8 baseline,
     # including the upstream shoulder influence, not a naive local-X addition.
     b,_,out_middle=drive_joint(base,doc,corrected,names,s['middle'],
                      s['middle'],s['distal'],orig_mid-target_middle*amp,105.)
     if .38<((u-STANCE)/(1-STANCE))<.62:
      probes[label]={'frame':frame,'forward_shoulder_world_deg':round(delta_deg(out_upper,orig_upper),2),
          'backward_middle_world_deg':round(delta_deg(orig_mid,out_middle),2),
          'local_shoulder_deg':round(a,2),'local_middle_deg':round(b,2)}
    for n in rows:rows[n].append(corrected[n])
   for n,values in rows.items():
    need(len(values)==PERIOD,'INCOMPLETE_FRONT_KEYFRAMES')
    full=values*3+[values[0]]
    output=base.emit_accessor(doc,binary,full,5126,'VEC4')
    tr[(n,'rotation')]['sampler']['output']=output
    change_count+=1
   doc['animations'][stage+2].setdefault('extras',{})['ownerForeSwingClearance']={
      'version':VERSION,'shoulderForwardTargetDeg':shoulder,
      'middleBackwardsTargetDeg':target_middle,
      'hinges':'Bone_015/Bone_014 and Bone_021/Bone_020 only',
      'footfall':'unchanged','rearLegs':'original v0.6.8 bytes','visualVerdict':'PENDING'}
   mid_probe[str(stage)]=probes
   if progress:progress('STAGE_'+str(stage)+'_FRONT_SHOULDER_AND_MIDDLE_TARGETS_BUILT')
  doc['asset'].setdefault('extras',{}).setdefault('replWalkCampaign',{}).update({
    'version':VERSION,'mode':'FRONT_SWING_CLEARANCE_ON_CANONICAL_V068',
    'humanVisualVerdict':'PENDING'})
  doc['nodes'][root]['translation']=saved_translation
  for key,v in oldparts.items():need(json.dumps(doc[key],sort_keys=True)==v,'CANONICAL_'+key.upper()+'_MODIFIED')
  need(json.dumps(doc['animations'][:3],sort_keys=True)==oldclips,'ACCEPTED_NONWALK_CLIP_MUTATION')
  need(bytes(binary[:len(bin0)])==bin0,'SOURCE_BINARY_PREFIX_CHANGED')
  output=base.glb_encode(doc,bytes(binary))
 finally:doc['nodes'][root]['translation']=saved_translation
 report=verify(source,output,base,previous,profile)
 report.update({'version':VERSION,'source_sha256':sha(source),'output_sha256':sha(output),
   'profile':{'shoulder_forward_deg':shoulder,'middle_back_deg':target_middle},
   'changed_channels':change_count,'swing_joint_probes':mid_probe,
   'protected_hind':'ALL_V068_KEYFRAMES_IDENTICAL',
   'visual_acceptance':'PENDING'})
 return output,report

def underside(base,doc,binary,track,pose,root,frame,xyz,joints,weights,indices):
 doc['nodes'][root]['translation']=list(track[(root,'translation')]['rows'][frame])
 w=base.world_matrices(doc,pose)
 skin=base.skin_matrices(doc,binary,w)
 return min(base.deform_vertex(xyz[i],joints[i],weights[i],skin)[1] for i in indices)

def verify(source,output,base,previous,profile):
 old,b0=previous.parse_glb(source);new,b1=previous.parse_glb(output)
 names=inspect(new,previous)
 need(len(new['animations'])==6,'CLIP_COUNT_CHANGED')
 for key in ('meshes','nodes','skins'):
  need(old[key]==new[key],'CANONICAL_'+key.upper()+'_MUTATED')
 need(old['animations'][:3]==new['animations'][:3],'MANE_TAIL_ANIMATIONS_MUTATED')
 need(b1[:len(b0)]==b0,'SOURCE_BINARY_PREFIX_MUTATED')
 btracks=[previous.tracks(old,b0,c,base) for c in old['animations'][3:]]
 atracks=[previous.tracks(new,b1,c,base) for c in new['animations'][3:]]
 root=names['Bone_000'];saved=list(new['nodes'][root]['translation'])
 hoof_mesh={label:previous.hoof_witnesses(new,b1,base,label) for label in FRONT}
 metrics={'all_three_stages':{},'front_hoof_clearance':{},'front_joint_angles':{},
    'min_mid_clearance':float('inf'),'min_early_clearance':float('inf'),
    'max_step_rotation_deg':0.,'preserved_rotations':0}
 try:
  need(len(btracks)==len(atracks)==3,'TRAVELING_WALK_STAGE_COUNT_WRONG')
  for stage,(before,after) in enumerate(zip(btracks,atracks),1):
   need(set(before)==set(after),'EXTRA_OR_MISSING_KEYFRAME_TRACKS')
   for k,prior in before.items():
    if k[1]=='rotation' and new['nodes'][k[0]].get('name') in EDITED:continue
    need(prior['rows']==after[k]['rows'],'UNAUTHORIZED_TRACK_EDIT:'+str((stage,k)))
    if k[1]=='rotation':metrics['preserved_rotations']+=1
   mustroot=(root,'translation')
   need(before[mustroot]['rows']==after[mustroot]['rows'],'FORWARD_TRAVEL_CHANGED')
   positions=after[mustroot]['rows']
   need(abs(positions[-1][2]-positions[0][2]-TRAVEL)<2e-5,'ROOT_TRAVEL_LOST')
   for label,spec in FRONT.items():
    for name in (spec['shoulder'],spec['middle']):
     oldq=before[(names[name],'rotation')]['rows']
     newq=after[(names[name],'rotation')]['rows']
     need(len(newq)==FRAMES,'FRAME_LENGTH_CHANGED:'+name)
     need(all(abs(x-y)<1e-7 for x,y in zip(newq[0],newq[-1])),
          'STRIDE_LOOP_DISCONTINUITY:'+name)
     for fr in range(PERIOD):
      _,stance=phase(label,fr)
      if stance:need(all(abs(x-y)<1e-7 for x,y in zip(oldq[fr],newq[fr])),
                     'STANCE_FRONT_JOINT_CHANGED:'+label+':'+name)
     for p,q in zip(newq,newq[1:]):
      metrics['max_step_rotation_deg']=max(metrics['max_step_rotation_deg'],previous.angle(p,q))
    xyz,joints,weights,ids=hoof_mesh[label]
    need(bool(ids),'EMPTY_HOOF_SKIN_SAMPLE:'+label)
    # Planted same-model underside is the geometric ground reference.
    planted=[fr for fr in range(PERIOD) if phase(label,fr)[1]]
    # Use the first planted frame, avoids a falsely low "ground" caused
    # by worst-case stance skidding; do not infer ground from mid-swing.
    anchor=planted[0]
    po=pose_track(before,anchor)
    ground=underside(base,new,b1,before,po,root,anchor,xyz,joints,weights,ids)
    local={'reference_ground_y':round(ground,5),'min_mid_clearance':float('inf'),
       'min_early_clearance':float('inf'),'max_baseline_mid_clearance':-999.,
       'tested_mid_frames':0,'tested_early_frames':0}
    for fr in range(PERIOD):
     u,stance=phase(label,fr)
     if stance:continue
     swing_fraction=(u-STANCE)/(1-STANCE)
     if swing_fraction<.18 or swing_fraction>.82:continue
     pold=pose_track(before,fr);pnew=pose_track(after,fr)
     before_y=underside(base,new,b0,before,pold,root,fr,xyz,joints,weights,ids)
     after_y=underside(base,new,b1,after,pnew,root,fr,xyz,joints,weights,ids)
     need(math.isfinite(before_y) and math.isfinite(after_y) and math.isfinite(ground),
          'NONFINITE_PHYSICAL_HOOF_COORDINATES:'+label+':'+str(fr))
     clearance=after_y-ground
     if .38<=swing_fraction<=.62:
      local['tested_mid_frames']+=1
      local['min_mid_clearance']=min(local['min_mid_clearance'],clearance)
      local['max_baseline_mid_clearance']=max(local['max_baseline_mid_clearance'],before_y-ground)
      # At mid-swing measure physical segment angles against v0.6.8.
      old_upper=segment_angle(base,new,pold,names,spec['shoulder'],spec['middle'])
      new_upper=segment_angle(base,new,pnew,names,spec['shoulder'],spec['middle'])
      old_mid=segment_angle(base,new,pold,names,spec['middle'],spec['distal'])
      new_mid=segment_angle(base,new,pnew,names,spec['middle'],spec['distal'])
      lead=delta_deg(new_upper,old_upper);fold=delta_deg(old_mid,new_mid)
      need(lead>profile[0]*.79,'ANATOMICAL_PROFILE_SHOULDER_NOT_FORWARD:'+label+':'+str((fr,lead)))
      need(fold>profile[1]*.79,'ANATOMICAL_PROFILE_MIDDLE_NOT_BACKWARD:'+label+':'+str((fr,fold)))
      metrics['front_joint_angles'][f'{stage}_{label}_{fr}']={'shoulder_forward_deg':round(lead,3),'middle_backward_deg':round(fold,3)}
     else:
      local['tested_early_frames']+=1
      local['min_early_clearance']=min(local['min_early_clearance'],clearance)
    need(local['tested_mid_frames']>=2 and local['tested_early_frames']>=2,
         'PHASE_WITNESSES_MISSING:'+label)
    need(math.isfinite(local['min_mid_clearance']) and math.isfinite(local['min_early_clearance']),
         'MISSING_FINITE_HOOF_CLEARANCE:'+label)
    local['min_mid_clearance']=round(local['min_mid_clearance'],6)
    local['min_early_clearance']=round(local['min_early_clearance'],6)
    metrics['front_hoof_clearance'][f'{stage}_{label}']=local
    metrics['min_mid_clearance']=min(metrics['min_mid_clearance'],local['min_mid_clearance'])
    metrics['min_early_clearance']=min(metrics['min_early_clearance'],local['min_early_clearance'])
    need(local['min_mid_clearance']>=MID_CLEARANCE,
         'CLEARANCE_MID_FRONT_HOOF_STILL_DRAGS:'+str((stage,label,local)))
    need(local['min_early_clearance']>=EARLY_CLEARANCE,
         'CLEARANCE_EARLY_FRONT_HOOF_PENETRATION:'+str((stage,label,local)))
   metrics['all_three_stages'][str(stage)]='PASS'
 finally:new['nodes'][root]['translation']=saved
 need(metrics['max_step_rotation_deg']<62.,'ANATOMICAL_PROFILE_KEYFRAME_DISCONTINUITY:'+str(metrics['max_step_rotation_deg']))
 return metrics
