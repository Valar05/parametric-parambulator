#!/usr/bin/env python3
"""Ares-method Lionheart FK surgical pelvis scale; no IK, no rotation rewrites."""
import argparse,copy,hashlib,json,math,pathlib,struct
MOVES=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
def sha(b):return hashlib.sha256(b).hexdigest()
def read_glb(data):
 if data[:4]!=b'glTF' or struct.unpack_from('<II',data,4)!=(2,len(data)):raise RuntimeError('INVALID_GLB_CONTAINER')
 n,k=struct.unpack_from('<I4s',data,12)
 if k!=b'JSON':raise RuntimeError('INVALID_JSON_CHUNK')
 g=json.loads(data[20:20+n]);p=20+n
 blen,btype=struct.unpack_from('<I4s',data,p)
 if btype!=b'BIN\0':raise RuntimeError('INVALID_BINARY_CHUNK')
 b=bytearray(data[p+8:p+8+blen]);return g,b

def read_acc(g,b,index):
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
 if a['componentType']!=5126 or a['type'] not in ('SCALAR','VEC3'):raise RuntimeError('UNSUPPORTED_ANIMATION_ACCESSOR')
 dim={'SCALAR':1,'VEC3':3}[a['type']];stride=v.get('byteStride',4*dim);off=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [list(struct.unpack_from('<'+'f'*dim,b,off+i*stride)) for i in range(a['count'])]
def append_acc(g,b,vals,kind):
 while len(b)%4:b.append(0)
 offset=len(b);dim=1 if kind=='SCALAR' else 3
 raw=struct.pack('<'+'f'*(len(vals)*dim),*(v for row in vals for v in row));b.extend(raw)
 v=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(raw)})
 a=len(g['accessors']);g['accessors'].append({'bufferView':v,'componentType':5126,'count':len(vals),'type':kind});return a
def serialize(g,b):
 g['buffers'][0]['byteLength']=len(b)
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*(-len(j)%4)
 bb=bytes(b);bb+=b'\0'*(-len(bb)%4)
 return struct.pack('<4sII',b'glTF',2,28+len(j)+len(bb))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(bb),b'BIN\0')+bb

