#!/usr/bin/env python3
"""Headless Blender 5 native donor measurement. No retargeting or source modification."""
from __future__ import annotations
import argparse,hashlib,json,math,pathlib,traceback,sys
import bpy
from mathutils import Vector
LION=['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
def apply_frame(f):
 x=math.floor(float(f));bpy.context.scene.frame_set(x,subframe=float(f)-x)
 bpy.context.view_layer.update()
def active_slot(action):
 choices=[]
 for slot in getattr(action,'slots',[]):
  if slot.target_id_type!='OBJECT':continue
  count=0
  for layer in action.layers:
   for strip in layer.strips:
    try:bag=strip.channelbag(slot,ensure=False)
    except (TypeError,RuntimeError,AttributeError):bag=None
    if bag:count+=len(bag.fcurves)
  choices.append((count,slot.identifier,slot))
 if not choices:return None,0
 count,name,slot=max(choices,key=lambda x:x[0])
 if count<6:raise RuntimeError('NATIVE_SOURCE_ACTION_HAS_NO_POPULATED_ARMATURE_SLOT_'+action.name)
 return slot,count
def set_action(arm,act):
 ad=arm.animation_data_create();ad.use_nla=False
 for tr in ad.nla_tracks:tr.mute=True
 ad.action=act
 slot,count=active_slot(act)
 if slot is not None:ad.action_slot=slot
 if ad.action!=act:raise RuntimeError('NATIVE_ACTION_ACTIVATION_MISMATCH_'+act.name)
 return {'slot':str(slot.identifier) if slot else None,'curveCount':count}
def joint(arm,side,name):
 return (arm.matrix_world@arm.pose.bones['mixamorig:'+side+name].matrix.translation)
def donor_rest(arm,side):
 a=arm.matrix_world@arm.data.bones['mixamorig:'+side+'Foot'].head_local
 b=arm.matrix_world@arm.data.bones['mixamorig:'+side+'ToeBase'].head_local
 return (a-b).length

def run(a):
 result={'schema':'OBSIDIANTI_TOE_ROLL_POST_ARP_v2.0.19','status':'BOOT','sourceSHA256':a.sha,'retargetRun':False,'sourceModified':False}
 report=pathlib.Path(a.output);report.parent.mkdir(parents=True,exist_ok=True)
 def save():report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 save()
 try:
  if bpy.app.version[:2]!=(5,0):raise RuntimeError('BLENDER5_HEADLESS_REQUIRED_'+bpy.app.version_string)
  if sha(a.source)!=a.sha:raise RuntimeError('NATIVE_DONOR_SHA_CHANGED')
  bpy.ops.wm.open_mainfile(filepath=a.source,load_ui=False)
  names=('LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase')
  arms=[o for o in bpy.data.objects if o.type=='ARMATURE' and all('mixamorig:'+b in o.pose.bones for b in names)]
  if len(arms)!=1:raise RuntimeError('NATIVE_DONOR_ARMATURE_AMBIGUOUS_'+repr([x.name for x in arms]))
  arm=arms[0];arm.data.pose_position='POSE'
  acts={x.name:x for x in bpy.data.actions};need=['Idle',*LION]
  if any(name not in acts for name in need):raise RuntimeError('NATIVE_LIONHEART_REQUIRED_SOURCE_ACTION_MISSING')
  sidebase={}
  set_action(arm,acts['Idle']);start=float(acts['Idle'].frame_range[0]);apply_frame(start)
  for side in ('Left','Right'):
   toe=joint(arm,side,'ToeBase');heel=joint(arm,side,'Foot')
   sidebase[side]={'idleToeZ':float(toe.z),'idleHeelAboveToe':float(heel.z-toe.z),'ankleToeLength':float(donor_rest(arm,side))}
  result['sourceNeutralReference']={'nativeIdleFrame':start,'feet':sidebase,'sourceArmature':arm.name,'sourceObjectMatrix':[[float(x) for x in row] for row in arm.matrix_world]}
  result['actions']={};result['sourceActionSlots']={}
  for name in LION:
   act=acts[name];result['sourceActionSlots'][name]=set_action(arm,act)
   start,end=[float(x) for x in act.frame_range]
   if end<=start or end-start>350:raise RuntimeError('NATIVE_ACTION_DURATION_INVALID_'+name)
   rows=[]
   for i in range(65):
    f=start+(end-start)*i/64;apply_frame(f);entry={}
    for side in ('Left','Right'):
     ankle=joint(arm,side,'Foot');toe=joint(arm,side,'ToeBase')
     entry[side]={'toeZ':float(toe.z),'ankleZ':float(ankle.z),**sidebase[side]}
    rows.append(entry)
   result['actions']['Lionheart_'+name]=rows
  result.update({'status':'DONOR_NATIVE_BLENDER_TOE_WITNESSES_VERIFIED','samplesPerAction':65,'sourceActionCount':len(LION)})
  save()
  print('DONOR_CONTACT_WITNESSES='+str(len(result['actions']))+' SHA256='+sha(report),flush=True)
 except BaseException as e:
  result.update({'status':'BLOCKED','error':str(e)[:850],'traceback':traceback.format_exc()[-2200:]});save();raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('source','sha','output'):p.add_argument('--'+n,required=True)
 run(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
