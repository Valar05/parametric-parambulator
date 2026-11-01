#!/usr/bin/env python3
"""Repl lower-limb articulated arc v0.6.4.1.

Owner wants the ACTUAL hoof articulation and joint directly above it to curl
rearward. Earlier versions keyed the front forefoot bones with the wrong bend
direction, while some original hind hoof tracks were already keyed. This
version detects those tracks and corrects all four without duplication.

Normal +Z is forward, +Y is up. Joint-axis signs must be measured against
actual skinned hoof mesh, not inferred from a diagram: the fore and hind cannons both need positive X to push the actual hoof
surface rearward after the IK compensation, as verified with actual skinned vertices. All hoof/fetlock toes use negative
X in this coordinate system. A material signed surface displacement test
fails the release if any hoof visibly moves the wrong direction.

Outputs only bytes and numerical receipts; caller exclusively updates the
canonical GLB after validation, via Termux Git (no direct connector mutation).
"""
from __future__ import annotations
import hashlib,json,math,struct

VERSION='0.6.4.1'
CANON='assets/repl/Repl.glb'
SOURCE_SHA='29bc09491f8d42bd272c2a03142252323d147a8bcc90b3aa7c75ed127a31be84'
SOURCE_BLOB='8e3afd9118f827f1592499300e511e5d90a16d45'
FRAMES=97;PER_STRIDE=32;STRIDE=1.28;STEP=.04;STANCE=.62;TRAVEL=.96
WALK_NAMES=('REPL_WALK_01_FORWARD_FOUR_BEAT_IK',
 'REPL_WALK_02_FORWARD_BODY_WEIGHT_TRANSFER',
 'REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED')
# Each pair is (joint ABOVE fetlock, physical hoof/fetlock joint).
# Both front hoof tracks exist. Hind hoof tracks may exist already or be absent.
LEGS={
 'LF':dict(phase=.25,base='Bone_016',upper=('Bone_015','Bone_014'),
           lower='Bone_013',hoof='Bone_012',end='Bone_011',
           cannon_target=14.0,hoof_target=-16.0),
 'RF':dict(phase=.75,base='Bone_022',upper=('Bone_021','Bone_020'),
           lower='Bone_019',hoof='Bone_018',end='Bone_017',
           cannon_target=14.0,hoof_target=-16.0),
 'LH':dict(phase=0.,base='Bone_027',upper=('Bone_026','Bone_025'),
           lower='Bone_024',hoof='Bone_023',end='Bone_023',
           cannon_target=25.0,hoof_target=-15.0),
 'RH':dict(phase=.5,base='Bone_032',upper=('Bone_031','Bone_030'),
           lower='Bone_029',hoof='Bone_028',end='Bone_028',
           cannon_target=25.0,hoof_target=-15.0),
}
# The structural proximal joint remains above the corrected arc; constraint
# optimization adjusts it only enough to preserve world-space hoof targets.
# For front legs, additionally allow one more upper joint for reach.
UPSTREAM={
 'LF':('Bone_015','Bone_014'), 'RF':('Bone_021','Bone_020'),
 'LH':('Bone_027','Bone_026','Bone_025'),
 'RH':('Bone_032','Bone_031','Bone_030'),
}
HIND_HOOF_TRACKS={'Bone_023','Bone_028'}
EXISTING_FOREFOOT_TRACKS={'Bone_012','Bone_018'}
MODIFIED=set(sum((list(UPSTREAM[n])+[d['lower'],d['hoof']] for n,d in LEGS.items()),[]))
class Blocked(RuntimeError):pass
def need(v,c):
 if not v:raise Blocked(c)