def main(src,out,report,measure):
 data=pathlib.Path(src).read_bytes();g,b=read_glb(data)
 if len(g.get('animations',[]))!=23:raise RuntimeError('FK_BASELINE_WRONG_ANIMATION_COUNT')
 oldbin=bytes(b);locked={k:copy.deepcopy(g[k]) for k in ('nodes','skins','meshes','scenes')}
 m=json.loads(pathlib.Path(measure).read_text());a=m['clips']['Heavy1']
 left=float(a['left']['anatomicalLengthRatio']);right=float(a['right']['anatomicalLengthRatio']);scale=(left+right)/2
 if not (.75<left<.98 and .75<right<.98 and abs(left-right)<.04):raise RuntimeError('ANATOMICAL_SCALE_INCONSISTENT')
 nmap={x.get('name'):i for i,x in enumerate(g['nodes'])};hip=nmap['mixamorig:Hips']
 idle=next((a for a in g['animations'] if a['name']=='LionheartIdle_UNREVIEWED'),None)
 if idle is None:raise RuntimeError('APPROVED_IDLE_MISSING')
 def hip_track(action):
  found=[c for c in action['channels'] if c['target']=={'node':hip,'path':'translation'}]
  if len(found)!=1:raise RuntimeError('HIP_TRANSLATION_NOT_UNIQUE '+action['name'])
  ch=found[0];s=action['samplers'][ch['sampler']]
  if s.get('interpolation','LINEAR')!='LINEAR':raise RuntimeError('UNSUPPORTED_HIP_INTERPOLATION '+action['name'])
  return s,read_acc(g,b,s['input']),read_acc(g,b,s['output'])
 _,_,idle_pos=hip_track(idle)
 base=idle_pos[0]
 protected={a['name']:copy.deepcopy(a) for a in g['animations'] if a['name'] not in {'Lionheart_'+x for x in MOVES}}
 oldanimations=copy.deepcopy(g['animations']);rows=[]
 for name in MOVES:
  clip=next((a for a in g['animations'] if a['name']=='Lionheart_'+name),None)
  if clip is None:raise RuntimeError('LIONHEART_CLIP_MISSING '+name)
  s,times,positions=hip_track(clip)
  if not positions or len(times)!=len(positions):raise RuntimeError('BAD_HIP_TRACK '+name)
  amended=[[base[i]+(p[i]-base[i])*scale for i in range(3)] for p in positions]
  if not all(math.isfinite(x) for p in amended for x in p):raise RuntimeError('NONFINITE_HIP_VALUES')
  s['output']=append_acc(g,b,amended,'VEC3')
  start=positions[0];step=max(math.dist(x,y) for x,y in zip(positions,amended))
  rows.append({'clip':name,'count':len(times),'fpsIndependentDurationSeconds':times[-1][0],
               'firstHipBefore':start,'firstHipAfter':amended[0],
               'maxHipCorrectionMeters':step,'originalMaxTravelFromIdle_m':max(math.dist(p,base) for p in positions),
               'correctedMaxTravelFromIdle_m':max(math.dist(p,base) for p in amended),
               'rotationsAndNonHipChannels':'UNCHANGED'})
 for action in g['animations']:
  if action['name'] in protected and action!=protected[action['name']]:raise RuntimeError('PROTECTED_CLIP_MUTATED '+action['name'])
 if any(a['name']!=bb['name'] for a,bb in zip(g['animations'],oldanimations)):raise RuntimeError('ANIMATION_IDENTITY_CHANGED')
 if bytes(b[:len(oldbin)])!=oldbin:raise RuntimeError('ORIGINAL_BIN_PREFIX_MUTATED')
 if any(g[k]!=locked[k] for k in locked):raise RuntimeError('SKELETON_OR_MESH_MUTATED')
 for old,new in zip(oldanimations,g['animations']):
  if old['name'] in protected:continue
  assert len(old['channels'])==len(new['channels']) and len(old['samplers'])==len(new['samplers'])
  diff=[i for i,(x,y) in enumerate(zip(old['samplers'],new['samplers'])) if x!=y]
  allowed={i for i,c in enumerate(new['channels']) if c['target']=={'node':hip,'path':'translation'} for i in [c['sampler']]}
  if set(diff)!=allowed:raise RuntimeError('UNAUTHORIZED_SAMPLER_MUTATION '+new['name'])
 final=serialize(g,b);ng,nb=read_glb(final)
 if len(ng['animations'])!=23 or bytes(nb[:len(oldbin)])!=oldbin:raise RuntimeError('REOPEN_FAILED')
 pathlib.Path(out).write_bytes(final)
 result={'schema':'obsidianti-ares-scaled-fk-review-v1','status':'UNAPPROVED_REVIEW_CANDIDATE',
         'algorithm':'EXACT_ARES_PELVIS_DELTA_SCALE_WITH_FK_LEG_ROTATIONS_PRESERVED',
         'motionSource':'HISTORICAL_PRECONTACT_IK_FK_MODEL_NOT_LATEST_V156',
         'sourceSha256':sha(data),'candidateSha256':sha(final),'ratioLeft':left,'ratioRight':right,'scaleApplied':scale,
         'anatomicalAsymmetryNote':'Mean bilateral leg ratio for common pelvis; foot controls not independently translated',
         'protectedOtherClips':list(protected),'changedClips':rows,'canonicalMutation':False,
         'limits':'Does not solve contact; user must compare geometry and skinned floor before acceptance.'}
 pathlib.Path(report).write_text(json.dumps(result,indent=2)+'\n')
 print('ARES_SCALE='+str(scale)+' SOURCE='+sha(data)+' REVIEW='+sha(final),flush=True)
 print('CHANGED_PELVIS_TRACKS=10 OTHER_ANIMATION_TRACKS_UNCHANGED=YES',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('report');p.add_argument('measure');a=p.parse_args()
 main(a.source,a.output,a.report,a.measure)
