#!/usr/bin/env python3
"""Use purchased Auto-Rig Pro operators (not a custom retargeter) in Blender 4.3.
Private add-on is imported only inside owner's Termux Debian instance.
"""
from __future__ import annotations
import argparse,hashlib,importlib,json,math,pathlib,sys,traceback
import bpy
from mathutils import Vector
CORE=('Hips','Spine','Spine1','Spine2','Neck','Head','LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase')
MONITOR=('LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','LeftForeArm','RightArm','RightForeArm','Spine2')

def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def context():
 """NEVER pin active_object: ARP needs to switch source/target during retarget."""
 wins=list(bpy.context.window_manager.windows)
 if not wins:return {}
 win=wins[0];scr=win.screen
 areas=[a for a in scr.areas if a.type=='VIEW_3D']
 area=areas[0] if areas else (scr.areas[0] if len(scr.areas) else None)
 if area is None:return {'window':win}
 regs=[r for r in area.regions if r.type=='WINDOW']
 return {'window':win,'area':area,**({'region':regs[0]} if regs else {})}

def operator(op,*args,**kw):
 override=context()
 with bpy.context.temp_override(**override):return op(*args,**kw)

def prep_armature_for_vendor_registration(create=False, arm=None):
 """Establish REAL POSE context before loading purchased ARP.

 An older public ARP version imports reset_all_controllers.py, whose module
 top-level calls bpy.ops.pose.select_all. Blender background startup defaults
 to Cube/Object Mode. Merely selecting an armature is NOT enough.

 All operations here are on a disposable probe skeleton or an imported target
 copy; canonical source assets are NEVER modified.
 """
 if create:
  # Do not reset factory settings again; keep default window/VIEW_3D context.
  # The probe is read-only and has its own process, no user objects to damage.
  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete(use_global=False)
  data=bpy.data.armatures.new('ARP_HEADLESS_REGISTRATION_ONLY')
  arm=bpy.data.objects.new('ARP_HEADLESS_REGISTRATION_ONLY',data)
  bpy.context.scene.collection.objects.link(arm)
 elif arm is None:
  choices=[o for o in bpy.data.objects if o.type=='ARMATURE' and o.visible_get()]
  if not choices:choices=[o for o in bpy.data.objects if o.type=='ARMATURE']
  if not choices:raise RuntimeError('ARP_REGISTRATION_NEEDS_ACTIVE_ARMATURE_NOT_MESH')
  arm=choices[0]
 if arm is None or arm.type!='ARMATURE':
  raise RuntimeError('ARP_CONTEXT_EXACT_TARGET_IS_NOT_ARMATURE')
 # Selection changes must start in object mode, including on the imported copy.
 if bpy.context.object and bpy.context.object.mode != 'OBJECT':
  operator(bpy.ops.object.mode_set,mode='OBJECT')
 for selected in tuple(bpy.context.selected_objects):selected.select_set(False)
 arm.select_set(True)
 bpy.context.view_layer.objects.active=arm
 bpy.context.view_layer.update()
 active=bpy.context.view_layer.objects.active
 if active != arm or active.type!='ARMATURE' or not hasattr(active.data,'collections_all'):
  raise RuntimeError('ARP_REGISTRATION_ARMATURE_CONTEXT_UNAVAILABLE')
 if create:
  # Build a real pose bone. An empty Armature object alone does not prove the
  # Pose Mode operators which ARP calls at module import time are usable.
  operator(bpy.ops.object.mode_set,mode='EDIT')
  eb=arm.data.edit_bones.new('ARP_CONTEXT_TEST_BONE')
  eb.head=(0.,0.,0.);eb.tail=(0.,0.,1.)
  operator(bpy.ops.object.mode_set,mode='OBJECT')
  if len(arm.pose.bones)!=1:raise RuntimeError('ARP_CONTEXT_TEST_BONE_NOT_CREATED')
 # Crucial missing precondition in v2.0.4: switch into genuine Pose Mode.
 if not bpy.ops.object.mode_set.poll():
  raise RuntimeError('ARP_POSE_CONTEXT_MODE_SET_POLL_FALSE')
 operator(bpy.ops.object.mode_set,mode='POSE')
 if bpy.context.mode != 'POSE' or active.mode != 'POSE':
  raise RuntimeError('ARP_POSE_CONTEXT_MODE_NOT_ENTERED '+str(bpy.context.mode))
 with bpy.context.temp_override(**context()):
  if not bpy.ops.pose.select_all.poll():
   raise RuntimeError('ARP_POSE_SELECT_ALL_POLL_FALSE_BEFORE_VENDOR_IMPORT')
  # The real Blender pose operator must work before loading ARP, not just poll.
  selected=bpy.ops.pose.select_all(action='DESELECT')
  if selected != {'FINISHED'}:
   raise RuntimeError('ARP_POSE_SELECT_ALL_NOT_FINISHED '+repr(selected))
 return {'activeObjectType':active.type,'activeObjectName':active.name,
         'boneCollectionsAvailable':True,'mode':bpy.context.mode,
         'poseSelectAllPoll':True,'poseSelectAllExecuted':True,
         'poseBoneCount':len(arm.pose.bones),
         'sceneObjectCount':len(bpy.context.scene.objects),'placeholder':bool(create)}