def sha(x):return hashlib.sha256(x).hexdigest()
def gitblob(x):return hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()
def parse_glb(data):
 need(data[:4]==b'glTF' and len(data)>28,'INVALID_GLB')
 _,v,size=struct.unpack_from('<4sII',data);need(v==2 and size==len(data),'INVALID_GLB_LENGTH')
 jsize,typ=struct.unpack_from('<I4s',data,12);need(typ==b'JSON','INVALID_GLB_JSON')
 at=20+jsize;bs,typ=struct.unpack_from('<I4s',data,at)
 need(typ==b'BIN\0' and at+8+bs==len(data),'INVALID_GLB_BINARY')
 return json.loads(data[20:at]),data[at+8:]
def pos(world,index):return tuple(world[index][i] for i in (3,7,11))
def norm(q):
 m=math.sqrt(sum(x*x for x in q));need(m>1e-12,'BAD_QUATERNION')
 return tuple(x/m for x in q)
def axis(world,node):
 v=tuple(world[node][i] for i in (0,1,2));m=math.sqrt(sum(x*x for x in v))
 need(m>1e-8,'BAD_ROTATION_AXIS');return tuple(x/m for x in v)
def angle(q,rest,ax,base):
 r=base.qmul((-rest[0],-rest[1],-rest[2],rest[3]),norm(q))
 value=math.degrees(2*math.atan2(sum(a*b for a,b in zip(r[:3],ax)),r[3]))
 return (value+180)%360-180
def ease(v):
 v=max(0.,min(1.,v));return v*v*(3-2*v)
def phase(spec,t):
 u=(t/STRIDE-spec['phase'])%1.
 return u, u<STANCE
def read_tracks(doc,binary,clip,base):
 out={}
 for ch in clip['channels']:
  sm=clip['samplers'][ch['sampler']];key=(ch['target']['node'],ch['target']['path'])
  need(sm['interpolation']=='LINEAR' and key not in out,'INVALID_DUPLICATE_OR_NONLINEAR_TRACK')
  rows=base.accessor(doc,binary,sm['output']);times=base.accessor(doc,binary,sm['input'])
  need(len(rows)==len(times)==FRAMES,'FRAME_COUNT_CHANGED')
  need(max(abs(row[0]-i*STEP) for i,row in enumerate(times))<5e-6,'FRAME_TIME_CHANGED')
  out[key]={'rows':rows,'sampler':sm,'times':times}
 return out

def solve_compensate(doc,base,pose,root_name_map,world_goal,upstream,effector,
                     upstream_baseline,max_delta=55.):
 """Bounded 2D damped Jacobian IK with line search; never touches distal arc.

 This is a *local correction* to the old swing pose. It fixes reach after
 the newly keyed distal joints bend, preserving the hoof target in world
 space rather than re-creating the foreleg from a guessed silhouette.
 """
 nodes=[root_name_map[n] for n in upstream]
 offsets=[0.]*len(nodes)
 def put(q):
  for k,n in enumerate(nodes):
   pose[n]=norm(base.qmul(upstream_baseline[n],base.axisq(axes[k],q[k])))
  return base.world_matrices(doc,pose)
 # Axes from input pose, not an unverified assumed anatomical frame.
 before=base.world_matrices(doc,pose)
 axes=[axis(before,n) for n in nodes]
 world=put(offsets)
 point=pos(world,effector)
 def err(point):return (world_goal[1]-point[1],world_goal[2]-point[2])
 for _ in range(65):
  ey,ez=err(point);distance=math.hypot(ey,ez)
  if distance<.002:break
  # Finite difference actual world-space skin tree response; no fake
  # planar path used when parent orientations are rotated.
  columns=[]
  for k in range(len(nodes)):
   candidate=list(offsets);candidate[k]+=.12
   wp=put(candidate);p=pos(wp,effector)
   columns.append(((p[1]-point[1])/.12,(p[2]-point[2])/.12))
  world=put(offsets)
  aa=.0001+sum(dy*dy for dy,dz in columns)
  bb=sum(dy*dz for dy,dz in columns)
  cc=.0001+sum(dz*dz for dy,dz in columns)
  det=aa*cc-bb*bb
  need(det>1e-12,'SINGULAR_UPPER_LEG_COMPENSATION')
  uy=(cc*ey-bb*ez)/det;uz=(aa*ez-bb*ey)/det
  raw=[dy*uy+dz*uz for dy,dz in columns]
  trial=None
  for scale in (1.,.5,.25,.125):
   v=[max(-max_delta,min(max_delta,offsets[k]+scale*max(-8.,min(8.,raw[k]))))
      for k in range(len(nodes))]
   w=put(v);p=pos(w,effector)
   if math.dist(p[1:],world_goal[1:])<distance-1e-7:
    trial=(v,w,p);break
  if trial is None:
   world=put(offsets);point=pos(world,effector);break
  offsets,world,point=trial
 world=put(offsets)
 return math.dist(pos(world,effector),world_goal),max(abs(x) for x in offsets)

