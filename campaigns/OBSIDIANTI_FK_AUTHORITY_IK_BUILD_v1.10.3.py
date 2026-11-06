"""Obsidianti FK-authoritative, Blender IK calibration and gated authoring candidate.
Reads an Ares-scaled FK GLB, never modifies the GLB; every FK action is preserved.
"""
import bpy, sys, math, json, pathlib, traceback, hashlib
from mathutils import Vector, Matrix
args=sys.argv[sys.argv.index('--')+1:]
model, output, reportfile=args
SIDES=('Left','Right')
MOVES=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
LIMIT={'hip_m':0.001,'knee_m':0.004,'ankle_m':0.004,'foot_deg':0.75}
report={'schema':'obsidianti-fk-authoritative-ik-v1.10.3','status':'BUILDING','authority':'EXACT_ARES_SCALED_FK_GLB','fkUnchanged':True,'limits':LIMIT,'clips':{},'calibration':{},'issues':[]}
def save():
 pathlib.Path(reportfile).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(reportfile).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
def curves(a):
 result=list(getattr(a,'fcurves',[]))
 if not result:
  for layer in getattr(a,'layers',[]):
   for strip in getattr(layer,'strips',[]):
    for bag in getattr(strip,'channelbags',[]):result.extend(getattr(bag,'fcurves',[]))
 return result
def times(a):
 ks=sorted({round(float(k.co.x),5) for f in curves(a) for k in f.keyframe_points})
 if not ks:raise RuntimeError('NO_KEYS_'+a.name)
 # Dense evaluation in actual Blender-frame units. Include the exact original
 # authored keys AND a regular fifth-frame grid, plus every segment midpoint.
 # This avoids relying on source key intervals being regular or on FK curves
 # having linear interpolation. The owner explicitly prefers accurate dense IK.
 start,end=ks[0],ks[-1]
 grid=[round(start+i*0.4,7) for i in range(int((end-start)/0.4)+1)]
 grid=[min(end,t) for t in grid]
 dense=sorted(set(ks+grid+[end]))
 # Any source interval shorter than the dense step must still be sampled.
 return sorted(set(dense+[(x+y)/2 for x,y in zip(dense,dense[1:])]))
def frame(t):
 k=math.floor(t);bpy.context.scene.frame_set(k,subframe=t-k);bpy.context.view_layer.update()
def snapshot(arm,side):
 p=arm.pose.bones;prefix='mixamorig:'+side
 hip=p[prefix+'UpLeg'];knee=p[prefix+'Leg'];ankle=p[prefix+'Foot']
 return {'hip':hip.head.copy(),'knee':knee.head.copy(),'ankle':ankle.head.copy(),'shinTail':knee.tail.copy(),'ankleMatrix':ankle.matrix.copy(),'legLengths':[(knee.head-hip.head).length,(ankle.head-knee.head).length]}
def pole_location(row,side,distance=.45):
 h,k,a=row['hip'],row['knee'],row['ankle'];leg=a-h
 if leg.length<.02:raise RuntimeError('DEGENERATE_HIP_ANKLE_'+side)
 bend=k-(h+leg*(k-h).dot(leg)/leg.length_squared)
 if bend.length<.005:raise RuntimeError('DEGENERATE_KNEE_BEND_'+side)
 return k+bend.normalized()*distance
def get_error(obj,row,side):
 dg=bpy.context.evaluated_depsgraph_get();eva=obj.evaluated_get(dg)
 p=eva.pose.bones;prefix='mixamorig:'+side
 h=p[prefix+'UpLeg'];k=p[prefix+'Leg'];f=p[prefix+'Foot']
 return {'hip_m':(h.head-row['hip']).length,'knee_m':(k.head-row['knee']).length,'ankle_m':(f.head-row['ankle']).length,'foot_deg':math.degrees(f.matrix.to_quaternion().rotation_difference(row['ankleMatrix'].to_quaternion()).angle)}
def control_at(author,side,row):
 ctl=author.pose.bones['CTRL_'+side+'_ANKLE_IK'];pole=author.pose.bones['CTRL_'+side+'_KNEE_POLE']
 # Set controller at SHIN TAIL. Blender IK's effector is this exact endpoint,
 # which may differ from the imported foot joint. This difference is explicitly measured.
 m=ctl.bone.matrix_local.copy();m.translation=row['shinTail'];ctl.matrix=m
 pole.matrix=Matrix.Translation(pole_location(row,side)) @ pole.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
 bpy.context.view_layer.update()
