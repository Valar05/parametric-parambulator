#!/usr/bin/env python3
"""Mwni 2.1.1 actual documented retarget experiment on owner's real donor and canonical target.
Only Blender add-on performs retarget & bake. Candidate source, target & outputs isolated.
"""
from __future__ import annotations
import bpy, addon_utils, argparse, hashlib, json, math, os, pathlib, shutil, sys, traceback
from mathutils import Matrix, Vector

PARTS=('Hips','Spine','Spine1','Spine2','Neck','Head','LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase')
JOINTS=('LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','LeftForeArm','RightArm','RightForeArm','Spine','Spine2')


def name(p):return 'mixamorig:'+p

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def save_json(path,o):pathlib.Path(path).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')

def active(obj):
 if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
 for o in bpy.context.selected_objects:o.select_set(False)
 obj.select_set(True);bpy.context.view_layer.objects.active=obj

def world(o,part):return o.matrix_world @ o.pose.bones[name(part)].matrix.translation

def bone_local_q(o,part):
 b=o.pose.bones[name(part)];m=b.parent.matrix.inverted_safe() @ b.matrix if b.parent else b.matrix
 return m.to_quaternion().normalized()

def angular(q,p):return math.degrees(q.rotation_difference(p).angle)

def frame_records(src,tgt,start,end,shoes):
 frames=sorted({float(start),float(end),float(start+.5),float(end-.5),float((start+end)/2)} | {float(i) for i in range(start,end+1)})
 rows=[]
 for f in frames:
  bpy.context.scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  source={p:world(src,p) for p in ('Hips','LeftFoot','RightFoot','LeftUpLeg','RightUpLeg')}
  target={p:world(tgt,p) for p in source}
  qs={p:bone_local_q(src,p) for p in JOINTS};qt={p:bone_local_q(tgt,p) for p in JOINTS}
  shoe=shoe_witnesses(shoes)
  rows.append({'f':f,'src':{k:list(v) for k,v in source.items()},'dst':{k:list(v) for k,v in target.items()},
    'qSrc':{k:list(v) for k,v in qs.items()},'qDst':{k:list(v) for k,v in qt.items()},'sole':shoe})
 return rows

def shoe_indices(meshes):
 result={s:[] for s in ('Left','Right')}
 for o in meshes:
  groups={g.index:g.name for g in o.vertex_groups}
  for v in o.data.vertices:
   for side in result:
    weight=sum(a.weight for a in v.groups if groups.get(a.group) in (name(side+'Foot'),name(side+'ToeBase')))
    if weight>=.4:result[side].append((o,v.index))
 for s,p in result.items():
  if len(p)<8:raise RuntimeError('NO_SKINNED_SOLE_WITNESSES_'+s)
  p.sort(key=lambda x:(x[0].name,x[1]));result[s]=[p[int(i*(len(p)-1)/min(119,len(p)-1))] for i in range(min(120,len(p)))]
 return result

def shoe_witnesses(shoes):
 deps=bpy.context.evaluated_depsgraph_get();evals={};answer={}
 try:
  for o in {o for side in shoes.values() for o,i in side}:
   e=o.evaluated_get(deps);evals[o]=(e,e.to_mesh())
  for side,points in shoes.items():
   heights=[]
   for o,i in points:
    e,m=evals[o]
    if i>=len(m.vertices):raise RuntimeError('EVALUATED_VERTEX_TOPOLOGY_MISMATCH')
    heights.append((e.matrix_world@m.vertices[i].co).z)
   heights.sort();answer[side]={'minZ':round(heights[0],5),'p10Z':round(heights[max(0,math.floor(len(heights)*.10)-1)],5)}
  return answer
 finally:
  for e,m in evals.values():e.to_mesh_clear()

def vector(row,key,part):return Vector(row[key][part])

def quatr(row,key,part):
 from mathutils import Quaternion
 return Quaternion(row[key][part])

