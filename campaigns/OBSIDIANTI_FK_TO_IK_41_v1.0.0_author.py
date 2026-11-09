"""Obsidianti 41-action FK->IK authoring; Blender 5 native, preserved source.
Run: blender --background --disable-autoexec --python author.py -- source.blend output.blend report.json
"""
import bpy, sys, json, pathlib, math, hashlib, traceback, collections
from mathutils import Vector, Matrix
SOURCE_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
V='OBSIDIANTI_FK_TO_IK_41_v1.0.0'
src,out,report=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:]); report.parent.mkdir(parents=True,exist_ok=True)
audit={'campaign':V,'stage':'BOOT','status':'STARTED','sourceSHA256':SOURCE_SHA,'ownerVisualAcceptance':'PENDING','newActions':{},'poseParity':{}}
def record():report.write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
def need(x,s):
 if not x:raise RuntimeError(s)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def curves(act):
 try: f=list(act.fcurves)
 except (AttributeError, RuntimeError):f=[]
 if not f:
  for layer in getattr(act,'layers',[]):
   for strip in getattr(layer,'strips',[]):
    for slot in getattr(act,'slots',[]):
     try:bag=strip.channelbag(slot,ensure=False)
     except (TypeError, AttributeError, RuntimeError):bag=None
     if bag:f.extend(list(bag.fcurves))
 return f
def signature(act):
 x=[]
 for f in curves(act):
  x.append((f.data_path,int(f.array_index),[(round(float(p.co.x),6),round(float(p.co.y),6)) for p in f.keyframe_points]))
 return hashlib.sha256(json.dumps(sorted(x),separators=(',',':')).encode()).hexdigest()
def keytimes(act):
 a=set()
 for c in curves(act):
  for p in c.keyframe_points:a.add(round(float(p.co.x),6))
 return sorted(a)
def setframe(f):
 base=math.floor(f);bpy.context.scene.frame_set(base,subframe=float(f-base));bpy.context.view_layer.update()
def slot_for(action, source_slot=None):
 slots=list(action.slots)
 need(slots,'MISSING_ACTION_SLOTS_'+action.name)
 if source_slot:
  v=next((s for s in slots if s.identifier==source_slot.identifier),None)
  if v:return v
 ranked=[]
 for sl in slots:
  n=0
  for layer in action.layers:
   for st in layer.strips:
    try:bag=st.channelbag(sl,ensure=False)
    except (RuntimeError,TypeError,AttributeError):bag=None
    if bag:n+=len(bag.fcurves)
  ranked.append((n,sl))
 best=max(ranked,key=lambda t:t[0]);need(best[0]>10,'EMPTY_ACTION_SLOT_'+action.name)
 return best[1]
def play(arm,act,slot):
 ad=arm.animation_data_create();ad.use_nla=False
 for track in ad.nla_tracks:track.mute=True
 ad.action=act;ad.action_slot=slot
 need(ad.action==act and ad.action_slot==slot,'BAD_SLOT_ASSIGNMENT_'+act.name)
def probe(arm,side):
 bones=arm.pose.bones
 u=bones['mixamorig:'+side+'UpLeg'];k=bones['mixamorig:'+side+'Leg'];f=bones['mixamorig:'+side+'Foot']
 hip=u.head.copy();knee=k.head.copy();ankle=f.head.copy(); axis=ankle-hip
 need(axis.length>.05,'BAD_LEG_LENGTH_'+side)
 proj=hip+axis*max(0,min(1,(knee-hip).dot(axis)/axis.length_squared))
 n=knee-proj
 if n.length<.004:
  # Keep a deterministic fallback in degenerate straight-knee frames.
  n=Vector((1,0,0)) if side=='Left' else Vector((-1,0,0))
 n.normalize()
 return {'foot':f.matrix.copy(),'knee':knee,'hip':hip,'pole':knee+n*max(.3,axis.length*.8)}
def controls(arm,side,pose):
 c=arm.pose.bones['CTRL_'+side+'_ANKLE_IK'];p=arm.pose.bones['CTRL_'+side+'_KNEE_POLE']
 c.matrix=pose['foot'].copy();m=p.bone.matrix_local.copy();m.translation=pose['pole'];p.matrix=m
 bpy.context.view_layer.update()
def error(arm,side,pose):
 ev=arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
 k=ev.pose.bones['mixamorig:'+side+'Leg'];f=ev.pose.bones['mixamorig:'+side+'Foot']
 return {'ankleM':float((f.matrix.translation-pose['foot'].translation).length),
  'kneeM':float((k.head-pose['knee']).length),
  'footDeg':float(math.degrees(f.matrix.to_quaternion().rotation_difference(pose['foot'].to_quaternion()).angle))}
