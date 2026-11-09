"""Independent Blender process: compare pristine native FK reference to restored IK41."""
import bpy,sys,json,pathlib,hashlib,math,traceback
SRC_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
OLD_SHA='f594543e098f553d02f09d7dcbdcd3019bc15181a8d513e64a5d98a0f3ad429a'
source,candidate,author_report,repair_report,report=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:])
result={'status':'STARTED','stage':'BOOT','ownerVisualAcceptance':'PENDING'}
def save():report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def curves(act):
 try:c=list(act.fcurves)
 except (AttributeError,RuntimeError):c=[]
 if not c:
  for layer in getattr(act,'layers',[]):
   for strip in getattr(layer,'strips',[]):
    for slot in getattr(act,'slots',[]):
     try:bag=strip.channelbag(slot,ensure=False)
     except (AttributeError,RuntimeError,TypeError):bag=None
     if bag:c+=list(bag.fcurves)
 return c
def snapshot(act):
 out={}
 for f in curves(act):
  key=(f.data_path,int(f.array_index));need(key not in out,'DUPLICATE_FCURVE_'+act.name+str(key))
  keys=[]
  for p in f.keyframe_points:
   keys.append((tuple(float(v) for v in p.co),tuple(float(v) for v in p.handle_left),tuple(float(v) for v in p.handle_right),str(p.interpolation),str(p.handle_left_type),str(p.handle_right_type)))
  out[key]=(str(f.extrapolation),keys)
 return out
def play(arm,act,slotid):
 slot=next((s for s in act.slots if s.identifier==slotid),None)
 need(slot is not None,'SLOT_MISSING_'+act.name)
 ad=arm.animation_data_create();ad.use_nla=False
 for track in ad.nla_tracks:track.mute=True
 ad.action=act;ad.action_slot=slot
 need(ad.action==act and ad.action_slot==slot,'PLAY_ASSIGNMENT_FAILED_'+act.name)
def frame(t):
 i=math.floor(t);bpy.context.scene.frame_set(i,subframe=float(t-i));bpy.context.view_layer.update()
