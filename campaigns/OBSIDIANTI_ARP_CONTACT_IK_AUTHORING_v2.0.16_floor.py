#!/usr/bin/env python3
"""Ground first-frame skinned FOOT SURFACE, via constant additive hip translation.
Only works on an isolated derivative of a purchased-ARP target .blend.
No IK edits, pose sculpting, toe edits, or canonical asset writes.
"""
from __future__ import annotations
import argparse,hashlib,json,math,pathlib,sys,traceback
import bpy
from mathutils import Vector

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def fail(msg):raise RuntimeError(msg)

def source_frame(action):return float(action.frame_range[0])

def apply_frame(f):
 bpy.context.scene.frame_set(math.floor(f),subframe=f-math.floor(f))
 bpy.context.view_layer.update()

def measure(arm,meshes,frame):
 apply_frame(frame);dg=bpy.context.evaluated_depsgraph_get();zs={'Left':[],'Right':[]};counts={}
 for ob in meshes:
  names={g.index:g.name.lower() for g in ob.vertex_groups}
  gids={side:{i for i,n in names.items() if 'mixamorig:' in n and ('left' if side=='Left' else 'right') in n and any(s in n for s in ('foot','toebase','toe'))} for side in zs}
  if not any(gids.values()):continue
  ev=ob.evaluated_get(dg);mesh=ev.to_mesh()
  try:
   if len(mesh.vertices)!=len(ob.data.vertices):fail('EVALUATED_VERTEX_COUNT_MISMATCH_FOR_FOOT_WEIGHT_CLASSIFICATION_'+ob.name)
   for v in ob.data.vertices:
    chosen=[side for side in zs if any(group.group in gids[side] and group.weight>=0.12 for group in v.groups)]
    if not chosen:continue
    vert=ev.matrix_world@mesh.vertices[v.index].co
    for side in chosen:zs[side].append(float(vert.z))
  finally:ev.to_mesh_clear()
 for side in zs:counts[side]=len(zs[side]);
 if min(counts.values())<8:fail('INSUFFICIENT_SKIN_WEIGHTED_FOOT_MESH_VERTICES_'+repr(counts))
 return {'leftMinZ':min(zs['Left']),'rightMinZ':min(zs['Right']),'lowestFootZ':min(min(zs['Left']),min(zs['Right'])),'vertices':counts}

def active_bag(action,slot):
 for layer in action.layers:
  for strip in layer.strips:
   try:bag=strip.channelbag(slot,ensure=False)
   except (TypeError,RuntimeError,AttributeError):bag=None
   if bag is not None:return bag
 fail('HIP_ACTION_SLOT_CHANNELBAG_MISSING')

def shift(action,slot,arm,offset):
 pelvis=arm.pose.bones.get('mixamorig:Hips')
 if pelvis is None:fail('NO_HIPS_BONE')
 # Bone location channels use local bone orientation, not necessarily Blender world Z.
 rot=(arm.matrix_world@pelvis.bone.matrix_local).to_3x3()
 displacement=rot.inverted()@Vector((0,0,offset))
 bag=active_bag(action,slot)
 fc_by_index={fc.array_index:fc for fc in bag.fcurves if fc.data_path=='pose.bones["mixamorig:Hips"].location'}
 if not fc_by_index:
  # A genuine static stance may lack hip translation FCurves. Add only this
  # requested constant height track, not an interpolation or IK correction.
  start,end=[float(x) for x in action.frame_range]
  original=pelvis.location.copy()
  for f in (start,max(start+1.0,end)):
   apply_frame(f);pelvis.location=original+displacement
   for axis in range(3):
    if not pelvis.keyframe_insert(data_path='location',index=axis,frame=f,group='Floor Anchoring'):
     fail('STATIC_HIP_KEYFRAME_INSERT_FAILED')
  bag=active_bag(action,slot)
  fc_by_index={fc.array_index:fc for fc in bag.fcurves if fc.data_path=='pose.bones["mixamorig:Hips"].location'}
  if len(fc_by_index)!=3:fail('STATIC_HIP_KEYFRAME_CHANNELS_MISSING')
  return [float(v) for v in displacement]
 if len(fc_by_index)!=3:
  fail('EXPECTED_THREE_HIP_LOCATION_FCURVES_FOR_NONDESTRUCTIVE_CONSTANT_SHIFT_'+repr(sorted(fc_by_index)))
 for axis,amount in enumerate(displacement):
  fc=fc_by_index[axis]
  for k in fc.keyframe_points:
   k.co.y+=amount;k.handle_left.y+=amount;k.handle_right.y+=amount
  fc.update()
 return [float(v) for v in displacement]

