#!/usr/bin/env python3
"""Fresh Blender-process reimport of exported GLB; fail if clips only move hips."""
from __future__ import annotations
import bpy, argparse, hashlib, json, math, pathlib, struct, sys, traceback
from mathutils import Quaternion
J=('LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','LeftForeArm','RightArm','RightForeArm','Spine2')
def Q(o,p):
 b=o.pose.bones['mixamorig:'+p];m=b.parent.matrix.inverted_safe()@b.matrix if b.parent else b.matrix
 return m.to_quaternion().normalized()
def maxangles(arm,frames):
 result={p:[] for p in J}
 for frame in frames:
  bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
  for p in J:result[p].append(Q(arm,p))
 return {p:round(max(math.degrees(q.rotation_difference(result[p][0]).angle) for q in result[p]),4) for p in J}
def parse(path):
 buf=pathlib.Path(path).read_bytes()
 if buf[:4]!=b'glTF' or struct.unpack_from('<I',buf,4)[0]!=2 or struct.unpack_from('<I',buf,8)[0]!=len(buf):raise RuntimeError('BAD_GLTF_V2_HEADER')
 size,tag=struct.unpack_from('<I4s',buf,12)
 if tag!=b'JSON':raise RuntimeError('BAD_GLTF_JSON')
 data=json.loads(buf[20:20+size]);nodes=data['nodes'];animations=data.get('animations',[])
 if not animations:raise RuntimeError('EXPORTED_GLB_NO_ANIMATIONS')
 channels=[]
 for anim in animations:
  for ch in anim['channels']:
   target=ch['target'];node=nodes[target['node']]
   channels.append((node.get('name',''),target['path']))
 live=[n for n,path in channels if path=='rotation' and any(n.endswith('mixamorig:'+p) or n=='mixamorig:'+p for p in J)]
 if len(set(live))<7:raise RuntimeError('EXPORTED_GLB_ONLY_HIP_CHANNELS_'+repr(live))
 return {'animationNames':[x.get('name') for x in animations],'channels':len(channels),'rotationJoints':sorted(set(live)),
         'meshes':len(data.get('meshes',[])),'skins':len(data.get('skins',[]))}
def run(args):
 result={'clip':args.clip,'status':'PREFLIGHT','glbSHA256':hashlib.sha256(pathlib.Path(args.glb).read_bytes()).hexdigest()}
 out=pathlib.Path(args.out)
 try:
  result['glTFStructure']=parse(args.glb)
  bpy.ops.wm.read_factory_settings(use_empty=True)
  bpy.ops.import_scene.gltf(filepath=args.glb,import_shading='NORMALS')
  arms=[o for o in bpy.data.objects if o.type=='ARMATURE' and all('mixamorig:'+p in o.pose.bones for p in J)]
  if len(arms)!=1:raise RuntimeError('REIMPORTED_RIG_NOT_UNIQUE')
  arm=arms[0];ad=arm.animation_data
  if ad is None:raise RuntimeError('REIMPORTED_GLB_NO_ANIMATION_DATA')
  actions=[a for a in bpy.data.actions if a.frame_range[1]-a.frame_range[0]>3]
  if not actions:raise RuntimeError('REIMPORTED_GLB_NO_FRAME_RANGE')
  duration=max(a.frame_range[1] for a in actions)-min(a.frame_range[0] for a in actions)
  start=int(round(min(a.frame_range[0] for a in actions)))
  end=int(round(max(a.frame_range[1] for a in actions)))
  if end-start>500 or end-start<4:raise RuntimeError('GLB_DURATION_INVALID')
  if ad.action is None and not len(ad.nla_tracks):
   raise RuntimeError('NO_ARMATURE_ANIMATION_ACTION_OR_NLA')
  frames=sorted(set([float(start),float(end)]+[float(start+i*(end-start)/18) for i in range(19)]))
  result['reimportExcursionsDegrees']=maxangles(arm,frames)
  prior=json.loads(pathlib.Path(args.prior).read_text())
  want=prior['targetExcursionDegrees'];has=result['reimportExcursionsDegrees'];fail=[]
  for p in J:
   if want.get(p,0)>9 and has[p]<max(3, .55*want[p]):fail.append(p+' prior='+str(want[p])+' reimport='+str(has[p]))
  if args.clip=='Kick' and not any(has[p]>=8 for p in ('LeftUpLeg','LeftLeg','RightUpLeg','RightLeg')):fail.append('REIMPORT_HIP_ONLY_KICK')
  if args.clip=='Light1' and not any(has[p]>=7 for p in ('LeftArm','LeftForeArm','RightArm','RightForeArm')):fail.append('REIMPORT_HIP_ONLY_LIGHT1')
  result['failures']=fail
  if fail:raise RuntimeError('REIMPORT_LOST_ANIMATION_'+repr(fail))
  result['status']='FRESH_BLENDER_GLTF_REIMPORT_ARTICULATION_PASSED_OWNER_REVIEW_PENDING'
 except Exception as exc:
  result['status']='BLOCKED';result['error']=str(exc);result['traceback']=traceback.format_exc()[-2800:]
 out.write_text(json.dumps(result,indent=2)+'\n')
 print('GLB_REIMPORT_STATUS='+result['status']+' '+args.clip,flush=True)
 if result['status']=='BLOCKED':raise RuntimeError(result['error'])
if __name__=='__main__':
 ap=argparse.ArgumentParser()
 for n in ('glb','clip','prior','out'):ap.add_argument('--'+n,required=True)
 run(ap.parse_args(sys.argv[sys.argv.index('--')+1:]))
