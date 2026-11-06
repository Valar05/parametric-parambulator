#!/usr/bin/env python3
"""Re-export one *already* Mwni-baked action from the exact v1.4.7 editable Blender snapshot.
Each variant uses a fresh Blender process, never mutates donor/canon/native snapshot.
"""
from __future__ import annotations
import bpy, argparse,hashlib,json,math,os,pathlib,sys,traceback
from mathutils import Quaternion
PARTS=('LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','LeftForeArm','RightArm','RightForeArm','Spine2')
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def local_rotation(arm,p):
 b=arm.pose.bones['mixamorig:'+p];m=b.parent.matrix.inverted_safe()@b.matrix if b.parent else b.matrix
 return m.to_quaternion().normalized()
def main(a):
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 rec={'schema':'obsidianti-mwni-export-variant-v1.4.8','clip':a.clip,'mode':a.mode,'sourceBlendSHA256':digest(a.blend),'status':'START'}
 def save():out.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n')
 save()
 try:
  if rec['sourceBlendSHA256']!=a.expected:raise RuntimeError('BLEND_SHA_NOT_EXACT')
  bpy.ops.wm.open_mainfile(filepath=a.blend,load_ui=False)
  if 'Blender 4.3' not in bpy.app.version_string:raise RuntimeError('WRONG_BLENDER_RUNTIME_'+bpy.app.version_string)
  want='SmartRigArmature|'+a.clip
  acts=[x for x in bpy.data.actions if x.name==want]
  if len(acts)!=1:raise RuntimeError('BAKED_ACTION_NOT_EXACT '+want)
  action=acts[0]
  rig=[o for o in bpy.data.objects if o.type=='ARMATURE' and o.animation_data is not None
       and all('mixamorig:'+p in o.pose.bones for p in PARTS)
       and o.name in ('SmartRigArmature', 'SmartRigArmature.001')]
  if len(rig)!=1:raise RuntimeError('TARGET_RIG_NOT_UNIQUE '+repr([o.name for o in rig]))
  arm=rig[0];ad=arm.animation_data
  if not any('pose.bones[' in f.data_path for f in action.fcurves):raise RuntimeError('BAKED_ACTION_MISSING_POSE_CHANNELS')
  if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
  for o in bpy.context.selected_objects:o.select_set(False)
  arm.select_set(True);bpy.context.view_layer.objects.active=arm
  ad.use_nla=False
  for tr in ad.nla_tracks:tr.mute=True
  ad.action=action
  arm.data.pose_position='POSE'
  if hasattr(arm,'retargeting_context'):
   ctx=arm.retargeting_context
   if not ctx.setting_disable_drivers:
    ctx.setting_disable_drivers=True;ctx.update_drivers()
  start=int(round(action.frame_range[0]));end=int(round(action.frame_range[1]))
  if not (4<=end-start<=140):raise RuntimeError('BAKED_ACTION_FRAME_RANGE_INVALID '+str((start,end)))
  bpy.context.scene.frame_start=start;bpy.context.scene.frame_end=end
  frames=[start,start+(end-start)*.2,start+(end-start)*.5,start+(end-start)*.8,end]
  q={p:[] for p in PARTS}
  for f in frames:
   bpy.context.scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
   for p in PARTS:q[p].append(local_rotation(arm,p))
  motion={p:round(max(math.degrees(x.rotation_difference(q[p][0]).angle) for x in q[p]),4) for p in PARTS}
  rec['preExportJointExcursionsDegrees']=motion
  if sum(v>5 for v in motion.values())<6:raise RuntimeError('BAKED_ACTION_STATIC_BEFORE_EXPORT '+str(motion))
  # Selection includes the full actual skinned character, not the source armature.
  meshes=[o for o in bpy.data.objects if o.type=='MESH' and
          (o.parent==arm or any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers))]
  if len(meshes)<1:raise RuntimeError('NO_TARGET_SKINNED_MESHES')
  for o in meshes:o.select_set(True);o.hide_set(False)
  bpy.context.view_layer.objects.active=arm
  bpy.context.scene.frame_set(start)
  mode=a.mode
  if mode=='NLA_TRACKS':
   ad.action=None
   for tr in ad.nla_tracks:tr.mute=True
   track=ad.nla_tracks.new();track.name='Mwni148_'+a.clip
   track.strips.new(a.clip,start,action)
   ad.use_nla=True
  elif mode in ('ACTIONS','ACTIVE_ACTIONS','SCENE'):
   ad.action=action;ad.use_nla=False
  else:raise RuntimeError('INVALID_EXPORT_MODE')
  opts=dict(filepath=str(out),export_format='GLB',use_selection=True,export_animations=True,
    export_animation_mode=mode,export_force_sampling=True,export_yup=True,
    export_apply=False,export_frame_range=True)
  if mode=='ACTIONS':opts.update(export_anim_single_armature=False)
  if mode=='SCENE':opts.update(export_anim_scene_split_object=False)
  bpy.ops.export_scene.gltf(**opts)
  if not out.is_file() or out.stat().st_size<1000000:raise RuntimeError('EXPORT_NOT_PRODUCED')
  rec.update({'status':'EXPORTED_VARIANT_UNREVIEWED','outputSHA256':digest(out),'outputBytes':out.stat().st_size,
              'poseAction':action.name,'armature':arm.name,'sourceMeshNames':[o.name for o in meshes],
              'bakedFcurves':len(action.fcurves),'frameRange':[start,end]})
  save();print('EXPORT_VARIANT='+a.clip+' MODE='+mode+' SHA='+rec['outputSHA256'],flush=True)
 except Exception as exc:
  rec.update({'status':'BLOCKED','error':str(exc),'traceback':traceback.format_exc()[-2500:]});save();raise
if __name__=='__main__':
 ap=argparse.ArgumentParser()
 for name in ('blend','expected','clip','mode','out'):ap.add_argument('--'+name,required=True)
 args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);main(args)