def enable_arp(root):
 active=bpy.context.view_layer.objects.active
 if active is None or active.type!='ARMATURE' or not hasattr(active.data,'collections_all'):
  raise RuntimeError('ARP_REGISTRATION_REFUSES_NON_ARMATURE_CONTEXT')
 if bpy.context.mode!='POSE' or not bpy.ops.pose.select_all.poll():
  raise RuntimeError('ARP_REGISTER_IMPORT_REQUIRES_POSE_MODE_AND_VALID_POLL')
 folder=pathlib.Path(root)
 modules=[p for p in folder.iterdir() if p.is_dir() and (p/'__init__.py').is_file()]
 if len(modules)!=1:raise RuntimeError('PRIVATE_ARP_INSTALL_NOT_UNIQUE_OR_INVALID')
 parent=str(folder)
 if parent not in sys.path:sys.path.insert(0,parent)
 module=modules[0].name
 try:
  importlib.import_module(module)
  try:
   bpy.ops.preferences.addon_enable(module=module)
  except Exception as enable_exc:
   # A registration exception can leave some RNA classes registered. NEVER
   # call register a second time after one has actually failed. Fallback to
   # direct registration ONLY for a missing installer/module discovery error.
   import traceback as tb
   trace=tb.format_exc()
   if not any(phrase in str(enable_exc).lower() for phrase in
       ('not found', 'no module named', 'not installed', 'not discoverable')):
    raise RuntimeError('ARP_PREFERENCE_ENABLE_EXCEPTION '+type(enable_exc).__name__+' '+str(enable_exc)[:260]) from enable_exc
   vend=importlib.import_module(module)
   if not hasattr(vend,'register'):raise enable_exc
   vend.register()
 except Exception as exc:raise RuntimeError('ARP_PRIVATE_ADDON_ACTIVATION_FAILED '+type(exc).__name__+' '+str(exc)[:280]) from exc
 names=['auto_scale','build_bones_list','retarget']
 registered={n:hasattr(bpy.ops.arp,n) for n in names}
 if not all(registered.values()):raise RuntimeError('ARP_REMAP_OPERATOR_MISSING '+repr(registered))
 return {'moduleName':module,'remapOperators':registered,'blender':bpy.app.version_string}

def angle(arm,p):
 b=arm.pose.bones['mixamorig:'+p]
 local=(b.parent.matrix.inverted_safe()@b.matrix if b.parent else b.matrix)
 return local.to_quaternion().normalized()

def witnesses(arm,start,end):
 scene=bpy.context.scene;rows=[];initial=None
 for i in range(17):
  frame=start+(end-start)*i/16
  scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
  qs={p:angle(arm,p) for p in MONITOR}
  if initial is None:initial={p:q.copy() for p,q in qs.items()}
  rows.append({'frame':round(frame,4),'rotationDeltaDeg':{p:round(math.degrees(initial[p].rotation_difference(q).angle),3) for p,q in qs.items()},
   'jointWorld':{p:[round(float(v),5) for v in (arm.matrix_world@arm.pose.bones['mixamorig:'+p].matrix.translation)] for p in ('Hips','LeftFoot','RightFoot')}})
 return rows