def candidate(source,base,progress=None,require_hash=True):
 if require_hash:need(sha(source)==SOURCE_SHA,'SOURCE_NOT_EXACT_CANONICAL_v0.6.3')
 doc,old_bin=parse_glb(source)
 need(len(doc['nodes'])==53 and len(doc['skins'][0]['joints'])==50,'RIG_NOT_ACCEPTED_50_JOINT')
 need(len(doc['animations'])==6,'OLD_CLIPS_COUNT_MISMATCH')
 for i,n in enumerate(WALK_NAMES):need(doc['animations'][i+3]['name']==n,'WALK_CLIP_ORDER_CHANGED')
 names={v.get('name'):i for i,v in enumerate(doc['nodes']) if v.get('name')}
 parents={c:i for i,v in enumerate(doc['nodes']) for c in v.get('children',[])}
 for label,d in LEGS.items():
  chain=list(UPSTREAM[label])+[d['lower'],d['hoof']]
  # For forelegs, upper list deliberately omits initial shoulder (Bone_016/022)
  # and for hind contains extra proximal joint; parent chain must be exact.
  for a,b in zip(chain,chain[1:]):
   need(parents.get(names[b])==names[a],'WRONG_REAL_BONE_PARENT_CHAIN:'+label+':'+a+'>'+b)
  need(parents.get(names[chain[0]])==names[d['base']] or chain[0]==d['base'],
      'WRONG_PROXIMAL_BONE_PARENT:'+label)
  if d['end']!=d['hoof']:need(parents.get(names[d['end']])==names[d['hoof']],
                             'WRONG_FORE_HOOF_TIP_PARENT:'+label)
 old_nodes=json.dumps(doc['nodes'],sort_keys=True)
 old_skins=json.dumps(doc['skins'],sort_keys=True)
 old_mesh=json.dumps(doc['meshes'],sort_keys=True)
 old_animations=json.dumps(doc['animations'][:3],sort_keys=True)
 binary=bytearray(old_bin)
 original=[read_tracks(doc,old_bin,a,base) for a in doc['animations'][3:]]
 root=names['Bone_000'];root_original=list(doc['nodes'][root].get('translation',(0.,0.,0.)))
 for tr in original:
  need((root,'translation') in tr,'NO_FORWARD_ROOT_TRACK')
  for label,d in LEGS.items():
   for n in (*UPSTREAM[label],d['lower']):
    need((names[n],'rotation') in tr,'MISSING_PREVIOUS_LEG_ANIMATION:'+n)
   key=(names[d['hoof']],'rotation')
   if label[1]=='F':
    need(key in tr,'EXPECTED_EXISTING_FRONT_HOOF_TRACK_MISSING:'+d['hoof'])
   else:
    # Actual production v0.6.3 already contains at least Bone_023.
    # Preserve and correct an existing hind hoof track, or create it if absent.
    need(key not in tr or len(tr[key]['rows'])==FRAMES,
         'EXISTING_REAR_HOOF_TRACK_MALFORMED:'+d['hoof'])
 created_by_clip={};existing_hind_by_clip={}
 for stage,tr in enumerate(original,1):
  created_by_clip['STAGE_'+str(stage)]=sorted(
   name for name in HIND_HOOF_TRACKS if (names[name],'rotation') not in tr)
  existing_hind_by_clip['STAGE_'+str(stage)]=sorted(
   name for name in HIND_HOOF_TRACKS if (names[name],'rotation') in tr)
  if progress:
   progress('STAGE_'+str(stage)+'_HIND_HOOF_EXISTING_'+
            (','.join(existing_hind_by_clip['STAGE_'+str(stage)]) or 'NONE')+
            '_MISSING_'+((','.join(created_by_clip['STAGE_'+str(stage)])) or 'NONE'))
 report={'stage_metrics':{},'leg_metrics':{},'swing_arc_samples':{},
         'world_travel':TRAVEL,'human_visual_acceptance':'PENDING',
         'source_sha256':sha(source),
         'new_hoof_keyed':sorted(set(sum(created_by_clip.values(),[]))),
         'created_hoof_tracks_by_clip':created_by_clip,
         'existing_hind_hoof_tracks_by_clip':existing_hind_by_clip,
         'corrected_existing_forehoof_tracks':sorted(EXISTING_FOREFOOT_TRACKS),
         'guarded_skin_geometry':'50 joints / 53 nodes / 2 original meshes'}
 all_changes={}
 try:
  for stage in (1,2,3):
   tr=original[stage-1]
   if progress:progress('STAGE_'+str(stage)+'_ALL_FOUR_DISTAL_ARCS_BEGIN')
   stage_result={}
   for label,d in LEGS.items():
    up=[names[n] for n in UPSTREAM[label]]
    lower=names[d['lower']];foot=names[d['hoof']];end=names[d['end']]
    monitored=up+[lower,foot]
    original_q={n:tr[(n,'rotation')]['rows'] if (n,'rotation') in tr
                else [base.node_rotation(doc['nodes'][n])]*FRAMES for n in monitored}
    rows={n:[] for n in monitored}
    legstats={'mid_swing_samples':0,'stance_frames':0,'max_hoof_marker_error':0.,
       'max_upper_correction_degrees':0.,'mid_cannon_backward_min_degrees':999.,
       'mid_hoof_toe_raise_min_degrees':999.,'max_track_step_degrees':0.}
    for frame in range(PER_STRIDE):
     t=frame*STEP;u,stance=phase(d,t)
     doc['nodes'][root]['translation']=list(tr[(root,'translation')]['rows'][frame])
     original_pose={n:v['rows'][frame] for (n,mode),v in tr.items() if mode=='rotation'}
     for n in monitored:original_pose[n]=original_q[n][frame]
     old_world=base.world_matrices(doc,original_pose)
     goal=pos(old_world,end)
     if stance:
      for n in monitored:rows[n].append(tuple(original_q[n][frame]))
      legstats['stance_frames']+=1;continue
     swing=(u-STANCE)/(1.-STANCE)
     # Zero at lift-off/touchdown, stronger at mid-swing. The upstream
     # solver preserves exactly the original target, not guessed rest IK.
     pulse=max(0.,math.sin(math.pi*swing))**1.35
     new_pose=dict(original_pose)
     for joint,desired_angle in ((lower,d['cannon_target']),
                                 (foot,d['hoof_target'])):
      origin_q=original_q[joint][frame]
      ref_q=base.node_rotation(doc['nodes'][joint])
      a=axis(old_world,joint)
      current=angle(origin_q,ref_q,a,base)
      # At pulse 1 the whole lower arc is at its calibrated target, but
      # both endpoints recover the exact earlier pose at swing boundaries.
      target=current+(desired_angle-current)*pulse
      new_pose[joint]=norm(base.qmul(ref_q,base.axisq(a,target)))
     upstream_base={n:tuple(original_q[n][frame]) for n in up}
     error,correction=solve_compensate(doc,base,new_pose,names,goal,
                            UPSTREAM[label],end,upstream_base)
     # No huge contortion allowed to conceal a bad pole/incorrect chain.
     need(error<.012,'DISTAL_ARC_HOOF_WORLD_TARGET_UNREACHABLE:'+label+':'+str((frame,error)))
     need(correction<55.01,'PROXIMAL_IK_WOULD_BE_HYPEREXTENDED:'+label)
     new_world=base.world_matrices(doc,new_pose)
     after=pos(new_world,end)
     error=math.dist(after,goal)
     legstats['max_hoof_marker_error']=max(legstats['max_hoof_marker_error'],error)
     if .27<=swing<=.73:
      # Actual signed distal local rotations are calibrated against the skinned hoof mesh. Validate
      # actual skinned hoof movement as well, not just these joint angles.
      la=angle(new_pose[lower],base.node_rotation(doc['nodes'][lower]),axis(new_world,lower),base)
      ha=angle(new_pose[foot],base.node_rotation(doc['nodes'][foot]),axis(new_world,foot),base)
      need(la>2.0 and ha<-2.0,
           'DISTAL_ARC_DIRECTION_WRONG:'+label+':'+str((frame,la,ha)))
      legstats['mid_cannon_backward_min_degrees']=min(legstats['mid_cannon_backward_min_degrees'],abs(la))
      legstats['mid_hoof_toe_raise_min_degrees']=min(legstats['mid_hoof_toe_raise_min_degrees'],-ha)
      legstats['mid_swing_samples']+=1
     legstats['max_upper_correction_degrees']=max(legstats['max_upper_correction_degrees'],correction)
     for n in monitored:rows[n].append(tuple(new_pose[n]))
    for n in monitored:
     rows[n]=rows[n]*3+[rows[n][0]]
     need(len(rows[n])==FRAMES,'INCORRECT_THREE_STRIDE_TRACK')
    need(legstats['mid_swing_samples']>=3,'NO_MIDSWING_ARC_VALIDATION:'+label)
    stage_result[label]=rows
    report['leg_metrics'][f'STAGE_{stage}_{label}']=legstats
   all_changes[stage]=stage_result
   if progress:progress('STAGE_'+str(stage)+'_ALL_FOUR_DISTAL_ARCS_SOLVED')
  # Solve each stage from its OWN prior tracks. Prior productions may
  # already have distinct rear hoof rotations in stage 3; copying stage 2
  # would corrupt stage-3 planted frames and silently override motion.
  names_changed=set()
  for stage in range(1,4):
   tr=original[stage-1]
   for label,legrows in all_changes[stage].items():
    for node,rows in legrows.items():
     name=doc['nodes'][node]['name'];names_changed.add(name)
     acc=base.emit_accessor(doc,binary,rows,5126,'VEC4')
     key=(node,'rotation')
     if key in tr:
      tr[key]['sampler']['output']=acc
     else:
      # Create only absent hind-foot rotation channels. Any existing
      # hind track is updated through the branch above, never duplicated.
      sm={'input':next(iter(tr.values()))['sampler']['input'],
          'output':acc,'interpolation':'LINEAR'}
      clip=doc['animations'][stage+2]
      si=len(clip['samplers']);clip['samplers'].append(sm)
      clip['channels'].append({'sampler':si,'target':{'node':node,'path':'rotation'}})
     report['stage_metrics'][f'STAGE_{stage}_TRACKS_UPDATED']=len(names_changed)
   doc['animations'][stage+2].setdefault('extras',{})['ownerDistalArcCorrection']={
      'version':VERSION,'fourFeet':True,'arcBendsBackwards':True,
      'foreLower':('Bone_013','Bone_019'),'foreHoof':('Bone_012','Bone_018'),
      'hindLower':('Bone_024','Bone_029'),'hindHoof':('Bone_023','Bone_028'),
      'rootForwardTravel':'PRESERVED','gaitPhase':'PRESERVED',
      'humanVisualVerdict':'PENDING'}
  doc.setdefault('asset',{}).setdefault('extras',{}).setdefault('replWalkCampaign',{})['version']=VERSION
  doc['asset']['extras']['replWalkCampaign']['lowerLimbArc']='all four cannon+hoof pairs; real distal hoof keyed'
  doc['asset']['extras']['replWalkCampaign']['humanVisualVerdict']='PENDING'
  doc['nodes'][root]['translation']=root_original
  need(json.dumps(doc['nodes'],sort_keys=True)==old_nodes,'NODE_GEOMETRY_CHANGED')
  need(json.dumps(doc['skins'],sort_keys=True)==old_skins,'SKIN_WEIGHTS_CHANGED')
  need(json.dumps(doc['meshes'],sort_keys=True)==old_mesh,'MESHES_CHANGED')
  need(json.dumps(doc['animations'][:3],sort_keys=True)==old_animations,'ACCEPTED_CLIPS_CHANGED')
  need(bytes(binary[:len(old_bin)])==old_bin,'PREVIOUS_BINARY_BUFFER_CHANGED')
  output=base.glb_encode(doc,bytes(binary))
 finally:
  doc['nodes'][root]['translation']=root_original
 report.update(validate(source,output,base,require_hash=require_hash))
 report['output_sha256']=sha(output)
 return output,report

