#!/usr/bin/env python3
"""Non-runtime Blender authoring rig with ALWAYS-ON editable foot IK, no IK/FK toggle.
Accepts the completed review-library GLB. Never retargets, exports or changes AxeKick.
The accepted AxeKick stays in the runtime GLB, not in this IK editing document.
"""
from __future__ import annotations
import argparse,hashlib,json,math,pathlib,sys,traceback
import bpy
from mathutils import Vector

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def fail(s):raise RuntimeError(s)

def frame_set(f):
 i=math.floor(float(f));bpy.context.scene.frame_set(i,subframe=float(f)-i);bpy.context.view_layer.update()

def action_slot(act):
 # Blender 5 layered actions: select the non-empty channel bag, never first slot blindly.
 score=[]
 for slot in getattr(act,'slots',[]):
  cnt=0
  for layer in act.layers:
   for strip in layer.strips:
    try:bag=strip.channelbag(slot,ensure=False)
    except (RuntimeError,TypeError,AttributeError):bag=None
    if bag:cnt+=len(bag.fcurves)
  score.append((cnt,slot))
 good=[x for x in score if x[0]>10]
 if not good:fail('NO_POPULATED_TARGET_ACTION_SLOT_'+act.name)
 return max(good,key=lambda x:x[0])[1]

def set_action(arm,act,slot):
 ad=arm.animation_data_create();ad.use_nla=False
 for tr in ad.nla_tracks:tr.mute=True
 ad.action=act;ad.action_slot=slot
 if ad.action!=act or ad.action_slot!=slot:fail('ACTION_OR_SLOT_ASSIGNMENT_FAILED_'+act.name)

def joint_position(arm,side,name):return arm.pose.bones['mixamorig:'+side+name].matrix.translation.copy()

def samples(arm,act,slot):
 set_action(arm,act,slot)
 start,end=[int(round(v)) for v in act.frame_range]
 if end-start<1 or end-start>400:fail('AUTHORING_ACTION_LENGTH_INVALID_'+act.name+'_'+str((start,end)))
 results=[]
 for f in range(start,end+1):
  frame_set(f)
  results.append({'frame':f,'LeftFoot':joint_position(arm,'Left','Foot'),
   'RightFoot':joint_position(arm,'Right','Foot'),
   'LeftKnee':joint_position(arm,'Left','Leg'),
   'RightKnee':joint_position(arm,'Right','Leg')})
 return results

def build_foot_controls(arm):
 bpy.ops.object.mode_set(mode='OBJECT')
 bpy.ops.object.select_all(action='DESELECT')
 arm.hide_set(False);arm.select_set(True);bpy.context.view_layer.objects.active=arm
 bpy.ops.object.mode_set(mode='EDIT')
 for side in ('Left','Right'):
  src=arm.data.edit_bones.get('mixamorig:'+side+'Foot')
  if src is None:fail('SOURCE_FOOT_EDIT_BONE_MISSING_'+side)
  key='CTRL_'+side+'Foot_IK'
  if arm.data.edit_bones.get(key):fail('IK_CONTROL_ALREADY_EXISTS_'+side)
  e=arm.data.edit_bones.new(key);e.head=src.head.copy();e.tail=src.head+Vector((0,0,0.15));e.use_deform=False
  e.parent=None
 bpy.ops.object.mode_set(mode='POSE')
 arm.show_in_front=True
 for side in ('Left','Right'):
  pb=arm.pose.bones['CTRL_'+side+'Foot_IK'];pb.bone.hide=False;pb.lock_scale=(True,True,True)
 return {side:arm.pose.bones['CTRL_'+side+'Foot_IK'] for side in ('Left','Right')}

def key_controllers(arm,act,slot,frames):
 set_action(arm,act,slot)
 for witness in frames:
  f=witness['frame'];frame_set(f)
  for side in ('Left','Right'):
   pb=arm.pose.bones['CTRL_'+side+'Foot_IK'];rest=pb.bone.matrix_local
   pb.location=rest.to_3x3().inverted()@(witness[side+'Foot']-pb.bone.head_local)
   if not pb.keyframe_insert(data_path='location',frame=f,group='Foot IK Controls'):
    fail('CANNOT_KEY_ALWAYS_ON_IK_CONTROLLER_'+act.name+'_'+side)
 if arm.animation_data.action is not act:fail('IK_CONTROLLER_WROTE_ANOTHER_ACTION_'+act.name)

def install_ik_constraints(arm):
 constraints=[]
 for side in ('Left','Right'):
  calf=arm.pose.bones.get('mixamorig:'+side+'Leg')
  if calf is None:fail('CALF_BONE_MISSING_'+side)
  if any(c.type=='IK' for c in calf.constraints):fail('PREEXISTING_CALF_IK_CONSTRAINT_'+side)
  c=calf.constraints.new('IK');c.name='EDITABLE_ALWAYS_ON_'+side+'_FOOT';c.target=arm
  c.subtarget='CTRL_'+side+'Foot_IK';c.chain_count=2;c.influence=1.0;c.iterations=200
  if hasattr(c,'use_stretch'):c.use_stretch=False
  for bone in ('mixamorig:'+side+'UpLeg','mixamorig:'+side+'Leg'):
   if bone in arm.pose.bones:arm.pose.bones[bone].ik_stretch=0.0
  constraints.append(c)
 return constraints

