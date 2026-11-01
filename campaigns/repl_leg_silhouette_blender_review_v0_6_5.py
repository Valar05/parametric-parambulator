#!/usr/bin/env python3
"""Optional additional Blender review of the ACTUAL single canonical Repl GLB.

Runs only if `blender` is available in the Termux execution environment.
It does not alter, re-export or commit GLB. Does not claim that a screenshot
passes equine-animation acceptance. Three action stages, three times each.
"""
import os
import sys
from pathlib import Path

try:
 import bpy
 from mathutils import Vector
except ImportError:
 print('BLENDER_REVIEW=NOT_IN_BLENDER_RUNTIME')
 raise SystemExit(2)

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def get(flag):
 if flag not in args:raise RuntimeError('Missing Blender argument: '+flag)
 return args[args.index(flag)+1]
source=Path(get('--glb'))
outdir=Path(get('--output'))
if not source.is_file():raise RuntimeError('CANONICAL_GLB_NOT_FOUND')
outdir.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.app.build_options.__dir__() else 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1280
scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.render.image_settings.file_format='PNG'
scene.render.fps=25
scene.render.fps_base=1.0
# A glTF import may distribute each action into several NLA tracks. Choose the
# exact existing walk clip by NLA track name; don't synthesize fake animation.
actions=[
 'REPL_WALK_01_FORWARD_FOUR_BEAT_IK',
 'REPL_WALK_02_FORWARD_BODY_WEIGHT_TRANSFER',
 'REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED'
]
def select_clip(wanted):
 hits=0
 for obj in bpy.data.objects:
  ad=obj.animation_data
  if ad is None:continue
  for track in ad.nla_tracks:
   name=track.name+' '+ ' '.join(s.action.name for s in track.strips if s.action)
   match=wanted in name
   track.mute=not match
   if match:hits+=1
 return hits
meshes=[o for o in bpy.data.objects if o.type=='MESH']
if not meshes:raise RuntimeError('NO_MESH_IMPORTED_FROM_CANONICAL_GLB')
# Place an illuminated camera at a proper side view, framing the real mesh.
frame=scene.frame_current
mins=Vector((1e6,1e6,1e6));maxs=Vector((-1e6,-1e6,-1e6))
for obj in meshes:
 for corner in obj.bound_box:
  p=obj.matrix_world@Vector(corner)
  for axis in range(3):
   mins[axis]=min(mins[axis],p[axis]);maxs[axis]=max(maxs[axis],p[axis])
center=(mins+maxs)*.5
size=max(maxs-mins)
camdata=bpy.data.cameras.new('Repl Side Review Camera')
camera=bpy.data.objects.new('Repl Side Review Camera',camdata)
scene.collection.objects.link(camera)
scene.camera=camera
camdata.type='ORTHO';camdata.ortho_scale=size*1.65
lightdata=bpy.data.lights.new('Repl Review Soft Key','AREA')
lightdata.energy=1500;lightdata.shape='DISK';lightdata.size=6
light=bpy.data.objects.new('Repl Review Soft Key',lightdata)
scene.collection.objects.link(light)
light.location=center+Vector((2,-3,5))
light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.6,.6,.6)
base_cam=center+Vector((size*1.75,-size*.03,size*.10))
for idx,action in enumerate(actions):
 matched=select_clip(action)
 if not matched:
  print(f'SKIPPED_BLENDER_CLIP_{idx+1}=NO_MATCHED_NLA_TRACK')
  continue
 for k,seconds in enumerate((.32,.80,1.54)):
  scene.frame_set(round(seconds*25)+1)
  # Travel approximately +Z glTF, mapped to Blender -Y by importer.
  # Camera follows scene bounds to avoid assuming a static centered horse.
  d=bpy.context.evaluated_depsgraph_get();bb=[]
  for obj in meshes:
   evaluated=obj.evaluated_get(d)
   for corner in evaluated.bound_box:
    bb.append(evaluated.matrix_world@Vector(corner))
  target=sum(bb,Vector())/len(bb) if bb else center
  camera.location=base_cam+(target-center)
  camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
  scene.render.filepath=str(outdir/f'Repl_WALK_stage{idx+1}_frame{k+1}.png')
  bpy.ops.render.render(write_still=True)
  print('BLENDER_FRAME='+scene.render.filepath,flush=True)
print('BLENDER_RENDER_COMPLETE=OPTIONAL_VISUAL_EVIDENCE_NOT_HUMAN_ACCEPTANCE',flush=True)
