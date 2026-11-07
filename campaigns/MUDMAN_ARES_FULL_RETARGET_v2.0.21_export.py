#!/usr/bin/env python3
"""Blender 5: export already-retargeted, saved ARP action for interactive GLB review.
No ARP calls. Does not alter original scene on disk or canonical GLB.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, traceback
import bpy

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def run(a):
 output=pathlib.Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
 receipt=pathlib.Path(a.receipt);receipt.parent.mkdir(parents=True,exist_ok=True)
 rec={'status':'BOOT','action':a.action,'sourceBlendSHA256':a.sha,'exportPath':str(output),'vendorAddonImported':False,'retargetExecuted':False,'canonicalModelModified':False}
 def save():receipt.write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n')
 save()
 try:
  if bpy.app.version[:2]!=(5,0):raise RuntimeError('BLENDER5_REQUIRED_'+bpy.app.version_string)
  if sha(a.source)!=a.sha:raise RuntimeError('SAVED_BLEND_INPUT_SHA_CHANGED')
  bpy.ops.wm.open_mainfile(filepath=a.source,load_ui=False)
  targets=[ob for ob in bpy.data.objects if ob.type=='ARMATURE' and bool(ob.get('mudman_target')) and all('mixamorig:'+x in ob.pose.bones for x in ('Hips','LeftFoot','RightFoot'))]
  if len(targets)!=1:raise RuntimeError('EXACT_SMARTRIG_TARGET_NOT_UNIQUE_'+repr([o.name for o in targets]))
  arm=targets[0]
  acts=[x for x in bpy.data.actions if x.name==a.action]
  if len(acts)!=1:raise RuntimeError('SAVED_TARGET_ACTION_MISSING_'+a.action)
  action=acts[0]
  ad=arm.animation_data_create();ad.use_nla=False
  for track in ad.nla_tracks:track.mute=True
  ad.action=action
  if hasattr(ad,'action_slot') and ad.action_slot is None and hasattr(action,'slots'):
   for slot in action.slots:
    ad.action_slot=slot;break
  arm.data.pose_position='POSE'
  # Restrict export to the saved target clip in this disposable in-memory copy.
  # Original .blend on disk and its other actions are never changed.
  rec['otherActionsExcludedFromReview']=len(bpy.data.actions)-1
  for other in tuple(bpy.data.actions):
   if other!=action:bpy.data.actions.remove(other,do_unlink=True)
  meshes=[o for o in bpy.data.objects if o.type=='MESH' and (o.parent==arm or any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers))]
  if not meshes:raise RuntimeError('NO_SKINNED_TARGET_MESHES')
  rec['targetRig']=arm.name;rec['meshes']=[m.name for m in meshes];rec['actionRange']=[float(x) for x in action.frame_range];rec['stage']='EXPORT_START';save()
  if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
  bpy.ops.object.select_all(action='DESELECT')
  for ob in [arm,*meshes]:ob.hide_set(False);ob.hide_viewport=False;ob.select_set(True)
  bpy.context.view_layer.objects.active=arm
  start,end=(int(round(float(x))) for x in action.frame_range)
  if end-start<5 or end-start>1200:raise RuntimeError('ACTION_FRAME_RANGE_INVALID')
  scene=bpy.context.scene;scene.frame_start=start;scene.frame_end=end;scene.frame_set(start)
  # Read the real Blender 5 exporter API, do not assume version-specific options.
  op=bpy.ops.export_scene.gltf
  meta=op.get_rna_type().properties
  available={p.identifier:p for p in meta}
  kw={'filepath':str(output),'export_format':'GLB','use_selection':True,
      'export_animations':True,'export_force_sampling':True,'export_frame_range':True}
  kw={k:v for k,v in kw.items() if k in available}
  if 'export_selected' in available:kw['export_selected']=True
  if 'export_animation_mode' in available:
   enum={x.identifier for x in available['export_animation_mode'].enum_items}
   if 'ACTIVE_ACTIONS' in enum:kw['export_animation_mode']='ACTIVE_ACTIONS'
   elif 'ACTIONS' in enum:kw['export_animation_mode']='ACTIONS'
   elif 'SCENE' in enum:kw['export_animation_mode']='SCENE'
   else:raise RuntimeError('BLENDER_GLTF_ACTION_EXPORT_MODE_UNKNOWN_'+repr(sorted(enum)))
  elif 'export_nla_strips' in available:kw['export_nla_strips']=False
  if kw.get('export_animation_mode')=='ACTIVE_ACTIONS' and 'export_nla_strips_merged_animation_name' in available:
   kw['export_nla_strips_merged_animation_name']=a.action
  rec['exportOptions']=sorted(kw);rec['exportAnimationMode']=kw.get('export_animation_mode','legacy')
  rec['stage']='EXPORT_OPERATOR';save()
  answer=op(**kw)
  if answer!={'FINISHED'}:raise RuntimeError('GLTF_EXPORT_NOT_FINISHED_'+repr(answer))
  if not output.is_file() or output.stat().st_size<200000:raise RuntimeError('EXPORTED_GLB_MISSING_OR_TOO_SMALL')
  rec['glbSHA256']=sha(output);rec['glbBytes']=output.stat().st_size;rec['status']='BLENDER5_SAVED_ARP_ACTION_EXPORTED_GLB';rec['stage']='EXPORTED';save()
  print('SAVED_ARP_GLTF_EXPORT='+a.action+' BYTES='+str(rec['glbBytes']),flush=True)
 except BaseException as exc:
  rec['status']='BLOCKED';rec['errorType']=type(exc).__name__;rec['error']=str(exc)[:850];rec['stage']=rec.get('stage','BOOT');save()
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for key in ('source','sha','action','output','receipt'):p.add_argument('--'+key,required=True)
 run(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
