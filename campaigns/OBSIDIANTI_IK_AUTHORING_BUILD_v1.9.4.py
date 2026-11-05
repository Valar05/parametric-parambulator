"""Obsidianti native GLB FK -> editable constrained IK, preserving original animation data.
No Lionheart input. No donor key times. Every original FK animation remains unchanged.
Only controller keys are synthesized; inverse-kinematic alignment is independently measured.
"""
import bpy,sys,json,pathlib,math,traceback,collections
from mathutils import Vector,Matrix
P=sys.argv[sys.argv.index('--')+1:]
model_glb,out_blend,out_report=P
MOVES=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
SIDES=('Left','Right')
report={'schema':'obsidianti-fk-to-ik-authoring-v1.9.4','status':'STARTED','inputGLB':model_glb,
        'sourceMotionAuthority':'EXACT_OBSIDIANTI_v1.5.6_GLB_ONLY','donorRead':False,
        'warnings':[],'originalFKPreserved':True}
def save():pathlib.Path(out_report).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
def curves(action):
    try: result=list(action.fcurves)
    except (AttributeError,RuntimeError):result=[]
    if not result:
        for layer in getattr(action,'layers',[]):
            for strip in getattr(layer,'strips',[]):
                for bag in getattr(strip,'channelbags',[]):result+=list(getattr(bag,'fcurves',[]))
    return result
def key_times(action):
    result=set()
    for fc in curves(action):
        for kp in fc.keyframe_points:result.add(round(float(kp.co.x),6))
    return sorted(result)
def resolve(rig):
    ad=rig.animation_data;items=[]
    for t in ad.nla_tracks:
        for strip in t.strips:
            if strip.action:items.append((t.name,strip.name,strip.action))
    if ad.action:items.append(('__ACTIVE__','__ACTIVE__',ad.action))
    clips={}
    for move in MOVES:
        target='Lionheart_'+move
        candidates={id(a):a for track,strip,a in items if target in (track,strip,a.name)}
        if len(candidates)!=1:raise RuntimeError('GLB_IMPORT_CLIP_IDENTITY_INVALID '+target+' '+str([(t,s,a.name) for t,s,a in items]))
        clips[move]=next(iter(candidates.values()))
    return clips,items
def settime(t):
    scene=bpy.context.scene;k=math.floor(t);scene.frame_set(k,subframe=t-k)
def difft(a,b):return (a.translation-b.translation).length
def rotdeg(a,b):return math.degrees(a.to_quaternion().rotation_difference(b.to_quaternion()).angle)
def snapshot(ref,side):
    up=ref.pose.bones['mixamorig:'+side+'UpLeg'];knee=ref.pose.bones['mixamorig:'+side+'Leg'];foot=ref.pose.bones['mixamorig:'+side+'Foot']
    h=up.head.copy();k=knee.head.copy();f=foot.head.copy()
    line=f-h
    if line.length<.005:raise RuntimeError('SOURCE_DEGENERATE_LEG '+side)
    axial=h+line*(max(0.,min(1.,(k-h).dot(line)/line.length_squared)))
    normal=k-axial
    if normal.length<.001:
        normal=Vector((1,0,0)) if side=='Left' else Vector((-1,0,0))
    normal.normalize()
    pole=k+normal*max(.25, line.length*.7)
    return {'foot':foot.matrix.copy(),'knee':k,'hip':h,'pole':pole}
def control_pose(author,side,row):
    ap=author.pose.bones['CTRL_'+side+'_ANKLE_IK']
    pole=author.pose.bones['CTRL_'+side+'_KNEE_POLE']
    # The ankle control is built with EXACTLY the source foot's rest matrix.
    # Its unparented pose matrix therefore equals the animated foot's armature-space matrix.
    ap.matrix=row['foot'].copy()
    pm=pole.bone.matrix_local.copy();pm.translation=row['pole'];pole.matrix=pm
    bpy.context.view_layer.update()
def match(ref,author,side,row):
    de=bpy.context.evaluated_depsgraph_get()
    b=author.evaluated_get(de)
    kn=b.pose.bones['mixamorig:'+side+'Leg']
    ft=b.pose.bones['mixamorig:'+side+'Foot']
    # Position/rotation of actual joint matrices, not proxy controller error.
    return {'ankle_m':difft(ft.matrix,row['foot']),
            'foot_deg':rotdeg(ft.matrix,row['foot']),
            'knee_m':(kn.head-row['knee']).length}
