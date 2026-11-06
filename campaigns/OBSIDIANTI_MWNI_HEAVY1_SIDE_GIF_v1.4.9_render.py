#!/usr/bin/env python3
"""Render exactly the existing Mwni Heavy1 editable .blend, not an exported GLB.
Blender 4.3.x in existing Termux Debian. No model/animation mutation or re-retargeting.
"""
from __future__ import annotations
import bpy, argparse, json, math, pathlib, sys, traceback
from mathutils import Vector

EXPECTED_ACTION = 'SmartRigArmature|Heavy1'
JOINTS = ('LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot',
          'LeftArm','LeftForeArm','RightArm','RightForeArm','Spine2')

def transform(obj, name):
    return obj.matrix_world @ obj.pose.bones['mixamorig:'+name].matrix.translation

def localq(obj, part):
    b=obj.pose.bones['mixamorig:'+part]
    rel=b.parent.matrix.inverted_safe() @ b.matrix if b.parent else b.matrix
    return rel.to_quaternion().normalized()

def target_armature():
    options=[o for o in bpy.data.objects if o.type=='ARMATURE'
       and all('mixamorig:'+p in o.pose.bones for p in JOINTS)
       and 'LeftFoot.IK' not in o.pose.bones]
    if len(options)!=1:
        raise RuntimeError('EXACT_TARGET_ARMATURE_UNRESOLVED '+repr([(o.name,len(o.pose.bones)) for o in options]))
    return options[0]

def skinned_meshes(arm):
    return [o for o in bpy.data.objects if o.type=='MESH' and
       (o.parent==arm or any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers))]

