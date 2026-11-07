#!/usr/bin/env python3
"""Blender 5 read-only action-slot and rig audit. Never imports or registers ARP."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,math,traceback,sys
import bpy
CORE=('Hips','Spine','Spine1','Spine2','Neck','Head','LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase')

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def bank(action,slot):
 curves=[]
 for layer in action.layers:
  for strip in layer.strips:
   try: cb=strip.channelbag(slot,ensure=False)
   except (RuntimeError,AttributeError,TypeError):cb=None
   if cb:curves.extend(cb.fcurves)
 return curves

def is_relevant_curve(f):
 return 'pose.bones["mixamorig:' in f.data_path

def movement(curves):
 moving=0
 for fc in curves:
  if len(fc.keyframe_points)<2:continue
  val=[p.co.y for p in fc.keyframe_points]
  if max(val)-min(val)>0.0001:moving+=1
 return moving

def safe_label(s):
 return ''.join(c if c.isalnum() or c in '._-' else '_' for c in s)

def scan():
 candidates=[o for o in bpy.data.objects if o.type=='ARMATURE' and all('mixamorig:'+p in o.pose.bones for p in CORE)]
 if len(candidates)!=1:raise RuntimeError('ARES_SOURCE_RIG_NOT_UNIQUE_'+repr([o.name for o in candidates]))
 arm=candidates[0]
 actions=[];excluded=[];seen=set()
 for a in sorted(bpy.data.actions,key=lambda x:x.name):
  choices=[]
  for slot in getattr(a,'slots',[]):
   if slot.target_id_type!='OBJECT':continue
   fcs=bank(a,slot)
   useful=[fc for fc in fcs if is_relevant_curve(fc)]
   choices.append({'action':a.name,'slot':str(slot.identifier),'fcurves':len(fcs),'mappedCurves':len(useful),'movingCurves':movement(useful), 'frameStart':float(a.frame_range[0]),'frameEnd':float(a.frame_range[1])})
  choices=[x for x in choices if x['mappedCurves']>=1 and x['fcurves']>=1]
  if not choices:
   excluded.append({'action':a.name,'reason':'NO_MAPPED_MIXAMO_ARMATURE_CURVES'});continue
  # Keep every populated source slot. In particular Cross's Player and Enemy
  # slots are distinct motions within the SAME Action datablock.
  for x in choices:
   name=a.name
   if len(choices)>1:
    name=a.name+'__'+safe_label(x['slot'])
    if a.name=='Cross' and 'enemy' in x['slot'].lower():name='Cross-Enemy'
    if a.name=='Cross' and 'player' in x['slot'].lower():name='Cross-Player'
   # If exact action names collide with a generated slot name, disambiguate.
   if name in seen:name=a.name+'__'+safe_label(x['slot'])+'_'+hashlib.sha256(x['slot'].encode()).hexdigest()[:7]
   if name in seen:raise RuntimeError('DUPLICATE_ACTION_SLOT_ID_'+name)
   seen.add(name);x['name']=name;x['static']=x['movingCurves']==0
   actions.append(x)
 missing_enemy=[name for name in ('Jab-Enemy','Cross-Enemy') if name not in seen]
 for name in missing_enemy:excluded.append({'action':name,'reason':'EXPECTED_ENEMY_ATTACK_SLOT_NOT_FOUND_REPORT_NOT_SILENT'})
 if len(actions)<25:raise RuntimeError('TOO_FEW_SOURCE_ACTION_SLOTS_'+str(len(actions)))
 # Priority attacks first so early partial review already has meaningful clips.
 priority={'Jab-Enemy':0,'Cross-Enemy':1,'Idle':2,'Run':3,'Jab':4,'Cross-Player':5,'Cross':6}
 actions.sort(key=lambda x:(priority.get(x['name'],10),x['name']))
 return arm,actions,excluded

def main(arg):
 r={'status':'BOOT','sourceSHA256':sha(arg.source),'targetFBXSHA256':sha(arg.target),'version':bpy.app.version_string,'mutates':False}
 path=pathlib.Path(arg.output);path.parent.mkdir(parents=True,exist_ok=True)
 def save():path.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 save()
 try:
  if bpy.app.version[:2]!=(5,0):raise RuntimeError('BLENDER_5_0_REQUIRED_'+bpy.app.version_string)
  if r['sourceSHA256']!=arg.source_sha or r['targetFBXSHA256']!=arg.target_sha:raise RuntimeError('EXACT_OWNER_INPUT_HASH_CHANGED')
  bpy.ops.wm.open_mainfile(filepath=arg.source,load_ui=False)
  arm,actions,excluded=scan()
  r.update({'sourceRig':arm.name,'sourceRigBoneCount':len(arm.pose.bones),'actions':actions,'excluded':excluded,'sourceActionDatablocks':len(bpy.data.actions),'stage':'SOURCE_AUDITED'})
  prior=set(bpy.data.objects)
  bpy.ops.import_scene.fbx(filepath=arg.target)
  arrivals=[o for o in bpy.data.objects if o not in prior]
  rigs=[o for o in arrivals if o.type=='ARMATURE' and all('mixamorig:'+p in o.pose.bones for p in CORE)]
  if len(rigs)!=1:raise RuntimeError('MUDMAN_MIXAMO_FBX_ARMATURE_NOT_UNIQUE_'+repr([o.name for o in rigs]))
  tgt=rigs[0]
  meshes=[m for m in arrivals if m.type=='MESH' and (m.parent==tgt or any(mod.type=='ARMATURE' and mod.object==tgt for mod in m.modifiers))]
  if not meshes:raise RuntimeError('MUDMAN_FBX_HAS_NO_SKINNED_MESH')
  r['target']={'armature':tgt.name,'bones':len(tgt.pose.bones),'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials if m]} for o in meshes], 'images':[im.name for im in bpy.data.images]}
  r['status']='SOURCE_AND_MUDMAN_RIG_AUDITED';r['stage']='DONE';save()
  print('ARES_ACTION_SLOTS='+str(len(actions))+' TOTAL_DATABLOCKS='+str(len(bpy.data.actions))+' MUDMAN_MESHES='+str(len(meshes)),flush=True)
 except BaseException as exc:
  r.update({'status':'BLOCKED','error':str(exc)[:1200],'traceback':traceback.format_exc()[-1600:]});save();raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ('source','source-sha','target','target-sha','output'):p.add_argument('--'+k,required=True)
 main(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
