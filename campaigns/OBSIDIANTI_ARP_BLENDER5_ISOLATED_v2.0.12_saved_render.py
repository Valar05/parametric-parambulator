#!/usr/bin/env python3
"""Render only saved, unapproved ARP-baked action; never retarget or modify originals."""
from __future__ import annotations
import argparse,json,math,pathlib,sys,traceback
import bpy
from mathutils import Vector

def frame_camera(scene,meshes,start,end):
 bounds=[]
 for frame in (start,(start+end)*.5,end):
  scene.frame_set(int(frame),subframe=frame-int(frame))
  bpy.context.view_layer.update()
  dg=bpy.context.evaluated_depsgraph_get()
  for ob in meshes:
   ev=ob.evaluated_get(dg);mesh=ev.to_mesh()
   try:
    if not mesh.vertices:continue
    points=[ev.matrix_world @ v.co for v in mesh.vertices]
    bounds.append((min(p.y for p in points),max(p.y for p in points),
                   min(p.z for p in points),max(p.z for p in points)))
   finally:ev.to_mesh_clear()
 if not bounds:raise RuntimeError('NO_DEFORMED_MESH_VERTICES_TO_FRAME')
 ymin=min(x[0] for x in bounds);ymax=max(x[1] for x in bounds)
 zmin=min(-.08,min(x[2] for x in bounds));zmax=max(x[3] for x in bounds)
 cy=(ymin+ymax)*.5;cz=(zmin+zmax)*.5;span=max(.6,ymax-ymin,zmax-zmin)*1.3
 camera_data=bpy.data.cameras.new('ARP Recovery Fixed Side +X')
 camera=bpy.data.objects.new('ARP Recovery Fixed Side +X',camera_data)
 scene.collection.objects.link(camera)
 camera_data.type='ORTHO';camera_data.ortho_scale=span
 camera.location=(10,cy,cz)
 camera.rotation_euler=(Vector((0,cy,cz))-camera.location).to_track_quat('-Z','Y').to_euler()
 scene.camera=camera
 floor_data=bpy.data.meshes.new('ARP Recovery Ground Z0')
 floor=bpy.data.objects.new('ARP Recovery Ground Z0',floor_data)
 scene.collection.objects.link(floor)
 half=span*.55
 verts=[(0,-half,-.025),(0,half,-.025),(0,half,.0),(0,-half,.0)]
 floor_data.from_pydata(verts,[],[(0,1,2,3)])
 floor.location=(0,cy,0)
 return {'camera':'+X orthographic','worldYBounds':[ymin,ymax],
         'worldZBounds':[zmin,zmax],'floorWorldZ':0,'orthoScale':span}

def main(a):
 out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=False)
 result={'status':'START','blend':pathlib.Path(a.blend).name,'frames':[]}
 def save(): (out/'RENDER.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 save()
 try:
  if bpy.app.version[:2]!=(5,0):raise RuntimeError('RENDER_REQUIRES_BLENDER_5_0')
  trial=json.loads(pathlib.Path(a.input).read_text())
  if trial.get('status') not in ('ARP_RETARGET_SAVED_PENDING_RENDER','ARP_RETARGET_SAVED_MOTION_GATE_REJECTED'):
   raise RuntimeError('RENDER_SOURCE_TRIAL_NOT_COMPLETED')
  bpy.ops.wm.open_mainfile(filepath=a.blend,load_ui=False)
  target=bpy.data.objects.get(trial.get('targetRig',''))
  if target is None or target.type!='ARMATURE':raise RuntimeError('SAVED_TARGET_ARMATURE_MISSING')
  meshes=[]
  for name in trial.get('targetMeshes',[]):
   obj=bpy.data.objects.get(name)
   if obj is None or obj.type!='MESH':raise RuntimeError('SAVED_SKINNED_MESH_MISSING '+str(name))
   if not (obj.parent==target or any(m.type=='ARMATURE' and m.object==target for m in obj.modifiers)):
    raise RuntimeError('MESH_NO_LONGER_SKINNED_TO_TARGET '+name)
   meshes.append(obj)
  if not meshes:raise RuntimeError('NO_SAVED_TARGET_SKIN_MESH')
  act=bpy.data.actions.get(trial.get('targetAction',''))
  if act is None:raise RuntimeError('SAVED_ARP_TARGET_ACTION_MISSING')
  ad=target.animation_data_create()
  ad.use_nla=False
  for track in ad.nla_tracks:track.mute=True
  ad.action=act
  target.data.pose_position='POSE'
  start,end=trial['actionRange']
  start=int(start);end=int(end)
  if end<=start or end-start>180:raise RuntimeError('UNEXPECTED_BAKED_ACTION_RANGE')
  sc=bpy.context.scene
  sc.frame_start=start;sc.frame_end=end
  for obj in bpy.data.objects:
   if obj.type=='MESH':obj.hide_render=obj not in meshes
   if obj.type=='ARMATURE':obj.hide_render=obj!=target
  for obj in meshes:obj.hide_render=False
  framing=frame_camera(sc,meshes,start,end)
  if a.engine=='WORKBENCH':
   sc.render.engine='BLENDER_WORKBENCH'
  elif a.engine=='CYCLES_CPU':
   sc.render.engine='CYCLES'
   sc.cycles.device='CPU';sc.cycles.samples=8
  else:raise RuntimeError('UNKNOWN_RENDER_ENGINE')
  sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL'
  sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
  sc.display.shading.background_type='WORLD'
  if sc.world is not None:sc.world.color=(.10,.13,.19)
  sc.render.resolution_x=512;sc.render.resolution_y=512;sc.render.resolution_percentage=100
  sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
  sc.render.film_transparent=False
  frames=out/'frames';frames.mkdir()
  sample=[]
  for index in range(16):
   f=start+(end-start)*(index/15)
   sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
   img=frames/('frame_%03d.png'%index)
   sc.render.filepath=str(img)
   bpy.ops.render.render(write_still=True)
   # Blender may append format suffix even when filepath already ends in .png.
   hits=list(frames.glob('frame_%03d*'%index))
   good=[p for p in hits if p.is_file() and p.stat().st_size>15000]
   if len(good)!=1:raise RuntimeError('FRAME_RENDER_OUTPUT_NOT_UNIQUE_'+str(index)+' '+str([p.name for p in hits]))
   sample.append({'index':index,'frame':round(f,4),'file':good[0].name,
      'hips':list(target.matrix_world@target.pose.bones['mixamorig:Hips'].matrix.translation) if 'mixamorig:Hips' in target.pose.bones else None})
  result.update({'status':'RENDERED_SAVED_ARP_ACTION','engine':a.engine,'frameCount':16,'targetAction':act.name,
                 'targetArmature':target.name,'frameFiles':[x['file'] for x in sample],
                 'framing':framing,'samples':sample})
  save()
  print('SAVED_ARP_PROJECT_RENDERED_16_REAL_FRAMES=YES',flush=True)
 except Exception as ex:
  result.update({'status':'BLOCKED','errorType':type(ex).__name__,'error':str(ex)[:650],
                 'stackLocal':traceback.format_exc()[-2800:]})
  save();raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('blend','input','output','engine'):p.add_argument('--'+n,required=True)
 main(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
