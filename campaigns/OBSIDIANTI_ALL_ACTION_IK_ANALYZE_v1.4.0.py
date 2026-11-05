#!/usr/bin/env python3
"""Read-only GLB reference pose and native Lionheart controller calibration auditor."""
import argparse, hashlib, json, math, pathlib, struct

VERSION='OBSIDIANTI_ALL_ACTION_IK_v1.4.0'
ACTIONS=('Idle','Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
PFX='mixamorig:'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def matmul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def ident():return [[float(i==j) for j in range(4)] for i in range(4)]
def xyz(m):return [round(m[k][3],9) for k in range(3)]
def scalarvec(v):return [round(float(x),9) for x in v]
def vecminus(a,b):return scalarvec([x-y for x,y in zip(a,b)])
def vlength(v):return math.sqrt(sum(x*x for x in v))
def trsmat(translation,quaternion,scale):
 x,y,z,w=quaternion; l=math.sqrt(x*x+y*y+z*z+w*w)
 if l<1e-14:raise ValueError('ZERO_QUATERNION')
 x,y,z,w=[t/l for t in (x,y,z,w)];sx,sy,sz=scale
 r=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
    [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
    [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
 return [[r[i][0]*sx,r[i][1]*sy,r[i][2]*sz,translation[i]] for i in range(3)]+[[0,0,0,1]]

def node_matrix(n,tr_override=None):
 if tr_override is None and 'matrix' in n:
  col=n['matrix'];return [[col[j*4+i] for j in range(4)] for i in range(4)]
 t=dict(translation=n.get('translation',[0,0,0]),rotation=n.get('rotation',[0,0,0,1]),scale=n.get('scale',[1,1,1]))
 if tr_override:t.update(tr_override)
 return trsmat(t['translation'],t['rotation'],t['scale'])

def load_glb(p):
 raw=pathlib.Path(p).read_bytes()
 if raw[:4]!=b'glTF' or struct.unpack_from('<II',raw,4)!=(2,len(raw)):raise RuntimeError('INVALID_GLB_HEADER')
 jsize,jtyp=struct.unpack_from('<I4s',raw,12)
 if jtyp!=b'JSON':raise RuntimeError('INVALID_GLB_JSON_CHUNK')
 g=json.loads(raw[20:20+jsize]);off=20+jsize
 bsize,btyp=struct.unpack_from('<I4s',raw,off)
 if btyp!=b'BIN\0':raise RuntimeError('INVALID_GLB_BIN_CHUNK')
 b=raw[off+8:off+8+bsize]
 return g,b

def accessor(g,b,idx):
 a=g['accessors'][idx];v=g['bufferViews'][a['bufferView']];ctype=a['componentType']
 fmt={5126:'f',5123:'H',5121:'B',5125:'I'}[ctype];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 size=struct.calcsize('<'+fmt*n);step=v.get('byteStride',size);base=v.get('byteOffset',0)+a.get('byteOffset',0)
 if base+size+(a['count']-1)*step>len(b):raise RuntimeError('GLB_ACCESSOR_OUT_OF_RANGE')
 return [list(struct.unpack_from('<'+fmt*n,b,base+i*step)) for i in range(a['count'])]

def world_nodes(g, overrides=None):
 nodes=g['nodes'];parents={}
 for p,n in enumerate(nodes):
  for c in n.get('children',[]):
   if c in parents:raise RuntimeError('MULTIPLE_NODE_PARENTS')
   parents[c]=p
 cache={};visiting=set()
 def world(i):
  if i not in cache:
   if i in visiting:raise RuntimeError('GLB_NODE_CYCLE')
   visiting.add(i)
   local=node_matrix(nodes[i],(overrides or {}).get(i))
   cache[i]=matmul(world(parents[i]),local) if i in parents else local
   visiting.remove(i)
  return cache[i]
 return {i:world(i) for i in range(len(nodes))}

def snapshot(g,mats):
 names={n['name']:i for i,n in enumerate(g['nodes']) if n.get('name')}
 keys=(PFX+'Hips',PFX+'LeftUpLeg',PFX+'LeftLeg',PFX+'LeftFoot',PFX+'LeftToeBase',
       PFX+'RightUpLeg',PFX+'RightLeg',PFX+'RightFoot',PFX+'RightToeBase')
 missing=[k for k in keys if k not in names]
 if missing:raise RuntimeError('TARGET_REQUIRED_BONES_MISSING:'+repr(missing))
 return {key:{'worldPositionMetres':xyz(mats[names[key]]),'worldMatrixRowMajor':[[round(z,9) for z in row] for row in mats[names[key]]]} for key in keys}

def target_idle(g,b):
 name='LionheartIdle_UNREVIEWED'
 clips=[x for x in g.get('animations',[]) if x['name']==name]
 if len(clips)!=1:raise RuntimeError('APPROVED_TARGET_STATIC_IDLE_MISSING')
 clip=clips[0];override={}
 for ch in clip['channels']:
  target=ch['target'];node=target.get('node');kind=target.get('path')
  if node is None or kind not in ('rotation','translation','scale'):continue
  vals=accessor(g,b,clip['samplers'][ch['sampler']]['output'])
  if not vals:raise RuntimeError('APPROVED_IDLE_MISSING_SAMPLES')
  override.setdefault(node,{})[kind]=vals[0]
 return name,world_nodes(g,override)

def audit(target,diagnostics):
 target_sha=sha(target);g,b=load_glb(target);bind=world_nodes(g);approved_name,approved=target_idle(g,b)
 target_bind=snapshot(g,bind);target_approved=snapshot(g,approved)
 root=pathlib.Path(diagnostics);source=json.loads((root/'source-rig.json').read_text())
 if source['version']!=VERSION or source['actionNames']!=list(ACTIONS):raise RuntimeError('SOURCE_RIG_METADATA_UNEXPECTED')
 source_idle=json.loads((root/'actions/Idle.json').read_text())
 if len(source_idle['frames'])!=1:raise RuntimeError('DONOR_IDLE_NOT_SINGLE_FRAME')
 src0=source_idle['frames'][0]['bones'];source_rest=source['restPose']
 scales={};baseline={};summary=[]
 for side in ('Left','Right'):
  p=PFX;sp=source_rest
  thigh_s=sp[p+side+'UpLeg']['boneLengthMetres'];shin_s=sp[p+side+'Leg']['boneLengthMetres']
  tp=target_bind
  thigh_t=vlength(vecminus(tp[p+side+'Leg']['worldPositionMetres'],tp[p+side+'UpLeg']['worldPositionMetres']))
  shin_t=vlength(vecminus(tp[p+side+'Foot']['worldPositionMetres'],tp[p+side+'Leg']['worldPositionMetres']))
  scale=(thigh_t+shin_t)/(thigh_s+shin_s)
  if not .35<scale<2.3:raise RuntimeError('LEG_LENGTH_RATIO_OUT_OF_RANGE:'+side)
  scales[side]={'donorThighMetres':thigh_s,'donorShinMetres':shin_s,'targetThighMetres':thigh_t,'targetShinMetres':shin_t,
    'thighRatio':round(thigh_t/thigh_s,8),'shinRatio':round(shin_t/shin_s,8),'combinedRatio':round(scale,8)}
  srcH=src0[p+'Hips']['worldPosition'];ctrl=src0[side+'Foot.IK']['worldPosition'];ank=src0[p+side+'Foot']['worldPosition']
  targetH=target_approved[p+'Hips']['worldPositionMetres'];targetA=target_approved[p+side+'Foot']['worldPositionMetres']
  relCtrl=vecminus(ctrl,srcH);relA=vecminus(targetA,targetH)
  delta=vecminus(relA,[scale*v for v in relCtrl])
  baseline[side]={'donorFootIKRelativePelvisMetres':relCtrl,'donorEvaluatedAnkleRelativePelvisMetres':vecminus(ank,srcH),
    'donorEvaluatedAnkleMinusControllerMetres':vecminus(ank,ctrl), 'targetApprovedAnkleRelativePelvisMetres':relA,
    'provisionalScaledControllerToTargetAnkleOffsetMetres':delta,
    'coordinateOrientationValidity':'UNVERIFIED_SOURCE_TO_TARGET_FACING_BASIS',
    'rawWorldQuaternionController':src0[side+'Foot.IK']['worldQuaternion']}
 for name in ACTIONS:
  action=json.loads((root/'actions'/f'{name}.json').read_text())
  if action['action']!=name or len(action['frames'])!=action['frameCount']:raise RuntimeError('SOURCE_ACTION_INVALID:'+name)
  series=[]
  for side in ('Left','Right'):
   first=action['frames'][0]['legsRelativePelvis'][side]['footControllerRelativePelvisMetres']
   idle=source_idle['frames'][0]['legsRelativePelvis'][side]['footControllerRelativePelvisMetres']
   data=[f['legsRelativePelvis'][side]['footControllerRelativePelvisMetres'] for f in action['frames']]
   relative=[vecminus(v,idle) for v in data]
   series.append({'side':side,'firstControllerFromNativeIdleMetres':vecminus(first,idle),
      'relativeFootControllerDeltaMinMetres':[round(min(v[i] for v in relative),8) for i in range(3)],
      'relativeFootControllerDeltaMaxMetres':[round(max(v[i] for v in relative),8) for i in range(3)],
      'firstControllerRelativePelvisMetres':first})
  summary.append({'name':name,'sourceFrameRange':action['sourceFrameRange'],'framesEvaluated':action['frameCount'],
                  'durationSeconds':action['durationSeconds'],'feet':series})
 result={'schema':'obsidianti-native-lionheart-ik-calibration-v1','version':VERSION,
   'modelSha256':target_sha,'targetApprovedIdleAction':approved_name,'nativeSourceSha256':source['sourceSha256'],
   'sourceObjectToMetres':'source blender armature scale from evaluated matrix; glTF Y-up conversion applied',
   'targetBind':target_bind,'targetApprovedCombatIdle':target_approved,'legRatios':scales,
   'sourceIdleControllerToTargetApprovedIdle':baseline,'actions':summary,
   'limits':['Source Foot.IK controllers are not ankle/sole skin points',
             'Offsets provisional until target actor facing/basis is calibrated',
             'Skinned donor/target sole contact not measured by this diagnostic',
             'No new GLB or IK animation produced']}
 out=root/'calibration.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 (root/'target-reference.json').write_text(json.dumps({'sourceModelSha256':target_sha,
         'targetName':'Obsidianti','targetBind':target_bind,'targetApprovedAction':approved_name,
         'approvedActionFrame0':target_approved},indent=2,sort_keys=True)+'\n')
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',required=True);p.add_argument('--diagnostics',required=True)
 args=p.parse_args();x=audit(args.target,args.diagnostics)
 print('CALIBRATION_SIDES='+','.join(x['legRatios'])+' ACTIONS='+str(len(x['actions'])))