def run(args):
 report=pathlib.Path(args.receipt);report.parent.mkdir(parents=True,exist_ok=True)
 rec={'schema':'OBSIDIANTI_ARP_CONTACT_v2.0.16','clip':args.action,'stage':'BOOT','sourceBlendSHA256':args.sha,'destination':args.output,'canonicalMutated':False,'retargetExecuted':False,'ikChanged':False}
 def save():report.write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n')
 save()
 try:
  if bpy.app.version[:2]!=(5,0):fail('PINNED_BLENDER5_REQUIRED')
  if sha(args.source)!=args.sha:fail('SAVED_ARP_BLEND_SHA_CHANGED')
  bpy.ops.wm.open_mainfile(filepath=args.source,load_ui=False)
  rigs=[ob for ob in bpy.data.objects if ob.type=='ARMATURE' and ob.name.startswith('SmartRigArmature') and 'mixamorig:Hips' in ob.pose.bones]
  if len(rigs)!=1:fail('EXPECTED_ONE_TARGET_SMARTRIG_ARMATURE')
  arm=rigs[0];ad=arm.animation_data_create();act=bpy.data.actions.get(args.action)
  if act is None:fail('ACTION_MISSING_'+args.action)
  ad.action=act;ad.use_nla=False
  for tr in ad.nla_tracks:tr.mute=True
  if ad.action_slot is None and hasattr(act,'slots'):
   # This action is from the purchased ARP target, not from the multislotted source.
   for s in act.slots:
    if s.target_id_type=='OBJECT':ad.action_slot=s;break
  if ad.action_slot is None:fail('TARGET_ARP_ACTION_SLOT_MISSING')
  meshes=[m for m in bpy.data.objects if m.type=='MESH' and (m.parent==arm or any(mod.type=='ARMATURE' and mod.object==arm for mod in m.modifiers))]
  if not meshes:fail('TARGET_SKINNED_MESH_NOT_FOUND')
  frame=source_frame(act);before=measure(arm,meshes,frame)
  hips=arm.pose.bones['mixamorig:Hips'];original=list(hips.location)
  # A single offset is applied to every existing pelvis location key. Relative
  # motion and ALL non-pelvis channels remain exactly as produced by ARP.
  delta=shift(act,ad.action_slot,arm,-before['lowestFootZ'])
  after=measure(arm,meshes,frame)
  if abs(after['lowestFootZ'])>.003:
   fail('FLOOR_CONTACT_NOT_CONFIRMED_MESH_'+str(after['lowestFootZ']))
  output=pathlib.Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
  if output.exists():fail('FLOOR_BLEND_OUTPUT_COLLISION')
  bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
  if not output.is_file() or output.stat().st_size<100000:fail('FLOOR_BLEND_NOT_SAVED')
  rec.update({'stage':'SAVED','status':'FIRST_FRAME_FOOT_SURFACE_GROUNDED','firstFrame':frame,'before':before,'after':after,
   'hipLocalConstantDelta':delta,'worldUp':'BLENDER_Z','floorZ':0.0,'blendSHA256':sha(output),'blendBytes':output.stat().st_size,
   'nonHipActionChannelsModified':False,'originalHipLocation':original})
  save();print('FLOOR_CONTACT_VERIFIED='+args.action+' DELTA='+str(delta)+' FOOT_MIN_Z='+str(after['lowestFootZ']),flush=True)
 except BaseException as e:
  rec['stage']=rec.get('stage','BOOT');rec.update({'status':'BLOCKED','errorType':type(e).__name__,'error':str(e)[:700],'traceback':traceback.format_exc()[-1800:]});save();raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for field in ('source','sha','action','output','receipt'):p.add_argument('--'+field,required=True)
 run(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