try:
 save()
 author=json.loads(author_report.read_text());repair=json.loads(repair_report.read_text())
 need(author.get('status')=='IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING' and author.get('outputSHA256')==OLD_SHA and author['poseParity']['passed'] and author['ikActionCount']==41,'ORIGINAL_AUTHOR_NOT_VERIFIED')
 need(repair.get('status')=='RESTORED_ACTIONS_SAVED_UNAPPROVED' and repair.get('oldCandidateSHA256')==OLD_SHA,'RESTORATION_REPORT_INVALID')
 need(sha(source)==SRC_SHA and sha(candidate)==repair['outputSHA256'],'PINNED_NATIVE_INPUT_SHA_MISMATCH')
 result['sourceSHA256']=SRC_SHA;result['outputSHA256']=repair['outputSHA256']
 result['stage']='CAPTURE_UNMODIFIED_SOURCE_ACTIONS';save()
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 originals={a.name:snapshot(a) for a in bpy.data.actions}
 need(len(originals)==82,'REFERENCE_NOT_82_ACTIONS_'+str(len(originals)))
 result['stage']='REOPEN_REPAIRED_FILE_COMPARE_CURVES';save()
 bpy.ops.wm.open_mainfile(filepath=str(candidate),load_ui=False)
 problems=[];maxd={'time':0.,'value':0.,'handle':0.};points=0
 for name,source_curves in sorted(originals.items()):
  act=bpy.data.actions.get(name)
  if act is None:problems.append({'name':name,'problem':'MISSING_ACTION'});continue
  need(act.use_fake_user,'PRESERVED_FK_ACTION_LACKS_FAKE_USER_'+name)
  now=snapshot(act)
  if source_curves.keys()!=now.keys():problems.append({'name':name,'problem':'FCURVE_PATHS_CHANGED'});continue
  for key,(extr,src_keys) in source_curves.items():
   other_extr,now_keys=now[key]
   if extr!=other_extr or len(src_keys)!=len(now_keys):problems.append({'name':name,'problem':'COUNT_OR_EXTRAPOLATION_CHANGED','bone':str(key)});continue
   for j,(a,b) in enumerate(zip(src_keys,now_keys)):
    if a[3:]!=b[3:]:problems.append({'name':name,'problem':'INTERPOLATION_CHANGED','key':j});continue
    dt=max(abs(a[0][0]-b[0][0]),0.)
    dv=abs(a[0][1]-b[0][1]);dh=max(abs(a[k][axis]-b[k][axis]) for k in (1,2) for axis in (0,1))
    maxd['time']=max(maxd['time'],dt);maxd['value']=max(maxd['value'],dv);maxd['handle']=max(maxd['handle'],dh);points+=1
    if dt>2e-5 or dv>2e-5 or dh>5e-5:
     if len(problems)<25:problems.append({'name':name,'problem':'KEY_NUMERIC_DRIFT','key':j,'delta':[dt,dv,dh]})
 result['fkCurveComparison']={'referenceActions':82,'comparedPoints':points,'worstDifferences':maxd,'firstProblems':problems[:25],'passed':not problems}
 save();need(not problems,'FK_ACTION_PRESERVATION_FAILED_'+repr(problems[:2]))
 result['stage']='IK41_PRESERVATION_AND_REOPEN_POSE';save()
 arm=bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE');reference=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 need(arm is not None and reference is not None and arm.type==reference.type=='ARMATURE' and arm.data!=reference.data,'REFERENCE_OR_IK_RIG_MISSING')
 need(len(arm.animation_data.nla_tracks)==41,'IK41_NLA_INVENTORY_INVALID')
 need({t.name for t in arm.animation_data.nla_tracks}==set(author['sourceClips']),'IK_CLIP_NAMES_CHANGED')
 need(len([a for a in bpy.data.actions if a.name.startswith('IK41_EDIT__')])==41,'IK41_EDIT_ACTIONS_MISSING')
 for side in ('Left','Right'):
  ctrl=arm.pose.bones.get('CTRL_'+side+'_ANKLE_IK');pole=arm.pose.bones.get('CTRL_'+side+'_KNEE_POLE')
  need(ctrl and pole and not ctrl.bone.use_deform and not pole.bone.use_deform,'CONTROLS_MISSING_'+side)
  shin=arm.pose.bones['mixamorig:'+side+'Leg'];foot=arm.pose.bones['mixamorig:'+side+'Foot']
  ik=shin.constraints.get('IK41_TWO_BONE_'+side);rot=foot.constraints.get('IK41_FOOT_ROT_'+side)
  need(ik and ik.type=='IK' and ik.chain_count==2 and ik.target==arm and ik.subtarget==ctrl.name and ik.pole_target==arm and ik.pole_subtarget==pole.name and not ik.use_stretch,'IK_CHAIN_INVALID_'+side)
  need(rot and rot.type=='COPY_ROTATION' and rot.target==arm and rot.subtarget==ctrl.name,'FOOT_ROTATION_INVALID_'+side)
  need(ik.influence==1. and rot.influence==1.,'IK_NOT_ALWAYS_ON_'+side)
 worst={'ankleM':0.,'kneeM':0.,'footDeg':0.};tested=0;expected_samples=0
 for name,entry in author['newActions'].items():
  track=arm.animation_data.nla_tracks.get(name);need(track and len(track.strips)==1,'IK_ACTION_TRACK_MISSING_'+name)
  strip=track.strips[0];act=strip.action
  need(act and act.name==entry['action'] and strip.action_slot is not None,'IK_ACTION_SLOT_OR_ID_INVALID_'+name)
  need(len([fc for fc in curves(act) if 'CTRL_' in fc.data_path])>=18,'IK_CONTROL_CHANNELS_MISSING_'+name)
  fk=bpy.data.actions.get(entry['sourceAction']);need(fk,'FK_FOR_REOPEN_MISSING_'+name)
  times=sorted({round(float(p.co.x),5) for fc in curves(fk) for p in fc.keyframe_points})
  need(times,'SOURCE_KEY_TIMES_MISSING_'+name)
  sample_times=sorted(set((times[0],times[len(times)//2],times[-1])))
  expected_samples+=len(sample_times)
  for t in sample_times:
   for side in ('Left','Right'):
    arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=0
    arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=0
   play(arm,fk,strip.action_slot.identifier);frame(t)
   source_poses={side:(arm.pose.bones['mixamorig:'+side+'Foot'].matrix.copy(),arm.pose.bones['mixamorig:'+side+'Leg'].head.copy()) for side in ('Left','Right')}
   for side in ('Left','Right'):
    arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=1
    arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=1
   play(arm,act,strip.action_slot.identifier);frame(t)
   for side in ('Left','Right'):
    foot=arm.pose.bones['mixamorig:'+side+'Foot'];knee=arm.pose.bones['mixamorig:'+side+'Leg']
    gold,kpos=source_poses[side]
    vals={'ankleM':float((foot.matrix.translation-gold.translation).length),'kneeM':float((knee.head-kpos).length),
      'footDeg':float(math.degrees(foot.matrix.to_quaternion().rotation_difference(gold.to_quaternion()).angle))}
    for k in worst:worst[k]=max(worst[k],vals[k])
   tested+=1
 limits=author['poseParity']['limits']
 result['actualIKWorst']=worst;result['actualIKPoseSamples']=tested;result['IKClipCount']=41;save()
 result['expectedIKPoseSamples']=expected_samples;save()
 need(expected_samples==121,'PINNED_41_CLIP_SAMPLE_CENSUS_CHANGED_'+str(expected_samples))
 need(tested==expected_samples,'REOPEN_POSE_SAMPLE_COUNT_MISMATCH_'+str(tested)+'_'+str(expected_samples))
 for k in worst:need(worst[k]<=limits[k],'REOPEN_POSE_EXCEEDS_ORIGINAL_LIMIT_'+k+'_'+str(worst[k]))
 need(sha(source)==SRC_SHA and sha(candidate)==repair['outputSHA256'],'REOPEN_INPUTS_CHANGED_DURING_VERIFY')
 result.update(status='VERIFIED_41_IK_NATIVE_REOPEN_OWNER_VISUAL_PENDING',stage='COMPLETE',ownerVisualAcceptance='PENDING');save()
 print('IK41_REOPEN_VERIFIED='+str(tested)+' '+json.dumps(worst),flush=True)
except BaseException as exc:
 result.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc()[-3500:]);save();raise