def neutral_fk_for_control(arm):
 for side in ('Left','Right'):
  arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=0
  arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=0
 bpy.context.view_layer.update()
def enable_ik(arm):
 for side in ('Left','Right'):
  arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side].influence=1
  arm.pose.bones['mixamorig:'+side+'Foot'].constraints['IK41_FOOT_ROT_'+side].influence=1
 bpy.context.view_layer.update()
try:
 record(); need(src.exists() and digest(src)==SOURCE_SHA,'PINNED_SOURCE_BLEND_SHA_MISMATCH')
 need(not out.exists(),'OUTPUT_COLLISION');bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 need(bpy.app.version[0]>=4,'BLENDER_4_PLUS_REQUIRED')
 ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 arm=bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE')
 need(ref and arm and ref.type=='ARMATURE' and arm.type=='ARMATURE' and ref.data!=arm.data,'SOURCE_RIGS_MISSING_OR_LINKED')
 need(not any(c.type=='IK' for pb in arm.pose.bones for c in pb.constraints),'BASE_ALREADY_HAS_IK')
 for side in ('Left','Right'):
  for bone in ('UpLeg','Leg','Foot'):need('mixamorig:'+side+bone in arm.pose.bones,'MISSING_BONE_'+side+bone)
 original_actions=set(bpy.data.actions);fingerprints={a.name:signature(a) for a in original_actions};audit['originalActionSignatures']=fingerprints
 ad=arm.animation_data;need(ad,'FK_EDITABLE_ANIMATION_DATA_MISSING')
 clip_sources=[]
 for tr in ad.nla_tracks:
  strips=[s for s in tr.strips if s.action]
  for si,st in enumerate(strips):
   clip_sources.append((tr.name if len(strips)==1 else tr.name+'__'+str(si+1),st.action,st.action_slot if hasattr(st,'action_slot') else None))
 need(len(clip_sources)==41,'FK_ACTION_41_CLIP_INVENTORY_MISMATCH_'+str(len(clip_sources)))
 names=[x[0] for x in clip_sources];need(len(set(names))==41,'DUPLICATE_SOURCE_CLIP_NAMES')
 audit['sourceClips']=names
 audit['stage']='CAPTURE_FK_POSES';record()
 # FK source remains on an independent reference rig throughout sampling.
 ref.hide_set(True);ref.hide_render=True
 arm.hide_set(False);arm.hide_render=False
 sampled={};allaction={}
 for name,act,origslot in clip_sources:
  slot=slot_for(act,origslot);play(arm,act,slot)
  keys=keytimes(act);need(len(keys)>0 and len(keys)<=1200,'INVALID_SOURCE_KEY_COUNT_'+name+'_'+str(len(keys)))
  start,end=keys[0],keys[-1];need(end>=start and end-start<=1200,'INVALID_ACTION_FRAME_RANGE_'+name)
  whole=[float(i) for i in range(math.ceil(start),math.floor(end)+1)]
  halves=[round(start+.5*i,6) for i in range(math.floor(2*(end-start))+1)]
  times=sorted(set(keys+whole+halves+[end]));need(len(times)<=2500,'EXCESS_SAMPLE_GRID_'+name)
  frames=[]
  for t in times:
   setframe(t)
   frames.append({'t':t,'legs':{side:probe(arm,side) for side in ('Left','Right')}})
  sampled[name]=frames
  allaction[name]=(act,slot)
  audit['newActions'][name]={'sourceAction':act.name,'sourceKeyCount':len(keys),'sampleCount':len(times)}
 audit['stage']='INSTALL_INDEPENDENT_IK_CONTROLS';record()
 # Existing FK rig becomes a new IK editable rig in a new BLEND only. All 41 original Actions
 # and the preserved FK reference remain in bpy.data unchanged.
 arm.animation_data_clear();arm.animation_data_create()
 for ob in bpy.context.selected_objects:ob.select_set(False)
 arm.select_set(True);bpy.context.view_layer.objects.active=arm
 bpy.ops.object.mode_set(mode='EDIT')
 for side in ('Left','Right'):
  foot=arm.data.edit_bones['mixamorig:'+side+'Foot'];knee=arm.data.edit_bones['mixamorig:'+side+'Leg']
  ctrl=arm.data.edit_bones.new('CTRL_'+side+'_ANKLE_IK');ctrl.matrix=foot.matrix.copy();ctrl.length=max(.1,foot.length*.8);ctrl.parent=None;ctrl.use_deform=False
  pole=arm.data.edit_bones.new('CTRL_'+side+'_KNEE_POLE');pole.head=knee.head+Vector((0.3 if side=='Left' else -.3,0,0));pole.tail=pole.head+Vector((0,0,.12));pole.parent=None;pole.use_deform=False
 bpy.ops.object.mode_set(mode='POSE')
 arm.show_in_front=True
 for side in ('Left','Right'):
  shin=arm.pose.bones['mixamorig:'+side+'Leg'];con=shin.constraints.new('IK');con.name='IK41_TWO_BONE_'+side
  con.target=arm;con.subtarget='CTRL_'+side+'_ANKLE_IK';con.pole_target=arm;con.pole_subtarget='CTRL_'+side+'_KNEE_POLE';con.pole_angle=0
  con.chain_count=2;con.influence=0;con.iterations=200;con.use_stretch=False
  arm.pose.bones['mixamorig:'+side+'UpLeg'].ik_stretch=0;shin.ik_stretch=0
  foot=arm.pose.bones['mixamorig:'+side+'Foot'];rot=foot.constraints.new('COPY_ROTATION');rot.name='IK41_FOOT_ROT_'+side
  rot.target=arm;rot.subtarget='CTRL_'+side+'_ANKLE_IK';rot.owner_space='WORLD';rot.target_space='WORLD';rot.mix_mode='REPLACE';rot.influence=0
  for kind in ('ANKLE_IK','KNEE_POLE'):
   p=arm.pose.bones['CTRL_'+side+'_'+kind];p.rotation_mode='QUATERNION';p.bone.hide=False;p.bone.use_deform=False
  arm.pose.bones['CTRL_'+side+'_ANKLE_IK'].bone['IK_AUTHORING']='Translate and rotate this target to control the foot.'
  arm.pose.bones['CTRL_'+side+'_KNEE_POLE'].bone['IK_AUTHORING']='Translate to control knee direction.'
 try:
  coll=arm.data.collections.new('IK41 EDIT CONTROLS')
  for side in ('Left','Right'):
   for kind in ('ANKLE_IK','KNEE_POLE'):coll.assign(arm.data.bones['CTRL_'+side+'_'+kind])
 except (AttributeError,RuntimeError):pass
 bpy.ops.object.mode_set(mode='OBJECT')
 audit['stage']='KEY_EVERY_SOURCE_ACTION_INDEPENDENTLY';record()
 new_actions={}
 for name,(orig,origslot) in allaction.items():
  action=orig.copy();action.name='IK41_EDIT__'+name;action.use_fake_user=True
  slot=slot_for(action,origslot);play(arm,action,slot)
  neutral_fk_for_control(arm)
  previous_quat={'Left':None,'Right':None}
  for row in sampled[name]:
   t=row['t'];setframe(t)
   for side in ('Left','Right'):
    controls(arm,side,row['legs'][side])
    ankle=arm.pose.bones['CTRL_'+side+'_ANKLE_IK']
    if previous_quat[side] is not None and ankle.rotation_quaternion.dot(previous_quat[side])<0:
     ankle.rotation_quaternion.negate()
    previous_quat[side]=ankle.rotation_quaternion.copy()
    for kind in ('ANKLE_IK','KNEE_POLE'):
     ctrl=arm.pose.bones['CTRL_'+side+'_'+kind]
     need(ctrl.keyframe_insert(data_path='location',frame=t,group='IK41 '+side),'IK_LOCATION_KEY_FAILED_'+name)
     if kind=='ANKLE_IK':need(ctrl.keyframe_insert(data_path='rotation_quaternion',frame=t,group='IK41 '+side),'IK_ROTATION_KEY_FAILED_'+name)
  # Original action copied without altering FK curves, new controller curves must be populated.
  controlcurves=[fc for fc in curves(action) if 'CTRL_' in fc.data_path]
  need(len(controlcurves)>=18,'IK_ACTION_CONTROLLER_CURVES_MISSING_'+name+'_'+str(len(controlcurves)))
  for fc in controlcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
  new_actions[name]=(action,slot_for(action,slot))
  audit['newActions'][name].update({'action':action.name,'controllerCurveCount':len(controlcurves),'controllerKeyFrames':len(sampled[name]),'fkActionUnmodified':signature(orig)==fingerprints[orig.name]})
  need(audit['newActions'][name]['fkActionUnmodified'],'SOURCE_FK_CURVES_CHANGED_'+name)
 # Pole angle: calibrate one fixed angle PER side across the library; don't bake angle keyframes.
 # Test at diverse poses across clips. This is bounded search, not visual acceptance.
 audit['stage']='CALIBRATE_POLE_ANGLES';record();enable_ik(arm)
 for side in ('Left','Right'):
  reps=[]
  for name,frames in sampled.items():
   for frame in (frames[0],frames[len(frames)//2],frames[-1]):reps.append((name,frame))
  # Bound calibration to 45 samples spread across the 41 clips.
  reps=reps[::max(1,len(reps)//45)][:45]
  constraint=arm.pose.bones['mixamorig:'+side+'Leg'].constraints['IK41_TWO_BONE_'+side]
  best=None
  for k in range(36):
   theta=-math.pi+2*math.pi*k/36;constraint.pole_angle=theta
   score=0
   for name,frame in reps:
    act,slot=new_actions[name];play(arm,act,slot);setframe(frame['t'])
    e=error(arm,side,frame['legs'][side]);score+=e['kneeM']**2+3*e['ankleM']**2
   if best is None or score<best[0]:best=(score,theta)
  constraint.pole_angle=best[1];audit.setdefault('poleCalibration',{})[side]={'angle':best[1],'objective':best[0],'representativeFrames':len(reps)}
 audit['stage']='FULL_POSE_PARITY_ON_ACTUAL_IK';record()
 limits={'ankleM':.012,'kneeM':.025,'footDeg':3.0}
 worst={side:{k:0 for k in limits} for side in ('Left','Right')};bad=[]
 for name,frames in sampled.items():
  act,slot=new_actions[name];play(arm,act,slot)
  for row in frames:
   setframe(row['t'])
   for side in ('Left','Right'):
    e=error(arm,side,row['legs'][side])
    for key in limits:worst[side][key]=max(worst[side][key],e[key])
    if any(e[key]>limits[key] for key in limits):
     if len(bad)<80:bad.append({'clip':name,'frame':row['t'],'side':side,**e})
  audit['newActions'][name]['evaluatedPoseSamples']=len(frames)
 audit['poseParity']={'limits':limits,'worst':worst,'failedSamplesFirst80':bad,'passed':not bool(bad)};record()
 # Fail closed: output only with verified actual-IK pose parity. Original FK source never changed.
 need(not bad,'IK41_ACTUAL_POSE_PARITY_FAILED_'+str(len(bad))+'_FIRST_'+repr(bad[:2]))
 need(all(signature(a)==fingerprints[a.name] for a in original_actions),'ORIGINAL_ACTION_DATA_CHANGED')
 need(len(new_actions)==41,'IK41_ACTION_COUNT_MISMATCH')
 # Playback NLA gets a track for every IK clip; mute all except selected one.
 arm.animation_data.action=None
 for i,(name,(act,slot)) in enumerate(new_actions.items()):
  track=arm.animation_data.nla_tracks.new();track.name=name
  st=track.strips.new(name,int(math.floor(act.frame_range[0])),act)
  st.action_slot=slot
  track.mute=True
 # Assign selected action directly, not NLA. All others remain selectable in Action Editor.
 initial=next((x for x in new_actions if 'Idle' in x),next(iter(new_actions)))
 act,slot=new_actions[initial];play(arm,act,slot)
 for tr in arm.animation_data.nla_tracks:tr.mute=True
 for ob in [ref,*[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('FK_EDITABLE__')]]:
  if ob==ref or ob.parent==ref:ob.hide_set(True);ob.hide_render=True
 arm.hide_set(False);arm.hide_render=False
 for ob in bpy.data.objects:
  if ob.type=='MESH' and ob.name.startswith('FK_EDITABLE__'):ob.hide_set(False);ob.hide_render=False
 arm['IK41_EDITABLE_ACTION_COUNT']=41;arm['IK41_SOURCE_SHA256']=SOURCE_SHA
 arm['IK41_INSTRUCTIONS']='Use IK41_EDIT__ actions in Action Editor; foot and knee controls keyed separately for every motion. Original 41 FK Actions preserved.'
 note=bpy.data.texts.new('OBSIDIANTI_IK41_READ_ME.txt');note.write('All 41 original FK actions are preserved. IK41_EDIT__ actions are independent IK-editable copies.\n')
 note.write('Select OBSIDIANTI_FK_FEET_EDITABLE rig and IK41_EDIT__ action. Select CTRL_Left/Right_ANKLE_IK or KNEE_POLE and edit keys.\n')
 note.write('DO NOT edit reference armature. Export must bake IK to GLB before game use. Owner visual approval pending.\n')
 out.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=False)
 audit.update({'stage':'BLEND_SAVED','status':'IK41_NATIVE_BLEND_VERIFIED_POSE_PARITY_OWNER_VISUAL_PENDING',
   'outputSHA256':digest(out),'outputBytes':out.stat().st_size,'originalFKActionCount':len(original_actions),
   'ikActionCount':len(new_actions),'activePreviewAction':initial,'sourceFileUnchanged':digest(src)==SOURCE_SHA})
 record();print('IK41_SAVED='+str(out)+' SHA256='+audit['outputSHA256'],flush=True)
except BaseException as ex:
 audit.update({'stage':audit.get('stage'),'status':'BLOCKED','error':str(ex),'traceback':traceback.format_exc()[-3200:]});record();raise
