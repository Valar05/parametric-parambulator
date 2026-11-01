"""Optional true-material Blender review for the ONE canonical in-repo Repl.glb.

Run by Termux automatically when `blender` is on its PATH. This script only
writes PNG/JPEG evidence; it does not modify or export a GLB. Blender may be
on a remote cauldron rather than the phone; no pretend remote transfer occurs.
"""
import bpy
import math
from mathutils import Vector
import os,sys,json,traceback

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args)!=2:raise SystemExit('USAGE: blender -b -P blender_review.py -- CANONICAL_GLB OUTPUT_DIR')
input_path,output_dir=args
os.makedirs(output_dir,exist_ok=True)
assert input_path.endswith('/assets/repl/Repl.glb'), 'ONLY_CANONICAL_MODEL_IS_RENDERABLE'
assert os.path.isfile(input_path),'CANONICAL_MODEL_MISSING'

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=input_path)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version >= (4,2,0) else 'BLENDER_EEVEE'
scene.render.resolution_x=1152
scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.color=(.2,.2,.2)
scene.render.film_transparent=False
try:
  scene.view_settings.view_transform='AgX'
except Exception:pass

meshes=[o for o in scene.objects if o.type=='MESH']
assert meshes,'NO_ACTUAL_MESH_IMPORTED'
pts=[o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
mins=Vector([min(p[i] for p in pts) for i in range(3)])
maxs=Vector([max(p[i] for p in pts) for i in range(3)])
center=(mins+maxs)/2
span=(maxs-mins).length
span=max(span,.5)

# Pin a demonstrable slow tail motion action; no unrelated NLA is allowed to
# move hooves or body in the tail-only review.
straights=[a for a in bpy.data.actions if 'SLOW_STRAIGHTEN' in a.name]
assert straights, 'BLENDER_IMPORT_STRAIGHTEN_ACTION_NOT_FOUND'
act=straights[0]
assigned=[]
for obj in scene.objects:
  if obj.type=='ARMATURE':
    obj.animation_data_create()
    ad=obj.animation_data
    if ad:
      for track in ad.nla_tracks:track.mute=True
      try:
        ad.action=act
        if hasattr(ad,'action_slot') and len(act.slots):
          slot=next((s for s in act.slots if s.target_id_type=='OBJECT'),act.slots[0])
          ad.action_slot=slot
        assigned.append(obj.name)
      except Exception as exc:
        print('BLENDER_ACTION_ASSIGNMENT_FAILED',obj.name,str(exc))
assert assigned,'NO_ARMATURE_FOR_STRAIGHTEN_ACTION'

# Set 14-second duration in native Blender frames.
scene.render.fps=24
scene.frame_start=1
scene.frame_end=337

# Plain studio camera and lights, no material replacement or vertex dots.
camdata=bpy.data.cameras.new('Repl review orthographic')
cam=bpy.data.objects.new('Repl review camera',camdata);scene.collection.objects.link(cam)
scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=span*1.22

def place_camera(kind):
  offset={'side':Vector((1.0,.24,.03)),
          'three':Vector((1.0,.35,-.72)),
          'rear':Vector((.03,.28,-1.0))}[kind].normalized()
  cam.location=center+offset*span*2.2
  direction=center-cam.location
  cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

def light(name,loc,energy,size):
  data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
  obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
  obj.location=center+Vector(loc)*span
  obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
light('soft key',(1.5,2.1,2.0),1500,span*1.3)
light('rear rim',(-1.0,1.2,-1.6),900,span*.9)
light('side fill',(-.8,.8,.9),650,span*1.5)

frames=[1,49,97,145,193,241,289,337]
images=[]
for kind in ('side','three','rear'):
  place_camera(kind)
  for frame in frames:
    scene.frame_set(frame)
    path=os.path.join(output_dir,f'Repl_v0.5.1_{kind}_f{frame:03d}.png')
    scene.render.filepath=path
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(path)>10000, f'BLENDER_RENDER_EMPTY:{path}'
    images.append(path)
    print('REVIEW_FRAME_RENDERED',kind,frame,os.path.basename(path),flush=True)

receipt={
  'source_glb':input_path,
  'source_is_single_canonical':True,
  'blender_version':bpy.app.version_string,
  'slow_straighten_action':act.name,
  'armature_bindings':assigned,
  'frames':len(images),
  'preview_frames':frames,
  'cameras':['side','three','rear'],
  'render_resolution':[1152,768],
  'textures':'original glTF material imports',
  'no_glbs_exported':True,
  'human_acceptance':'PENDING'
}
with open(os.path.join(output_dir,'REPL_v0.5.1_blender_review_receipt.json'),'w',encoding='utf8') as f:
  json.dump(receipt,f,indent=2)
print('BLENDER_REVIEW=FULL_TEXTURED_FRAMES_GENERATED',len(images),flush=True)
