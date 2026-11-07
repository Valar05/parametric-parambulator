#!/usr/bin/env python3
"""Read original Vanguard GLB2 without Blender; verify real ORG animation and weights."""
import argparse,collections,hashlib,json,math,pathlib,struct
VANGUARD='ca91335b8f4d5dc7d89267c18eff8740652e2bfc90710cebe6997d29caa1e541'
CLIPS=['0T-Pose','ClubIdle','Idle','Jump','JumpCrouch','JumpForward','Land','LedgeClimb','LedgeGrab','LedgeGrabHang','Midair','MidairSwordAttack1','MidairSwordAttack2','RunForwardOld','SpinAttack','SwordAttack1','SwordAttack2','SwordAttack4','SwordAttack5']
ORG=['ORG-hips','ORG-spine','ORG-chest','ORG-neck','ORG-head','ORG-shoulder.L','ORG-upper_arm.L','ORG-forearm.L','ORG-hand.L','ORG-shoulder.R','ORG-upper_arm.R','ORG-forearm.R','ORG-hand.R','ORG-thigh.L','ORG-shin.L','ORG-foot.L','ORG-toe.L','ORG-thigh.R','ORG-shin.R','ORG-foot.R','ORG-toe.R']

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def glb(path):
 data=pathlib.Path(path).read_bytes()
 if data[:4]!=b'glTF' or struct.unpack_from('<II',data,4)!=(2,len(data)):raise ValueError('SOURCE_NOT_EXACT_GLB2')
 length,kind=struct.unpack_from('<I4s',data,12)
 if kind!=b'JSON':raise ValueError('SOURCE_NO_JSON_CHUNK')
 doc=json.loads(data[20:20+length]);p=20+length
 bytecount,bintype=struct.unpack_from('<I4s',data,p)
 if bintype!=b'BIN\0':raise ValueError('SOURCE_NO_BIN_CHUNK')
 blob=data[p+8:p+8+bytecount]
 return doc,blob

def accessor(doc,blob,idx):
 a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']]
 if a['componentType']!=5126 or 'sparse' in a:raise ValueError('SOURCE_ANIM_ACCESSOR_NOT_FLOAT')
 shape={'SCALAR':1,'VEC3':3,'VEC4':4};n=shape[a['type']]
 start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',4*n)
 return [struct.unpack_from('<'+'f'*n,blob,start+k*stride) for k in range(a['count'])]

def inspect(path):
 if sha(path)!=VANGUARD:raise ValueError('VANGUARD_INPUT_BYTES_NOT_OWNER_UPLOADED_SHA')
 doc,blob=glb(path)
 names=[n.get('name','') for n in doc['nodes']]
 required=set(ORG)
 if not required.issubset(set(names)):raise ValueError('VANGUARD_ORG_BONES_NOT_AS_EXPECTED_'+repr(sorted(required-set(names))))
 if len(doc.get('skins',[]))!=1 or len(doc['skins'][0]['joints'])<400:raise ValueError('VANGUARD_NOT_437_JOINT_RIG')
 clips=[a.get('name') for a in doc.get('animations',[])]
 if clips!=CLIPS:raise ValueError('VANGUARD_CLIP_LIST_CHANGED '+repr(clips))
 mesh_names=[n.get('name') for n in doc['nodes'] if n.get('mesh') is not None]
 if 'Long_Sword' not in mesh_names or 'Body' not in mesh_names:raise ValueError('VANGUARD_SWORD_MESH_NOT_PRESENT')
 rows={}
 for a in doc['animations']:
  moving=set()
  for ch in a['channels']:
   bone=names[ch['target']['node']]
   if bone not in required or ch['target']['path'] not in ('rotation','translation'):continue
   sm=a['samplers'][ch['sampler']]
   vals=accessor(doc,blob,sm['output'])
   if vals and max(abs(v-x) for row in vals for v,x in zip(row,vals[0]))>1e-4:moving.add(bone)
  rows[a['name']]={'channelCount':len(a['channels']),'movingMappedBones':sorted(moving),'movingMappedBoneCount':len(moving)}
  if a['name']!='0T-Pose' and not moving:raise ValueError('NATIVE_VANGUARD_CLIP_STATIC_'+a['name'])
 return {'status':'OWNER_VANGUARD_GLB_VERIFIED','sha256':VANGUARD,'bytes':pathlib.Path(path).stat().st_size,
  'nodeCount':len(doc['nodes']),'jointCount':len(doc['skins'][0]['joints']),
  'rig':'RIGIFY_STYLE_ORG_DEF_MCH','mappedOrgBoneCount':len(required),'allClips':CLIPS,
  'actionEvidence':rows,'meshes':mesh_names,'0T-Pose':'STATIC_REFERENCE_NOT_ATTACK'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True)
 args=ap.parse_args();proof=inspect(args.source)
 pathlib.Path(args.output).write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
 print('VANGUARD_SOURCE_VERIFIED='+proof['sha256']+' CLIPS='+str(len(proof['allClips']))+' MAPPED_ORG='+str(proof['mappedOrgBoneCount']),flush=True)

