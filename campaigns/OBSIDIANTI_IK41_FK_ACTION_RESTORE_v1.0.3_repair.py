"""Restore only source FK actions lost on save, without rebuilding IK animation.
Blender 5, input: source.blend candidate.blend output.blend repair_report.json
"""
import bpy, sys, pathlib, hashlib, json, traceback
SRC_SHA='30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27'
OLD_SHA='f594543e098f553d02f09d7dcbdcd3019bc15181a8d513e64a5d98a0f3ad429a'
src,candidate,out,report=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:])
result={'campaign':'OBSIDIANTI_IK41_FK_ACTION_RESTORE_v1.0.3','status':'STARTED','sourceSHA256':SRC_SHA,'oldCandidateSHA256':OLD_SHA,'ownerVisualAcceptance':'PENDING'}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def need(x,msg):
 if not x:raise RuntimeError(msg)
def save():report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
try:
 save()
 need(src.is_file() and sha(src)==SRC_SHA,'PINNED_REFERENCE_BINARY_INVALID')
 need(candidate.is_file() and sha(candidate)==OLD_SHA,'PINNED_IK_BINARY_INVALID')
 need(not out.exists(),'NEW_OUTPUT_COLLISION')
 # The library load does not modify the reference blend file.
 with bpy.data.libraries.load(str(src),link=False) as (available,_):
  reference_names=list(available.actions)
 need(len(reference_names)==82,'REFERENCE_ACTIONS_NOT_82_'+str(len(reference_names)))
 bpy.ops.wm.open_mainfile(filepath=str(candidate),load_ui=False)
 prior_ik={a.name for a in bpy.data.actions if a.name.startswith('IK41_EDIT__')}
 need(len(prior_ik)==41,'EXISTING_IK41_ACTIONS_NOT_41_'+str(len(prior_ik)))
 need(bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT') and bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE'),'MISSING_REFERENCE_OR_EDIT_RIG')
 present=set(a.name for a in bpy.data.actions)
 missing=set(reference_names)-present
 need(missing,'NO_MISSING_ACTIONS_REQUIRES_NO_RECOVERY')
 need(all(name.startswith('FK_EDITABLE__') for name in missing),'UNEXPECTED_MISSING_ORIGINAL_ACTIONS_'+repr(sorted(missing)[:5]))
 result.update(missingCount=len(missing),missingActions=sorted(missing),referenceActionCount=len(reference_names),ikActionCount=len(prior_ik))
 save()
 with bpy.data.libraries.load(str(src),link=False) as (data_from,data_to):
  need(missing.issubset(set(data_from.actions)),'SOURCE_MISSING_REQUIRED_FK_ACTION')
  data_to.actions=sorted(missing)
 restored=list(data_to.actions)
 need(len(restored)==len(missing) and all(a is not None for a in restored),'ACTION_APPEND_INCOMPLETE')
 need({a.name for a in restored}==missing,'ACTION_APPEND_NAMES_CHANGED')
 for action in bpy.data.actions:
  if action.name in reference_names:
   action.use_fake_user=True
 need(set(reference_names).issubset({a.name for a in bpy.data.actions}),'FK_ACTION_INVENTORY_INCOMPLETE')
 need(prior_ik=={a.name for a in bpy.data.actions if a.name.startswith('IK41_EDIT__')},'IK_ACTION_NAMES_CHANGED')
 # Preserve independent reference model and editable rig, original animation channels and NLA.
 arm=bpy.data.objects['OBSIDIANTI_FK_FEET_EDITABLE']
 need(len(arm.animation_data.nla_tracks)==41,'IK_NLA_COUNT_CHANGED')
 # Fake users keep original data blocks in the saved file even if they are not selected in an NLA track.
 result['restoredActionsHaveFakeUsers']=all(bpy.data.actions[n].use_fake_user for n in missing)
 need(result['restoredActionsHaveFakeUsers'],'RESTORED_ACTION_NOT_PERSISTENT')
 out.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=False)
 need(out.stat().st_size>1_000_000,'BLEND_SAVE_TOO_SMALL')
 result.update(status='RESTORED_ACTIONS_SAVED_UNAPPROVED',outputSHA256=sha(out),outputBytes=out.stat().st_size,sourceUnchanged=sha(src)==SRC_SHA,candidateUnchanged=sha(candidate)==OLD_SHA)
 save()
 print('RESTORED_NATIVE_BLEND='+str(out)+' SHA256='+result['outputSHA256']+' RESTORED_ACTIONS='+str(len(missing)),flush=True)
except BaseException as e:
 result.update(status='BLOCKED',error=str(e),traceback=traceback.format_exc()[-3200:]);save();raise
