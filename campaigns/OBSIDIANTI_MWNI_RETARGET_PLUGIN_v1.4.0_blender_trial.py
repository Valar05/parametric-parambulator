#!/usr/bin/env python3
"""Real Blender/Mwni integration test. Runs only inside the owner-approved Termux Blender lane.
No bespoke retargeting solver. Uses Mwni's Context/IK/drivers and its own bake operator.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,pathlib,shutil,sys,time,traceback
import bpy
from mathutils import Vector, Matrix

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def pos(o,b):return o.matrix_world @ o.pose.bones[b].matrix.translation

def rest_pos(o,b):return o.matrix_world @ o.data.bones[b].head_local

def relrot(a,b):
 # signed yaw within Blender's XY plane, preserving the source object's original Z-up transformation
 u=Vector((a.x,a.y));v=Vector((b.x,b.y))
 if u.length<1.e-6 or v.length<1.e-6:raise RuntimeError('REST_LATERAL_BASIS_DEGENERATE')
 return math.atan2(u.x*v.y-u.y*v.x, u.dot(v))

def choose_action(text,prefer_exact=True):
 available=list(bpy.data.actions)
 found=[a for a in available if a.name==text]
 if len(found)==1:return found[0]
 found=[a for a in available if text in a.name]
 if len(found)!=1:raise RuntimeError('ACTION_UNRESOLVED '+text+' '+repr([a.name for a in available]))
 return found[0]

def active(obj):
 bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode!='OBJECT' else None
 for x in bpy.context.selected_objects:x.select_set(False)
 obj.select_set(True);bpy.context.view_layer.objects.active=obj

def metadata(src,tgt,clip,setup):
 return {'clip':clip,'setup':setup,'sourceName':src.name,'targetName':tgt.name,'sourceBones':len(src.pose.bones),'targetBones':len(tgt.pose.bones),'blenderVersion':bpy.app.version_string}

def candidates_for_shoe(tgt, meshes):
 """Actual deforming mesh vertices: grouped by strong original FOOT/TOE skin weights."""
 shoes={s:[] for s in ('Left','Right')}
 for obj in meshes:
  if obj.type!='MESH':continue
  groups={i:g.name for i,g in enumerate(obj.vertex_groups)}
  for v in obj.data.vertices:
   by={s:0.0 for s in shoes}
   for group in v.groups:
    name=groups.get(group.group,'')
    for s in shoes:
     if name in ('mixamorig:'+s+'Foot','mixamorig:'+s+'ToeBase'):
      by[s]+=group.weight
   for s in shoes:
    if by[s]>.35:shoes[s].append((obj,v.index,by[s]))
 # Deterministic evenly distributed sample; never select all body vertices accidentally.
 for s,pts in shoes.items():
  if not pts:raise RuntimeError('SKINNED_WEDGE_WITNESSES_MISSING '+s)
  pts.sort(key=lambda x:(x[0].name,x[1]))
  if len(pts)>120:pts=[pts[int(i*(len(pts)-1)/119)] for i in range(120)]
  shoes[s]=pts
 return shoes

def skin_heights(shoes):
 deps=bpy.context.evaluated_depsgraph_get();out={}
 objs=set(o for s in shoes for o,_,w in shoes[s]);evalmesh={}
 try:
  for obj in objs:
   ev=obj.evaluated_get(deps);mesh=ev.to_mesh();evalmesh[obj]=(ev,mesh)
  for side in shoes:
   p=[]
   for obj,i,w in shoes[side]:
    ev,mesh=evalmesh[obj]
    if i>=len(mesh.vertices):raise RuntimeError('EVALUATED_VERTEX_INDEX_CHANGED')
    p.append((ev.matrix_world@mesh.vertices[i].co).z)
   p.sort();out[side]={'minZ':round(p[0],6),'p10Z':round(p[max(0,int(len(p)*.10)-1)],6),'sampledVertices':len(p)}
  return out
 finally:
  for ev,mesh in evalmesh.values():ev.to_mesh_clear()

def sample(src,tgt,clip,mode,frame_range,shoes):
 rows=[];start,end=frame_range
 for frame in list(range(start,end+1,2))+[start+.5,(start+end)/2,end-.5]:
  bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame))
  bpy.context.view_layer.update()
  s={x:list(pos(src,'mixamorig:'+x+'Foot')) for x in ('Left','Right')}
  t={x:list(pos(tgt,'mixamorig:'+x+'Foot')) for x in ('Left','Right')}
  z=skin_heights(shoes)
  rows.append({'frame':frame,'t_s':round((frame-start)/30,5),'sourceBoneFoot':s,'targetBoneFoot':t,'skinnedWedges':z})
 return rows

def report_metrics(rows):
 # Compare to *scaled and aligned* source foot trajectory, not absolute foot position.
 out={}
 for side in ('Left','Right'):
  first=rows[0]
  drift=[];sole=[]
  for r in rows:
   s=Vector(r['sourceBoneFoot'][side])-Vector(first['sourceBoneFoot'][side]);t=Vector(r['targetBoneFoot'][side])-Vector(first['targetBoneFoot'][side]);drift.append((t-s).length)
   sole.append(r['skinnedWedges'][side]['p10Z'])
  out[side]={'footMotionDiscrepancyRms_m':round(math.sqrt(sum(x*x for x in drift)/len(drift)),6),
             'footMotionDiscrepancyMax_m':round(max(drift),6),
             'sole10thPercentileZRange_m':round(max(sole)-min(sole),6),'soleZRange':list(map(lambda x:round(x,6),(min(sole),max(sole))))}
 return out

def main(args):
 outfile=pathlib.Path(args.out);outfile.mkdir(parents=True,exist_ok=True)
 evidence={'schema':'obsidianti-mwni-plugin-test-v1.4.0','status':'STARTING','sourceSHA256':sha(args.source),'targetSHA256':sha(args.target),
           'addonRevision':args.addon_rev,'clip':args.clip,'exceptions':[],'outputPaths':{},'candidateOnly':True}
 def save(): (outfile/'TRIAL.json').write_text(json.dumps(evidence,indent=2)+'\n')
 save()
 try:
  import addon_utils
  addons=pathlib.Path(bpy.utils.user_resource('SCRIPTS',path='addons',create=True))
  addon_dir=addons/'animation_retargeting';src_dir=pathlib.Path(args.addon)/'animation_retargeting'
  if not src_dir.is_dir():raise RuntimeError('DOWNLOADED_ADDON_DIRECTORY_MISSING')
  if addon_dir.exists():
   def digest(root):return {str(p.relative_to(root)):sha(p) for p in root.rglob('*.py')}
   if digest(addon_dir)!=digest(src_dir):raise RuntimeError('EXISTING_ADDON_INSTALL_DIFFERENT_NOT_OVERWRITING')
  else:
   tmp=addons/('.obs-mwni-v140-'+str(os.getpid()))
   if tmp.exists():raise RuntimeError('TEMP_ADDON_COLLISION')
   shutil.copytree(src_dir,tmp)
   os.rename(tmp,addon_dir)
  evidence['persistentAddonInstall']=str(addon_dir)
  bpy.utils.refresh_script_paths()
  if str(addons) not in sys.path:sys.path.insert(0,str(addons))
  enabled=addon_utils.enable('animation_retargeting',default_set=True,persistent=False)
  if enabled is None:raise RuntimeError('MWNI_ADDON_ENABLE_RETURNED_NONE')
  import animation_retargeting as addon
  if not hasattr(bpy.types.Object,'retargeting_context'):raise RuntimeError('ADDON_NOT_REGISTERED')
  evidence['addonModulePath']=str(pathlib.Path(addon.__file__).resolve())
  evidence['addonVersion']=addon.bl_info.get('version')
  # Save only the add-on's enabled state to Blender's ordinary user preferences.
  try:bpy.ops.wm.save_userpref();evidence['preferencesSaved']=True
  except Exception as ex:evidence['preferencesSaved']=False;evidence['preferencesWarning']=str(ex)
  print('MWNI_INSTALLED_ENABLED='+str(addon_dir),flush=True)
  # Reload source .blend only after activating the add-on? Blender file loading can reset handlers.
  bpy.ops.wm.open_mainfile(filepath=args.source,load_ui=False)
  # File load can reset driver namespace and addon preference; ensure registered again.
  if not hasattr(bpy.types.Object,'retargeting_context'):
   enabled=addon_utils.enable('animation_retargeting',default_set=True)
   if enabled is None:raise RuntimeError('MWNI_LOST_AFTER_LOADING_SOURCE')
  srcarms=[o for o in bpy.data.objects if o.type=='ARMATURE' and 'mixamorig:LeftFoot' in o.pose.bones and 'LeftFoot.IK' in o.pose.bones]
  if len(srcarms)!=1:raise RuntimeError('SOURCE_ARMATURE_AMBIGUOUS '+repr([o.name for o in srcarms]))
  src=srcarms[0];sourceobjs=set(bpy.data.objects)
  bpy.ops.import_scene.gltf(filepath=args.target,import_shading='NORMALS')
  newobjs=[o for o in bpy.data.objects if o not in sourceobjs]
  targets=[o for o in newobjs if o.type=='ARMATURE' and all('mixamorig:'+s+'Foot' in o.pose.bones for s in ('Left','Right'))]
  if len(targets)!=1:raise RuntimeError('TARGET_ARMATURE_AMBIGUOUS '+repr([(o.name,len(o.pose.bones)) for o in targets]))
  tgt=targets[0]
  meshes=[o for o in newobjs if o.type=='MESH' and (o.parent==tgt or any(m.type=='ARMATURE' and m.object==tgt for m in o.modifiers))]
  if not meshes:raise RuntimeError('TARGET_RIG_SKIN_MESHES_MISSING')
  if src==tgt:raise RuntimeError('SAME_SOURCE_AND_TARGET')
  action=choose_action(args.clip);source_idle=choose_action('Idle')
  target_idle=choose_action('LionheartIdle_UNREVIEWED')
  for o in (src,tgt):
   ad=o.animation_data_create();ad.use_nla=False
   for track in ad.nla_tracks:track.mute=True
  src.animation_data.action=source_idle;tgt.animation_data.action=target_idle
  bpy.context.scene.frame_set(-1)
  bpy.context.view_layer.update()
  # Match source to the target's rest-chain scale and left-right lateral direction.
  # No algorithmic retarget. This is the add-on's required scene alignment precondition.
  def chainlen(o,side):
   b=['mixamorig:'+side+s for s in ('UpLeg','Leg','Foot')]
   return (rest_pos(o,b[0])-rest_pos(o,b[1])).length+(rest_pos(o,b[1])-rest_pos(o,b[2])).length
  sl=(chainlen(src,'Left')+chainlen(src,'Right'))/2
  tl=(chainlen(tgt,'Left')+chainlen(tgt,'Right'))/2
  k=tl/sl
  if not .5<k<2.0:raise RuntimeError('LIMB_SCALE_RATIO_OUT_OF_SAFE_RANGE '+str(k))
  src.matrix_world=Matrix.Scale(k,4)@src.matrix_world
  source_lateral=rest_pos(src,'mixamorig:RightUpLeg')-rest_pos(src,'mixamorig:LeftUpLeg')
  target_lateral=rest_pos(tgt,'mixamorig:RightUpLeg')-rest_pos(tgt,'mixamorig:LeftUpLeg')
  yaw=relrot(source_lateral,target_lateral)
  src.matrix_world=Matrix.Rotation(yaw,4,'Z')@src.matrix_world
  move=pos(tgt,'mixamorig:Hips')-pos(src,'mixamorig:Hips')
  src.matrix_world=Matrix.Translation(move)@src.matrix_world
  bpy.context.view_layer.update()
  evidence['sceneAlignment']={'sourceScaleMultiplier':round(k,7),'yawRadians':round(yaw,7),'hipTranslationApplied':list(move)}
  active(tgt)
  ctx=tgt.retargeting_context
  ctx.is_importing=True
  ctx.source=src;ctx.target=tgt;ctx.selected_source=src
  common=[b.name for b in tgt.data.bones if b.name in src.data.bones and b.name.startswith('mixamorig:') and not b.name.endswith('_End')]
  if not all('mixamorig:'+side+part in common for side in ('Left','Right') for part in ('UpLeg','Leg','Foot')):
   raise RuntimeError('MAPPING_BONES_INCOMPLETE '+str(common))
  from animation_retargeting.util import matrix_to_list
  for name in common:
   m=ctx.mappings.add();m.source=name;m.target=name
   m.rest=matrix_to_list(tgt.pose.bones[name].matrix)
   m.offset=matrix_to_list(tgt.pose.bones[name].matrix_basis)
  ctx.is_importing=False
  evidence['mappedBones']=common
  if len(common)<9:raise RuntimeError('TOO_FEW_MAPPED_BONES')
  tgt.animation_data.action=None
  # Preserve target approved idle as add-on rest-alignment offset, not a replacement source animation.
  ctx.did_setup_empty_alignment=True
  src.animation_data.action=action
  scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
  start,end=map(lambda x:int(round(x)),action.frame_range)
  if start<0 or end-start>90:raise RuntimeError('UNEXPECTED_ACTION_FRAME_RANGE')
  scene.frame_start=start;scene.frame_end=end
  scene.frame_set(start)
  ctx.setting_disable_drivers=False
  ctx.update_drivers()
  source_before={s:list(pos(src,'mixamorig:'+s+'Foot')) for s in ('Left','Right')}
  wedges=candidates_for_shoe(tgt,meshes)
  noik=sample(src,tgt,args.clip,'mapped_fk',(start,end),wedges)
  evidence['noIK']={'metrics':report_metrics(noik),'samples':noik}
  # Upstream Mwni v2.1.1 uses bpy.ctx in two IK PropertyGroup update lambdas.
  # This is an isolated runtime alias, never a vendor source-code modification.
  if not hasattr(bpy,'ctx'):setattr(bpy,'ctx',bpy.context)
  ctx.setting_correct_feet=True
  for side in ('Left','Right'):
   limb=ctx.get_ik_limb_by_name(side.lower()+'-foot')
   if limb is None:raise RuntimeError('ADDON_FAILED_TO_CREATE_IK_LIMB '+side)
   limb.origin_bone='mixamorig:'+side+'UpLeg'
   limb.target_bone='mixamorig:'+side+'Foot'
  ctx.handle_ik_change();ctx.update_drivers()
  enabled={limb.name:bool(limb.enabled) for limb in ctx.ik_limbs}
  if not enabled.get('left-foot') or not enabled.get('right-foot'):
   raise RuntimeError('MWNI_BILATERAL_IK_NOT_ENABLED '+repr(enabled))
  for side in ('Left','Right'):
   cs=[c for c in tgt.pose.bones['mixamorig:'+side+'Foot'].constraints if c.type=='IK' and c.name=='Retarget IK']
   if len(cs)!=1:raise RuntimeError('MWNI_IK_CONSTRAINT_MISSING '+side)
  evidence['pluginIKEnabled']=enabled
  ikrows=sample(src,tgt,args.clip,'mwni_ik',(start,end),wedges)
  evidence['withIK']={'metrics':report_metrics(ikrows),'samples':ikrows}
  # Actual third-party baking path, not our own rotation sampling or direct fcurve patcher.
  ctx.setting_bake_step=1;ctx.setting_bake_linear=True
  active(tgt)
  bpy.ops.object.mode_set(mode='POSE')
  try:
   addon.baking.transfer_anim(ctx)
  finally:
   bpy.ops.object.mode_set(mode='OBJECT')
  baked=tgt.animation_data.action
  if baked is None:raise RuntimeError('MWNI_BAKE_NO_TARGET_ACTION')
  evidence['bakedActionName']=baked.name
  ctx.setting_disable_drivers=True;ctx.update_drivers()
  after=sample(src,tgt,args.clip,'mwni_baked',(start,end),wedges)
  evidence['baked']={'metrics':report_metrics(after),'samples':after}
  # Verify before-and-after bake pose parity, at actual deforming skinned wedges.
  diffs={}
  for side in ('Left','Right'):
   diffs[side]=max((Vector(a['targetBoneFoot'][side])-Vector(b['targetBoneFoot'][side])).length for a,b in zip(ikrows,after))
  evidence['maxBakingFootWorldDrift_m']=diffs
  if max(diffs.values())>.04:raise RuntimeError('BLAKE_BAKE_WORLD_FOOT_PARITY_FAILED '+repr(diffs))
  # Produce a human-inspectable editable review and separately exported candidate GLB.
  for o in newobjs:
   if o.type in ('MESH','ARMATURE'):o.hide_set(False)
  for o in sourceobjs:
   if o.type=='MESH':o.hide_set(True)
  for o in bpy.context.selected_objects:o.select_set(False)
  tgt.select_set(True)
  for m in meshes:m.select_set(True)
  bpy.context.view_layer.objects.active=tgt
  glb=outfile/('MWNI_'+args.clip+'_UNAPPROVED.glb')
  export_args=dict(filepath=str(glb),export_format='GLB',use_selection=True,
     export_animations=True,export_force_sampling=True,export_yup=True,export_apply=False)
  # Prefer active target action, never allow an export mode that silently replaces the user's canon.
  try:
   bpy.ops.export_scene.gltf(**export_args,export_animation_mode='ACTIVE_ACTIONS')
  except (TypeError,ValueError,RuntimeError) as exc:
   evidence['exportModeCompatibilityWarning']=str(exc)
   # Compatibility fallback for old glTF exporter. Still an unapproved review-only file.
   bpy.ops.export_scene.gltf(**export_args,export_animation_mode='ACTIONS')
  if not glb.is_file() or glb.stat().st_size<100000:raise RuntimeError('GLB_EXPORT_NOT_PRODUCED')
  evidence['outputPaths']['candidateGLB']={'path':str(glb),'sha256':sha(glb),'bytes':glb.stat().st_size}
  blend=outfile/('MWNI_'+args.clip+'_UNAPPROVED.blend')
  bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
  evidence['outputPaths']['editableBlend']={'path':str(blend),'sha256':sha(blend),'bytes':blend.stat().st_size}
  evidence['status']='PLUGIN_IK_BAKE_EXPORT_TESTED_UNAPPROVED'
  save();print('PLUGIN_REAL_TEST='+args.clip+' STATUS='+evidence['status']+' GLB_SHA256='+sha(glb),flush=True)
 except Exception as ex:
  evidence['status']='BLOCKED_'+type(ex).__name__
  evidence['exceptions'].append({'error':str(ex),'traceback':traceback.format_exc()[-6000:]})
  save();print('PLUGIN_REAL_TEST_BLOCKED='+str(ex),flush=True)
  raise

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--target',required=True);ap.add_argument('--addon',required=True);ap.add_argument('--addon-rev',required=True);ap.add_argument('--clip',required=True,choices=('Heavy1','Light2'));ap.add_argument('--out',required=True)
 main(ap.parse_args(sys.argv[sys.argv.index('--')+1:]))
