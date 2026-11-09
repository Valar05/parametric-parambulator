"""Strict recovery audit: compare all preserved FK actions with source, evaluate all IK41 clips.
Runs only inside the owner's Blender through Termux; never saves or modifies either source.
"""
import bpy, sys, json, pathlib, hashlib, math, traceback
from collections import defaultdict
SOURCE_EXPECTED='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
CAND_EXPECTED='f594543e098f553d02f09d7dcbdcd3019bc15181a8d513e64a5d98a0f3ad429a'
source,candidate,author_report,destination=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:])
result={'campaign':'OBSIDIANTI_IK41_REOPEN_RECOVERY_v1.0.2','status':'STARTED','stage':'INPUT_CHECK','referenceSHA256':SOURCE_EXPECTED,'candidateSHA256':CAND_EXPECTED,'ownerVisualAcceptance':'PENDING'}
def save():destination.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
def need(condition,msg):
 if not condition:raise RuntimeError(msg)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def curves(act):
 try:fc=list(act.fcurves)
 except (AttributeError,RuntimeError):fc=[]
 if not fc:
  for layer in getattr(act,'layers',[]):
   for strip in getattr(layer,'strips',[]):
    for slot in getattr(act,'slots',[]):
     try:bag=strip.channelbag(slot,ensure=False)
     except (AttributeError,TypeError,RuntimeError):bag=None
     if bag:fc+=list(bag.fcurves)
 return fc
def action_snapshot(act):
 out={}
 for fc in curves(act):
  key=(fc.data_path,int(fc.array_index))
  need(key not in out,'DUPLICATE_FCURVE_TARGET_'+act.name+'_'+repr(key))
  points=[]
  for p in fc.keyframe_points:
   points.append({'co':(float(p.co.x),float(p.co.y)),
    'left':(float(p.handle_left.x),float(p.handle_left.y)),
    'right':(float(p.handle_right.x),float(p.handle_right.y)),
    'interp':str(p.interpolation),'handleLeftType':str(p.handle_left_type),
    'handleRightType':str(p.handle_right_type)})
  out[key]={'points':points,'extrapolation':str(fc.extrapolation)}
 return out
def setframe(t):
 i=math.floor(t);bpy.context.scene.frame_set(i,subframe=float(t-i));bpy.context.view_layer.update()
def play(arm,act,slot_id):
 slot=next((s for s in act.slots if s.identifier==slot_id),None)
 need(slot is not None,'ACTION_SLOT_NOT_FOUND_'+act.name+'_'+slot_id)
 ad=arm.animation_data_create();ad.use_nla=False
 for tr in ad.nla_tracks:tr.mute=True
 ad.action=act;ad.action_slot=slot
 need(ad.action==act and ad.action_slot==slot,'ACTION_SLOT_ASSIGNMENT_FAILED_'+act.name)
