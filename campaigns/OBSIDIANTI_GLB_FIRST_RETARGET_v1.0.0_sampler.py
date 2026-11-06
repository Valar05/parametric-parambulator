"""Sample the EXPORTED Lionheart GLB through the exact Ares import route."""
import bpy,sys,json,math,re,pathlib
from mathutils import Matrix
source,out=sys.argv[sys.argv.index('--')+1:]
if source.lower().endswith('.blend'):
 bpy.ops.wm.open_mainfile(filepath=source)
else:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=source,import_shading='NORMALS')
arms=[o for o in bpy.data.objects if o.type=='ARMATURE' and len(o.pose.bones)>=26]
assert len(arms)==1,('EXPORTED_GLB_RIG_COUNT',[(o.name,len(o.pose.bones)) for o in arms])
arm=arms[0];ad=arm.animation_data_create()
for tr in ad.nla_tracks:tr.mute=True
ad.use_nla=False
if not source.lower().endswith('.blend'):
 for pb in arm.pose.bones:
  assert not any(c.type=='IK' and not c.mute and c.influence>0 for c in pb.constraints),'GLB_STILL_HAS_ACTIVE_IK'
required=('Idle','Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
original=list(bpy.data.actions)
def match(name):
 cand=[a for a in original if a.name==name]
 if len(cand)==1:return cand[0]
 cand=[a for a in original if re.sub(r'(?:_(?:Armature|rig))?(?:\.\d+)?$','',a.name,flags=re.I)==name]
 if len(cand)!=1:raise RuntimeError('EXPORTED_ACTION_AMBIGUOUS '+name+' '+repr([a.name for a in original]))
 return cand[0]
acts={name:match(name) for name in required}
axis=Matrix.Rotation(math.radians(-90),4,'X')
scene=bpy.context.scene;fps=float(scene.render.fps)/scene.render.fps_base
assert 10<=fps<=120,'GLB_SAMPLE_FPS_INVALID'
def record(frame):
 whole=math.floor(frame);scene.frame_set(whole,subframe=frame-whole)
 bpy.context.view_layer.update()
 basis=(axis@arm.matrix_world).to_3x3()
 objscale=sum(arm.matrix_world.to_scale())/3
 bones={}
 for pb in arm.pose.bones:
  rest=pb.bone.matrix_local.copy();posed=pb.matrix.copy();parent=pb.parent
  restL=parent.bone.matrix_local.inverted_safe()@rest if parent else rest
  poseL=parent.matrix.inverted_safe()@posed if parent else posed
  q=(restL.inverted_safe()@poseL).to_quaternion().normalized()
  wr=(basis@rest.to_3x3()).to_quaternion().normalized()
  pt=axis@(arm.matrix_world@posed.translation)
  local=poseL.translation-restL.translation;local*=objscale
  bones[pb.name]={'localDeltaQuat':[q.x,q.y,q.z,q.w],'restWorldQuat':[wr.x,wr.y,wr.z,wr.w], 'worldPosition':[pt.x,pt.y,pt.z],'localDeltaPosition':[local.x,local.y,local.z]}
 return bones
results={}
for name,act in acts.items():
 ad.action=act
 start,end=map(float,act.frame_range)
 assert end-start<=400,'CLIP_TOO_LONG '+name
 if name=='Idle':seq=[start]
 else:
  # Evaluate every GLB-imported animation frame, preserving its actual baked curves.
  seq=[start+i for i in range(int(math.floor(end-start))+1)]
  if seq[-1]<end-1e-5:seq.append(end)
  assert len(seq)>=2,'EMPTY_CLIP '+name
 frames=[{'time':round((f-start)/fps,7),'sourceFrame':round(f,7),'bones':record(f)} for f in seq]
 results[name]={'frames':frames,'sourceAction':act.name,'sourceFrameRange':[start,end],'sourceFPS':fps}
 print('GLB_SAMPLED',name,len(seq),flush=True)
pathlib.Path(out).write_text(json.dumps({'schema':'obsidianti-evaluated-source-motion-v1','sourceKind':'native_blend' if source.lower().endswith('.blend') else 'lionheart_glb_as_ares','source':source,'blenderVersion':bpy.app.version_string,'fps':fps,'actionCount':len(results),'actions':results},separators=(',',':')))
print('SOURCE_GLB_REIMPORT_SAMPLING_COMPLETE=YES',flush=True)
