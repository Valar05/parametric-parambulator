#!/usr/bin/env python3
"""Actual Blender IK target/pole constraints, not FK-shim or a surrogate 2-bone solver.

Build a TEMPORARY control rig from target GLB's true bind matrices. Initialize it
from approved combat Idle. Drive it from v1.4 Blender-evaluated native Lionheart
Foot.IK/Knee.IK and foot-roll. Sample solved deform joint rotation data only.
Never save the .blend, export a substitute GLB, or edit the model itself.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, pathlib, sys
import bpy
from mathutils import Matrix, Quaternion, Vector

VER='OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.3'
SIDES=('Left','Right')
PARTS=('UpLeg','Leg','Foot')
G2B=Matrix.Rotation(math.pi/2,4,'X')       # glTF Y-up to Blender Z-up
B2G=G2B.inverted()
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
HEAVY1_SHA='a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4'
CALIB_SHA='b6d23f49c67df7816124362f4b1ee540db5c16a672fbc8c435a7f503ca123336'
MATH_SHA='dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f'

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):
   h.update(chunk)
 return h.hexdigest()

def mat4(flat):return Matrix([flat[i:i+4] for i in range(0,16,4)])
def v3(v):return Vector(v)
def seq(v):return [float(x) for x in v]
def q_bl(q):return Quaternion((q[3],q[0],q[1],q[2]))
def q_json(q):
 q=q.normalized();return [float(q.x),float(q.y),float(q.z),float(q.w)]
def norm(v):
 if v.length<1e-8:raise RuntimeError('SINGULAR_ANATOMICAL_BASIS')
 return v.normalized()
def err(a,b):return (v3(a)-v3(b)).length

def anatomical_basis(hip_q,left_up,right_up,hip_pos):
 lateral=norm(hip_q.inverted() @ (v3(left_up)-v3(right_up)))
 vertical=hip_q.inverted() @ Vector((0,1,0))
 vertical=norm(vertical-lateral*vertical.dot(lateral))
 forward=norm(lateral.cross(vertical))
 vertical=norm(forward.cross(lateral))
 return Matrix((lateral,vertical,forward)).transposed()

def args():
 p=argparse.ArgumentParser()
 for s in ('model','source','calibration','math-helper','report','output'):
  p.add_argument('--'+s,required=True)
 p.add_argument('--amplitude',type=float,default=1.0)
 arg=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 return p.parse_args(arg)

def main():
 a=args()
 if bpy.app.version < (4,0,0):raise RuntimeError('BLENDER_4_REQUIRED_FOR_ACTUAL_IK_CONSTRAINTS')
 for path,expected in ((a.model,MODEL_SHA),(a.source,HEAVY1_SHA),(a.calibration,CALIB_SHA),(a.math_helper,MATH_SHA)):
  if sha(path)!=expected:raise RuntimeError('PINNED_SOURCE_HASH_MISMATCH '+path)
 if not .80<=a.amplitude<=1.08:raise RuntimeError('UNAUTHORIZED_AMPLITUDE')
 spec=importlib.util.spec_from_file_location('h151_pinned_math',a.math_helper)
 M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
 g,b=M.load_glb(a.model)
 source=json.loads(pathlib.Path(a.source).read_text())
 calibration=json.loads(pathlib.Path(a.calibration).read_text())
 if source['action']!='Heavy1' or len(source['frames'])!=61 or calibration['modelSha256']!=MODEL_SHA:raise RuntimeError('INPUT_SEMANTICS_WRONG')
 ids={n.get('name'):i for i,n in enumerate(g['nodes']) if n.get('name')}
 required=['mixamorig:Hips',*(f'mixamorig:{s}{p}' for s in SIDES for p in PARTS)]
 if any(n not in ids for n in required):raise RuntimeError('TARGET_BONES_MISSING')
 idle=next((x for x in g['animations'] if x['name']=='LionheartIdle_UNREVIEWED'),None)
 attack=next((x for x in g['animations'] if x['name']=='Lionheart_Heavy1'),None)
 if not idle or not attack:raise RuntimeError('TARGET_APPROVED_IDLE_OR_HEAVY1_NOT_FOUND')
 # Original rejected attack supplies the LOCKED HIPS CHANNEL ONLY. Leg rotations
 # in that broken clip are never sampled to initialize or solve this rig.
 idle_world=M.global_matrices(g,M.channels(g,b,idle),0.)
 rest_world=M.global_matrices(g,{},0.)
 attack_tracks=M.channels(g,b,attack)
 nodes=g['nodes'];parent={k:i for i,node in enumerate(nodes) for k in node.get('children',[])}
 for s in SIDES:
  u,k,f=[ids[f'mixamorig:{s}{p}'] for p in PARTS]
  if not (parent[k]==u and parent[f]==k and parent[u]==ids['mixamorig:Hips']):raise RuntimeError('TARGET_LEG_PARENTAGE_WRONG')

 bpy.ops.wm.read_factory_settings(use_empty=True)
 armdata=bpy.data.armatures.new('ObsidiantiTemporaryIKData')
 arm=bpy.data.objects.new('ObsidiantiTemporaryIKRig',armdata)
 bpy.context.scene.collection.objects.link(arm)
 bpy.context.view_layer.objects.active=arm
 arm.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT')
 ebmap={}
 for n in required:
  eb=armdata.edit_bones.new(n);ebmap[n]=eb
  matrix=G2B @ mat4(rest_world[ids[n]])
  if (matrix.to_3x3().determinant()<.9):raise RuntimeError('BAD_WORLD_REST_TRANSFORM '+n)
  eb.matrix=matrix
  if n=='mixamorig:Hips':eb.length=.135
  else:
   side='Left' if 'Left' in n else 'Right'
   part=next(p for p in PARTS if n.endswith(p))
   nextn=f'mixamorig:{side}'+{'UpLeg':'Leg','Leg':'Foot','Foot':'ToeBase'}[part]
   if nextn not in ids:raise RuntimeError('NO_NEXT_BONE_LENGTH '+nextn)
   eb.length=(v3([rest_world[ids[nextn]][4*r+3] for r in range(3)])-v3([rest_world[ids[n]][4*r+3] for r in range(3)])).length
   if eb.length<.05:raise RuntimeError('DEGENERATE_BONE_LENGTH '+n)
 for s in SIDES:
  up,leg,foot=(ebmap[f'mixamorig:{s}{p}'] for p in PARTS)
  up.parent=ebmap['mixamorig:Hips'];leg.parent=up;foot.parent=leg
  up.use_connect=False;leg.use_connect=False;foot.use_connect=False
 bpy.ops.object.mode_set(mode='OBJECT')
 for name in required:arm.pose.bones[name].rotation_mode='QUATERNION'
 bpy.context.view_layer.update()
 # The temporary rig's rest geometry MUST match the original GLB rest heads.
 for n in required:
  rest_pos=(G2B@mat4(rest_world[ids[n]])).translation
  actual=arm.data.bones[n].matrix_local.translation
  if (actual-rest_pos).length>.001:raise RuntimeError('BLENDER_BIND_RECONSTRUCTION_FAILED '+n)

 def pbone(n):return arm.pose.bones[n]
 def solve_matrices():
  bpy.context.view_layer.update()
  evalu=arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
  return {n:evalu.pose.bones[n].matrix.copy() for n in required}

 init_hip=mat4(idle_world[ids['mixamorig:Hips']]);init_inv=init_hip.inverted_safe()
 # Ensure initial pose is from ACTUAL APPROVED IDLE, never the rejected FK attack.
 def base_idle_under_hip(hip_gl):
  pbone('mixamorig:Hips').matrix=G2B @ hip_gl
  bpy.context.view_layer.update()
  for s in SIDES:
   for part in PARTS:
    n=f'mixamorig:{s}{part}'
    pbone(n).matrix=G2B @ (hip_gl @ init_inv @ mat4(idle_world[ids[n]]))
    bpy.context.view_layer.update()

 hipnode=ids['mixamorig:Hips']
 node_hip=nodes[hipnode]
 ancestors=[];idx=hipnode
 while idx in parent:
  idx=parent[idx];ancestors.append(idx)
 if any(any(key[0]==idx for key in attack_tracks) for idx in ancestors):raise RuntimeError('ANIMATED_HIP_PARENT_NEEDS_PRESERVATION')
 restParent=mat4(rest_world[parent[hipnode]]) if hipnode in parent else Matrix.Identity(4)
 def locked_hip_at(t):
  T=M.sampled(*attack_tracks[(hipnode,'translation')],t) if (hipnode,'translation') in attack_tracks else node_hip.get('translation',[0,0,0])
  Q=M.sampled(*attack_tracks[(hipnode,'rotation')],t,True) if (hipnode,'rotation') in attack_tracks else node_hip.get('rotation',[0,0,0,1])
  S=node_hip.get('scale',[1,1,1])
  if (hipnode,'scale') in attack_tracks:S=M.sampled(*attack_tracks[(hipnode,'scale')],t)
  return restParent@mat4(M.mat_trs(T,Q,S))
 hip0=locked_hip_at(0.)
 base_idle_under_hip(hip0)
 before=solve_matrices()
 for n in required:
  desired=hip0 @ init_inv @ mat4(idle_world[ids[n]])
  if n=='mixamorig:Hips':desired=hip0
  if (before[n].translation-(G2B@desired).translation).length>.003:
   raise RuntimeError('APPROVED_IDLE_IMPORT_MISMATCH '+n)
  angle=before[n].to_quaternion().rotation_difference((G2B@desired).to_quaternion()).angle
  if angle>.05:raise RuntimeError('APPROVED_IDLE_BONE_AXIS_ROTATION_MISMATCH '+n+' '+str(angle))

 frame0=source['frames'][0]['bones'];qsh=q_bl(frame0['mixamorig:Hips']['worldQuaternion'])
 qth=init_hip.to_quaternion()
 source_basis=anatomical_basis(qsh,frame0['mixamorig:LeftUpLeg']['worldPosition'],frame0['mixamorig:RightUpLeg']['worldPosition'],frame0['mixamorig:Hips']['worldPosition'])
 target_basis=anatomical_basis(qth,(mat4(idle_world[ids['mixamorig:LeftUpLeg']])).translation,(mat4(idle_world[ids['mixamorig:RightUpLeg']])).translation,init_hip.translation)
 align=target_basis@source_basis.transposed()
 if abs(align.determinant()-1)>1e-5:raise RuntimeError('ANATOMICAL_MAPPING_REFLECTED')
 # Both target and source hip-local axes must agree on left/right and upward.
 if (align@source_basis.col[0]-target_basis.col[0]).length>.001:raise RuntimeError('LATERAL_AXIS_MAPPING_WRONG')
 hipLocal={}
 for s in SIDES:
  nm=f'mixamorig:{s}Foot'
  idleFoot=mat4(idle_world[ids[nm]])
  hipLocal[s]={'foot':init_inv@idleFoot,'ankle':(init_inv@idleFoot).translation,
               'knee':(init_inv@mat4(idle_world[ids[f'mixamorig:{s}Leg']])).translation}

 def goals(row,hip_pose):
  output={}
  for side in SIDES:
   controller=row['bones'][side+'Foot.IK']; controller0=frame0[side+'Foot.IK']
   ankle=row['bones'][f'mixamorig:{side}Foot']; ankle0=frame0[f'mixamorig:{side}Foot']
   pole=row['bones'][side+'Knee.IK']
   # WORLD delta is authoritative. The source pelvis's large world translation
   # is excluded from this six-track transfer, because target pelvis is LOCKED.
   worldDelta=v3(controller['worldPosition'])-v3(controller0['worldPosition'])
   # Native evaluated ankle offset, independent of source hip and any pole error.
   residual=(v3(ankle['worldPosition'])-v3(controller['worldPosition']))-(v3(ankle0['worldPosition'])-v3(controller0['worldPosition']))
   scale=float(calibration['legRatios'][side]['combinedRatio'])*a.amplitude
   target_local=hipLocal[side]['ankle']+align@(worldDelta+residual)*scale
   poleLever=v3(pole['worldPosition'])-v3(controller['worldPosition'])
   pole_local=target_local+align@poleLever*scale
   # Map the source foot's WORLD rotation delta into the target anatomical basis.
   source_delta=(q_bl(ankle['worldQuaternion'])@q_bl(ankle0['worldQuaternion']).inverted()).normalized()
   mapped_delta=(align@source_delta.to_matrix()@align.transposed()).to_quaternion()
   idle_target_world=(hip_pose.to_quaternion()@hipLocal[side]['foot'].to_quaternion()).normalized()
   qworld=(mapped_delta@idle_target_world).normalized()
   output[side]={'ankleWorld':hip_pose@target_local,'poleWorld':hip_pose@pole_local,
       'footWorldRot':qworld, 'sourceDelta':worldDelta.length,
       'poleSeparation':(pole_local-target_local).length}
  return output

 # These empties genuinely drive Blender's IK constraints (not skinned controls).
 controls={}
 for s in SIDES:
  for label in ('FootTarget','KneePole','FootRotation'):
   obj=bpy.data.objects.new(s+label,None);bpy.context.scene.collection.objects.link(obj);obj.empty_display_type='PLAIN_AXES';controls[s,label]=obj
  ik=pbone(f'mixamorig:{s}Leg').constraints.new('IK')
  ik.target=controls[s,'FootTarget'];ik.pole_target=controls[s,'KneePole'];ik.chain_count=2;ik.influence=1.;ik.use_stretch=False
  rot=pbone(f'mixamorig:{s}Foot').constraints.new('COPY_ROTATION')
  rot.target=controls[s,'FootRotation'];rot.owner_space='WORLD';rot.target_space='WORLD';rot.influence=1.
  try:rot.mix_mode='REPLACE'
  except Exception:pass
  controls[s,'constraint']=ik

 def apply_targets(go):
  for s in SIDES:
   ctrl=go[s]
   controls[s,'FootTarget'].location=G2B.to_3x3()@ctrl['ankleWorld']
   controls[s,'KneePole'].location=G2B.to_3x3()@ctrl['poleWorld']
   controls[s,'FootRotation'].rotation_mode='QUATERNION'
   rot=(G2B.to_quaternion()@ctrl['footWorldRot']).normalized()
   controls[s,'FootRotation'].rotation_quaternion=rot
  bpy.context.view_layer.update()

 # At t=0 a physically valid Blender pole angle MUST reproduce the approved
 # knee location while keeping the desired ankle. Scan the actual Blender IK
 # constraint, not a hand-authored analytic pole-plane substitute.
 g0=goals(source['frames'][0],hip0)
 apply_targets(g0)
 pole_calibration={}
 for s in SIDES:
  con=controls[s,'constraint'];kn=f'mixamorig:{s}Leg';ft=f'mixamorig:{s}Foot'
  knee_approved=(G2B@(hip0@init_inv@mat4(idle_world[ids[kn]]))).translation
  estimates=[]
  for i in range(24):
   angle=-math.pi+i*math.pi/12
   con.pole_angle=angle;bpy.context.view_layer.update()
   w=solve_matrices()
   estimates.append(((w[kn].translation-knee_approved).length,(w[ft].translation-(G2B.to_3x3()@g0[s]['ankleWorld'])).length,angle))
  estimates.sort();best=estimates[0]
  # Refine pole angle continuously around the best coarse solution.
  for step in (.06,.015,.003):
   current=best[2]
   for sign in (-2,-1,0,1,2):
    an=current+step*sign;con.pole_angle=an;bpy.context.view_layer.update()
    w=solve_matrices();res=((w[kn].translation-knee_approved).length,(w[ft].translation-(G2B.to_3x3()@g0[s]['ankleWorld'])).length,an)
    if (res[0]+res[1]*3)<(best[0]+best[1]*3):best=res
  con.pole_angle=best[2];pole_calibration[s]={'angleRadians':float(best[2]),'kneeMismatchMetres':float(best[0]),'ankleMismatchMetres':float(best[1])}
  if best[0]>.045 or best[1]>.009:raise RuntimeError('APPROVED_IDLE_IK_POLE_CALIBRATION_FAILED '+s+' '+str(best))

 bpy.context.view_layer.update()
 # Source trajectory supplies controllers and poles at every evaluated half-frame.
 frames=[];previousQuat={}
 for row in source['frames']:
  t=float(row['timeSeconds']);hp=locked_hip_at(t);gh=goals(row,hp)
  pbone('mixamorig:Hips').matrix=G2B@hp
  apply_targets(gh)
  evalpose=solve_matrices()
  out={'timeSeconds':t,'joints':{},'observed':{},'control':{}}
  for s in SIDES:
   up,leg,foot=[f'mixamorig:{s}{part}' for part in PARTS]
   glmat={n:B2G@evalpose[n] for n in (up,leg,foot)}
   # Convert evaluated Blender world orientation to exact target glTF LOCAL TRS.
   for name,pr in ((up,hp),(leg,glmat[up]),(foot,glmat[leg])):
    localq=(pr.to_quaternion().inverted()@glmat[name].to_quaternion()).normalized()
    vals=q_json(localq)
    prev=previousQuat.get(name)
    if prev and sum(x*y for x,y in zip(prev,vals))<0:vals=[-x for x in vals]
    previousQuat[name]=vals;out['joints'][name]=vals
   goal=gh[s]['ankleWorld'];fkpos=glmat[foot].translation
   out['observed'][s]={'ankleWorld':seq(fkpos),'kneeWorld':seq(glmat[leg].translation),
      'ankleGoal':seq(goal),'ankleMissMetres':float((fkpos-goal).length),
      'poleWorld':seq(gh[s]['poleWorld']),'poleSeparationMetres':float(gh[s]['poleSeparation'])}
   out['control'][s]={'footIK':row['bones'][s+'Foot.IK']['worldPosition'],
        'kneeIK':row['bones'][s+'Knee.IK']['worldPosition']}
  frames.append(out)
 if len(frames)!=61:raise RuntimeError('BLENDER_SOURCE_NOT_ALL_61_FRAMES')
 result={'schema':'heavy1-blender-native-ik-evaluated-v1','version':VER,
    'engine':'Blender 4.x actual IK constraint chainCount=2 and Copy Rotation, original v1.4 Foot.IK/Knee.IK controller trajectories',
    'sourceModelSHA256':MODEL_SHA,'sourceActionSHA256':HEAVY1_SHA,
    'originalBadFKUsedForLegBasis':False,'heavy1OriginalPelvisLocked':True,
    'targetInitialization':'ACTUAL_ACCEPTED_LIONHEART_IDLE',
    'trajectoryBasis':'SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION',
    'axisAlignment':[[float(align[i][j]) for j in range(3)] for i in range(3)],
    'poleCalibration':pole_calibration,'amplitude':a.amplitude,'frames':frames}
 pathlib.Path(a.output).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(a.output).write_text(json.dumps(result,separators=(',',':'))+'\n')
 pathlib.Path(a.report).write_text(json.dumps({'status':'NATIVE_BLENDER_IK_EVALUATED_NOT_YET_SKIN_VALIDATED',
 'samples':len(frames),'poleCalibration':pole_calibration,'amplitude':a.amplitude,
 'largestNativeIKAnkleErrorMetres':max(f['observed'][s]['ankleMissMetres'] for f in frames for s in SIDES)},indent=2)+'\n')
 print('STATUS=NATIVE_BLENDER_IK_EVALUATED_NOT_YET_SKIN_VALIDATED',flush=True)
 print('SAMPLES='+str(len(frames)),flush=True)

if __name__=='__main__':main()