def motion_stats(rows):
 maxima={p:max(r['rotationDeltaDeg'][p] for r in rows) for p in MONITOR}
 return {'maxRotationDegrees':maxima,'changingBonesOver5Deg':[p for p,v in maxima.items() if v>5],
   'animatedLimbGroups':{'leftLeg':max(maxima[p] for p in ('LeftUpLeg','LeftLeg'))>5,
                         'rightLeg':max(maxima[p] for p in ('RightUpLeg','RightLeg'))>5,
                         'upper':max(maxima[p] for p in ('LeftArm','LeftForeArm','RightArm','RightForeArm','Spine2'))>5},
   'sampledFrames':len(rows)}

def frame_camera(scene,arm,meshes,start,end):
 limits=[]
 for frame in (start,(start+end)*.5,end):
  scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
  dg=bpy.context.evaluated_depsgraph_get()
  for ob in meshes:
   ev=ob.evaluated_get(dg);me=ev.to_mesh()
   try:
    if len(me.vertices)==0:continue
    pts=[ev.matrix_world @ v.co for v in me.vertices]
    limits.append([min(p.y for p in pts),max(p.y for p in pts),min(p.z for p in pts),max(p.z for p in pts)])
   finally:ev.to_mesh_clear()
 if not limits:raise RuntimeError('RENDER_NO_EVALUATED_TARGET_MESH')
 ymin=min(v[0] for v in limits);ymax=max(v[1] for v in limits)
 zmin=min(-.08,min(v[2] for v in limits));zmax=max(v[3] for v in limits)
 cy=(ymin+ymax)/2;cz=(zmin+zmax)/2;span=max(.5,ymax-ymin,zmax-zmin)*1.3
 camdat=bpy.data.cameras.new('ARP Side Capture');cam=bpy.data.objects.new('ARP Side Capture',camdat)
 scene.collection.objects.link(cam);camdat.type='ORTHO';camdat.ortho_scale=span
 cam.location=(10,cy,cz);cam.rotation_euler=(Vector((0,cy,cz))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,cy,-.012));floor=bpy.context.object;floor.name='ARP_FIXED_FLOOR_REFERENCE_Z0'
 floor.dimensions=(.04,span*1.2,.024)
 return {'yExtent':[round(ymin,4),round(ymax,4)],'zExtent':[round(zmin,4),round(zmax,4)],'floor':0,'ortho':round(span,4)}

def render_frames(arm,meshes,output,start,end,clip):
 scene=bpy.context.scene
 for ob in bpy.data.objects:
  if ob.type=='MESH':ob.hide_render=ob not in meshes
 for ob in meshes:ob.hide_render=False
 for ob in bpy.data.objects:
  if ob.type=='ARMATURE':ob.hide_render=(ob!=arm)
 framing=frame_camera(scene,arm,meshes,start,end)
 scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
 scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.show_object_outline=True
 scene.display.shading.background_type='WORLD';scene.world.color=(.11,.15,.21)
 scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False
 dest=output/'frames';dest.mkdir(exist_ok=True)
 filelist=[]
 for i in range(16):
  f=start+(end-start)*i/15;scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  png=dest/('frame_%03d.png'%i);scene.render.filepath=str(png);bpy.ops.render.render(write_still=True)
  if not png.is_file() or png.stat().st_size<15000:raise RuntimeError('REAL_BLENDER_FRAME_NOT_RENDERED_'+str(i))
  filelist.append(png.name)
 return {'frames':filelist,'framing':framing,'format':'BLENDER_WORKBENCH_512_SIDE_+X', 'clip':clip}