def metrics(rows,floor_z):
 if len(rows)<5:raise RuntimeError('TOO_FEW_ANIMATION_SAMPLES')
 first=rows[0];angle_src={p:max(angular(quatr(r,'qSrc',p),quatr(first,'qSrc',p)) for r in rows) for p in JOINTS}
 angle_dst={p:max(angular(quatr(r,'qDst',p),quatr(first,'qDst',p)) for r in rows) for p in JOINTS}
 foot={}
 for side in ('Left','Right'):
  p=side+'Foot';so=[];to=[];rel=[]
  for r in rows:
   sr=vector(r,'src',p)-vector(r,'src','Hips');tr=vector(r,'dst',p)-vector(r,'dst','Hips')
   so.append(sr);to.append(tr)
   rel.append(float((tr-to[0]-(sr-so[0])).length))
  srun=max((x-so[0]).length for x in so);trun=max((x-to[0]).length for x in to)
  absolute_errors=[(vector(r,'dst',p)-vector(r,'src',p)).length for r in rows]
  ground_distances=[abs(r['sole'][side]['p10Z']-floor_z) for r in rows]
  contacts=[r for r in rows if abs(r['sole'][side]['p10Z']-floor_z)<=.08]
  adjacent_contacts=[(a,b) for a,b in zip(rows,rows[1:]) if
       abs(a['sole'][side]['p10Z']-floor_z)<=.08 and abs(b['sole'][side]['p10Z']-floor_z)<=.08]
  horizontal_contact_drift=max((Vector((vector(b,'dst',p).x-vector(a,'dst',p).x,
       vector(b,'dst',p).y-vector(a,'dst',p).y)).length for a,b in adjacent_contacts),default=0.)
  foot[side]={'maxAbsoluteFootWorldError_m':round(max(absolute_errors),5),
   'bestSoleContactDistance_m':round(min(ground_distances),5),
   'contactFramesWithin8cm':len(contacts),'totalFrames':len(rows),
   'maxConsecutiveContactFootHorizontalDrift_m':round(horizontal_contact_drift,5),
   'minSkinnedSoleZ':round(min(r['sole'][side]['minZ'] for r in rows),5),
   'sourceHipRelativeExcursion_m':round(srun,5),'targetHipRelativeExcursion_m':round(trun,5),'hipRelativeMotionErrorMax_m':round(max(rel),5),
   'soleRange_m':round(max(r['sole'][side]['p10Z'] for r in rows)-min(r['sole'][side]['p10Z'] for r in rows),5)}
 seps=[(vector(r,'src','LeftFoot')-vector(r,'src','RightFoot')).length for r in rows]
 tseps=[(vector(r,'dst','LeftFoot')-vector(r,'dst','RightFoot')).length for r in rows]
 error=max(abs(a-b) for a,b in zip(seps,tseps))
 return {'sourceExcursionDegrees':{k:round(v,3) for k,v in angle_src.items()},'targetExcursionDegrees':{k:round(v,3) for k,v in angle_dst.items()},
  'foot':foot,'sourceFootSeparationRange_m':[round(min(seps),5),round(max(seps),5)],'targetFootSeparationRange_m':[round(min(tseps),5),round(max(tseps),5)],
  'maxAbsoluteFootSeparationMismatch_m':round(error,5),'referenceSoleFloorZ':round(floor_z,5)}

