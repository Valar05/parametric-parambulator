#!/usr/bin/env python3
"""Fresh Blender-process reimport of exported GLB; fail if clips only move hips."""
from __future__ import annotations
import bpy, argparse, hashlib, json, math, pathlib, struct, sys, traceback
from mathutils import Vector
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
def skinned_shoe_sites(arm):
 meshes=[o for o in bpy.data.objects if o.type=='MESH' and
    (o.parent==arm or any(mod.type=='ARMATURE' and mod.object==arm for mod in o.modifiers))]
 if not meshes:raise RuntimeError('REIMPORTED_GLB_HAS_NO_TARGET_SKIN')
 sites={side:[] for side in ('Left','Right')}
 for obj in meshes:
  groups={g.index:g.name for g in obj.vertex_groups}
  for vert in obj.data.vertices:
   for side in sites:
    w=sum(g.weight for g in vert.groups if groups.get(g.group) in
      ('mixamorig:'+side+'Foot','mixamorig:'+side+'ToeBase'))
    if w>=.4:sites[side].append((obj,vert.index))
 for side,points in sites.items():
  if len(points)<8:raise RuntimeError('REIMPORT_NO_REAL_WEIGHTED_SHOE_SAMPLES_'+side)
  points.sort(key=lambda it:(it[0].name,it[1]))
  if len(points)>120:sites[side]=[points[int(i*(len(points)-1)/119)] for i in range(120)]
 return sites

def real_shoe_frame(sites):
 deps=bpy.context.evaluated_depsgraph_get();cache={};out={}
 try:
  for obj in {o for p in sites.values() for o,i in p}:
   ev=obj.evaluated_get(deps);cache[obj]=(ev,ev.to_mesh())
  for side,points in sites.items():
   z=[]
   for obj,i in points:
    ev,mesh=cache[obj]
    if i>=len(mesh.vertices):raise RuntimeError('REIMPORT_SKIN_TOPOLOGY_INVALID')
    z.append((ev.matrix_world@mesh.vertices[i].co).z)
   z.sort();out[side]={'minZ':z[0],'p10Z':z[max(0,int(len(z)*.1)-1)]}
  return out
 finally:
  for ev,mesh in cache.values():ev.to_mesh_clear()

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
  # Fresh process must independently confirm the OUTPUT'S actual weighted
  # shoe positions, not merely inspect bone rotation channels.
  sites=skinned_shoe_sites(arm)
  shoes=[]
  for frame in frames:
   bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
   shoes.append(real_shoe_frame(sites))
  result['reimportShoeWitnesses']=shoes
  result['reimportExcursionsDegrees']=maxangles(arm,frames)
  prior=json.loads(pathlib.Path(args.prior).read_text())
  want=prior['targetExcursionDegrees'];has=result['reimportExcursionsDegrees'];fail=[]
  floor=float(prior['referenceSoleFloorZ'])
  result['restSoleFloorZ']=floor
  result['reimportContact']={}
  for side in ('Left','Right'):
   ps=[x[side]['p10Z'] for x in shoes]
   mins=[x[side]['minZ'] for x in shoes]
   witness={'minSoleZ':round(min(mins),5),'minP10DistanceToOriginalRestFloor_m':round(min(abs(x-floor) for x in ps),5),
            'contactFramesWithin8cm':sum(abs(x-floor)<=.08 for x in ps),
            'animatedSoleRange_m':round(max(ps)-min(ps),5),
            'priorBakedSoleRange_m':prior['foot'][side]['soleRange_m']}
   result['reimportContact'][side]=witness
   if witness['minSoleZ']<floor-.055:fail.append('GLB_REIMPORT_SHOE_PENETRATION_'+side)
   if witness['minP10DistanceToOriginalRestFloor_m']>.15:fail.append('GLB_REIMPORT_FLOATING_SHOE_'+side)
   if abs(witness['animatedSoleRange_m']-witness['priorBakedSoleRange_m'])>.13:
    fail.append('GLB_EXPORT_SKIN_SOLE_MOTION_DIFFERENT_'+side)
  if args.clip=='Light1' and any(result['reimportContact'][side]['contactFramesWithin8cm']<2 for side in ('Left','Right')):
   fail.append('GLB_REIMPORT_STANDING_FEET_NOT_GROUNDED')
  if args.clip=='Kick' and sum(x['contactFramesWithin8cm'] for x in result['reimportContact'].values())<2:
   fail.append('GLB_REIMPORT_SUPPORT_FOOT_MISSING')
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
