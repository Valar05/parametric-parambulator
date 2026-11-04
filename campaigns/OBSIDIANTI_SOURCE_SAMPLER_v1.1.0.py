#!/usr/bin/env python3
"""BLENDER BACKGROUND ONLY. Sample actual evaluated armature constraints and IK of source actions.

Runs on Android under an existing Debian/proot Blender. Never exports an alternate GLB,
changes source meshes, saves source .blend, or edits the published target.
"""
from __future__ import annotations
import json, math, os, re, sys
import bpy
from mathutils import Matrix, Vector

LIONHEART=('Idle','Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
ARES=('Idle-Cross','StepForward','StepBack','StepLeft','StepRight','StepForwardLeft','StepForwardRight','StepBackLeft','StepBackRight','AxeKick')
AXIS=Matrix.Rotation(math.radians(-90),4,'X')  # Blender Z-up -> glTF Y-up

def args():
 import argparse
 arg=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--kind',choices=('lionheart','ares'),required=True);return p.parse_args(arg)

def make_action_map(objects,exact_names):
 actions=list(bpy.data.actions)
 found={}
 for name in exact_names:
  exact=[x for x in actions if x.name==name]
  if len(exact)==1:found[name]=exact[0];continue
  normalized=[x for x in actions if re.sub(r'(?:_(?:Armature|rig))?(?:\.\d+)?$','',x.name,flags=re.I)==name]
  if len(normalized)!=1:
   raise RuntimeError('SOURCE_ACTION_MISSING_OR_AMBIGUOUS '+name+' candidates='+','.join(x.name for x in actions))
  found[name]=normalized[0]
 return found

def sample_armature(obj,action,frame):
 # Armature-space rest basis and evaluated pose after existing native Blender IK/constraints.
 scene=bpy.context.scene;scene.frame_set(math.floor(frame),subframe=float(frame-math.floor(frame)))
 bpy.context.view_layer.update()
 result={}
 basis=(AXIS @ obj.matrix_world).to_3x3()
 scale=(obj.matrix_world.to_scale().x+obj.matrix_world.to_scale().y+obj.matrix_world.to_scale().z)/3
 for pb in obj.pose.bones:
  rest=pb.bone.matrix_local.copy()
  posed=pb.matrix.copy()  # EVALUATED after active constraints, unlike raw F-curves
  parent=pb.parent
  restL=parent.bone.matrix_local.inverted_safe() @ rest if parent else rest
  poseL=parent.matrix.inverted_safe() @ posed if parent else posed
  delta=restL.inverted_safe() @ poseL
  q=delta.to_quaternion().normalized()
  restW=(basis @ rest.to_3x3()).to_quaternion().normalized()
  pos=AXIS @ (obj.matrix_world @ posed.translation)
  localvec=poseL.translation-restL.translation
  # Source bone-local translational offsets must include source object scale.
  localvec*=scale
  result[pb.name]={
   'localDeltaQuat':[q.x,q.y,q.z,q.w],
   'restWorldQuat':[restW.x,restW.y,restW.z,restW.w],
   'worldPosition':[pos.x,pos.y,pos.z],
   'localDeltaPosition':[localvec.x,localvec.y,localvec.z],
  }
 return result

def main():
 a=args();src=os.path.abspath(a.source);out=os.path.abspath(a.out)
 if not os.path.isfile(src):raise RuntimeError('SOURCE_ASSET_MISSING '+src)
 if a.kind=='lionheart':
  bpy.ops.wm.open_mainfile(filepath=src)
 else:
  bpy.ops.wm.read_factory_settings(use_empty=True)
  bpy.ops.import_scene.gltf(filepath=src,import_shading='NORMALS')
 arms=[ob for ob in bpy.data.objects if ob.type=='ARMATURE' and len(ob.pose.bones)>=26]
 if len(arms)!=1:raise RuntimeError('EXPECTED_SINGLE_RIG_SOURCE actual='+repr([(x.name,len(x.pose.bones)) for x in arms]))
 arm=arms[0]
 names=LIONHEART if a.kind=='lionheart' else ARES
 mapping=make_action_map(arms,names)
 ad=arm.animation_data_create()
 for strip in ad.nla_tracks:strip.mute=True
 ad.use_nla=False
 originalAction=ad.action
 scene=bpy.context.scene
 fps=float(scene.render.fps)/float(scene.render.fps_base)
 if fps<10 or fps>120:raise RuntimeError('SOURCE_FPS_UNREASONABLE '+repr(fps))
 results={}
 for name in names:
  action=mapping[name]
  ad.action=action
  start,end=action.frame_range
  if a.kind=='lionheart' and name=='Idle':start=end=-1
  if end-start>400:raise RuntimeError('SOURCE_ACTION_TOO_LONG '+name)
  seq=[]
  # Preserve authored timing in real source seconds; include last partial frame.
  current=start
  while current<=end+0.00001:
   seq.append(round(float(current),6));current+=1
  if not seq or seq[-1]<end-.00001:seq.append(float(end))
  if len(seq)<2 and name!='Idle':raise RuntimeError('SOURCE_MOTION_SINGLE_FRAME '+name)
  frames=[]
  for f in seq:
   frame={'time':round(float((f-start)/fps),7),'sourceFrame':f,'bones':sample_armature(arm,action,f)}
   frames.append(frame)
  results[name]={'frames':frames,'sourceAction':action.name,'sourceFrameRange':[float(start),float(end)],'sourceFPS':fps}
  print('SOURCE_CLIP',name,'FRAMES',len(frames),'DURATION_SEC',frames[-1]['time'],flush=True)
 ad.action=originalAction
 result={'schema':'obsidianti-evaluated-source-motion-v1','sourceKind':a.kind,'source':src,'blenderVersion':bpy.app.version_string,'fps':fps,'actionCount':len(results),'actions':results}
 os.makedirs(os.path.dirname(out),exist_ok=True)
 with open(out,'w') as fp:json.dump(result,fp,separators=(',',':'))
 print('SAMPLES_WRITTEN='+out,flush=True)
if __name__=='__main__':main()
