"""Independent readback of saved .blend, original timing and armature isolation."""
import bpy,sys,json,pathlib,collections
file,report_path,output_path=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=file,load_ui=False)
report=json.loads(pathlib.Path(report_path).read_text())
assert report['status']=='IK_EDIT_AUTHORING_COPY_CREATED_REVIEW_PENDING', 'build incomplete'
ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
auth=bpy.data.objects.get('OBSIDIANTI_IK_EDITABLE')
assert ref and auth and ref.type==auth.type=='ARMATURE', 'two isolated armatures missing'
assert ref.data!=auth.data, 'armature data aliased'
refclips=[d['importedAction'] for d in report['importedClipAssociations'].values()]
assert len(refclips)==10 and len(set(refclips))==10, 'imported original FK clips lost or merged'
for name in refclips:assert bpy.data.actions.get(name) is not None,'missing original FK action '+name
assert not ref.animation_data.use_nla, 'reference NLA still participates in active clip evaluation'
assert all(t.mute for t in ref.animation_data.nla_tracks), 'NLA must be muted for action editing'
checks={}
for move,meta in report['editableActions'].items():
    a=bpy.data.actions.get(meta['action']);assert a is not None,'missing editable action '+move
    intended=set(round(float(t),5) for t in meta['sourceKeys'])
    actual=set()
    try:curves=list(a.fcurves)
    except (AttributeError,RuntimeError):curves=[]
    if not curves:
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:curves.extend(list(bag.fcurves))
    for fc in curves:
        for kp in fc.keyframe_points:actual.add(round(float(kp.co.x),5))
    if actual!=intended:raise RuntimeError('EDITABLE_ACTION_TIMING_CHANGED '+move+' '+str((sorted(actual-intended),sorted(intended-actual))))
    checks[move]={'sparseKeyCount':len(intended),'curveCount':len(curves)}
for side in ('Left','Right'):
    shin=auth.pose.bones['mixamorig:'+side+'Leg']
    foot=auth.pose.bones['mixamorig:'+side+'Foot']
    assert any(c.type=='IK' and c.target==auth and c.chain_count==2 for c in shin.constraints),'missing native target IK '+side
    assert any(c.type=='COPY_ROTATION' and c.target==auth for c in foot.constraints),'missing foot orientation constraint '+side
    for name in ('CTRL_'+side+'_ANKLE_IK','CTRL_'+side+'_KNEE_POLE'):
        assert name in auth.pose.bones and not auth.pose.bones[name].bone.use_deform,'controller missing/deforms '+name
    assert all(c.type!='IK' for pb in ref.pose.bones for c in pb.constraints),'reference skeleton changed IK'
result={'readbackStatus':'PERSISTED_AUTHORING_BLEND_STRUCTURALLY_VERIFIED_NOT_VISUALLY_APPROVED','originalBakedReferenceActionCount':len(refclips),'sparseEditableActions':checks,'nativeIKConstraints':2,'footRotationConstraints':2,'referenceArmatureUnchangedByConstraints':True,'meshObjects':len([o for o in bpy.data.objects if o.type=='MESH']),'warnings':['IK visual quality and interpolation against source still require user review']}
pathlib.Path(output_path).write_text(json.dumps(result,indent=2)+'\n')
print('AUTHORING_BLEND_READBACK_VERIFIED=YES',flush=True)