def validate(before,after,base,require_hash=True):
 if require_hash:need(sha(before)==SOURCE_SHA,'WRONG_PREVIOUS_CANONICAL_BYTES')
 old,oldb=parse_glb(before);new,newb=parse_glb(after)
 need(new['nodes']==old['nodes'] and new['skins']==old['skins'] and
      new['meshes']==old['meshes'],'UNEXPECTED_MESH_RIG_OR_SKIN_CHANGE')
 need(new['animations'][:3]==old['animations'][:3],'APPROVED_OLDER_ANIMATIONS_CHANGED')
 need(len(new['animations'])==6,'ANIMATION_LIST_CHANGED')
 need(newb[:len(oldb)]==oldb,'SOURCE_GLB_BIN_PREFIX_MUTATED')
 names={n.get('name'):i for i,n in enumerate(new['nodes'])}
 a=[read_tracks(old,oldb,clip,base) for clip in old['animations'][3:]]
 b=[read_tracks(new,newb,clip,base) for clip in new['animations'][3:]]
 root=names['Bone_000'];orig=list(new['nodes'][root]['translation'])
 driven=set(MODIFIED)|HIND_HOOF_TRACKS
 longest_error=0.;max_stance_error=0.;changed=unchanged=0
 max_step=0.;peak_below=0.;swing_contact_warnings={}
 for stage in range(3):
  former,current=a[stage],b[stage]
  allowed_new={(names[n],'rotation') for n in HIND_HOOF_TRACKS
               if (names[n],'rotation') not in former}
  need(set(current)==set(former)|allowed_new,'EXTRA_ANIMATION_TRACKS_OR_MISSING_OLD')
  for key in former:
   if key[1]=='rotation' and new['nodes'][key[0]].get('name') in MODIFIED:changed+=1
   else:
    need(former[key]['rows']==current[key]['rows'],
        'UNAUTHORISED_ANIM_TRACK_CHANGE:'+str(key))
    unchanged+=1
  rt=current[(root,'translation')]['rows']
  need(abs(rt[-1][2]-rt[0][2]-TRAVEL)<1e-5,'FORWARD_TRAVEL_CHANGED')
  for label,d in LEGS.items():
   end=names[d['end']]
   for frame in range(FRAMES):
    t=frame*STEP;_,stance=phase(d,t)
    new['nodes'][root]['translation']=list(rt[frame])
    prev_pose={node:track['rows'][frame] for (node,path),track in former.items() if path=='rotation'}
    next_pose={node:track['rows'][frame] for (node,path),track in current.items() if path=='rotation'}
    po=pos(base.world_matrices(new,prev_pose),end)
    pn=pos(base.world_matrices(new,next_pose),end)
    err=math.dist(po,pn)
    if stance:
     max_stance_error=max(max_stance_error,err)
     # All animation tracks on limbs MUST remain bitwise identical during
     # stance. Added hoof track can be the real rest rotation.
     for n in list(UPSTREAM[label])+[d['lower']]:
      joint=names[n]
      need(former[(joint,'rotation')]['rows'][frame] ==
           current[(joint,'rotation')]['rows'][frame],
           'PLANTED_LEG_MOVED:'+label+':'+str(frame))
     original_foot=former.get((names[d['hoof']],'rotation'))
     expected=(tuple(original_foot['rows'][frame]) if original_foot is not None
               else tuple(base.node_rotation(new['nodes'][names[d['hoof']]])))
     need(tuple(current[(names[d['hoof']],'rotation')]['rows'][frame])==expected,
          'PLANTED_HOOF_CHANGED_FROM_PREVIOUS_ACTUAL_POSE:'+label+':'+str(frame))
    else:
     longest_error=max(longest_error,err)
  # Avoid velocity discontinuities at stride boundaries for every changed
  # and newly created channel; sample-to-sample increments bounded.
  for label,d in LEGS.items():
   for name in list(UPSTREAM[label])+[d['lower'],d['hoof']]:
    rows=current[(names[name],'rotation')]['rows']
    need(len(rows)==FRAMES and rows[0]==rows[-1],
         'INVALID_CYCLIC_REST_TRACK:'+name)
    for r,s in zip(rows,rows[1:]):
     dot=min(1.,abs(sum(i*j for i,j in zip(r,s))))
     deg=math.degrees(2*math.acos(dot))
     max_step=max(max_step,deg)
 new['nodes'][root]['translation']=orig
 # Physical skinned mesh checks. Bone-position targets alone did not catch
 # the owner's earlier reversed-looking hooves. Sample real body vertices
 # around all four hooves, not a proxy sphere attached to the skeleton.
 body=new['meshes'][0]['primitives'][0]
 original_positions=base.accessor(new,newb,body['attributes']['POSITION'])
 joints=base.accessor(new,newb,body['attributes']['JOINTS_0'])
 weights=base.accessor(new,newb,body['attributes']['WEIGHTS_0'])
 hoof_samples={}
 for label,d in LEGS.items():
  sign=-1 if label[0]=='L' else 1
  ids=[i for i,(x,y,z) in enumerate(original_positions)
       if y<.13 and x*sign>.05 and (z>.14 if label[1]=='F' else z<-.62)]
  need(len(ids)>90,'REAL_HOOF_SURFACE_NOT_MAPPED:'+label)
  hoof_samples[label]=ids
 skin_witness={'sample_vertex_count':{n:len(v) for n,v in hoof_samples.items()},
               'swing_surface_min_y':{},'stance_max_surface_deviation':0.,
               'swing_surface_max_delta':{},'mid_swing_surface_rearward_median_z_vs_neutral_distal_pose':{}}
 try:
  for stage in (0,1):
   former,current=a[stage],b[stage]
   rt=current[(root,'translation')]['rows']
   for label,d in LEGS.items():
    miny=1e6;maxd=0.;signed_z=[]
    for frame in range(0,PER_STRIDE):
     t=frame*STEP;_,stance=phase(d,t)
     # Every stance vertex must be stationary relative to previous accepted
     # v0.6.3 mesh pose; a no-op on a terminal bone is not proof.
     if (not stance) and frame%2!=0:continue
     new['nodes'][root]['translation']=list(rt[frame])
     oldpose={n:track['rows'][frame] for (n,k),track in former.items() if k=='rotation'}
     newpose={n:track['rows'][frame] for (n,k),track in current.items() if k=='rotation'}
     oldskin=base.skin_matrices(new,oldb,base.world_matrices(new,oldpose))
     newskin=base.skin_matrices(new,newb,base.world_matrices(new,newpose))
     # Judge bending against the SAME upstream pose with lower+hoof bones
     # neutral, not against the previous animated pose. The production
     # source can already have a curled hind hoof, so a tiny delta from
     # the old clip is not proof of wrong direction.
     neutralpose=dict(newpose)
     for distal in (d['lower'],d['hoof']):
      neutralpose[names[distal]]=base.node_rotation(new['nodes'][names[distal]])
     neutral_skin=base.skin_matrices(new,newb,base.world_matrices(new,neutralpose))
     for i in hoof_samples[label]:
      q0=base.deform_vertex(original_positions[i],joints[i],weights[i],oldskin)
      q1=base.deform_vertex(original_positions[i],joints[i],weights[i],newskin)
      delta=math.dist(q0,q1)
      if stance:skin_witness['stance_max_surface_deviation']=max(
           skin_witness['stance_max_surface_deviation'],delta)
      else:
       miny=min(miny,q1[1]);maxd=max(maxd,delta)
       phase_u,_=phase(d,t)
       swing_frac=(phase_u-STANCE)/(1-STANCE)
       if .42<=swing_frac<=.58:
        qneutral=base.deform_vertex(original_positions[i],joints[i],weights[i],neutral_skin)
        signed_z.append(q1[2]-qneutral[2])
    need(bool(signed_z),'MID_SWING_PHYSICAL_HOOF_DIRECTION_NOT_SAMPLED:'+label)
    signed_z.sort();median=signed_z[len(signed_z)//2]
    skin_witness['mid_swing_surface_rearward_median_z_vs_neutral_distal_pose'][f'STAGE_{stage+1}_{label}']=median
    need(median<(-.002 if label[1]=='F' else -.00005),
         'HOOF_SKIN_BENDS_FORWARD_INSTEAD_OF_BACKWARD:'+label+':'+str(median))
    skin_witness['swing_surface_min_y'][f'STAGE_{stage+1}_{label}']=miny
    skin_witness['swing_surface_max_delta'][f'STAGE_{stage+1}_{label}']=maxd
 finally:new['nodes'][root]['translation']=orig
 need(skin_witness['stance_max_surface_deviation']<1e-6,
      'ACTUAL_SKINNED_PLANTED_HOOF_MOVED')
 need(min(skin_witness['swing_surface_min_y'].values())>-.070,
      'DISTAL_HOOF_SURFACE_PENETRATES_GROUND_EXCESSIVELY')
 need(max(skin_witness['swing_surface_max_delta'].values())<.18,
      'SWING_HOOF_MESH_DEFORMATION_EXCESSIVE')
 need(max_stance_error<1e-6,'STANCE_HOOF_MARKER_DID_MOVE')
 need(longest_error<.012,'SWING_WORLD_HOOF_TARGET_REGRESSED')
 need(max_step<42.,'JOINT_ANIMATION_POP_TOO_LARGE:'+str(max_step))
 return {'max_stance_marker_drift':max_stance_error,
  'max_swing_marker_deviation':longest_error,
  'max_joint_step_degrees':max_step,
  'changed_old_tracks':changed,'unchanged_old_tracks':unchanged,
  'new_hoof_tracks_by_walk':{
   'STAGE_'+str(i+1):sum((names[n],'rotation') not in a[i]
     for n in HIND_HOOF_TRACKS) for i in range(3)},
  'existing_hind_hoof_tracks_by_walk':{
   'STAGE_'+str(i+1):sum((names[n],'rotation') in a[i]
     for n in HIND_HOOF_TRACKS) for i in range(3)},
  'corrected_existing_forehoof_tracks_each_walk':2,
  'all_previous_clips_preserved':True,
  'model_structure_untouched':True,'world_travel_exact':TRAVEL,
  'physical_hoof_skin_validation':skin_witness,'visual_verdict':'PENDING'}
