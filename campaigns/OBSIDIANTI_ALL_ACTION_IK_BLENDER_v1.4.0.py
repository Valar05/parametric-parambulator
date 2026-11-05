#!/usr/bin/env python3
"""Read-only native Blender source sampler; all Lionheart actions, full evaluated bone transforms."""
import argparse, hashlib, json, math, os, re, sys
import bpy
from mathutils import Matrix

VERSION='OBSIDIANTI_ALL_ACTION_IK_v1.4.0'
ACTION_NAMES=('Idle','Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
CONTROL_NAMES=('LeftFoot.IK','RightFoot.IK','LeftKnee.IK','RightKnee.IK')
DEF_NAMES=('mixamorig:Hips','mixamorig:LeftUpLeg','mixamorig:LeftLeg','mixamorig:LeftFoot','mixamorig:LeftToeBase','mixamorig:RightUpLeg','mixamorig:RightLeg','mixamorig:RightFoot','mixamorig:RightToeBase')
WORLD_AXIS=Matrix.Rotation(math.radians(-90),4,'X')

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def mat44(m):return [[round(float(m[i][j]),9) for j in range(4)] for i in range(4)]
def vector(v):return [round(float(v[i]),9) for i in range(3)]
def quat(m):
    q=m.to_quaternion().normalized()
    return [round(float(q.x),9),round(float(q.y),9),round(float(q.z),9),round(float(q.w),9)]

def action_map():
    seen={}
    for name in ACTION_NAMES:
        exact=[a for a in bpy.data.actions if a.name==name]
        if len(exact)==1:
            seen[name]=exact[0];continue
        variants=[a for a in bpy.data.actions if re.sub(r'(?:_(?:Armature|rig))?(?:\.\d+)?$','',a.name,flags=re.I)==name]
        if len(variants)!=1:raise RuntimeError('MISSING_OR_AMBIGUOUS_LIONHEART_ACTION:'+name)
        seen[name]=variants[0]
    return seen

def sample_frame(arm,frame,allnames):
    scene=bpy.context.scene
    scene.frame_set(int(math.floor(frame)),subframe=float(frame-math.floor(frame)))
    bpy.context.view_layer.update()
    dep=bpy.context.evaluated_depsgraph_get()
    evalarm=arm.evaluated_get(dep)
    result={}
    for name in allnames:
        pb=evalarm.pose.bones.get(name)
        if pb is None:raise RuntimeError('EVALUATED_BONE_MISSING:'+name)
        # Blender evaluated pose (constraints ON) to glTF Y-up model world, metres.
        mat=WORLD_AXIS @ evalarm.matrix_world @ pb.matrix
        result[name]={'worldPosition':vector(mat.translation),'worldQuaternion':quat(mat), 'worldMatrixRowMajor':mat44(mat)}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--expected-sha256',required=True)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if digest(args.source)!=args.expected_sha256:raise RuntimeError('SOURCE_BLEND_SHA256_MISMATCH')
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.source))
    arms=[x for x in bpy.data.objects if x.type=='ARMATURE' and len(x.pose.bones)>=26]
    if len(arms)!=1:raise RuntimeError('SOURCE_ARMATURE_CARDINALITY_MISMATCH')
    arm=arms[0]; action_by_name=action_map();names=sorted(b.name for b in arm.pose.bones)
    missing=[x for x in (*CONTROL_NAMES,*DEF_NAMES) if x not in names]
    if missing:raise RuntimeError('REQUIRED_IK_OR_DEFORM_BONES_MISSING:'+repr(missing))
    fps=float(bpy.context.scene.render.fps)/float(bpy.context.scene.render.fps_base)
    if fps<10 or fps>120:raise RuntimeError('SOURCE_FPS_OUT_OF_RANGE')
    ad=arm.animation_data_create();originalAction=ad.action
    for track in ad.nla_tracks:track.mute=True
    ad.use_nla=False
    # Source rest matrices, lengths and native constraints are preserved in the output.
    rest={}
    for pb in arm.pose.bones:
        bone=pb.bone
        restworld=WORLD_AXIS @ arm.matrix_world @ bone.matrix_local
        rest[pb.name]={
            'parent':pb.parent.name if pb.parent else None,
            'boneLengthMetres':round(float(bone.length*sum(abs(v) for v in arm.matrix_world.to_scale())/3),9),
            'worldRestPosition':vector(restworld.translation),
            'worldRestQuaternion':quat(restworld),
            'worldRestMatrixRowMajor':mat44(restworld),
            'constraints':[{'name':c.name,'type':c.type,'influence':round(float(c.influence),7),
                'targetObject':c.target.name if hasattr(c,'target') and c.target else None,
                'subtarget':str(c.subtarget) if hasattr(c,'subtarget') else None,
                'poleObject':c.pole_target.name if hasattr(c,'pole_target') and c.pole_target else None,
                'poleSubtarget':str(c.pole_subtarget) if hasattr(c,'pole_subtarget') else None,
                'chainCount':int(c.chain_count) if hasattr(c,'chain_count') else None} for c in pb.constraints]
        }
    root=os.path.abspath(args.output);os.makedirs(os.path.join(root,'actions'),exist_ok=True)
    manifest={'schema':'obsidianti-lionheart-ik-native-all-actions-v1','version':VERSION,
      'sourceSha256':args.expected_sha256,'blenderVersion':bpy.app.version_string,'fps':fps,
      'objectTransformWorldRowMajor':mat44(arm.matrix_world),'sourceAxis':'Blender Z-up converted to glTF Y-up',
      'units':'metres','restPose':rest,'actionNames':list(ACTION_NAMES),'samplePhase':'each integer and half frame',
      'sourceGeometryEvaluated':False,'controllerToSoleContactValidated':False}
    with open(os.path.join(root,'source-rig.json'),'w') as f:json.dump(manifest,f,separators=(',',':'),sort_keys=True)
    for name,action in action_by_name.items():
        ad.action=action
        start,end=(float(x) for x in action.frame_range)
        if name=='Idle':start=end=-1.0
        if end-start>400 or end<start:raise RuntimeError('SOURCE_ACTION_RANGE_INVALID:'+name)
        frames=sorted(set([start,end]+[start+.5*i for i in range(1,int(math.floor((end-start)*2))+1) if start+.5*i<end]))
        if name!='Idle' and len(frames)<3:raise RuntimeError('SOURCE_TOO_FEW_ACTION_KEYS:'+name)
        seq=[]
        for frame in frames:
            poses=sample_frame(arm,frame,names)
            hip=poses['mixamorig:Hips']['worldPosition']
            relations={}
            for side in ('Left','Right'):
                ctrl=poses[side+'Foot.IK']['worldPosition']
                ankle=poses['mixamorig:'+side+'Foot']['worldPosition']
                knee=poses[side+'Knee.IK']['worldPosition']
                relations[side]={
                  'footControllerRelativePelvisMetres':[round(x-y,9) for x,y in zip(ctrl,hip)],
                  'ankleRelativePelvisMetres':[round(x-y,9) for x,y in zip(ankle,hip)],
                  'controllerToEvaluatedAnkleMetres':[round(x-y,9) for x,y in zip(ankle,ctrl)],
                  'kneePoleRelativePelvisMetres':[round(x-y,9) for x,y in zip(knee,hip)]
                }
            seq.append({'sourceFrame':round(frame,7),'timeSeconds':round((frame-start)/fps,9),
                        'bones':poses,'legsRelativePelvis':relations})
        out={'action':name,'sourceAction':action.name,'sourceFrameRange':[start,end],
              'sourceFPS':fps,'durationSeconds':round((end-start)/fps,9),
              'frameCount':len(seq),'frames':seq}
        path=os.path.join(root,'actions',name+'.json')
        with open(path,'w') as f:json.dump(out,f,separators=(',',':'))
        print('EVALUATED_ACTION='+name+' FRAMES='+str(len(seq)),flush=True)
    ad.action=originalAction
    print('ALL_LIONHEART_ACTIONS_EVALUATED='+str(len(action_by_name)),flush=True)

if __name__=='__main__':main()
