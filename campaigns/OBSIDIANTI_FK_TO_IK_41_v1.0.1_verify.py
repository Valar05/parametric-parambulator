"""Independent Blender reopen and animation-control verification for IK41."""
import bpy,sys,json,pathlib,hashlib,math
src,report,out=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:]);a=json.loads(report.read_text());result={'status':'STARTED'}
def need(v,s):
 if not v:raise RuntimeError(s)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def curves(act):
 try:f=list(act.fcurves)
 except (AttributeError,RuntimeError):f=[]
 if not f:
  for layer in act.layers:
   for st in layer.strips:
    for slot in act.slots:
     try:bag=st.channelbag(slot,ensure=False)
     except (AttributeError,RuntimeError,TypeError):bag=None
     if bag:f+=list(bag.fcurves)
 return f
def signature(act):
 x=[(f.data_path,int(f.array_index),[(round(float(p.co.x),6),round(float(p.co.y),6)) for p in f.keyframe_points]) for f in curves(act)]
 return hashlib.sha256(json.dumps(sorted(x),separators=(',',':')).encode()).hexdigest()
def setframe(t):
 i=math.floor(t);bpy.context.scene.frame_set(i,subframe=t-i);bpy.context.view_layer.update()
def play(arm,act,ident):
 sl=next((x for x in act.slots if x.identifier==ident),None)
 need(sl is not None,'ACTION_SLOT_NOT_FOUND_'+act.name)
 ad=arm.animation_data;ad.use_nla=False
 for tr in ad.nla_tracks:tr.mute=True
 ad.action=act;ad.action_slot=sl
 need(ad.action_slot==sl,'REOPEN_SLOT_ASSIGNMENT_FAILED')
try:
 need(a['status']=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING','BUILD_NOT_SUCCESS')
 need(digest(src)==a['outputSHA256'],'REOPEN_INPUT_SHA_MISMATCH')
 bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 arm=bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE');ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 need(arm and ref and arm.data!=ref.data,'REFERENCE_RIG_LOST')
 need(len(arm.animation_data.nla_tracks)==41,'REOPEN_IK41_NLA_COUNT_WRONG')
 need(set(x.name for x in arm.animation_data.nla_tracks)==set(a['sourceClips']),'REOPEN_SOURCE_CLIP_IDENTITY_CHANGED')
 need(len(a['newActions'])==41,'REOPEN_IK41_ACTION_MANIFEST_NOT_41')
 for side in ('Left','Right'):
  ctrl=arm.pose.bones.get('CTRL_'+side+'_ANKLE_IK');pole=arm.pose.bones.get('CTRL_'+side+'_KNEE_POLE')
  need(ctrl and pole and not ctrl.bone.use_deform and not pole.bone.use_deform,'REOPEN_CONTROL_NOT_PRESENT')
  shin=arm.pose.bones['mixamorig:'+side+'Leg'];foot=arm.pose.bones['mixamorig:'+side+'Foot']
  ik=shin.constraints.get('IK41_TWO_BONE_'+side);rot=foot.constraints.get('IK41_FOOT_ROT_'+side)
  need(ik and ik.type=='IK' and ik.influence==1 and ik.chain_count==2 and ik.target==arm and ik.subtarget==ctrl.name,'REOPEN_IK_NOT_LIVE_'+side)
  need(ik.pole_target==arm and ik.pole_subtarget==pole.name and not ik.use_stretch,'REOPEN_POLE_IK_WRONG_'+side)
  need(rot and rot.type=='COPY_ROTATION' and rot.influence==1 and rot.target==arm,'REOPEN_FOOT_ORIENTATION_MISSING_'+side)
 for name,sha in a['originalActionSignatures'].items():
  act=bpy.data.actions.get(name);need(act and signature(act)==sha,'ORIGINAL_FK_ACTION_CHANGED_'+name)
 worst={'ankleM':0,'kneeM':0,'footDeg':0};tested=0
 for name,info in a['newActions'].items():
  tr=arm.animation_data.nla_tracks[name];need(len(tr.strips)==1,'IK_NLA_CLIP_STRIP_COUNT_'+name)
  st=tr.strips[0];act=st.action;need(act and act.name==info['action'],'IK_ACTION_NOT_ATTACHED_'+name)
  ctrlcurves=[fc for fc in curves(act) if 'CTRL_' in fc.data_path]
  need(len(ctrlcurves)>=18,'REOPEN_IK_CONTROLLER_KEYS_MISSING_'+name)
  need(st.action_slot is not None,'REOPEN_IK_ACTION_SLOT_MISSING_'+name)
  # Same FK action on the SAME skeleton, with IK off, is our reproducible gold reference.
  fk=bpy.data.actions.get(info['sourceAction']);need(fk,'FK_REFERENCE_ACTION_MISSING_'+name)
  times=sorted({round(float(p.co.x),5) for fc in curves(fk) for p in fc.keyframe_points})
  need(times,'FK_KEY_TIMES_MISSING_'+name)
  for t in sorted(set([times[0],times[len(times)//2],times[-1]])):
   for side in ('Left','Right'):
    arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=0
    arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=0
   # FK source Action slot from recorded IK slot's identifier, both action copies keep that slot.
   play(arm,fk,st.action_slot.identifier);setframe(t)
   saved={}
   for side in ('Left','Right'):
    saved[side]={'foot':arm.pose.bones['mixamorig:'+side+'Foot'].matrix.copy(),
      'knee':arm.pose.bones['mixamorig:'+side+'Leg'].head.copy()}
    arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=1
    arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=1
   play(arm,act,st.action_slot.identifier);setframe(t)
   for side in ('Left','Right'):
    foot=arm.pose.bones['mixamorig:'+side+'Foot'];knee=arm.pose.bones['mixamorig:'+side+'Leg']
    v={'ankleM':float((foot.matrix.translation-saved[side]['foot'].translation).length),
      'kneeM':float((knee.head-saved[side]['knee']).length),
      'footDeg':math.degrees(foot.matrix.to_quaternion().rotation_difference(saved[side]['foot'].to_quaternion()).angle)}
    for k in worst:worst[k]=max(worst[k],v[k])
   tested+=1
 for k,limit in a['poseParity']['limits'].items():need(worst[k]<=limit,'REOPEN_ACTUAL_POSE_PARITY_FAILED_'+k+'_'+str(worst[k]))
 # The original source file is untouched, and this check does not save any changes.
 result={'status':'REOPEN_41_ACTIONS_IK_VERIFIED_VISUAL_PENDING','sha256':a['outputSHA256'],
  'originalActionCount':len(a['originalActionSignatures']),'ikActions':41,'testedKeyPoses':tested,'reopenWorst':worst,
  'ownerVisualAcceptance':'PENDING'}
 out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print('REOPEN_VERIFIED',json.dumps(result),flush=True)
except BaseException as e:
 result.update(status='BLOCKED',error=repr(e));out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');raise