def select_action(src,name,slot_id):
 action=bpy.data.actions.get(name)
 if action is None:raise RuntimeError('SOURCE_ACTION_MISSING_'+name)
 slots=[s for s in action.slots if s.identifier==slot_id and s.target_id_type=='OBJECT']
 if len(slots)!=1:raise RuntimeError('SOURCE_ANIMATION_SLOT_NOT_FOUND_'+name+'_'+slot_id)
 chosen=slots[0];num=0;useful=0
 for layer in action.layers:
  for strip in layer.strips:
   try:bag=strip.channelbag(chosen,ensure=False)
   except (AttributeError,RuntimeError,TypeError):bag=None
   if not bag:continue
   num+=len(bag.fcurves)
   useful+=sum(1 for fc in bag.fcurves if 'pose.bones["mixamorig:' in fc.data_path)
 if num<1 or useful<1:raise RuntimeError('SOURCE_ACTION_SLOT_HAS_NO_ARMATURE_MOTION_'+name+'_'+slot_id)
 ad=src.animation_data_create();ad.use_nla=False
 for tr in ad.nla_tracks:tr.mute=True
 ad.action=action;ad.action_slot=chosen
 if ad.action_slot!=chosen:raise RuntimeError('EXACT_ARES_ACTION_SLOT_BINDING_FAILED_'+name+'_'+slot_id)
 src['mudman_source_action']=name;src['mudman_source_slot']=slot_id
 src['mudman_source_curve_count']=num;src['mudman_source_useful_curves']=useful
 return action

