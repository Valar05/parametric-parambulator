"""Read back real Blender .blend and compare original GLB reference to editable rig."""
import bpy,sys,json,pathlib,math,collections
p,report_path,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=p,load_ui=False)
r=json.loads(pathlib.Path(report_path).read_text())
ref=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT');edit=bpy.data.objects.get('OBSIDIANTI_IK_EDITABLE')
assert ref and edit and ref.type==edit.type=='ARMATURE' and ref.data!=edit.data,'ARMATURE_ISOLATION_FAILED'
assert r.get('sourceMotionAuthority')=='EXACT_OBSIDIANTI_v1.5.6_GLB_ONLY' and r.get('donorRead') is False,'DONOR_MOTION_PROHIBITED'
assert r.get('glbClipCount',0)>=23,'REFERENCE_CLIPS_NOT_PRESERVED'
assert len(r.get('editableActions',{}))==10,'NOT_ALL_TEN_EDITABLE_ACTIONS'
assert len(r.get('sourceActions',{}))==10,'ORIGINAL_ACTION_ASSOCIATIONS_MISSING'
for side in ('Left','Right'):
    shin=edit.pose.bones['mixamorig:'+side+'Leg'];foot=edit.pose.bones['mixamorig:'+side+'Foot']
    ik=[c for c in shin.constraints if c.type=='IK' and c.chain_count==2 and c.target==edit and abs(c.influence-1)<1e-8]
    rot=[c for c in foot.constraints if c.type=='COPY_ROTATION' and c.target==edit and abs(c.influence-1)<1e-8]
    assert len(ik)==len(rot)==1,'IK_NOT_FULLY_ENABLED_'+side
    for label in ('ANKLE_IK','KNEE_POLE'):
        pb=edit.pose.bones.get('CTRL_'+side+'_'+label)
        assert pb and not pb.bone.use_deform,'CONTROL_MISSING_OR_DEFORMING'
assert all(c.type not in ('IK','COPY_ROTATION') for b in ref.pose.bones for c in b.constraints),'FK_REFERENCE_MODIFIED'
assert r['physicalParity']['sampling']=='ALL_SOURCE_GLB_KEY_TIMES_AND_MIDPOINTS'
check={}
for move,data in r['editableActions'].items():
    src=bpy.data.actions.get(data['sourceFKAction']);dst=bpy.data.actions.get(data['action'])
    assert src and dst,'SOURCE_OR_EDITABLE_ACTION_MISSING_'+move
    def collect(a):
        try:fc=list(a.fcurves)
        except (AttributeError,RuntimeError):fc=[]
        if not fc:
            for layer in getattr(a,'layers',[]):
                for strip in getattr(layer,'strips',[]):
                    for bag in getattr(strip,'channelbags',[]):fc+=list(getattr(bag,'fcurves',[]))
        return fc
    orig={ (fc.data_path,fc.array_index):[(round(float(k.co.x),6),round(float(k.co.y),6),k.interpolation) for k in fc.keyframe_points] for fc in collect(src) }
    copied={ (fc.data_path,fc.array_index):[(round(float(k.co.x),6),round(float(k.co.y),6),k.interpolation) for k in fc.keyframe_points] for fc in collect(dst) if not fc.data_path.startswith('pose.bones["CTRL_') }
    if orig!=copied:raise RuntimeError('ORIGINAL_FK_FCURVES_CHANGED_'+move)
    allowed={round(x,5) for x in r['sourceActions'][move]['sourceKeyFrames']}
    for ctrl,keys in data['controllerKeys'].items():
        if not keys or not set(round(x,5) for x in keys).issubset(allowed):raise RuntimeError('CONTROLLER_NOT_SOURCE_KEY_ALIGNED_'+move+'_'+ctrl)
    check[move]={'sourceCurveCount':len(orig),'editableCurveCount':len(collect(dst)),
                 'controllerKeyCounts':{n:len(ts) for n,ts in data['controllerKeys'].items()}}
status='REOPENED_AND_PHYSICALLY_VALIDATED' if r['physicalParity']['passed'] else 'REOPENED_QUARANTINED_PHYSICAL_PARITY_FAILED'
result={'readbackStatus':status,'actions':check,'ikConstraints':2,'footRotationConstraints':2,
        'sourceGLBOnly':True,'originalFKSourcesUntouched':True,'physicalParity':r['physicalParity']}
pathlib.Path(out).write_text(json.dumps(result,indent=2)+'\n')
print('BLENDER_NATIVE_REOPEN='+status,flush=True)