def choose_pole_angle(author,ref,side,representative):
    con=next(c for c in author.pose.bones['mixamorig:'+side+'Leg'].constraints if c.type=='IK')
    # Full sweep of pole angle; choose one calibration for the ENTIRE side across ALL clips.
    best=(1e30,None,{})
    for i in range(48):
        theta=-math.pi+2*math.pi*i/48
        con.pole_angle=theta
        errs=[]
        for action,t,row in representative:
            author.animation_data.action=action;settime(t)
            control_pose(author,side,row)
            e=match(ref,author,side,row)
            errs.append(e)
        score=sum(e['knee_m']**2+e['ankle_m']**2*3 for e in errs)/len(errs)
        if score<best[0]:best=(score,theta,{'avgKnee_m':sum(e['knee_m'] for e in errs)/len(errs),
                                            'avgAnkle_m':sum(e['ankle_m'] for e in errs)/len(errs)})
    con.pole_angle=best[1]
    return {'radians':best[1],**best[2],'score':best[0]}
def reduce_path(rows,tolpos=.0015,tolrot=.5):
    # Geometric adaptive reduction of controller samples. Never invent key times.
    # Return source GLB sample indices only; final full-pose check remains authoritative.
    if len(rows)<=2:return list(range(len(rows)))
    keep={0,len(rows)-1}
    def err(i,a,b):
        t0,ma=rows[a];t1,mb=rows[b];t,m=rows[i]
        u=max(0.,min(1.,(t-t0)/max(1e-8,t1-t0)))
        pos=ma.translation.lerp(mb.translation,u)
        qa=ma.to_quaternion();qb=mb.to_quaternion()
        if qa.dot(qb)<0:qb.negate()
        q=qa.slerp(qb,u)
        d=(m.translation-pos).length/tolpos
        r=math.degrees(q.rotation_difference(m.to_quaternion()).angle)/tolrot
        return max(d,r)
    todo=[(0,len(rows)-1)]
    while todo:
        a,b=todo.pop()
        if b-a<=1:continue
        k=max(range(a+1,b),key=lambda i:err(i,a,b))
        if err(k,a,b)>1.0:keep.add(k);todo.extend([(a,k),(k,b)])
    return sorted(keep)