def run(args):
 out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=False)
 result={'status':'BOOT','schema':'obsidianti-arp-3.79.17-blender5-v2.0.12','clip':args.clip,
         'inputSHA256':{'source':digest(args.source),'target':digest(args.target)},'vendorPrivate':True,'sourceCodePublished':False}
 def save(): (out/'TRIAL.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 save()
 try:
  if bpy.app.version[:2]!=(5,0):raise RuntimeError('BLENDER_5_0_REQUIRED_ACTUAL_'+bpy.app.version_string)
  if digest(args.target)!=args.target_sha or digest(args.source)!=args.source_sha:raise RuntimeError('PINNED_CHARACTER_SOURCE_SHA_MISMATCH')
  bpy.ops.wm.open_mainfile(filepath=args.source,load_ui=False)
  source_candidates=[o for o in bpy.data.objects if o.type=='ARMATURE' and all('mixamorig:'+p in o.pose.bones for p in MONITOR)]
  if len(source_candidates)!=1:raise RuntimeError('NATIVE_SOURCE_ARMATURE_NOT_UNIQUE '+repr([o.name for o in source_candidates]))
  src=source_candidates[0];action=select_action(src,args.action,args.slot)
  source_objects=set(bpy.data.objects)
  from importlib.util import spec_from_file_location,module_from_spec
  fbx_spec=spec_from_file_location('mudman_fbx_native',str(pathlib.Path(__file__).with_name('fbx_native.py')))
  fbx_module=module_from_spec(fbx_spec);fbx_spec.loader.exec_module(fbx_module)
  result['targetImporter']=fbx_module.import_mudman_fbx(bpy,args.target)
  # This is the native FBX skin/rig. Its Running Action is deliberately excluded;
  # only Ares's selected Action slot is the animation donor.
  arrivals=[o for o in bpy.data.objects if o not in source_objects]
  targets=[o for o in arrivals if o.type=='ARMATURE' and all('mixamorig:'+p in o.pose.bones for p in MONITOR)]
  if len(targets)!=1:raise RuntimeError('TARGET_ARMATURE_NOT_UNIQUE '+repr([o.name for o in targets]))
  tgt=targets[0];tgt['mudman_target']=True;meshes=[o for o in arrivals if o.type=='MESH' and (o.parent==tgt or any(m.type=='ARMATURE' and m.object==tgt for m in o.modifiers))]
  if not meshes:raise RuntimeError('TARGET_WEIGHTED_SKIN_MISSING')
  image_path=pathlib.Path(args.target).with_suffix('.png')
  if not image_path.is_file():raise RuntimeError('EXACT_MUDMAN_PNG_MISSING_'+str(image_path))
  image=bpy.data.images.load(str(image_path),check_existing=True)
  # A texture may be embedded by FBX or linked through material nodes; ensure
  # the owner's uploaded original is what is present in the review output.
  wired=0
  for ob in meshes:
   if not ob.data.materials:
    mat=bpy.data.materials.new(name='MUDMAN_ORIGINAL_MESHY_TEXTURE');ob.data.materials.append(mat)
   for mat in ob.data.materials:
    if mat is None:continue
    mat.use_nodes=True
    bsdf=next((node for node in mat.node_tree.nodes if node.type=='BSDF_PRINCIPLED'),None)
    if bsdf is None:continue
    tex=next((node for node in mat.node_tree.nodes if node.type=='TEX_IMAGE' and node.image==image),None)
    if tex is None:
     tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);wired+=1
  if wired<1:raise RuntimeError('MUDMAN_ORIGINAL_TEXTURE_NOT_WIRED')
  result['mudmanTexture']={'name':image.name,'materialLinks':wired,'source':image_path.name}
  tgt.data.pose_position='POSE'
  ad=tgt.animation_data_create();ad.use_nla=False;ad.action=None
  for tr in ad.nla_tracks:tr.mute=True
  src.data.pose_position='POSE'
  start,end=map(int,map(round,action.frame_range))
  if end-start>1200:raise RuntimeError('ACTION_TOO_LONG_FOR_REVIEW_'+str(end-start))
  if end-start<5:result['sourceStaticOrShort']=True;end=start+6
  scene=bpy.context.scene;scene.frame_start=start;scene.frame_end=end
  result.update({'sourceRig':src.name,'targetRig':tgt.name,'targetMeshes':[x.name for x in meshes],
                 'action':action.name,'actionRange':[start,end],'sourceBones':len(src.pose.bones),'targetBones':len(tgt.pose.bones)})
  result['sourceWitness17']=witnesses(src,start,end)
  result['sourceMotion']=motion_stats(result['sourceWitness17'])
  # The glTF importer may leave a mesh selected. Registration must have an
  # Armature as context, not a mesh whose data lacks bone collections.
  result['registrationContext']=prep_armature_for_vendor_registration(create=False,arm=tgt)
  # Prefer the exact target after source+glTF are loaded, not an arbitrary rig.
  arp=enable_arp(args.private);result['arp']=arp
  if not hasattr(scene,'source_rig') or not hasattr(scene,'target_rig'):raise RuntimeError('ARP_SCENE_RIG_PROPERTIES_NOT_REGISTERED')
  scene.source_rig=src.name;scene.target_rig=tgt.name
  # ARP Remap's auto_scale/build_bones_list poll REQUIRES source_action.
  # Set it after the source/target callbacks, which may reset action selection.
  if not hasattr(scene,'source_action'):raise RuntimeError('ARP_SOURCE_ACTION_PROPERTY_MISSING')
  scene.source_action=action.name
  if scene.source_action!=action.name:raise RuntimeError('ARP_SOURCE_ACTION_NOT_PRESERVED')
  result['arpSourceAction']=scene.source_action
  ss=next((slot for slot in action.slots if slot.identifier==args.slot),None)
  if ss is None:raise RuntimeError('SOURCE_SLOT_LOST_AFTER_ARP_SCENE_CALLBACK')
  src.animation_data.action=action;src.animation_data.action_slot=ss
  result['sourceSlot']={'identifier':ss.identifier,'sourceAction':action.name,
     'curveCount':int(src['mudman_source_curve_count']),
     'mappedCurveCount':int(src['mudman_source_useful_curves'])}
  if 'arp_retarget_bound' in tgt.keys():tgt['arp_retarget_bound']=False
  for o in bpy.context.selected_objects:o.select_set(False)
  tgt.select_set(True);bpy.context.view_layer.objects.active=tgt
  with bpy.context.temp_override(**context()):
   if not bpy.ops.arp.auto_scale.poll():raise RuntimeError('ARP_AUTO_SCALE_POLL_FALSE_WITH_COMPLETE_REMAP_CONFIGURATION')
   if not bpy.ops.arp.build_bones_list.poll():raise RuntimeError('ARP_BUILD_BONES_LIST_POLL_FALSE_WITH_COMPLETE_REMAP_CONFIGURATION')
  result['autoScaleOperator']=list(operator(bpy.ops.arp.auto_scale))
  result['buildMappingOperator']=list(operator(bpy.ops.arp.build_bones_list))
  mapping=getattr(scene,'bones_map_v2',None)
  if mapping is None:raise RuntimeError('ARP_BONES_MAP_V2_UNAVAILABLE')
  match=set(CORE)&{b.name.split(':')[-1] for b in src.pose.bones}&{b.name.split(':')[-1] for b in tgt.pose.bones}
  expected={'mixamorig:'+p for p in match}
  active=[];dropped=[]
  for i in reversed(range(len(mapping))):
   item=mapping[i];source_name=getattr(item,'source_bone','')
   if source_name not in expected:
    dropped.append(source_name);mapping.remove(i);continue
   item.name=source_name
   if item.name!=source_name:raise RuntimeError('ARP_MAPPING_TARGET_ASSIGNMENT_NOT_PRESERVED '+source_name)
   if hasattr(item,'set_as_root'):item.set_as_root=(source_name=='mixamorig:Hips')
   if hasattr(item,'location') and source_name=='mixamorig:Hips':item.location=True
   active.append({'source':source_name,'target':item.name})
  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped),
    'profile':'ARES_ALL_SLOTS_TO_MUDMAN_MIXAMO','hipsLocation':True,'hipsRoot':True}
  result['stage']='BONE_MAP_CREATED';save()
  required={'mixamorig:'+p for p in ('Hips','Spine','LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','RightArm')}
  if len(active)<18 or not required.issubset({x['source'] for x in active}):raise RuntimeError('ARP_CORE_MAPPING_INCOMPLETE')
  save()
  # Actual purchased retarget operator, no hand-coded FK/IK solve.
  result['stage']='BEFORE_RETARGET_RNA';save()
  allowed={p.identifier for p in bpy.ops.arp.retarget.get_rna_type().properties}
  retarget_options={k:v for k,v in [('frame_start',start),('frame_end',end)] if k in allowed}
  result['retargetOperatorOptions']=sorted(retarget_options)
  result['stage']='BEFORE_RETARGET_POLL';save()
  with bpy.context.temp_override(**context()):
   if not bpy.ops.arp.retarget.poll():raise RuntimeError('ARP_RETARGET_POLL_FALSE_AFTER_MAPPING')
  result['stage']='BEFORE_RETARGET_EXEC';save()
  result['retargetOperator']=list(operator(bpy.ops.arp.retarget,'EXEC_DEFAULT',**retarget_options))
  result['stage']='RETARGET_EXEC_RETURNED';save()
  targetad=tgt.animation_data
  if targetad is None or targetad.action is None:raise RuntimeError('ARP_RETARGET_RETURNED_WITHOUT_TARGET_ACTION')
  output_action=targetad.action
  output_action.name=args.clip+'_remap'
  result['targetAction']=output_action.name
  result['targetWitness17']=witnesses(tgt,start,end)
  result['targetMotion']=motion_stats(result['targetWitness17'])
  result['stage']='TARGET_MOTION_CAPTURED';save()
  result['motionGate']=(all(result['targetMotion']['animatedLimbGroups'].values()) and len(result['targetMotion']['changingBonesOver5Deg'])>=6)
  # SAVE FIRST: use a second Blender process to render without ARP registration.
  result['stage']='SAVING_RETARGETED_BLEND';save()
  bpy.ops.wm.save_as_mainfile(filepath=str(out/('ARP_'+args.clip+'_UNAPPROVED.blend')),compress=True)
  result['blendSHA256']=digest(out/('ARP_'+args.clip+'_UNAPPROVED.blend'))
  result['status']='ARP_RETARGET_SAVED_PENDING_RENDER' if result['motionGate'] else 'ARP_RETARGET_SAVED_MOTION_GATE_REJECTED'
  result['stage']='SAVED_BLEND';save()
  save();print('REAL_ARP_RETARGET='+args.clip+' STATUS='+result['status'],flush=True)
 except BaseException as exc:
  result.update({'status':'BLOCKED','errorType':type(exc).__name__,'error':str(exc)[:900],
                 'traceback':traceback.format_exc()[-3800:]})
  save();print('ARP_BLENDER_BLOCKED='+type(exc).__name__+' '+str(exc)[:900],flush=True)
  raise

if __name__=='__main__':
 ap=argparse.ArgumentParser()
 for n in ('private','source','source-sha','target','target-sha','clip','action','slot','output'):ap.add_argument('--'+n,required=True)
 run(ap.parse_args(sys.argv[sys.argv.index('--')+1:]))