def run(a):
 receipt=pathlib.Path(a.receipt);receipt.parent.mkdir(parents=True,exist_ok=True)
 out={'status':'BOOT','stage':'BOOT','sourceGLBSHA256':a.sha,'masterBlend':a.output,
  'canonicalModified':False,'acceptedAxeKickRetargeted':False,'IKFKTogglePresent':False,'IKConstraintInfluence':1.0}
 def save():receipt.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
 save()
 try:
  if bpy.app.version[:2]!=(5,0):fail('REQUIRES_VERIFIED_BLENDER5')
  if sha(a.source)!=a.sha:fail('REVIEW_LIBRARY_GLB_SHA_CHANGED')
  bpy.ops.import_scene.gltf(filepath=a.source)
  rigs=[o for o in bpy.data.objects if o.type=='ARMATURE' and 'mixamorig:LeftFoot' in o.pose.bones and 'mixamorig:RightFoot' in o.pose.bones]
  if len(rigs)!=1:fail('ONE_SMARTRIG_ARMATURE_REQUIRED_'+str([o.name for o in rigs]))
  arm=rigs[0];arm.data.pose_position='POSE';arm.animation_data_create()
  # Exactly exclude the accepted AxeKick and the earlier Heavy1 control from IK authoring.
  # They remain byte-identical in the separate runtime GLB.
  for protected in ('AxeKick','Heavy1_old_ARP'):
   ac=bpy.data.actions.get(protected)
   if ac is not None:bpy.data.actions.remove(ac,do_unlink=True)
  actions={act.name:act for act in bpy.data.actions if act.name.startswith(('Lionheart_','Ares_'))}
  expected=json.loads(pathlib.Path(a.expected).read_text())
  if set(actions)!=set(expected):fail('AUTHORING_ACTION_INVENTORY_MISMATCH_missing='+repr(sorted(set(expected)-set(actions)))+'_extra='+repr(sorted(set(actions)-set(expected))))
  if len(actions)<12:fail('NOT_ALL_RUNTIME_SOURCE_ACTIONS_IMPORTED_'+repr(sorted(actions)))
  if 'AxeKick' in actions:fail('AXEKICK_MUST_NOT_BE_IK_REBUILT')
  original={}
  for name,act in sorted(actions.items()):
   slot=action_slot(act);original[name]={'action':act,'slot':slot,'frames':samples(arm,act,slot)}
  out['sourceActions']=list(sorted(original));out['stage']='SOURCE_FK_WITNESSES_CAPTURED';save()
  controls=build_foot_controls(arm)
  for name,x in sorted(original.items()):key_controllers(arm,x['action'],x['slot'],x['frames'])
  constraints=install_ik_constraints(arm)
  if len(constraints)!=2 or any(c.influence!=1 or c.target!=arm for c in constraints):fail('ALWAYS_ON_BOTH_FOOT_IK_NOT_ENFORCED')
  # Validate actual new constrained poses, including frame-0 and all integer frames.
  metrics={};worst_foot=0.;worst_knee=0.
  for name,x in sorted(original.items()):
   set_action(arm,x['action'],x['slot'])
   maxfoot=0.;maxknee=0.;worstframe=None
   for witness in x['frames']:
    frame_set(witness['frame'])
    for side in ('Left','Right'):
     err=(joint_position(arm,side,'Foot')-witness[side+'Foot']).length
     knee=(joint_position(arm,side,'Leg')-witness[side+'Knee']).length
     if err>maxfoot:maxfoot=float(err);worstframe=witness['frame']
     maxknee=max(maxknee,float(knee))
   worst_foot=max(worst_foot,maxfoot);worst_knee=max(worst_knee,maxknee)
   metrics[name]={'maxFootHeadDeviationM':round(maxfoot,6),'maxKneeHeadDeviationM':round(maxknee,6),'worstFrame':worstframe,'keyedFrames':len(x['frames'])}
  out['poseParity']={'worstFootDeviationM':worst_foot,'worstKneeDeviationM':worst_knee,'perAction':metrics}
  # An IK control rig may require OWNER edits. Do not misrepresent large deviations as
  # preserved baseline, but allow the unapproved editing artifact to exist for inspection.
  out['posePreservationPass']=worst_foot<=0.03 and worst_knee<=0.12
  output=pathlib.Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
  if output.exists():fail('IK_AUTHORING_BLEND_COLLISION')
  bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
  if not output.is_file() or output.stat().st_size<100000:fail('IK_AUTHORING_BLEND_NOT_SAVED')
  out.update({'status':'ALWAYS_ON_FOOT_IK_AUTHORING_BLEND_SAVED_UNAPPROVED','stage':'SAVED',
   'footIKControls':['CTRL_LeftFoot_IK','CTRL_RightFoot_IK'],
   'activeIKConstraints':[c.name for c in constraints],
   'blendSHA256':sha(output),'blendBytes':output.stat().st_size,
   'axes':'BLENDER_Z_UP','acceptedAxeKickOriginalGLBUnmodified':True})
  save();print('IK_AUTHORING_SAVED='+str(output)+' PARITY='+('PASS' if out['posePreservationPass'] else 'REVIEW_REQUIRED'),flush=True)
 except BaseException as e:
  out.update({'status':'BLOCKED','errorType':type(e).__name__,'error':str(e)[:800],'traceback':traceback.format_exc()[-1800:]});save();raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for key in ('source','sha','output','receipt','expected'):p.add_argument('--'+key,required=True)
 run(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