try:
 need(source.is_file() and sha(source)==SOURCE_EXPECTED,'PINNED_FK_SOURCE_MISSING_OR_DIFFERENT')
 need(candidate.is_file() and sha(candidate)==CAND_EXPECTED,'PINNED_IK_CANDIDATE_MISSING_OR_DIFFERENT')
 audit=json.loads(author_report.read_text())
 need(audit.get('status')=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING','CANDIDATE_AUTHORING_NOT_COMPLETE')
 need(audit.get('outputSHA256')==CAND_EXPECTED and audit.get('sourceSHA256')==SOURCE_EXPECTED,'AUTHOR_AUDIT_SOURCE_OR_OUTPUT_CHANGED')
 need(audit.get('ikActionCount')==41 and audit.get('poseParity',{}).get('passed') is True,'AUTHOR_41_ACTION_POSE_PARITY_NOT_PASSED')
 result['stage']='CAPTURE_NATIVE_REFERENCE_ACTIONS';save()
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 reference={act.name:action_snapshot(act) for act in bpy.data.actions}
 need(len(reference)==82,'EXPECTED_82_PRESERVED_FK_ACTIONS_'+str(len(reference)))
 result['referenceActionCount']=len(reference)
 # Fresh independent file open, not a duplicated in-memory Blender data block.
 result['stage']='REOPEN_CANDIDATE_AND_COMPARE_FK';save()
 bpy.ops.wm.open_mainfile(filepath=str(candidate),load_ui=False)
 changed=[];worst_value=0.;worst_time=0.;worst_handle=0.;count_points=0
 for name,snap in sorted(reference.items()):
  act=bpy.data.actions.get(name)
  if act is None:
   changed.append({'action':name,'reason':'MISSING'})
   continue
  current=action_snapshot(act)
  if snap.keys()!=current.keys():
   changed.append({'action':name,'reason':'FCURVE_TARGET_SET_CHANGED','removed':len(snap.keys()-current.keys()),'added':len(current.keys()-snap.keys())})
   continue
  for key,prior in snap.items():
   after=current[key]
   if prior['extrapolation']!=after['extrapolation'] or len(prior['points'])!=len(after['points']):
    changed.append({'action':name,'target':repr(key),'reason':'FCURVE_METADATA_OR_KEY_COUNT_CHANGED'})
    continue
   for i,(p,q) in enumerate(zip(prior['points'],after['points'])):
    if any(p[k]!=q[k] for k in ('interp','handleLeftType','handleRightType')):
     changed.append({'action':name,'target':repr(key),'key':i,'reason':'INTERPOLATION_OR_HANDLE_TYPE_CHANGED'})
     continue
    dt=abs(p['co'][0]-q['co'][0]);dv=abs(p['co'][1]-q['co'][1]);dh=max(abs(p[k][d]-q[k][d]) for k in ('left','right') for d in (0,1))
    worst_time=max(worst_time,dt);worst_value=max(worst_value,dv);worst_handle=max(worst_handle,dh);count_points+=1
    # Blade-safe numeric comparison: permit serialization-level float error ONLY.
    if dt>0.00002 or dv>0.00002 or dh>0.00005:
     if len(changed)<24:changed.append({'action':name,'target':repr(key),'key':i,'reason':'NUMERIC_DRIFT_ABOVE_SERIALIZATION_TOLERANCE','time':dt,'value':dv,'handle':dh})
 result['fkCurveComparison']={'referenceActions':len(reference),'sourceKeyframePoints':count_points,'maxFrameTimeDifference':worst_time,'maxValueDifference':worst_value,'maxHandleDifference':worst_handle,'tolerances':{'timeFrames':2e-5,'value':2e-5,'handle':5e-5},'firstProblems':changed[:24],'passed':not changed}
 save()
 need(not changed,'ORIGINAL_FK_CURVES_ACTUALLY_CHANGED_'+repr(changed[:2]))
 result['stage']='REOPEN_IK41_CONTROLS_AND_POSE_SAMPLES';save()
 arm=bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE');ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 need(arm and ref and arm.type==ref.type=='ARMATURE' and arm.data!=ref.data,'INDEPENDENT_RIGS_MISSING')
 need(arm.animation_data and len(arm.animation_data.nla_tracks)==41,'IK41_NLA_TRACK_COUNT_INVALID')
 need(set(x.name for x in arm.animation_data.nla_tracks)==set(audit['sourceClips']),'IK41_CLIP_INVENTORY_CHANGED')
 for side in ('Left','Right'):
  target=arm.pose.bones.get('CTRL_'+side+'_ANKLE_IK');pole=arm.pose.bones.get('CTRL_'+side+'_KNEE_POLE')
  need(target and pole and not target.bone.use_deform and not pole.bone.use_deform,'IK_CONTROL_MISSING_'+side)
  shin=arm.pose.bones['mixamorig:'+side+'Leg'];foot=arm.pose.bones['mixamorig:'+side+'Foot']
  ik=shin.constraints.get('IK41_TWO_BONE_'+side);orient=foot.constraints.get('IK41_FOOT_ROT_'+side)
  need(ik and ik.type=='IK' and ik.chain_count==2 and ik.target==arm and ik.subtarget==target.name and ik.pole_target==arm and ik.pole_subtarget==pole.name and not ik.use_stretch,'IK_CHAIN_MISSING_'+side)
  need(orient and orient.type=='COPY_ROTATION' and orient.target==arm and orient.subtarget==target.name,'FOOT_ORIENTATION_MISSING_'+side)
 worst={'ankleM':0.,'kneeM':0.,'footDeg':0.};tested=0
 for clip,info in audit['newActions'].items():
  tr=arm.animation_data.nla_tracks.get(clip)
  need(tr and len(tr.strips)==1,'IK_ACTION_TRACK_MISSING_'+clip)
  strip=tr.strips[0];act=strip.action
  need(act and act.name==info['action'],'IK_ACTION_WRONG_'+clip)
  need(strip.action_slot,'IK_ACTION_SLOT_MISSING_'+clip)
  need(len([fc for fc in curves(act) if 'CTRL_' in fc.data_path])>=18,'IK_CONTROLLER_CURVES_MISSING_'+clip)
  fk=bpy.data.actions.get(info['sourceAction']);need(fk,'REFERENCE_ACTION_MISSING_'+clip)
  times=sorted({round(float(p.co.x),5) for fc in curves(fk) for p in fc.keyframe_points})
  need(times,'FK_ACTION_HAS_NO_KEYS_'+clip)
  for t in sorted(set((times[0],times[len(times)//2],times[-1]))):
   for side in ('Left','Right'):
    arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=0
    arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=0
   play(arm,fk,strip.action_slot.identifier);setframe(t)
   saved={side:{'foot':arm.pose.bones['mixamorig:'+side+'Foot'].matrix.copy(),'knee':arm.pose.bones['mixamorig:'+side+'Leg'].head.copy()} for side in ('Left','Right')}
   for side in ('Left','Right'):
    arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=1
    arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=1
   play(arm,act,strip.action_slot.identifier);setframe(t)
   for side in ('Left','Right'):
    foot=arm.pose.bones['mixamorig:'+side+'Foot'];knee=arm.pose.bones['mixamorig:'+side+'Leg']
    now={'ankleM':(foot.matrix.translation-saved[side]['foot'].translation).length,
      'kneeM':(knee.head-saved[side]['knee']).length,
      'footDeg':math.degrees(foot.matrix.to_quaternion().rotation_difference(saved[side]['foot'].to_quaternion()).angle)}
    for k,v in now.items():worst[k]=max(worst[k],float(v))
   tested+=1
 limits=audit['poseParity']['limits']
 for key in worst:need(worst[key]<=limits[key],'REOPEN_ACTUAL_POSE_PARITY_FAILED_'+key+'_'+str(worst[key]))
 need(tested>=123,'INSUFFICIENT_REOPEN_KEY_SAMPLES_'+str(tested))
 result.update(status='VERIFIED_41_IK_NATIVE_REOPEN_OWNER_VISUAL_PENDING',stage='COMPLETE',
  actualIKPoseSamples=tested,actualIKWorst=worst,sourceUnchanged=sha(source)==SOURCE_EXPECTED,
  candidateUnchanged=sha(candidate)==CAND_EXPECTED)
 save();print('RECOVERY_BLENDER_REOPEN_VERIFIED='+str(tested)+' '+json.dumps(worst),flush=True)
except BaseException as exc:
 result.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc()[-4000:]);save();raise