def main(args):
    out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=False)
    evidence={'status':'BOOT','source':str(args.blend),'action':EXPECTED_ACTION,
              'render':'EXACT_SAVED_BLENDER_SCENE_SIDE_ON_NOT_GLB','samples':[]}
    def save(): (out/'RENDER.json').write_text(json.dumps(evidence,indent=2)+'\n')
    save()
    try:
        if bpy.app.version[:2] != (4,3):raise RuntimeError('REQUIRES_BLENDER_4_3 '+bpy.app.version_string)
        bpy.ops.wm.open_mainfile(filepath=args.blend,load_ui=False)
        arm=target_armature();meshes=skinned_meshes(arm)
        if not meshes:raise RuntimeError('TARGET_SKIN_MISSING')
        actions=[a for a in bpy.data.actions if a.name==EXPECTED_ACTION]
        if len(actions)!=1:raise RuntimeError('SAVED_HEAVY1_BAKED_ACTION_UNRESOLVED '+repr([a.name for a in bpy.data.actions]))
        action=actions[0]
        if not any('pose.bones[' in fc.data_path for fc in action.fcurves):raise RuntimeError('BAKED_HEAVY1_HAS_NO_BONE_FCURVES')
        ad=arm.animation_data_create();ad.use_nla=False
        for track in ad.nla_tracks:track.mute=True
        ad.action=action
        arm.data.pose_position='POSE'
        # Saved Mwni add-on trial disables its drivers at end; no retarget solver is invoked.
        for ob in bpy.data.objects:
            if ob.type in ('MESH','CURVE','FONT'):
                ob.hide_render=ob not in meshes
            elif ob.type=='ARMATURE': ob.hide_render=ob!=arm
        for mesh in meshes:mesh.hide_render=False
        scene=bpy.context.scene
        start=int(round(action.frame_range[0]));end=int(round(action.frame_range[1]))
        if end-start<4 or end-start>180:raise RuntimeError('HEAVY1_ACTION_DURATION_INVALID '+repr(action.frame_range[:]))
        scene.frame_start=start;scene.frame_end=end;scene.render.fps=30;scene.render.fps_base=1
        evidence.update({'targetArmature':arm.name,'targetMeshes':[o.name for o in meshes],
                         'blenderVersion':bpy.app.version_string,'actionFrames':[start,end],
                         'bakedFcurveCount':len(action.fcurves),'camera':'WORLD_POSITIVE_X_SIDE_PROFILE',
                         'framesRequested':24})
        # Determine body framing from ACTUAL skinned geometry in three evaluated poses.
        limits=[]
        for frame in [start,(start+end)//2,end]:
            scene.frame_set(frame);bpy.context.view_layer.update()
            deps=bpy.context.evaluated_depsgraph_get()
            for ob in meshes:
                ev=ob.evaluated_get(deps);me=ev.to_mesh()
                try:
                    # sample all vertices for accurate frame/camera without guessing object origin
                    if len(me.vertices)==0:continue
                    pos=[ev.matrix_world @ v.co for v in me.vertices]
                    limits.extend((min(p.y for p in pos),max(p.y for p in pos),
                                   min(p.z for p in pos),max(p.z for p in pos)))
                finally:ev.to_mesh_clear()
        # Parsing per-mesh extents in Y/Z above: values repeat every 4 elements.
        if not limits or len(limits)%4:raise RuntimeError('CANNOT_FRAME_REAL_SKINNED_GEOMETRY')
        y_min=min(limits[i] for i in range(0,len(limits),4));y_max=max(limits[i] for i in range(1,len(limits),4))
        z_min=min(limits[i] for i in range(2,len(limits),4));z_max=max(limits[i] for i in range(3,len(limits),4))
        z_min=min(z_min,-.08)
        width=max(.6,y_max-y_min);height=max(.6,z_max-z_min)
        # Equal vertical/horizontal pixel scale; substantial margin prevents foot crop.
        ortho=max(width,height)*1.28
        cy=(y_min+y_max)/2;cz=(z_min+z_max)/2
        cam_data=bpy.data.cameras.new('Heavy1 FIXED side +X camera')
        cam=bpy.data.objects.new('Heavy1 FIXED side +X camera',cam_data)
        scene.collection.objects.link(cam);cam_data.type='ORTHO';cam_data.ortho_scale=ortho
        cam.location=(10,cy,cz)
        cam.rotation_euler=(Vector((0,cy,cz))-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.camera=cam
        # Constant floor marker at imported target's original world Z=0, not following hips.
        bpy.ops.mesh.primitive_cube_add(size=1,location=(0,cy,-.015))
        floor=bpy.context.object;floor.name='FIXED_REFERENCE_FLOOR_Z0';floor.dimensions=(.1,max(ortho*1.2,3.0),.03)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        floor.hide_render=False
        scene.render.engine='BLENDER_WORKBENCH'
        scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
        scene.display.shading.show_shadows=True
        scene.display.shading.show_cavity=True
        scene.display.shading.show_object_outline=True
        scene.display.shading.background_type='WORLD'
        scene.world.color=(.10,.14,.20)
        scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='BMP';scene.render.image_settings.color_mode='RGB'
        scene.render.film_transparent=False
        initial={}
        fs=[]
        for i in range(24):
            f=start+(end-start)*(i/23)
            scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
            joints={p:localq(arm,p) for p in JOINTS}
            if not initial:initial=joints.copy()
            degrees={p:round(math.degrees(q.rotation_difference(initial[p]).angle),3) for p,q in joints.items()}
            feet={p:[round(x,5) for x in transform(arm,p)] for p in ('LeftFoot','RightFoot','Hips')}
            framefile=out/('frame_%03d.bmp'%i)
            scene.render.filepath=str(framefile);bpy.ops.render.render(write_still=True)
            if not framefile.is_file() or framefile.stat().st_size<50000:raise RuntimeError('ACTUAL_FRAME_RENDER_MISSING '+str(framefile))
            fs.append({'index':i,'frame':round(f,5),'file':framefile.name,'feetAndHipsWorld':feet,'localExcursionDeg':degrees})
        evidence.update({'status':'SIDE_PROFILE_FRAMES_RENDERED_FROM_SAVED_BLEND',
           'frameFiles':[f['file'] for f in fs], 'samples':fs,
           'maxJointExcursionsDeg':{p:max(f['localExcursionDeg'][p] for f in fs) for p in JOINTS},
           'framing':{'horizontalWorldAxis':'Y','verticalWorldAxis':'Z','fixedFloorZ':0,'orthographicScale':ortho,
                      'worldYBounds':[y_min,y_max],'worldZBounds':[z_min,z_max]}})
        save()
        print('BLENDER_SIDE_RENDER=24_TRUE_SAVED_BLEND_FRAMES',flush=True)
    except Exception as exc:
        evidence.update({'status':'BLOCKED','error':str(exc),'traceback':traceback.format_exc()[-4800:]})
        save();raise

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--blend',required=True);ap.add_argument('--output',required=True)
    main(ap.parse_args(sys.argv[sys.argv.index('--')+1:]))