def check(m,clip):
 """Hard physical gate; rejects hip-only tracks even if upstream IK and bake are green."""
 fail=[];src=m['sourceExcursionDegrees'];dst=m['targetExcursionDegrees']
 for side in ('Left','Right'):
  for segment in ('UpLeg','Leg'):
   part=side+segment
   if src[part]>=8 and dst[part]<max(3,src[part]*.22):fail.append('STIFF_'+part+'_SOURCE_'+str(src[part])+'_TARGET_'+str(dst[part]))
 for p in ('LeftArm','RightArm','LeftForeArm','RightForeArm','Spine2'):
  if src[p]>=12 and dst[p]<max(4,src[p]*.22):fail.append('UNTRANSFERRED_'+p)
 if clip=='Kick' and not any(dst[p]>=8 for p in ('LeftUpLeg','RightUpLeg','LeftLeg','RightLeg')):fail.append('KICK_NO_ARTICULATED_LEG')
 if clip=='Light1' and not any(dst[p]>=7 for p in ('LeftArm','RightArm','LeftForeArm','RightForeArm')):fail.append('LIGHT1_NO_ARTICULATED_ARMS')
 if m['maxAbsoluteFootSeparationMismatch_m']>.22:fail.append('FOOT_SEPARATION_MISMATCH_GT_22CM')
 for side,v in m['foot'].items():
  if v['sourceHipRelativeExcursion_m']>.08 and v['targetHipRelativeExcursion_m']<.22*v['sourceHipRelativeExcursion_m']:
   fail.append('HIP_ONLY_'+side+'Foot')
  if v['hipRelativeMotionErrorMax_m']>.24:fail.append('FOOT_TRAJECTORY_MISMATCH_'+side)
  if v['maxAbsoluteFootWorldError_m']>.24:fail.append('FOOT_WORLD_POSITION_NOT_REACHED_'+side)
  if v['bestSoleContactDistance_m']>.15:fail.append('SHOE_NEVER_NEAR_REST_FLOOR_'+side)
  if v.get('minSkinnedSoleZ',m.get('referenceSoleFloorZ',0.0))<m.get('referenceSoleFloorZ',0.0)-.055:fail.append('SHOE_PENETRATES_REST_FLOOR_'+side)
  if v.get('maxConsecutiveContactFootHorizontalDrift_m',0)>.22:fail.append('SUPPORT_FOOT_SLIDING_'+side)
 if clip=='Light1' and any(v.get('contactFramesWithin8cm',2)<max(2,v.get('totalFrames',10)//8) for v in m['foot'].values()):
  fail.append('LIGHT1_STANDING_FEET_NOT_PLANTED')
 if clip=='Kick' and sum(v.get('contactFramesWithin8cm',2) for v in m['foot'].values())<2:
  fail.append('KICK_NO_GROUNDED_SUPPORT_FOOT')
 return fail

def setup_addon(addon_dir):
 root=pathlib.Path(addon_dir)/'animation_retargeting'
 if not root.joinpath('__init__.py').is_file():raise RuntimeError('MISSING_PINNED_ADDON')
 # Use installed exact upstream addon, not a forked interpretation of its IK math.
 scriptroot=pathlib.Path(bpy.utils.user_resource('SCRIPTS',path='addons',create=True))
 target=scriptroot/'animation_retargeting'
 if not target.exists():
  tmp=scriptroot/('.mwni-v147-'+str(os.getpid()));shutil.copytree(root,tmp);os.rename(tmp,target)
 elif {p.name:sha(p) for p in root.glob('*.py')}!={p.name:sha(p) for p in target.glob('*.py')}:
  raise RuntimeError('EXISTING_ADDON_DIFFERENT_FROM_PINNED_SOURCE')
 bpy.utils.refresh_script_paths()
 if str(scriptroot) not in sys.path:sys.path.insert(0,str(scriptroot))
 if addon_utils.enable('animation_retargeting',default_set=True,persistent=False) is None:raise RuntimeError('ADDON_ENABLE_FAILED')
 import animation_retargeting as addon
 return addon

def get_action(label):
 r=[a for a in bpy.data.actions if a.name==label]
 if len(r)!=1:raise RuntimeError('SOURCE_ACTION_NOT_EXACTLY_FOUND_'+label)
 return r[0]

def align_scene(src,tgt):
 # Target scale MUST be unit per pinned upstream README.
 if max(abs(s-1) for s in tgt.matrix_world.to_scale())>.0003:
  raise RuntimeError('DOCUMENTED_MWNI_TARGET_SCALE_NOT_ONE_'+repr(list(tgt.matrix_world.to_scale())))
 def length(o,side):
  bones=[o.matrix_world@o.data.bones[name(side+p)].head_local for p in ('UpLeg','Leg','Foot')]
  return (bones[0]-bones[1]).length+(bones[1]-bones[2]).length
 before={side:length(src,side) for side in ('Left','Right')}
 target={side:length(tgt,side) for side in ('Left','Right')}
 k=sum(target.values())/sum(before.values())
 if not (.45<k<2.5):raise RuntimeError('SOURCE_SCALE_FIT_UNSAFE_'+str(k))
 src.matrix_world=Matrix.Scale(k,4) @ src.matrix_world
 src_r=src.matrix_world@src.data.bones[name('RightUpLeg')].head_local
 src_l=src.matrix_world@src.data.bones[name('LeftUpLeg')].head_local
 tgt_r=tgt.matrix_world@tgt.data.bones[name('RightUpLeg')].head_local
 tgt_l=tgt.matrix_world@tgt.data.bones[name('LeftUpLeg')].head_local
 v=src_r-src_l;u=tgt_r-tgt_l
 if Vector((v.x,v.y)).length<.005 or Vector((u.x,u.y)).length<.005:raise RuntimeError('NO_REST_LATERAL_AXIS')
 yaw=math.atan2(v.x*u.y-v.y*u.x,v.x*u.x+v.y*u.y)
 src.matrix_world=Matrix.Rotation(yaw,4,'Z') @ src.matrix_world
 src.matrix_world=Matrix.Translation(world(tgt,'Hips')-world(src,'Hips')) @ src.matrix_world
 return {'sourceScaleFactor':k,'yawRadians':yaw,'sourceLegLengths':before,'targetLegLengths':target,'targetUnitScale':list(tgt.matrix_world.to_scale())}

def establish_alignment(ctx,addon,mode):
 """Use actual Mwni documented enter -> pose target to source rest -> store -> leave workflow."""
 active(ctx.target)
 addon.alignment.enter_alignment_mode(ctx)
 src=ctx.source;tgt=ctx.target
 if src.data.pose_position!='REST':raise RuntimeError('PLUGIN_ALIGNMENT_DID_NOT_SET_SOURCE_REST')
 before={m.target:Matrix((m.offset[0:4],m.offset[4:8],m.offset[8:12],m.offset[12:16])) for m in ctx.mappings}
 try:
  for bone in tgt.pose.bones:
   if bone.name not in {m.target for m in ctx.mappings}:continue
   source=src.data.bones.get(bone.name)
   if not source:continue
   desired_rotation=(tgt.matrix_world.to_quaternion().inverted() @ (src.matrix_world@source.matrix_local).to_quaternion()).normalized()
   current=bone.matrix.copy();loc=current.translation.copy()
   if mode=='full_rest_orientation':
    q=desired_rotation
   elif mode=='bone_axis_no_roll':
    current_direction=bone.tail-bone.head
    source_vector=src.matrix_world.to_3x3()@(source.tail_local-source.head_local)
    target_direction=tgt.matrix_world.to_3x3().inverted_safe()@source_vector
    q=current.to_quaternion()
    if current_direction.length>.0001 and target_direction.length>.0001:
     q=current_direction.normalized().rotation_difference(target_direction.normalized())@q
   else:raise RuntimeError('INVALID_ALIGNMENT_STRATEGY')
   bone.matrix=Matrix.Translation(loc)@q.to_matrix().to_4x4()
   bpy.context.view_layer.update()
  addon.alignment.store_alignments(ctx)
  changed=ctx.get_bone_alignments_count()
  if changed<5:raise RuntimeError('ALIGNMENT_NOT_STORED_OR_TRIVIAL_'+str(changed))
 finally:
  addon.alignment.leave_alignment_mode(ctx)
 return {'mode':mode,'changedBoneCount':changed,'restOffsetPrevious':len(before)}

def is_floor_only_fail(fail):
 # The standing/support contact requirements are consequences of the SAME
 # floor displacement, not independent evidence of broken bone articulation.
 return bool(fail) and all(x.startswith('SHOE_NEVER_NEAR_REST_FLOOR_') or
   x in ('LIGHT1_STANDING_FEET_NOT_PLANTED','KICK_NO_GROUNDED_SUPPORT_FOOT') for x in fail)

def measured_floor_bias(rows, floor_z):
 """Measure existing skinned wedges, not bones/proxy empties, before scene-placement adjustment."""
 lowest={side:min(float(r['sole'][side]['p10Z']) for r in rows) for side in ('Left','Right')}
 return {'perSideLowestP10Z':lowest,'bias_m':(sum(lowest.values())/2.0)-floor_z,
         'sideDifference_m':abs(lowest['Left']-lowest['Right'])}

def adjust_scene_root_world(src,tgt,src_base,tgt_base,mesh_base,shift,mode):
 """Scene-space placement of EXISTING plugin source/target, never edit animation curves.
 Keep source and target together for a common floor correction; let plugin drivers solve.
 Try source-only placement first. Do not touch original rig data or model files.
 """
 src.matrix_world=src_base.copy()
 tgt.matrix_world=tgt_base.copy()
 for mesh,m in mesh_base.items():
  if mesh.parent is None: mesh.matrix_world=m.copy()
 correction=Matrix.Translation(Vector((0,0,-shift)))
 if mode=='source_only':
  src.matrix_world=correction@src_base
 elif mode=='group_world':
  src.matrix_world=correction@src_base
  tgt.matrix_world=correction@tgt_base
  # Only separately move standalone meshes. Parent-driven meshes inherit their parent's transform.
  for mesh,m in mesh_base.items():
   if mesh.parent is None: mesh.matrix_world=correction@m
 else:raise RuntimeError('UNRECOGNIZED_FLOOR_PLACEMENT_'+mode)
 bpy.context.view_layer.update()

def export_review(tgt,meshes,clip,out,suffix):
 """Direct Blender exporter of native Mwni baked action. Review-only; no canonical writes."""
 out.mkdir(parents=True,exist_ok=True)
 active(tgt)
 for o in bpy.context.selected_objects:o.select_set(False)
 for o in [tgt]+meshes:o.select_set(True);o.hide_set(False)
 bpy.context.view_layer.objects.active=tgt
 glb=out/('MWNI147_'+clip+'_'+suffix+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,
   export_animations=True,export_animation_mode='ACTIVE_ACTIONS',
   export_force_sampling=True,export_yup=True,export_apply=False)
 if not glb.is_file() or glb.stat().st_size<1000000:raise RuntimeError('REVIEW_EXPORT_TOO_SMALL_'+str(glb))
 return {'path':str(glb),'sha256':sha(glb),'bytes':glb.stat().st_size}

def run_clip(src,tgt,addon,action,meshes,clip,out,try_modes):
 ctx=tgt.retargeting_context
 start,end=map(int,map(round,action.frame_range));bpy.context.scene.frame_start=start;bpy.context.scene.frame_end=end
 bpy.context.scene.render.fps=30;bpy.context.scene.render.fps_base=1
 if end-start<4 or end-start>130:raise RuntimeError('INVALID_SOURCE_ACTION_DURATION_'+clip)
 src.animation_data.action=action
 shoes=shoe_indices(meshes)
 attempts=[]
 src_base=src.matrix_world.copy();tgt_base=tgt.matrix_world.copy()
 mesh_base={o:o.matrix_world.copy() for o in meshes}
 diagnostic=None
 for mode in try_modes:
  row={'mode':mode,'clip':clip,'status':'RUNNING'};attempts.append(row)
  try:
   # Restore exact scene state before each independent plugin rest-alignment attempt.
   adjust_scene_root_world(src,tgt,src_base,tgt_base,mesh_base,0,'group_world')
   # Reset previous plugin controls, drivers and target pose between independent strategies.
   ctx.setting_disable_drivers=True;ctx.update_drivers();ctx.did_setup_empty_alignment=False
   ctx.setting_correct_feet=False;ctx.update_drivers()
   tgt.animation_data.action=None
   for m in ctx.mappings:m.reset_offset()
   for b in tgt.pose.bones:
    b.matrix_basis=Matrix.Identity(4)
   bpy.context.scene.frame_set(start)
   reference_sole=shoe_witnesses(shoes)
   floor_z=min(reference_sole[side]['p10Z'] for side in ('Left','Right'))
   row['referenceRestSoles']=reference_sole
   row['restFootBoneWorld']={side:list(tgt.matrix_world@tgt.data.bones[name(side+'Foot')].head_local)
                             for side in ('Left','Right')}
   row['sourceBaseMatrix']=[list(line) for line in src_base]
   row['targetBaseMatrix']=[list(line) for line in tgt_base]
   row['alignment']=establish_alignment(ctx,addon,mode)
   ctx.setting_disable_drivers=False;ctx.update_drivers()
   noik=frame_records(src,tgt,start,end,shoes)
   row['plain']=metrics(noik,floor_z)
   row['plainSoleSample']=[{'frame':r['f'],'left':r['sole']['Left']['p10Z'],
      'right':r['sole']['Right']['p10Z']} for r in noik]
   # Always measure articulating limbs BEFORE enabling foot IK. IK cannot compensate missing source-to-target bone rotations.
   srcm=row['plain']['sourceExcursionDegrees'];dstm=row['plain']['targetExcursionDegrees']
   bone_fail=[p for p in JOINTS if srcm[p]>12 and dstm[p]<max(3,srcm[p]*.20)]
   if bone_fail:raise RuntimeError('MAPPED_DRIVERS_MISSING_SOURCE_ARTICULATION_'+repr(bone_fail))
   row['withoutIKPhysicalFailures']=check(row['plain'],clip)
   if not row['withoutIKPhysicalFailures']:
    # Optional IK is not mandatory when documented driver retarget itself passes physical checks.
    pre=noik;row['withIK']=row['plain'];row['correctionMode']='PLUGIN_MAPPED_DRIVERS_NO_IK_NEEDED'
   else:
    if not hasattr(bpy,'ctx'):setattr(bpy,'ctx',bpy.context) # old upstream PropertyGroup callback spelling
    ctx.setting_correct_feet=True
    for side in ('Left','Right'):
     limb=ctx.get_ik_limb_by_name(side.lower()+'-foot')
     if limb is None:raise RuntimeError('MWNI_FOOT_LIMB_MISSING_'+side)
     limb.origin_bone=name(side+'UpLeg');limb.target_bone=name(side+'Foot')
    ctx.handle_ik_change();ctx.update_drivers()
    if not all(ctx.get_ik_limb_by_name(side.lower()+'-foot').enabled for side in ('Left','Right')):
     raise RuntimeError('MWNI_BOTH_IK_LIMBS_NOT_ACTIVE')
    pre=frame_records(src,tgt,start,end,shoes);row['withIK']=metrics(pre,floor_z)
    row['correctionMode']='PLUGIN_OPTIONAL_BILATERAL_FOOT_IK'
   row['ikSoleSample']=[{'frame':r['f'],'left':r['sole']['Left']['p10Z'],
      'right':r['sole']['Right']['p10Z']} for r in pre]
   fail=check(row['withIK'],clip);row['physicalFailures']=fail
   row['placementExploration']=[]
   # Do not "fix" incorrect legs with an IK toggle. If limb articulation and relative
   # foot trajectories are already good, investigate whether the whole imported
   # source ACTION sits above the target's REST foot plane by a common Z offset.
   if is_floor_only_fail(fail):
    initial=measured_floor_bias(pre,floor_z)
    row['floorBiasMeasuredFromActualSkin']=initial
    if .20<initial['bias_m']<1.6 and initial['sideDifference_m']<.20:
     # Bounded feedback search within documented source/target scene alignment.
     # Source-only first, then common-world placement if the old drivers are
     # invariant to a source-only world offset. No bone animation curves altered.
     for placement in ('source_only','group_world'):
      for factor in (1.0,.9,1.1):
       amount=initial['bias_m']*factor
       adjust_scene_root_world(src,tgt,src_base,tgt_base,mesh_base,amount,placement)
       ctx.update_drivers()
       candidate_rows=frame_records(src,tgt,start,end,shoes)
       candidate_metrics=metrics(candidate_rows,floor_z)
       candidate_fail=check(candidate_metrics,clip)
       info={'placement':placement,'shiftZ_m':round(-amount,5),
             'measuredSkinFloorBias':measured_floor_bias(candidate_rows,floor_z),
             'footMotion':candidate_metrics['foot'],
             'failures':candidate_fail}
       row['placementExploration'].append(info)
       if not candidate_fail:
        pre=candidate_rows;row['withIK']=candidate_metrics
        row['physicalFailures']=[];row['placementAcceptedForBake']=info
        row['correctionMode']+='__SCENE_REST_FLOOR_PLACEMENT_'+placement
        break
      if not row['physicalFailures']:break
     if row['physicalFailures']:
      adjust_scene_root_world(src,tgt,src_base,tgt_base,mesh_base,0,'group_world')
      ctx.update_drivers()
    else:
     row['floorPlacementNotAttempted']='UNSAFE_OR_ASYMMETRIC_BIAS'
   fail=row['physicalFailures']
   if fail:raise RuntimeError('PRE_BAKE_PHYSICAL_GATE_'+repr(fail))
   active(tgt);bpy.ops.object.mode_set(mode='POSE')
   try:
    ctx.setting_bake_step=1;ctx.setting_bake_linear=True;addon.baking.transfer_anim(ctx)
   finally:bpy.ops.object.mode_set(mode='OBJECT')
   baked=tgt.animation_data.action
   if baked is None:raise RuntimeError('MWNI_BAKE_NO_ACTION')
   row['bakedAction']=baked.name
   ctx.setting_disable_drivers=True;ctx.update_drivers()
   post=frame_records(src,tgt,start,end,shoes);row['baked']=metrics(post,floor_z)
   problems=check(row['baked'],clip)
   for p in JOINTS:
    b=row['baked']['targetExcursionDegrees'][p];a=row['withIK']['targetExcursionDegrees'][p]
    if a>10 and b<.75*a:problems.append('BAKE_LOST_'+p)
   if problems:raise RuntimeError('BAKED_PHYSICAL_GATE_'+repr(problems))
   # Export only plugin-native baked bones after both motion and skin gates pass.
   row['outputGLB']=export_review(tgt,meshes,clip,out,'UNAPPROVED')
   blend=out/('MWNI147_'+clip+'_UNAPPROVED.blend')
   bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
   row['outputBlend']={'path':str(blend),'sha256':sha(blend),'bytes':blend.stat().st_size}
   row['status']='BLENDER_IK_BAKE_AND_MOTION_GATES_PASSED_UNAPPROVED'
   return row,attempts,diagnostic
  except Exception as exc:
   row['status']='FAILED_VALIDATION';row['error']=str(exc);row['traceback']=traceback.format_exc()[-2400:]
   print('PLUGIN_ATTEMPT_FAILED='+clip+' mode='+mode+' '+str(exc),flush=True)
   # A physically rejected candidate can still be useful for OWNER VISUAL
   # DIAGNOSIS. Export a clearly rejected plugin-native action only if it really
   # articulates limbs and the failed criteria were skin/floor placement only.
   if diagnostic is None and is_floor_only_fail(row.get('physicalFailures')):
    try:
     ctx.update_drivers();active(tgt);bpy.ops.object.mode_set(mode='POSE')
     try:
      ctx.setting_bake_step=1;ctx.setting_bake_linear=True;addon.baking.transfer_anim(ctx)
     finally:bpy.ops.object.mode_set(mode='OBJECT')
     if tgt.animation_data.action is None:raise RuntimeError('DIAGNOSTIC_BAKE_NO_ACTION')
     ctx.setting_disable_drivers=True;ctx.update_drivers()
     diagnostic={'status':'REJECTED_PHYSICAL_GATE_DIAGNOSTIC_NOT_ACCEPTED',
       'clip':clip,'failures':row['physicalFailures'],
       'outputGLB':export_review(tgt,meshes,clip,out/'diagnostic','REJECTED_DIAGNOSTIC'),
       'baked':metrics(frame_records(src,tgt,start,end,shoes),floor_z)}
     row['diagnosticPreviewExport']=diagnostic['outputGLB']
    except Exception as diagnostic_exc:
     row['diagnosticPreviewError']=str(diagnostic_exc)
   try:
    ctx.setting_disable_drivers=True;ctx.update_drivers()
   except Exception:pass
 return None,attempts,diagnostic

def main(args):
 output=pathlib.Path(args.output);output.mkdir(parents=True,exist_ok=True)
 receipt={'schema':'obsidianti-mwni-documented-retarget-v1.4.7','status':'START','sourceSha256':sha(args.source),'targetSha256':sha(args.target),'clips':{},'attempts':{},'diagnostics':{},'pluginVendorSha':args.vendor_sha}
 def save():save_json(output/'BLENDER_EVIDENCE.json',receipt)
 save()
 try:
  addon=setup_addon(args.addon)
  bpy.ops.wm.open_mainfile(filepath=args.source,load_ui=False)
  if not hasattr(bpy.types.Object,'retargeting_context'):
   addon=setup_addon(args.addon)
  source=[o for o in bpy.data.objects if o.type=='ARMATURE' and 'LeftFoot.IK' in o.pose.bones and name('LeftFoot') in o.pose.bones]
  if len(source)!=1:raise RuntimeError('SOURCE_ARMATURE_AMBIGUOUS')
  src=source[0];sourceobjs=set(bpy.data.objects)
  bpy.ops.import_scene.gltf(filepath=args.target,import_shading='NORMALS')
  newobjs=[o for o in bpy.data.objects if o not in sourceobjs]
  targets=[o for o in newobjs if o.type=='ARMATURE' and all(name(s) in o.pose.bones for s in PARTS)]
  if len(targets)!=1:raise RuntimeError('TARGET_ARMATURE_AMBIGUOUS')
  tgt=targets[0];meshes=[o for o in newobjs if o.type=='MESH' and (o.parent==tgt or any(m.type=='ARMATURE' and m.object==tgt for m in o.modifiers))]
  if not meshes:raise RuntimeError('TARGET_SKIN_MISSING')
  for o in (src,tgt):
   ad=o.animation_data_create();ad.use_nla=False
   for tr in ad.nla_tracks:tr.mute=True
  # Source actions are native donor actions. Imported glTF target actions may be
  # prefixed with an armature name, split into NLA strips, or renamed by Blender.
  # Do not require an exact target idle action to set up Mwni: per documentation,
  # the alignment reference is BOTH ARMATURES IN REST POSE, not animation playback.
  available=sorted([a.name for a in bpy.data.actions])
  target_nla=[{'name':track.name,'strips':[st.name for st in track.strips]}
              for track in tgt.animation_data.nla_tracks] if tgt.animation_data else []
  receipt['actionInventory']={'allActions':available,'sourceInitialAction':getattr(src.animation_data.action,'name',None),
    'targetInitialAction':getattr(tgt.animation_data.action,'name',None),'targetNLA':target_nla,
    'sourceRequired':['Idle','Kick','Light1'],
    'targetIdleMatches':[name for name in available if name.endswith('LionheartIdle_UNREVIEWED')]}
  selected=[get_action('Kick'),get_action('Light1')]
  src.animation_data.action=get_action('Idle')
  # Target animation is intentionally unassigned. Comparing rest-to-rest avoids
  # treating an action's arbitrary glTF importer alias as a skeletal requirement.
  tgt.animation_data.action=None
  source_old_pose=src.data.pose_position;target_old_pose=tgt.data.pose_position
  try:
   src.data.pose_position='REST';tgt.data.pose_position='REST'
   bpy.context.scene.frame_set(-1);bpy.context.view_layer.update()
   receipt['scenePreflight']=align_scene(src,tgt)
  finally:
   src.data.pose_position=source_old_pose;tgt.data.pose_position=target_old_pose
  receipt['sourceSetup']={'targetIdlePolicy':'GLTF_IMPORTER_NAME_NOT_REQUIRED',
    'alignmentReference':'REST_POSE_BOTH_ARMATURES','targetActionCleared':True,
    'targetIdleExactLookupSkipped':True}
  save()
  active(tgt);ctx=tgt.retargeting_context;ctx.is_importing=True
  ctx.source=src;ctx.target=tgt;ctx.selected_source=src;ctx.mappings.clear()
  for part in PARTS:
   if name(part) not in src.pose.bones or name(part) not in tgt.pose.bones:raise RuntimeError('EXACT_RIG_BONE_MISSING_'+part)
   m=ctx.mappings.add();m.source=m.target=name(part)
  extras=sorted(n for n in ({b.name for b in src.data.bones}&{b.name for b in tgt.data.bones})
      if n not in {name(p) for p in PARTS} and any(k in n.lower() for k in ('weapon','lance','sword','shield','blade','axe')))
  for extra in extras:
   m=ctx.mappings.add();m.source=m.target=extra
  ctx.is_importing=False
  receipt['mappedBones']=[m.source for m in ctx.mappings]
  receipt['weaponAuxiliaryMappings']=extras
  receipt['unmappedSourceBones']=[b.name for b in src.data.bones if b.name not in receipt['mappedBones']]
  receipt['unmappedTargetBones']=[b.name for b in tgt.data.bones if b.name not in receipt['mappedBones']]
  if len({m.source for m in ctx.mappings})!=len(ctx.mappings):raise RuntimeError('DUPLICATE_MAPPINGS')
  tgt.animation_data.action=None
  src.animation_data.action=selected[0]
  ctx.setting_disable_drivers=True
  strategies=['full_rest_orientation','bone_axis_no_roll']
  scene_source_base=src.matrix_world.copy();scene_target_base=tgt.matrix_world.copy()
  scene_mesh_base={o:o.matrix_world.copy() for o in meshes}
  for action in selected:
   # No inter-clip inheritance of scene-placement corrections or prior bake poses.
   adjust_scene_root_world(src,tgt,scene_source_base,scene_target_base,scene_mesh_base,0,'group_world')
   clip=action.name;row,attempts,diagnostic=run_clip(src,tgt,addon,action,meshes,clip,output/clip,strategies)
   receipt['attempts'][clip]=attempts
   if row:receipt['clips'][clip]=row
   if diagnostic:receipt['diagnostics'][clip]=diagnostic
   save()
  if not receipt['clips'] and not receipt['diagnostics']:raise RuntimeError('NO_PLUGIN_PREVIEW_OR_PHYSICALLY_VALID_CANDIDATE')
  receipt['status']=('BLENDER_VALIDATED_CANDIDATES_UNAPPROVED' if receipt['clips'] else 'ONLY_REJECTED_DIAGNOSTIC_PREVIEWS_AVAILABLE')
  save();print('MOTION_GATES_PASSED_CLIPS='+','.join(receipt['clips']),flush=True)
 except Exception as e:
  receipt['status']='BLOCKED';receipt['error']=str(e);receipt['traceback']=traceback.format_exc()[-6500:];save();raise

if __name__=='__main__':
 ap=argparse.ArgumentParser()
 for n in ('source','target','addon','vendor_sha','output'):ap.add_argument('--'+n.replace('_','-'),required=True)
 main(ap.parse_args(sys.argv[sys.argv.index('--')+1:]))
