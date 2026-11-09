"""Create a separate FK-foot Blender authoring rig from a SHA-pinned 41-clip GLB.
Never changes the LFS source or baked source actions.
Run in Blender --background --python author.py -- input.glb output.blend audit.json
"""
import bpy, sys, json, pathlib, hashlib, traceback
from collections import Counter

argv = sys.argv[sys.argv.index('--')+1:]
source, output, report = map(pathlib.Path, argv)
EXPECTED='9ff2b5423b4bf5fea1bf67295b52d848803381699fede56164aca9ce65bea9b7'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(ok,msg):
    if not ok:raise RuntimeError(msg)
def write(data):report.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def bonekey(s):return ''.join(c for c in s.lower() if c.isalnum())
def action_fingerprint(a):
    # Counts and data are preserved through copying; verify via native Blender reopen too.
    fc=[]
    try:fc=list(a.fcurves)
    except (AttributeError,RuntimeError):pass
    if not fc:
        for layer in getattr(a,'layers',[]):
            for st in getattr(layer,'strips',[]):
                for bag in getattr(st,'channelbags',[]):
                    fc.extend(list(getattr(bag,'fcurves',[])))
    out=[]
    for f in fc:
        points=[]
        for k in f.keyframe_points:
            points.append([round(float(v),7) for v in k.co])
        out.append([f.data_path,int(f.array_index),points])
    return hashlib.sha256(json.dumps(sorted(out,key=lambda z:(z[0],z[1])),separators=(',',':')).encode()).hexdigest()

data={'campaign':'OBSIDIANTI_FK_FEET_AUTHOR_v1.0.0','status':'STARTED','sourceSHA256':digest(source),'source':str(source),'output':str(output)}
try:
    require(data['sourceSHA256']==EXPECTED,'SOURCE_SHA_MISMATCH')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
    require(len(rigs)==1,'ARMATURE_COUNT_NOT_ONE_'+str(len(rigs)))
    ref=rigs[0];ref.name='OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT'
    all_actions=list(bpy.data.actions)
    imported_nla=[(t.name,s.name,s.action.name) for t in ref.animation_data.nla_tracks for s in t.strips if s.action] if ref.animation_data else []
    require(len(imported_nla)>=41,'GLTF_IMPORTED_NLA_MISSING_'+str(len(imported_nla)))
    require(len({x[2] for x in imported_nla})>=35,'IMPORT_MOTION_SET_INCOMPLETE')
    base_meshes=[o for o in bpy.data.objects if o.type=='MESH' and (o.parent==ref or any(m.type=='ARMATURE' and m.object==ref for m in o.modifiers))]
    require(base_meshes,'NO_ARMATURE_MESHES')
    rig=ref.copy();rig.data=ref.data.copy();bpy.context.collection.objects.link(rig)
    rig.name='OBSIDIANTI_FK_FEET_EDITABLE'
    require(rig.data!=ref.data,'RIG_DATA_NOT_INDEPENDENT')
    copy_meshes=[]
    for obj in base_meshes:
        clone=obj.copy();clone.data=obj.data.copy();bpy.context.collection.objects.link(clone)
        clone.name='FK_EDITABLE__'+obj.name
        if obj.parent==ref:clone.parent=rig
        for modifier in clone.modifiers:
            if modifier.type=='ARMATURE' and modifier.object==ref:modifier.object=rig
        copy_meshes.append(clone)
    # Duplicate all imported action datablocks as separate edit-domain objects.
    mapping={a:a.copy() for a in all_actions}
    for old,new in mapping.items():new.name='FK_EDITABLE__'+old.name
    if rig.animation_data:
        if rig.animation_data.action:
            prev=rig.animation_data.action
            rig.animation_data.action=mapping[prev]
            if hasattr(ref.animation_data,'action_slot') and ref.animation_data.action_slot:
                ident=ref.animation_data.action_slot.identifier
                slot=next((x for x in rig.animation_data.action.slots if x.identifier==ident),None)
                if slot:rig.animation_data.action_slot=slot
        for track in rig.animation_data.nla_tracks:
            for strip in track.strips:
                if strip.action in mapping:strip.action=mapping[strip.action]
    bnames=[b.name for b in rig.data.bones]
    sides={}
    for side in ('left','right'):
        possibles=[s for s in bnames if side+'foot' in bonekey(s) or bonekey(s).endswith('foot'+('l' if side=='left' else 'r'))]
        require(len(possibles)==1,'FK_FOOT_BONE_NOT_UNAMBIGUOUS_'+side+'_'+repr(possibles))
        sides[side]=possibles[0]
    # GLB stores FK deformation-bone rotations. Do NOT create IK constraints and alter those tracks.
    for side,name in sides.items():
        pb=rig.pose.bones[name]
        require(not any(c.type=='IK' for c in pb.constraints),'UNEXPECTED_IMPORTED_FOOT_IK_'+side)
        pb.bone['FK_FOOT_CONTROL']='TRUE'
        pb.bone['FK_AUTHOR_HINT']='Rotate this deformation foot in Pose Mode; key rotations in a NEW editable action.'
        pb.rotation_mode='QUATERNION'
    # Put foot bones into a purpose-labelled authoring collection, not a new constraint system.
    try:
        col=rig.data.collections.new('FK Feet (direct bone rotation)')
        for n in sides.values():col.assign(rig.data.bones[n])
    except AttributeError:
        pass
    ref['ARCHIVE_LOCK']='Do not edit. Original imported 41-clip action library.'
    rig['AUTHORING_SCOPE']='Direct FK feet; independent action copies; no IK constraints required.'
    rig['SOURCE_SHA256']=EXPECTED
    # Hide source model in viewport to prevent double geometry, but retain objects and actions.
    for o in [ref,*base_meshes]:o.hide_set(True);o.hide_render=True
    for o in [rig,*copy_meshes]:o.hide_set(False);o.hide_render=False
    for o in bpy.context.selected_objects:o.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    before=Counter((a.name,action_fingerprint(a)) for a in all_actions)
    result=Counter((old.name,action_fingerprint(new)) for old,new in mapping.items())
    require(before==result,'ACTION_COPY_FCURVE_CONTENT_CHANGED')
    require(len(mapping)>=35,'TOO_FEW_DUPLICATED_ACTIONS')
    data.update(status='BLENDER_SAVED_UNAPPROVED',rigs=[ref.name,rig.name],footBones=sides,
      inputAnimationCount=len(imported_nla),uniqueActionCopies=len(mapping),
      originalNames=[x[1] for x in imported_nla],meshDuplicates=len(copy_meshes),
      originalActionFingerprintParity=True,ownerVisualAcceptance='PENDING')
    bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=False)
    data['outputSHA256']=digest(output)
    write(data)
    print('FK_FEET_SAVED='+str(output)+' SHA256='+data['outputSHA256'],flush=True)
except Exception as exc:
    data.update(status='BLOCKED',error=str(exc),traceback=traceback.format_exc())
    write(data)
    raise