def scalar_matrix_at(p):return p.matrix.copy()
try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)
    scene=bpy.context.scene
    refarms=[o for o in scene.objects if o.type=='ARMATURE']
    if len(refarms)!=1:raise RuntimeError('GLB_ARMATURE_COUNT_NOT_ONE '+str(len(refarms)))
    ref=refarms[0];ref.name='OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT'
    originals={a.name:a for a in bpy.data.actions}
    if len(originals)<23:raise RuntimeError('GLB_ANIMATIONS_NOT_ALL_PRESENT '+str(len(originals)))
    for act in originals.values():act.use_fake_user=True
    clips,associations=resolve(ref)
    report['glbClipCount']=len(originals)
    report['sourceActions']={n:{'importedAction':a.name,'sourceKeyCount':len(key_times(a)),
                                 'sourceKeyFrames':[round(t,5) for t in key_times(a)],
                                 'durationFrames':list(map(float,a.frame_range))} for n,a in clips.items()}
    report['importedNLAInventory']=[{'track':x,'strip':y,'action':z.name} for x,y,z in associations]
    if ref.animation_data:
        for t in ref.animation_data.nla_tracks:t.mute=True
        ref.animation_data.use_nla=False
    for side in SIDES:
        for part in ('UpLeg','Leg','Foot'):
            if 'mixamorig:'+side+part not in ref.pose.bones:raise RuntimeError('LEG_BONE_MISSING')
    # Keep exact FK source skeleton/actions and all original mesh data intact.
    author=ref.copy();author.data=ref.data.copy();scene.collection.objects.link(author)
    author.name='OBSIDIANTI_IK_EDITABLE';author.animation_data_clear();author.animation_data_create()
    meshes=[]
    for obj in list(scene.objects):
        if obj.type!='MESH':continue
        if obj.parent!=ref and not any(m.type=='ARMATURE' and m.object==ref for m in obj.modifiers):continue
        dup=obj.copy();dup.data=obj.data.copy();scene.collection.objects.link(dup)
        dup.name='EDIT_'+obj.name
        if dup.parent==ref:dup.parent=author;dup.matrix_parent_inverse=obj.matrix_parent_inverse.copy()
        for m in dup.modifiers:
            if m.type=='ARMATURE' and m.object==ref:m.object=author
        obj.hide_render=True;obj.hide_set(True)
        meshes.append(dup.name)
    ref.hide_set(True);ref.hide_render=True
    bpy.ops.object.select_all(action='DESELECT');author.select_set(True);bpy.context.view_layer.objects.active=author
    bpy.ops.object.mode_set(mode='EDIT')
    for side in SIDES:
        f=author.data.edit_bones['mixamorig:'+side+'Foot']
        k=author.data.edit_bones['mixamorig:'+side+'Leg']
        up=author.data.edit_bones['mixamorig:'+side+'UpLeg']
        ctrl=author.data.edit_bones.new('CTRL_'+side+'_ANKLE_IK')
        ctrl.matrix=f.matrix.copy();ctrl.length=f.length;ctrl.use_deform=False
        # Parentless controller, sharing the foot bind-frame exactly.
        pole=author.data.edit_bones.new('CTRL_'+side+'_KNEE_POLE')
        h=up.head.copy();kn=k.head.copy();ft=f.head.copy()
        d=ft-h
        bend=(kn-(h+d*(kn-h).dot(d)/max(d.length_squared,1e-6)))
        if bend.length<.001:bend=Vector((0,0,1))
        pole.head=kn+bend.normalized()*.45
        pole.tail=pole.head+Vector((0,0,.1));pole.use_deform=False
    bpy.ops.object.mode_set(mode='POSE')
    for side in SIDES:
        shin=author.pose.bones['mixamorig:'+side+'Leg']
        c=shin.constraints.new('IK');c.name='AUTHOR_TWO_BONE_IK_'+side
        c.target=author;c.subtarget='CTRL_'+side+'_ANKLE_IK';c.chain_count=2
        c.use_stretch=False;c.influence=1.0
        c.pole_target=author;c.pole_subtarget='CTRL_'+side+'_KNEE_POLE'
        c.pole_angle=0.0
        foot=author.pose.bones['mixamorig:'+side+'Foot']
        rot=foot.constraints.new('COPY_ROTATION');rot.name='AUTHOR_FOOT_ORIENTATION_'+side
        rot.target=author;rot.subtarget='CTRL_'+side+'_ANKLE_IK'
        rot.target_space='POSE';rot.owner_space='POSE';rot.mix_mode='REPLACE'
    bpy.ops.object.mode_set(mode='OBJECT')
    report['sourceRig']='OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT'
    report['editableRig']='OBSIDIANTI_IK_EDITABLE'
    report['meshesCloned']=meshes
    # Create editable actions as DATA COPIES of actual target GLB imported Actions.
    # Not a fresh sparse recreation from Lionheart. This preserves pelvis, torso, weapon,
    # foot and all other existing FK FCurves, including their original interpolation.
    edit={}
    for move,src in clips.items():
        a=src.copy();a.name='EDITABLE_IK_'+move;a.use_fake_user=True
        edit[move]=a
    # Collect evaluated matrices of the actual target at every original GLB key and midpoint.
    samples={};reps={side:[] for side in SIDES}
    for move,src in clips.items():
        ref.animation_data.action=src
        times=key_times(src)
        if not times:raise RuntimeError('SOURCE_GLB_ACTION_HAS_NO_KEYS '+move)
        combined=sorted(set(times+[(x+y)/2 for x,y in zip(times,times[1:])]))
        frames=[]
        for t in combined:
            settime(t);bpy.context.view_layer.update()
            frame={'t':t,'legs':{side:snapshot(ref,side) for side in SIDES}}
            frames.append(frame)
        samples[move]=frames
        # Equal time-weighted representative sampling from all 10 actions.
        for side in SIDES:
            for item in frames[::max(1,len(frames)//4)][:4]:
                reps[side].append((edit[move],item['t'],item['legs'][side]))
    report['sampling']={move:len(frames) for move,frames in samples.items()}
    # Temporary control pose keys used for pole calibration. Stored on NO published action.
    # Original FK channels are preserved on edit copies throughout.
    for move,frames in samples.items():
        author.animation_data.action=edit[move]
        for item in frames:
            settime(item['t'])
            for side in SIDES:control_pose(author,side,item['legs'][side])
    calib={}
    for side in SIDES:calib[side]=choose_pole_angle(author,ref,side,reps[side])
    report['poleCalibration']=calib
    save()
    # Keys for actual FK animation are NEVER rewritten; only CTRL_* channels added.
    for move,frames in samples.items():
        action=edit[move];author.animation_data.action=action
        times=key_times(clips[move])
        keyed={}
        for side in SIDES:
            for which in ('ANKLE_IK','KNEE_POLE'):
                name='CTRL_'+side+'_'+which
                rows=[]
                for item in frames:
                    t=item['t']
                    if not any(abs(t-k)<1e-5 for k in times):continue
                    row=item['legs'][side]
                    m=row['foot'] if which=='ANKLE_IK' else Matrix.Translation(row['pole'])
                    rows.append((t,m))
                chosen=reduce_path(rows,tolpos=.0008,tolrot=.25)
                keyed[name]=[rows[i][0] for i in chosen]
                prevq=None
                for i in chosen:
                    t=rows[i][0];settime(t)
                    pb=author.pose.bones[name]
                    control_pose(author,side,next(item['legs'][side] for item in frames if abs(item['t']-t)<1e-5))
                    pb.rotation_mode='QUATERNION'
                    if prevq is not None and pb.rotation_quaternion.dot(prevq)<0:pb.rotation_quaternion.negate()
                    prevq=pb.rotation_quaternion.copy()
                    pb.keyframe_insert(data_path='location',frame=t,group=name)
                    if which=='ANKLE_IK':pb.keyframe_insert(data_path='rotation_quaternion',frame=t,group=name)
        for fc in curves(action):
            if not fc.data_path.startswith('pose.bones["CTRL_'):continue
            for kp in fc.keyframe_points:kp.interpolation='LINEAR'
        report.setdefault('editableActions',{})[move]={'action':action.name,'sourceFKAction':clips[move].name,
            'sourceFKKeyCount':len(times),'controllerKeys':keyed,
            'preservedFKSources':True}
    # Validate against the input GLB sampled poses with IK fully enabled.
    # Kinematics/cameras/pole angles may be bad even when the .blend is structurally valid.
    limits={'ankle_m':.012,'knee_m':.018,'foot_deg':5.0}
    checks={};passed=True
    for move,frames in samples.items():
        author.animation_data.action=edit[move]
        action_checks={side:{'ankle_m':0.,'knee_m':0.,'foot_deg':0.,'worstFrame':None} for side in SIDES}
        for item in frames:
            settime(item['t'])
            for side in SIDES:
                observed=match(ref,author,side,item['legs'][side])
                row=action_checks[side]
                for k,v in observed.items():row[k]=max(row[k],v)
                if any(observed[k]>limits[k] for k in limits):row['worstFrame']=item['t'];passed=False
        checks[move]=action_checks
    report['physicalParity']={'passed':passed,'limits':limits,'actions':checks,
        'sampling':'ALL_SOURCE_GLB_KEY_TIMES_AND_MIDPOINTS','constraintInfluence':1.0}
    # A failed contact/pose check is not success. Save quarantined preview for inspection
    # but do not label it verified, approved or publish it as an editable authoring baseline.
    author.animation_data.action=edit['Heavy1']
    scene.frame_start=int(math.floor(min(key_times(clips['Heavy1']))))
    scene.frame_end=int(math.ceil(max(key_times(clips['Heavy1']))))
    note=bpy.data.texts.new('READ_ME_OBSIDIANTI_IK.txt')
    note.write('Original Obsidianti GLB is the ONLY motion source. Original FK Actions remain unchanged.\n')
    note.write('EDITABLE_IK_* are COPIES of original target Actions with controller channels added.\n')
    note.write('The new controller trajectories were sampled from actual Obsidianti foot/knee matrices.\n')
    note.write('FK -> IK pose parity metrics are in the accompanying report; reject failures.\n')
    note.write('Do not confuse structure or sparse keys with correct physical IK.\n')
    bpy.ops.wm.save_as_mainfile(filepath=out_blend,check_existing=False,compress=False)
    report['outputBlend']=out_blend
    report['status']='IK_EDITABLE_POSE_PARITY_PASSED' if passed else 'IK_EDITABLE_POSE_PARITY_FAILED_UNAPPROVED'
    save()
    print('GLB_FK_TO_IK='+report['status'],flush=True)
except Exception as exc:
    report['status']='BLOCKED';report['error']=type(exc).__name__+': '+str(exc);save();traceback.print_exc();raise