def verify_target_candidate(path):
 """Inspect actual exported target joint weights to prove shield is absent and lance present."""
 doc,blob=glb(path)
 names=[n.get('name','') for n in doc.get('nodes',[])]
 if not doc.get('skins') or not doc.get('animations'):raise ValueError('CANDIDATE_MISSING_TARGET_SKIN_OR_ACTIONS')
 # The shield's LeftWeapon.L bone may be pruned if no longer weighted after export.
 expected={'mixamorig:Hips','mixamorig:LeftFoot','mixamorig:RightFoot','mixamorig:RightWeapon.R'}
 if not expected.issubset(set(names)):raise ValueError('CANDIDATE_NOT_ORIGINAL_OBSIDIANTI_RIG '+repr(expected-set(names)))
 skin=doc['skins'][0];joints=skin['joints']
 stats=[]
 for mesh in doc['meshes']:
  total=0.;left=0.;right=0.
  for prim in mesh['primitives']:
   attrs=prim['attributes']
   if 'JOINTS_0' not in attrs or 'WEIGHTS_0' not in attrs:continue
   ja=doc['accessors'][attrs['JOINTS_0']];jw=doc['accessors'][attrs['WEIGHTS_0']]
   if ja['count']!=jw['count'] or ja['type']!='VEC4' or jw['type']!='VEC4':raise ValueError('CANDIDATE_JOINT_WEIGHTS_UNEXPECTED')
   def rows(accessor):
    a=doc['accessors'][accessor];v=doc['bufferViews'][a['bufferView']]
    code={5121:'B',5123:'H',5126:'f'}.get(a['componentType'])
    if code is None or 'sparse' in a:raise ValueError('CANDIDATE_UNSUPPORTED_JOINT_COMPONENT')
    n=4;size=struct.calcsize('<'+code*n)
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    stride=v.get('byteStride',size)
    return [struct.unpack_from('<'+code*n,blob,offset+k*stride) for k in range(a['count'])]
   js=rows(attrs['JOINTS_0']);ws=rows(attrs['WEIGHTS_0'])
   for ji,wi in zip(js,ws):
    for idx,w in zip(ji,wi):
     if w<=0.0001:continue
     bone=names[joints[int(idx)]]
     total+=float(w)
     if bone=='mixamorig:LeftWeapon.L':left+=float(w)
     if bone=='mixamorig:RightWeapon.R':right+=float(w)
  stats.append({'mesh':mesh.get('name',''), 'leftWeaponFraction':round(left/max(total,1),6),
   'rightWeaponFraction':round(right/max(total,1),6)})
 if any(m['leftWeaponFraction']>.80 for m in stats):raise ValueError('SHIELD_STILL_VISIBLE_IN_EXPORTED_GLB_'+repr(stats))
 if not any(m['rightWeaponFraction']>.80 for m in stats):raise ValueError('LANCE_MISSING_FROM_EXPORTED_GLB_'+repr(stats))
 return {'status':'SHIELD_ABSENT_LANCE_PRESENT','targetRigVerified':True,
  'meshes':stats,'actionCount':len(doc['animations']),
  'sha256':sha(path)}
