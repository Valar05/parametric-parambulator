"""Blender 4.x: inspect both native .blend files, then create a separate sparse-key IK authoring copy.
Never save either original .blend or the input GLB. Existing imported FK clips remain on a
separate locked reference rig. IK and its controllers exist on a duplicate editing rig.
"""
import bpy,sys,json,pathlib,math,traceback,collections
from mathutils import Vector,Matrix
args=sys.argv[sys.argv.index('--')+1:]
source_blend,target_blend,model_glb,out_blend,out_report=args
report={'schema':'obsidianti-native-ik-author-v1.9.0','status':'STARTED','source':source_blend,'target':target_blend,'inputGLB':model_glb,'warnings':[]}
def save_report():pathlib.Path(out_report).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
def action_keys(action):
    keys=set();channels=0
    try:
        curves=list(action.fcurves)
    except (AttributeError,RuntimeError):curves=[]
    if not curves:
        for layer in getattr(action,'layers',[]):
            for strip in getattr(layer,'strips',[]):
                for bag in getattr(strip,'channelbags',[]):curves.extend(list(getattr(bag,'fcurves',[])))
    for fc in curves:
        channels+=1
        for kp in fc.keyframe_points:keys.add(round(float(kp.co.x),6))
    return sorted(keys),channels

def native_inventory(path,label):
    bpy.ops.wm.open_mainfile(filepath=path,load_ui=False)
    arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
    inventory={'filepath':path,'armatures':[],'actions':{},'fps':bpy.context.scene.render.fps,'fpsBase':bpy.context.scene.render.fps_base}
    for o in arms:
        bones=[]
        for pb in o.pose.bones:
            constraints=[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None),'subtarget':getattr(c,'subtarget',None),'chainCount':getattr(c,'chain_count',None),'mute':c.mute,'influence':c.influence} for c in pb.constraints]
            bones.append({'name':pb.name,'deform':pb.bone.use_deform,'constraints':constraints})
        inventory['armatures'].append({'name':o.name,'bones':bones,'boneCount':len(bones),'objectScale':list(o.scale),'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None})
    for a in bpy.data.actions:
        ks,c=action_keys(a)
        inventory['actions'][a.name]={'range':list(map(float,a.frame_range)),'keyTimes':ks,'uniqueKeyCount':len(ks),'fcurveCount':c}
    report[label]=inventory
    save_report()
    return inventory

try:
    donor=native_inventory(source_blend,'lionheartNative')
    native_target=native_inventory(target_blend,'obsidiantiNative')
    if not any(x['boneCount']>=25 for x in donor['armatures']):raise RuntimeError('LIONHEART_SOURCE_ARMATURE_NOT_FOUND')
    if not any(x['boneCount']>=25 for x in native_target['armatures']):raise RuntimeError('OBSIDIANTI_SOURCE_ARMATURE_NOT_FOUND')
    if not any(c['type']=='IK' for arm in donor['armatures'] for b in arm['bones'] for c in b['constraints']):raise RuntimeError('LIONHEART_EXPECTED_NATIVE_IK_MISSING')
    # Action assignment uses actual source names, not assumptions about the initial pose.
    moves=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
    source_actions={}
    for move in moves:
        found=[(name,data) for name,data in donor['actions'].items() if name==move or name.endswith('_'+move) or name.endswith('|'+move) or name.endswith('.'+move)]
        if len(found)!=1:raise RuntimeError('NATIVE_SOURCE_ACTION_MISSING_OR_AMBIGUOUS '+move+' '+str([x[0] for x in found]))
        name,data=found[0];keys=data['keyTimes']
        if not keys:raise RuntimeError('NATIVE_SOURCE_ACTION_HAS_NO_KEYFRAMES '+move)
        a,b=data['range'];keys=sorted(set(keys+[a,b]))
        source_actions[move]={'actualName':name,'sourceFrameRange':[a,b],'keys':keys,'durationSeconds':(b-a)/(donor['fps']/donor['fpsBase'])}
    report['actionKeyPlan']=source_actions
    save_report()

    # Imported GLB is not the native source .blend. This FK rig is a preserved reference.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=donor['fps'];bpy.context.scene.render.fps_base=donor['fpsBase']
    bpy.ops.import_scene.gltf(filepath=model_glb)
    refs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    if len(refs)!=1:raise RuntimeError('IMPORTED_GLB_ARMATURE_COUNT_INVALID '+str(len(refs)))
    ref=refs[0];ref.name='OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT'
    ref_actions={a.name:a for a in bpy.data.actions}
    for a in ref_actions.values():a.use_fake_user=True
    required=['mixamorig:'+side+part for side in ('Left','Right') for part in ('UpLeg','Leg','Foot')]
    for n in required:
        if n not in ref.pose.bones:raise RuntimeError('TARGET_BONE_MISSING '+n)
    allclips={move:ref_actions.get('Lionheart_'+move) for move in moves}
    if any(a is None for a in allclips.values()):raise RuntimeError('TARGET_GLB_ACTIONS_MISSING '+str([n for n,a in allclips.items() if a is None]))
    # Keep the original reference model, all its animations and its own armature untouched.
    ref.hide_render=True;ref.hide_set(True)
    for obj in bpy.context.scene.objects:
        if obj.type=='MESH' and (obj.parent==ref or any(m.type=='ARMATURE' and m.object==ref for m in obj.modifiers)):
            obj.hide_render=True;obj.hide_set(True)
    author=ref.copy();author.data=ref.data.copy();bpy.context.collection.objects.link(author)
    author.name='OBSIDIANTI_IK_EDITABLE';author.hide_set(False);author.hide_render=False
    # Clone meshes, linking geometry/material data but not transforming / altering originals.
    cloned=[]
    for obj in list(bpy.context.scene.objects):
        if obj.type!='MESH' or obj in cloned:continue
        if not (obj.parent==ref or any(m.type=='ARMATURE' and m.object==ref for m in obj.modifiers)):continue
        cp=obj.copy();cp.data=obj.data.copy();bpy.context.collection.objects.link(cp)
        cp.name='EDIT_'+obj.name;cp.hide_set(False);cp.hide_render=False
        if obj.parent==ref:cp.parent=author;cp.matrix_parent_inverse=obj.matrix_parent_inverse.copy()
        for mod in cp.modifiers:
            if mod.type=='ARMATURE' and mod.object==ref:mod.object=author
        cloned.append(cp)
    author.animation_data_clear();author.animation_data_create()
    # Actual shin IK plus independent foot orientation target on same action/armature.
    bpy.ops.object.select_all(action='DESELECT');author.select_set(True);bpy.context.view_layer.objects.active=author
    bpy.ops.object.mode_set(mode='EDIT')
    control_names={}
    for side in ('Left','Right'):
        u=author.data.edit_bones['mixamorig:'+side+'UpLeg']
        k=author.data.edit_bones['mixamorig:'+side+'Leg']
        f=author.data.edit_bones['mixamorig:'+side+'Foot']
        # These controls are in armature coordinates, detached from root/pelvis travel.
        a=f'CTRL_{side}_ANKLE_IK';p=f'CTRL_{side}_KNEE_POLE'
        ankle=author.data.edit_bones.new(a);ankle.head=f.head.copy();ankle.tail=f.head+Vector((0,0,.12));ankle.use_deform=False
        pole=author.data.edit_bones.new(p)
        knee=k.head.copy();ank=f.head.copy();upper=u.head.copy()
        axis=(knee-(upper+ank)*.5)
        if axis.length<.0001:axis=Vector((0,0,1))
        axis.normalize();pole.head=knee+axis*.42;pole.tail=pole.head+Vector((0,0,.12));pole.use_deform=False
        control_names[side]=(a,p)
    bpy.ops.object.mode_set(mode='POSE')
    for side in ('Left','Right'):
        a,p=control_names[side]
        shin=author.pose.bones['mixamorig:'+side+'Leg']
        ik=shin.constraints.new('IK');ik.name='AUTHOR_NativeTwoBoneIK_'+side
        ik.target=author;ik.subtarget=a;ik.chain_count=2;ik.influence=1;ik.use_stretch=False
        ik.pole_target=author;ik.pole_subtarget=p;ik.pole_angle=0
        foot=author.pose.bones['mixamorig:'+side+'Foot']
        copy=foot.constraints.new('COPY_ROTATION');copy.name='AUTHOR_FootOrientation_'+side
        copy.target=author;copy.subtarget=a;copy.target_space='WORLD';copy.owner_space='WORLD'
    bpy.ops.object.mode_set(mode='OBJECT')
    report['ikEditRig']={'armature':author.name,'referenceArmature':ref.name,'controls':control_names,'constraintCount':4,'referenceClipCount':len(ref_actions)}
    save_report()

    fps=donor['fps']/donor['fpsBase']
    scene=bpy.context.scene;scene.render.fps=donor['fps'];scene.render.fps_base=donor['fpsBase']
    result={}
    for move in moves:
        source=source_actions[move];key_frames=source['keys'];ref_action=allclips[move]
        if not ref.animation_data:ref.animation_data_create()
        ref.animation_data.action=ref_action
        # Capture sampled *existing* motion before applying any new constraints on author.
        samples=[]
        for key in key_frames:
            t=(key-source['sourceFrameRange'][0])/fps
            scene.frame_set(0,subframe=0)
            # GLB imports at 24fps/30fps depending on Blender; convert source seconds to scene seconds.
            seconds_frame=t*scene.render.fps/scene.render.fps_base
            f=math.floor(seconds_frame);scene.frame_set(f,subframe=seconds_frame-f)
            bpy.context.view_layer.update()
            joints={}
            for b in ref.pose.bones:
                m=b.matrix_basis.copy();joints[b.name]=m
            legs={}
            for side in ('Left','Right'):
                up=ref.pose.bones['mixamorig:'+side+'UpLeg'];knee=ref.pose.bones['mixamorig:'+side+'Leg'];ft=ref.pose.bones['mixamorig:'+side+'Foot']
                hip=up.head.copy();kp=knee.head.copy();ankle=ft.head.copy()
                v=kp-(hip+ankle)*.5
                if v.length<.001:v=Vector((0,0,1))
                v.normalize()
                pole=kp+v*.42
                legs[side]={'anklePose':ft.matrix.copy(),'polePoint':pole,'knee':kp.copy()}
            samples.append((key,joints,legs))
        # One distinct Action per authoring clip, containing native original source key times.
        act=bpy.data.actions.new('EDITABLE_IK_'+move);act.use_fake_user=True
        author.animation_data.action=act
        for key,joints,legs in samples:
            scene.frame_set(math.floor(key),subframe=key-math.floor(key))
            for pb in author.pose.bones:
                if pb.name.startswith('CTRL_'):continue
                if pb.name not in joints:continue
                if any(pb.name=='mixamorig:'+side+part for side in ('Left','Right') for part in ('UpLeg','Leg','Foot')):continue
                loc,q,scale=joints[pb.name].decompose()
                pb.rotation_mode='QUATERNION';pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
                pb.keyframe_insert(data_path='location',frame=key,group=pb.name)
                pb.keyframe_insert(data_path='rotation_quaternion',frame=key,group=pb.name)
            for side in ('Left','Right'):
                a,p=control_names[side];ankle=author.pose.bones[a];pole=author.pose.bones[p]
                # Controller bone rest transform is subtracted automatically by pose.matrix assignment.
                ankle.matrix=legs[side]['anklePose'].copy()
                pole_m=pole.matrix.copy();pole_m.translation=legs[side]['polePoint'];pole.matrix=pole_m
                bpy.context.view_layer.update()
                for ctrl in (ankle,pole):
                    ctrl.rotation_mode='QUATERNION'
                    ctrl.keyframe_insert(data_path='location',frame=key,group=ctrl.name)
                    if ctrl==ankle:ctrl.keyframe_insert(data_path='rotation_quaternion',frame=key,group=ctrl.name)
        result[move]={'action':act.name,'originalSourceKeyCount':len(key_frames),'sourceKeys':key_frames,'originalTargetReference':ref_action.name,'nativeIKEditable':True}
    report['editableActions']=result
    report['caveat']='Sparse reconstruction keyed at donor-authored times; source and target curves differ between keys. Native donor IK is not cloned; new target IK constraints require visual calibration.'
    # Match a normal clip range, with controller-visible author rig on scene and source FK hidden.
    author.animation_data.action=bpy.data.actions['EDITABLE_IK_Heavy1']
    scene.frame_start=int(min(source_actions['Heavy1']['keys']));scene.frame_end=int(max(source_actions['Heavy1']['keys']))
    # Text block documents how to switch: all controls share the same single armature Action.
    text=bpy.data.texts.new('READ_ME_OBSIDIANTI_IK.txt')
    text.write('EDITABLE IK AUTHORING COPY, not an approved retarget.\n')
    text.write('Choose OBSIDIANTI_IK_EDITABLE, open Dope Sheet > Action Editor, select EDITABLE_IK_<move>.\n')
    text.write('Each action keys the original donor keyframe times, not every sampled frame.\n')
    text.write('CTRL_Left/Right_ANKLE_IK and CTRL_Left/Right_KNEE_POLE are nondeforming editable controls.\n')
    text.write('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT retains the original imported baked clips.\n')
    text.write('IMPORTANT: Animation authored keys are a sparse reconstruction of existing GLB playback, NOT original Lionheart F-curves.\n')
    text.write('Original target and donor .blend files were inspected read-only; no source overwrite.\n')
    text.write('IK pole angle and native keyframe interpolation need owner visual review and refinement.\n')
    bpy.ops.wm.save_as_mainfile(filepath=out_blend,check_existing=False,compress=True)
    report['outputBlend']=out_blend;report['status']='IK_EDIT_AUTHORING_COPY_CREATED_REVIEW_PENDING';save_report()
except Exception as e:
    report['status']='BLOCKED';report['error']=type(e).__name__+': '+str(e);save_report();traceback.print_exc();raise
