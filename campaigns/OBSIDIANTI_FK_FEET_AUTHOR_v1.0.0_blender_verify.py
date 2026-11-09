"""Independent Blender re-open verifier for FK feet authoring copy."""
import bpy,sys,json,pathlib,hashlib
f,audit,output=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:])
a=json.loads(audit.read_text());assert a['status']=='BLENDER_SAVED_UNAPPROVED',a['status']
bpy.ops.wm.open_mainfile(filepath=str(f),load_ui=False)
ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
rig=bpy.data.objects.get('OBSIDIANTI_FK_FEET_EDITABLE')
assert ref and rig and ref.type==rig.type=='ARMATURE' and ref.data!=rig.data
assert rig.get('SOURCE_SHA256')==a['sourceSHA256']
for n in a['footBones'].values():
    b=rig.pose.bones[n]
    assert b.bone.get('FK_FOOT_CONTROL')=='TRUE'
    assert not any(c.type=='IK' for c in b.constraints)
assert sum(1 for x in bpy.data.actions if x.name.startswith('FK_EDITABLE__'))>=a['uniqueActionCopies']
assert hashlib.sha256(f.read_bytes()).hexdigest()==a['outputSHA256']
result={'status':'REOPENED_FK_FEET_VERIFIED','sha256':a['outputSHA256'],'footBones':a['footBones'],
'originalAnimationCount':a['inputAnimationCount'],'ownerVisualAcceptance':'PENDING'}
output.write_text(json.dumps(result,indent=2)+'\n')
print('REOPEN_VERIFIED',result,flush=True)