def resolve_actions(ref):
 ad=ref.animation_data
 rows=[]
 for t in ad.nla_tracks:
  for s in t.strips:
   if s.action:rows.append((t.name,s.name,s.action))
 if ad.action:rows.append(('__ACTIVE__','__ACTIVE__',ad.action))
 ans={}
 for move in MOVES:
  key='Lionheart_'+move
  cand={id(a):a for t,s,a in rows if key in (t,s,a.name)}
  if len(cand)!=1:raise RuntimeError('ACTION_IDENTITY_'+key+' candidates='+str([(t,s,a.name) for t,s,a in rows]))
  ans[move]=next(iter(cand.values()))
 return ans
try:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=model)
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
 if len(rigs)!=1:raise RuntimeError('EXPECTED_ONE_ARMATURE '+str(len(rigs)))
 ref=rigs[0];ref.name='OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT'
 source=resolve_actions(ref)
 for a in bpy.data.actions:a.use_fake_user=True
 ref.animation_data.use_nla=False
 for track in ref.animation_data.nla_tracks:track.mute=True
 for side in SIDES:
  for suffix in ('UpLeg','Leg','Foot'):
   if 'mixamorig:'+side+suffix not in ref.pose.bones:raise RuntimeError('MISSING_BONE_'+side+suffix)
 author=ref.copy();author.data=ref.data.copy();bpy.context.collection.objects.link(author)
 author.name='OBSIDIANTI_IK_EDITABLE_UNAPPROVED';author.animation_data_clear();author.animation_data_create()
 for obj in list(bpy.context.scene.objects):
  if obj.type!='MESH':continue
  if obj.parent!=ref and not any(m.type=='ARMATURE' and m.object==ref for m in obj.modifiers):continue
  dup=obj.copy();dup.data=obj.data.copy();bpy.context.collection.objects.link(dup)
  dup.name='EDIT_'+obj.name
  if dup.parent==ref:dup.parent=author;dup.matrix_parent_inverse=obj.matrix_parent_inverse.copy()
  for mod in dup.modifiers:
   if mod.type=='ARMATURE' and mod.object==ref:mod.object=author
  obj.hide_render=True;obj.hide_set(True)
 ref.hide_render=True;ref.hide_set(True)
 bpy.ops.object.select_all(action='DESELECT');author.select_set(True);bpy.context.view_layer.objects.active=author
 bpy.ops.object.mode_set(mode='EDIT')
 for side in SIDES:
  upper=author.data.edit_bones['mixamorig:'+side+'UpLeg'];shin=author.data.edit_bones['mixamorig:'+side+'Leg'];foot=author.data.edit_bones['mixamorig:'+side+'Foot']
  c=author.data.edit_bones.new('CTRL_'+side+'_ANKLE_IK');c.head=shin.tail.copy();c.tail=c.head+Vector((0,0,.12));c.use_deform=False
  pole=author.data.edit_bones.new('CTRL_'+side+'_KNEE_POLE');pole.head=upper.head+Vector((0,.4,0));pole.tail=pole.head+Vector((0,0,.12));pole.use_deform=False
  pole.parent=c;pole.use_connect=False
  footrot=author.data.edit_bones.new('CTRL_'+side+'_FOOT_ROTATION');footrot.matrix=foot.matrix.copy();footrot.length=max(.1,foot.length);footrot.use_deform=False
 bpy.ops.object.mode_set(mode='POSE')
 for side in SIDES:
  shin=author.pose.bones['mixamorig:'+side+'Leg']
  con=shin.constraints.new('IK');con.name='FK_RECONSTRUCT_IK_'+side
  con.target=author;con.subtarget='CTRL_'+side+'_ANKLE_IK';con.chain_count=2;con.use_stretch=False;con.influence=1.0
  con.pole_target=author;con.pole_subtarget='CTRL_'+side+'_KNEE_POLE'
  rot=author.pose.bones['mixamorig:'+side+'Foot'].constraints.new('COPY_ROTATION')
  rot.name='FK_RECONSTRUCT_FOOT_'+side;rot.target=author;rot.subtarget='CTRL_'+side+'_FOOT_ROTATION'
  rot.target_space='WORLD';rot.owner_space='WORLD';rot.mix_mode='REPLACE';rot.influence=1.0
 # Pre-sample FULL original evaluated FK at keys and midpoints, no IK contamination.
 samples={};identities={}
 for move,a in source.items():
  ref.animation_data.action=a
  ts=times(a);samples[move]=[]
  for t in ts:
   frame(t)
   samples[move].append({'t':t,'leg':{s:snapshot(ref,s) for s in SIDES}})
  identities[move]={'originalAction':a.name,'samples':len(ts),'keys':sum(1 for t in ts if abs(t-round(t))<1e-6)}
 report['clips']=identities
 for move,rows in samples.items():
  max_gap=max(b['t']-a['t'] for a,b in zip(rows,rows[1:]))
  if max_gap>0.20001:raise RuntimeError('DENSE_SAMPLING_GAP '+move+' '+str(max_gap))
 # One action per clip, copying every native FK curve without modification.
 edit={}
 for move,a in source.items():
  dup=a.copy();dup.name='EDIT_IK_'+move;dup.use_fake_user=True;edit[move]=dup
 # Store FK joint length / shin endpoint mismatch. A major endpoint discrepancy is a
 # structural stop rather than an excuse to move the target ankle arbitrarily.
 endpoint={side:max((p['leg'][side]['shinTail']-p['leg'][side]['ankle']).length for frames in samples.values() for p in frames) for side in SIDES}
 report['shinTailToAnkleMax_m']=endpoint
 if max(endpoint.values())>.008:raise RuntimeError('IK_EFFECTOR_NOT_AT_FOOT_JOINT '+str(endpoint))
 # Key controllers at ALL source sample times. No sparse reduction before parity.
 # Knee poles are PARENTED to corresponding foot IK controls; their saved location keys
 # are therefore relative to the ankle controller, never world coordinates.
 prior_foot_quat={}
 for move,rows in samples.items():
  author.animation_data.action=edit[move]
  for row in rows:
   t=row['t'];frame(t)
   for side in SIDES:
    ctl=author.pose.bones['CTRL_'+side+'_ANKLE_IK'];pol=author.pose.bones['CTRL_'+side+'_KNEE_POLE'];fr=author.pose.bones['CTRL_'+side+'_FOOT_ROTATION']
    # Avoid edit-on-evaluated feedback: only the control bones are assigned.
    m=ctl.matrix.copy();m.translation=row['leg'][side]['shinTail'];ctl.matrix=m
    pm=pol.matrix.copy();pm.translation=pole_location(row['leg'][side],side);pol.matrix=pm
    # Quaternion mode must be selected BEFORE matrix assignment. Track the
    # previous key's hemisphere explicitly; otherwise Blender can interpolate
    # an apparent 180-degree foot flip even when both sampled poses match.
    fr.rotation_mode='QUATERNION'
    fr.matrix=row['leg'][side]['ankleMatrix'].copy()
    bpy.context.view_layer.update()
    q=fr.rotation_quaternion.copy()
    prior=prior_foot_quat.get((move,side))
    if prior is not None and q.dot(prior)<0:
     q.negate()
     fr.rotation_quaternion=q
    prior_foot_quat[(move,side)]=q.copy()
    ctl.keyframe_insert(data_path='location',frame=t,group=ctl.name)
    pol.keyframe_insert(data_path='location',frame=t,group=pol.name)
    fr.keyframe_insert(data_path='location',frame=t,group=fr.name)
    fr.keyframe_insert(data_path='rotation_quaternion',frame=t,group=fr.name)
  for fc in curves(edit[move]):
   if 'CTRL_' in fc.data_path:
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 report['denseKeying']={'gridStepFrames':0.4,'maximumSampleGapFrames':0.2,
                        'sampleCounts':{m:len(rows) for m,rows in samples.items()},
                        'footQuaternionHemisphereUnwrapped':True,
                        'noControllerCurveSimplification':True}

 # Determine whether any sampled pole-angle calibration works across all movements.
 # Difference from prior 1.9.5: do not silently assume nearest 7.5deg angle is valid.
 # Quantify true evaluated parity for EACH side over all clips.
 angles=[(-180+i*5)*math.pi/180 for i in range(72)]
 calibrated={}
 for side in SIDES:
  con=author.pose.bones['mixamorig:'+side+'Leg'].constraints['FK_RECONSTRUCT_IK_'+side]
  best=(float('inf'),None,{})
  representatives=[]
  for move,rows in samples.items():
   idx=sorted(set((0,len(rows)//4,len(rows)//2,3*len(rows)//4,len(rows)-1)))
   representatives.extend((move,rows[i]) for i in idx)
  for angle in angles:
   con.pole_angle=angle;worst={k:0 for k in LIMIT};score=0
   for move,row in representatives:
    author.animation_data.action=edit[move];frame(row['t'])
    e=get_error(author,row['leg'][side],side)
    for k in LIMIT:worst[k]=max(worst[k],e[k]);score+=(e[k]/LIMIT[k])**2
   if score<best[0]:best=(score,angle,worst)
  con.pole_angle=best[1];calibrated[side]={'poleAngle_deg':round(math.degrees(best[1]),4),'sampleScore':best[0],'representativeWorst':best[2]}
 report['calibration']=calibrated
 report['poleParentage']={s:{'pole':'CTRL_'+s+'_KNEE_POLE','parent':author.pose.bones['CTRL_'+s+'_KNEE_POLE'].parent.name,'connected':author.data.bones['CTRL_'+s+'_KNEE_POLE'].use_connect} for s in SIDES}
 if any(v['parent']!='CTRL_'+s+'_ANKLE_IK' or v['connected'] for s,v in report['poleParentage'].items()):raise RuntimeError('KNEE_POLE_PARENTAGE_FAILED')
 # Gated pole-plane reconstruction: ankle IK endpoint and foot orientation already
 # match the source within micrometers. Reposition only the knee pole controller in
 # the plane perpendicular to the FK hip/ankle axis, using the actual FK knee.
 # This preserves ALL original deform-bone FK action curves and foot target keys.
 # Crucially, edit the pole in armature/world space, then key its PARENT-LOCAL
 # location so that moving the ankle controller carries the knee pole along.
 pole_stats={}
 for move,rows in samples.items():
  author.animation_data.action=edit[move]
  pole_stats[move]={}
  for side in SIDES:
   pol=author.pose.bones['CTRL_'+side+'_KNEE_POLE']
   stats={'adjustedSamples':0,'maxBeforeKnee_m':0.,'maxAfterKnee_m':0.,'maxOffset_deg':0.,'under4mm':0,'sampleCount':len(rows),'examples':[]}
   previous_phase=0.
   for row in rows:
    frame(row['t']);refrow=row['leg'][side]
    before=get_error(author,refrow,side)['knee_m']
    stats['maxBeforeKnee_m']=max(stats['maxBeforeKnee_m'],before)
    h,k,a=refrow['hip'],refrow['knee'],refrow['ankle']
    axis=a-h
    if axis.length<.015:raise RuntimeError('INVALID_LEG_AXIS '+move+' '+side)
    axis.normalize();origin=h+axis*(k-h).dot(axis)
    ref_dir=k-origin
    if ref_dir.length<.00025:
     # At near full extension, the knee plane is nearly indeterminate.
     # Retain the previous phase, never make a discontinuous arbitrary flip.
     ref_dir=Vector((0.,1.,0.))
     ref_dir=ref_dir-axis*ref_dir.dot(axis)
     if ref_dir.length<.001:ref_dir=Vector((1.,0.,0.))-axis*axis.x
    ref_dir.normalize()
    distance=max(.35,sum(refrow['legLengths'])*.65)
    def try_phase(theta):
     rotated=Matrix.Rotation(theta,4,axis).to_3x3()@ref_dir
     point=origin+rotated*distance
     m=pol.matrix.copy();m.translation=point;pol.matrix=m
     bpy.context.view_layer.update()
     e=get_error(author,refrow,side)
     return e['knee_m'],point
    # Search a continuous correction for this exact FK sample, never using a
    # single universal pole angle to force geometrically different knee planes.
    # The first call recovers a stable seed; only sample positions are adjusted.
    if before>LIMIT['knee_m']*.5:
     import math as _math
     phases=[previous_phase + _math.radians(i*30) for i in range(-6,7)]
     measurements=[(try_phase(phi)[0],phi) for phi in phases]
     best_err,best_phi=min(measurements,key=lambda x:x[0]+1e-7*abs(x[1]-previous_phase))
     step=_math.radians(15)
     for _ in range(7):
      tests=[(try_phase(best_phi+j*step)[0],best_phi+j*step) for j in (-1,0,1)]
      best_err,best_phi=min(tests,key=lambda x:x[0]+1e-7*abs(x[1]-previous_phase))
      step*=.5
     after,point=try_phase(best_phi)
     previous_phase=best_phi
     pol.keyframe_insert(data_path='location',frame=row['t'],group=pol.name)
     stats['adjustedSamples']+=1
     stats['maxOffset_deg']=max(stats['maxOffset_deg'],abs(math.degrees(best_phi)))
     if after>LIMIT['knee_m'] and len(stats['examples'])<10:
      stats['examples'].append({'time':row['t'],'before_m':before,'after_m':after,'angle_deg':math.degrees(best_phi)})
    else:
     after=before
    stats['maxAfterKnee_m']=max(stats['maxAfterKnee_m'],after)
    if after<=LIMIT['knee_m']:stats['under4mm']+=1
   pole_stats[move][side]=stats
 report['perSampleKneePoleRefinement']=pole_stats
 # A very large pole rotation is not automatically failure because 360 degrees
 # can be an equivalent phase, but report the outliers for operator inspection.
 report['polePhaseOutliers']=[{'move':m,'side':s,'maxOffset_deg':v['maxOffset_deg']}
   for m,stats in pole_stats.items() for s,v in stats.items() if v['maxOffset_deg']>120]
 # Full half-frame parity, with original FK rest meshes and actions retained.
 ok=True;checks={}
 for move,rows in samples.items():
  author.animation_data.action=edit[move];summary={s:{k:0.0 for k in LIMIT} for s in SIDES};worst=[]
  for row in rows:
   frame(row['t'])
   for side in SIDES:
    e=get_error(author,row['leg'][side],side)
    for k in LIMIT:summary[side][k]=max(summary[side][k],e[k])
    if any(e[k]>LIMIT[k] for k in LIMIT):
     ok=False
     if len(worst)<12:worst.append({'frame':row['t'],'side':side,'errors':{k:round(v,6) for k,v in e.items()}})
  checks[move]={'max':summary,'violations':worst}
 # Independent holdout: interpolated between ALL fitted sample times. This catches
 # knee flips or bad controller interpolation that a fitted-key-only test misses.
 holdout={}
 for move,rows in samples.items():
  author.animation_data.action=edit[move]
  ref.animation_data.action=source[move]
  worst={side:{k:0.0 for k in LIMIT} for side in SIDES}
  failures=[]
  for a,b in zip(rows,rows[1:]):
   t=(a['t']+b['t'])/2
   frame(t)
   for side in SIDES:
    actual_fk=snapshot(ref,side)
    e=get_error(author,actual_fk,side)
    for k in LIMIT:worst[side][k]=max(worst[side][k],e[k])
    if any(e[k]>LIMIT[k] for k in LIMIT):
     ok=False
     if len(failures)<10:failures.append({'time':t,'side':side,'errors':{k:round(v,7) for k,v in e.items()}})
  holdout[move]={'sampleCount':max(0,len(rows)-1),'max':worst,'violations':failures}
 report['holdoutParity']={'passed':all(not x['violations'] for x in holdout.values()),'actions':holdout,
                            'sampling':'INDEPENDENT_MIDPOINTS_OF_DENSE_CONTROLLER_SAMPLES'}
 report['parity']={'passed':ok,'limits':LIMIT,'actions':checks,
                   'sampling':'EXACT_SOURCE_KEYS_AND_DENSE_0.2_FRAME_SAMPLES_PLUS_INDEPENDENT_HOLDOUT'}
 author.animation_data.action=edit['Heavy1'];scene=bpy.context.scene
 scene.frame_start=int(min(times(source['Heavy1'])));scene.frame_end=int(max(times(source['Heavy1'])))
 doc=bpy.data.texts.new('READ_ME_IK_PARITY_STATUS')
 doc.write('Exact Ares-scaled FK target source, all 10 native attack Actions preserved.\n')
 doc.write('The editable IK copy has NOT been visually approved.\n')
 doc.write('FULL evaluated dense-frame parity: '+str(ok)+'; read parity.json.\n')
 doc.write('No source GLB or canonical GLB was changed.\n')
 pathlib.Path(output).parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=output,check_existing=False,compress=False)
 report['blendSha256']=hashlib.sha256(pathlib.Path(output).read_bytes()).hexdigest()
 report['status']='PARITY_PASS_UNAPPROVED_FOR_VISUAL_REVIEW' if ok else 'PARITY_FAIL_DIAGNOSTIC_ONLY'
 save();print('POSE_PARITY='+('PASS' if ok else 'FAIL'),flush=True)
except Exception as e:
 report['status']='BLOCKED_NO_AUTHORING_APPROVAL';report['error']=type(e).__name__+': '+str(e);save();traceback.print_exc();raise
