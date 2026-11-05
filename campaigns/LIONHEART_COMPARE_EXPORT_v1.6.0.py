#!/usr/bin/env python3
"""Executed inside Blender: export original evaluated Lionheart character animations."""
import bpy, sys, os, hashlib, json, traceback
from pathlib import Path
PREF='LIONHEART_SIDE_BY_SIDE_v1.6.0'
ARGS=sys.argv[sys.argv.index('--')+1:]
source,out,expected=ARGS

def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
if digest(source)!=expected:raise RuntimeError('BLEND_SOURCE_SHA_MISMATCH')
bpy.ops.wm.open_mainfile(filepath=source)
scene=bpy.context.scene
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
if len(arms)!=1:raise RuntimeError('SOURCE_ARMATURE_CARDINALITY '+str(len(arms)))
arm=arms[0]
if arm.animation_data is None:arm.animation_data_create()
# Preserve the file on disk: all actions/export selection are in-memory only.
actions={a.name:a for a in bpy.data.actions}
selection=[]
for o in bpy.data.objects:
 if o.type=='ARMATURE' and o is arm:selection.append(o)
 elif o.type=='MESH':
  belongs=o.parent==arm or any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers)
  if belongs:selection.append(o)
if not any(o.type=='MESH' for o in selection):raise RuntimeError('NO_SOURCE_SKIN_MESH')
for o in bpy.context.selected_objects:o.select_set(False)
for o in selection:
 if o.hide_get():o.hide_set(False)
 o.select_set(True)
bpy.context.view_layer.objects.active=arm
out=Path(out);out.mkdir(parents=True,exist_ok=True)
records={}
for action_name in ('Heavy1','Heavy3'):
 choices=[a for a in bpy.data.actions if a.name==action_name or a.name.split('.')[0]==action_name]
 if len(choices)!=1:raise RuntimeError('SOURCE_ACTION_NOT_UNIQUE '+action_name+' '+repr([a.name for a in choices]))
 act=choices[0]
 if arm.animation_data.nla_tracks:
  for track in arm.animation_data.nla_tracks:track.mute=True
 arm.animation_data.action=act
 start,end=act.frame_range
 scene.render.fps=30
 scene.frame_start=int(round(start));scene.frame_end=int(round(end))
 scene.frame_set(scene.frame_start)
 path=out/('Lionheart_'+action_name+'_SOURCE.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
   export_animations=True,export_animation_mode='ACTIVE_ACTIONS',
   export_force_sampling=True,export_frame_range=True,export_frame_step=1,
   export_yup=True,export_apply=False,export_current_frame=False,
   export_reset_pose_bones=False)
 if not path.exists() or path.stat().st_size<10000:raise RuntimeError('NO_EXPORTED_GLB '+action_name)
 records[action_name]={'file':path.name,'sha256':digest(path),'bytes':path.stat().st_size,
   'frames':[float(start),float(end)],'fps':scene.render.fps,'duration':(float(end)-float(start))/scene.render.fps,
   'sourceAction':act.name,'meshCount':sum(o.type=='MESH' for o in selection)}
 print('SOURCE_GLTF_EXPORTED='+action_name+' SHA256='+records[action_name]['sha256'],flush=True)
(out/'source_exports.json').write_text(json.dumps({'campaign':PREF,'sourceBlendSHA256':expected,'blender':bpy.app.version_string,'actions':records},indent=2))
