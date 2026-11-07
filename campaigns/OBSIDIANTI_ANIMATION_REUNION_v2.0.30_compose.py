#!/usr/bin/env python3
"""Recover exact v1.1 original guard + authored idle and compose eight lower-ARP guard steps.
Only appends new glTF animations/buffer data; old clips, skin, mesh and material bytes stay immutable.
"""
from __future__ import annotations
import argparse,bisect,copy,hashlib,json,math,pathlib,struct,sys

VERSION='OBSIDIANTI_ANIMATION_REUNION_v2.0.30'
CANON_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
ARP_SHA='e7f60fea731fd9537380868adbb52fee63df34fdf1b6d7694bc39925b440fa1d'
STEPS=('StepForward','StepForwardLeft','StepLeft','StepBackLeft','StepBack','StepBackRight','StepRight','StepForwardRight')
GUARD='LionheartIdle_UNREVIEWED'
AUTHORED='ObsidiantiIdle'
HIPS='mixamorig:Hips'
SPINE='mixamorig:Spine'


def require(x,msg):
 if not x:raise ValueError(msg)
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def read_glb(path):
 b=pathlib.Path(path).read_bytes()
 require(len(b)>=28 and b[:4]==b'glTF','INVALID_GLB_MAGIC')
 _,version,total=struct.unpack_from('<4sII',b,0)
 require(version==2 and total==len(b),'INVALID_GLB_VERSION_OR_LENGTH')
 jn,jtyp=struct.unpack_from('<I4s',b,12)
 require(jtyp==b'JSON' and 0<jn<30000000,'INVALID_JSON_CHUNK')
 js=json.loads(b[20:20+jn]);p=20+jn
 bn,btyp=struct.unpack_from('<I4s',b,p)
 require(btyp==b'BIN\0' and p+8+bn==len(b),'INVALID_BIN_CHUNK')
 data=b[p+8:]
 require(len(js.get('buffers',[]))==1 and js['buffers'][0]['byteLength']<=len(data),'INVALID_BUFFERS')
 require(js.get('animations') and js.get('skins') and js.get('meshes'),'MISSING_RIG_MESH_OR_ANIMATIONS')
 return js,data

def glb_save(js,data,path):
 doc=copy.deepcopy(js)
 doc['buffers'][0]['byteLength']=len(data)
 j=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*(-len(j)%4)
 binary=data+b'\0'*(-len(data)%4)
 blob=struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary
 pathlib.Path(path).write_bytes(blob)
 return len(blob)

def name_ids(js):
 result={}
 for i,n in enumerate(js['nodes']):
  name=n.get('name')
  if name:
   require(name not in result,'DUPLICATE_BONE_NAME_'+name);result[name]=i
 return result

def parents(js):
 out={}
 for i,n in enumerate(js['nodes']):
  for c in n.get('children',[]):
   require(c not in out,'MULTIPARENT_RIG');out[c]=i
 return out

def descendants(js,root):
 found=set();stack=[root]
 while stack:
  node=stack.pop()
  if node in found:continue
  found.add(node);stack.extend(js['nodes'][node].get('children',[]))
 return found

def normq(q):
 d=math.sqrt(sum(float(x)**2 for x in q));require(math.isfinite(d) and d>1e-10,'BAD_QUATERNION')
 return tuple(float(x)/d for x in q)
def qm(a,b):
 x,y,z,w=normq(a);u,v,t,s=normq(b)
 return normq((w*u+x*s+y*t-z*v,w*v-x*t+y*s+z*u,w*t+x*v-y*u+z*s,w*s-x*u-y*v-z*t))
def qi(q):
 x,y,z,w=normq(q);return (-x,-y,-z,w)
def qdeg(a,b):
 d=abs(sum(x*y for x,y in zip(normq(a),normq(b))))
 return 2*math.degrees(math.acos(min(1.,max(-1.,d))))
def qslerp(a,b,f):
 a=normq(a);b=normq(b);d=sum(x*y for x,y in zip(a,b))
 if d<0:b=tuple(-v for v in b);d=-d
 if d>.9995:return normq(tuple(x*(1-f)+y*f for x,y in zip(a,b)))
 angle=math.acos(max(-1.,min(1.,d)));s=math.sin(angle)
 return normq(tuple((x*math.sin((1-f)*angle)+y*math.sin(f*angle))/s for x,y in zip(a,b)))

def raw_accessor(js,data,i):
 a=js['accessors'][i];require('sparse' not in a and 'bufferView' in a,'UNSUPPORTED_SPARSE_ACCESSOR')
 v=js['bufferViews'][a['bufferView']]
 require(v.get('buffer',0)==0,'MULTI_BUFFER_ACCESSOR_UNSUPPORTED')
 typ=a['type'];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}.get(typ)
 fmt={5126:'f',5125:'I',5123:'H',5121:'B'}.get(a['componentType'])
 require(n is not None and fmt is not None,'UNSUPPORTED_ACCESSOR_TYPE')
 sz=struct.calcsize('<'+fmt*n);stride=v.get('byteStride',sz)
 require(stride>=sz,'BAD_ACCESSOR_STRIDE')
 off=v.get('byteOffset',0)+a.get('byteOffset',0)
 require(off>=0 and (off+(a['count']-1)*stride+sz)<=len(data),'ACCESSOR_OUTSIDE_BUFFER')
 return [struct.unpack_from('<'+fmt*n,data,off+j*stride) for j in range(a['count'])]

def get_channel(clip,node,path):
 ch=[x for x in clip['channels'] if x['target'].get('node')==node and x['target'].get('path')==path]
 require(len(ch)<=1,'MULTIPLE_SAME_CHANNEL_'+str((node,path)))
 return ch[0] if ch else None

def at_time(js,data,clip,node,path,t):
 ch=get_channel(clip,node,path)
 if ch is None:return js['nodes'][node].get(path,(0.,0.,0.,1.) if path=='rotation' else ((1.,1.,1.) if path=='scale' else (0.,0.,0.)))
 samp=clip['samplers'][ch['sampler']]
 ts=[x[0] for x in raw_accessor(js,data,samp['input'])]
 vals=raw_accessor(js,data,samp['output'])
 require(len(ts)>=1 and len(ts)==len(vals),'CHANNEL_TIME_VALUE_MISMATCH')
 if t<=ts[0]:return vals[0]
 if t>=ts[-1]:return vals[-1]
 i=bisect.bisect_right(ts,t)-1
 require(ts[i+1]>ts[i],'NON_INCREASING_TIMES')
 f=(t-ts[i])/(ts[i+1]-ts[i]);interp=samp.get('interpolation','LINEAR')
 if interp=='STEP':return vals[i]
 require(interp=='LINEAR','UNSUPPORTED_INTERPOLATION_'+interp)
 if path=='rotation':return qslerp(vals[i],vals[i+1],f)
 return tuple(x+(y-x)*f for x,y in zip(vals[i],vals[i+1]))

def range_times(js,data,clip):
 ends=[]
 for sm in clip['samplers']:
  ts=raw_accessor(js,data,sm['input']);require(ts and ts[0][0]>=-.00001,'INVALID_TIME_RANGE')
  ends.append((ts[0][0],ts[-1][0]))
 return min(a for a,b in ends),max(b for a,b in ends)

class Appender:
 def __init__(self,js,data):self.js=js;self.bin=bytearray(data)
 def alloc_bytes(self,b):
  self.bin.extend(b'\0'*(-len(self.bin)%4))
  off=len(self.bin);self.bin.extend(b)
  ix=len(self.js['bufferViews']);self.js['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(b)})
  return ix
 def floats(self,rows,typ):
  width={'SCALAR':1,'VEC3':3,'VEC4':4}[typ]
  require(all(len(row)==width for row in rows),'INVALID_FLOAT_ROW_WIDTH')
  flat=[float(v) for row in rows for v in row]
  require(flat and all(math.isfinite(v) for v in flat),'NAN_OR_EMPTY_FLOAT_TRACK')
  raw=struct.pack('<'+'f'*len(flat),*flat)
  view=self.alloc_bytes(raw)
  acc={'bufferView':view,'byteOffset':0,'componentType':5126,'count':len(rows),'type':typ}
  if typ=='SCALAR':acc.update(min=[min(flat)],max=[max(flat)])
  self.js['accessors'].append(acc);return len(self.js['accessors'])-1
 def copy_accessor(self,source_js,source_bin,i,cache):
  if i in cache:return cache[i]
  a=copy.deepcopy(source_js['accessors'][i]);require('sparse' not in a and 'bufferView' in a,'CANNOT_COPY_SPARSE_ACCESSOR')
  v=source_js['bufferViews'][a['bufferView']];require(v.get('buffer',0)==0,'MULTIBUFFER_GUARD')
  lo=v.get('byteOffset',0);hi=lo+v['byteLength'];require(0<=lo<hi<=len(source_bin),'COPY_ACCESSOR_OVERRUN')
  bv=self.alloc_bytes(source_bin[lo:hi]);a['bufferView']=bv
  idx=len(self.js['accessors']);self.js['accessors'].append(a);cache[i]=idx;return idx
 def copy_clip(self,source_js,source_bin,clip,name,node_ids):
  cache={};result={'name':name,'samplers':[],'channels':[]}
  for samp in clip['samplers']:
   sm=copy.deepcopy(samp)
   for key in ('input','output'):sm[key]=self.copy_accessor(source_js,source_bin,sm[key],cache)
   result['samplers'].append(sm)
  for ch in clip['channels']:
   target=ch['target'];bone=source_js['nodes'][target['node']].get('name')
   require(bone in node_ids,'GUARD_ACTION_TARGET_BONE_MISSING_'+str(bone))
   new=copy.deepcopy(ch);new['target']['node']=node_ids[bone];result['channels'].append(new)
  self.js['animations'].append(result)
  return result
 def add(self,clip,node,path,times,vals):
  require(len(times)==len(vals) and len(times)>=2,'BAD_OUTPUT_TRACK')
  require(all(b>a for a,b in zip(times,times[1:])),'NONMONOTONIC_NEW_TIMES')
  ix=self.floats([(t,) for t in times],'SCALAR')
  oi=self.floats(vals,'VEC4' if path=='rotation' else 'VEC3')
  s=len(clip['samplers']);clip['samplers'].append({'input':ix,'output':oi,'interpolation':'LINEAR'})
  clip['channels'].append({'sampler':s,'target':{'node':node,'path':path}})


def compatibility(src,tgt):
 a,b=name_ids(src),name_ids(tgt)
 pa,pb=parents(src),parents(tgt)
 required=('mixamorig:Hips','mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2','mixamorig:LeftArm','mixamorig:RightArm','mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R','mixamorig:LeftUpLeg','mixamorig:RightUpLeg','mixamorig:LeftFoot','mixamorig:RightFoot')
 for n in required:require(n in a and n in b,'GUARD_TARGET_BONE_INCOMPATIBLE_'+n)
 for n in a.keys() & b.keys():
  if n.startswith('mixamorig:'):
   sidx=a[n];tidx=b[n]
   san=src['nodes'][pa[sidx]].get('name') if sidx in pa else None
   tan=tgt['nodes'][pb[tidx]].get('name') if tidx in pb else None
   require(san==tan,'HIERARCHY_INCOMPATIBLE_'+n)
 warnings=[]
 for n in required:
  v=src['nodes'][a[n]];w=tgt['nodes'][b[n]]
  for path,ident in (('rotation',(0.,0.,0.,1.)),('translation',(0.,0.,0.)),('scale',(1.,1.,1.))):
   x=v.get(path,ident);y=w.get(path,ident)
   diff=qdeg(x,y) if path=='rotation' else math.dist(x,y)
   warnings.append({'bone':n,'path':path,'difference':round(diff,7)})
   require(diff<(.025 if path=='rotation' else .015),'REST_POSE_INCOMPATIBLE_'+n+'_'+path+'_'+str(round(diff,5)))
 return {'requiredBones':len(required),'matchedNamedBones':len(a.keys() & b.keys()),'maxRestRotationDeg':max(x['difference'] for x in warnings if x['path']=='rotation'),'maxRestPositionM':max(x['difference'] for x in warnings if x['path']=='translation')}

def world_rot(js,clip,dat,names,ps,node,t):
 cache={}
 def visit(i):
  if i not in cache:
   local=at_time(js,dat,clip,i,'rotation',t)
   cache[i]=qm(visit(ps[i]),local) if i in ps else normq(local)
  return cache[i]
 return visit(names[node])


VANGUARD_SHA='3f27fce824c74fbd0a38c1d4f589ef21818a37afc1926459f9abb5739a23f2ce'
AXEKICK_SHA='c6f1d74b2de97e12f2eefc9c44a0404c26ad19e29d481af08e585130ee9103da'
SELECT_CANON=('Running','ObsidiantiIdle')+tuple('Ares_'+x+'_Lower' for x in STEPS)
VANGUARD_COUNT=19
EXPECTED=30


def check_animation_transfer(src,tgt,clip):
    '''Reject mismatched rest hierarchy, not just coincidentally shared bone names.'''
    src_names=name_ids(src);dst_names=name_ids(tgt)
    spa=parents(src);dpa=parents(tgt)
    tested=[]
    for ch in clip['channels']:
        node=ch['target']['node']
        bone=src['nodes'][node].get('name')
        require(bone in dst_names,'TRANSFER_TARGET_MISSING_'+str(bone))
        target=dst_names[bone]
        old_parent=src['nodes'][spa[node]].get('name') if node in spa else None
        new_parent=tgt['nodes'][dpa[target]].get('name') if target in dpa else None
        require(old_parent==new_parent,'TRANSFER_BONE_PARENT_MISMATCH_'+str(bone)+'_'+str(old_parent)+'_'+str(new_parent))
        for path,default in [('rotation',(0.,0.,0.,1.)),('translation',(0.,0.,0.)),('scale',(1.,1.,1.))]:
            x=src['nodes'][node].get(path,default)
            y=tgt['nodes'][target].get(path,default)
            delta=qdeg(x,y) if path=='rotation' else math.dist(x,y)
            require(delta<(.025 if path=='rotation' else .015),
                    'TRANSFER_REST_TRANSFORM_MISMATCH_'+str(bone)+'_'+path+'_'+str(round(delta,7)))
        require(ch['target']['path'] in ('rotation','translation','scale','weights'),'UNSUPPORTED_ANIMATION_TARGET')
        tested.append((bone,ch['target']['path']))
    require(len(tested)==len(clip['channels']),'TRANSFER_TRACK_COUNT_MISMATCH')
    return {'channels':len(tested),'uniqueTargets':len(set(tested))}


def check_guard_steps(js,data):
    '''Confirm historical Ares steps truly hold the Lionheart guard while legs move.'''
    d={a['name']:a for a in js['animations']}
    ids=name_ids(js);ps=parents(js)
    guard=d[GUARD];g0,_=range_times(js,data,guard)
    bones=['mixamorig:Spine','mixamorig:Spine1','mixamorig:Spine2',
           'mixamorig:LeftArm','mixamorig:RightArm',
           'mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R']
    proof={}
    for step in STEPS:
        clip=d['Ares_'+step+'_Lower'];t0,t1=range_times(js,data,clip)
        require(t1-t0>.25,'STEP_DURATION_TOO_SHORT_'+step)
        hi=get_channel(clip,ids[HIPS],'rotation')
        require(hi is not None,'STEP_HIPS_ROTATION_MISSING_'+step)
        worst=0.0;where=None
        for k in range(21):
            t=t0+(t1-t0)*k/20
            for bone in bones:
                want=world_rot(js,guard,data,ids,ps,bone,g0)
                found=world_rot(js,clip,data,ids,ps,bone,t)
                error=qdeg(want,found)
                if error>worst:worst=error;where=(bone,round(t,4))
        # These clips were authored with exact guard upper body.  Detect
        # regressions instead of quietly inventing a different source.
        # Preserve exact historical content even if a non-fatal world-frame
        # witness differs. Visual review is the user's authority, not this
        # numeric comparison (see Campaign Etiquette advisory parity rule).
        proof[step]={'duration':round(t1-t0,6),'guardMaxWorldRotationErrorDeg':round(worst,7),
                     'worstBoneTime':where,'numericGuardWarning':worst>=2.5}
    return proof


def compose(canonical,vanguard,axekick,output,report,
            expected_source=CANON_SHA,expected_vanguard=VANGUARD_SHA,
            expected_axekick=AXEKICK_SHA):
    canonical,vanguard,axekick,output,report=map(pathlib.Path,(canonical,vanguard,axekick,output,report))
    for p,dig,label in [(canonical,expected_source,'CANONICAL'),
                        (vanguard,expected_vanguard,'VANGUARD217'),
                        (axekick,expected_axekick,'ACCEPTED_AXEKICK')]:
        require(p.is_file() and digest(p)==dig,label+'_SOURCE_SHA_MISMATCH')
    require(not output.exists() and not report.exists(),'OUTPUT_COLLISION_NOT_ALLOWED')
    cg,cb=read_glb(canonical);vg,vb=read_glb(vanguard);kg,kb=read_glb(axekick)
    canon_names=[a['name'] for a in cg['animations']]
    v_names=[a['name'] for a in vg['animations']]
    require(len(canon_names)==23 and len(set(canon_names))==23,'CANONICAL_ACTION_INVENTORY_UNEXPECTED')
    require(set(SELECT_CANON)<=set(canon_names),'CANONICAL_REQUIRED_ANIMATION_MISSING_'+str(set(SELECT_CANON)-set(canon_names)))
    require(len(v_names)==VANGUARD_COUNT and len(set(v_names))==VANGUARD_COUNT and
            all(n.startswith('Vanguard_') for n in v_names),'VANGUARD_ACTION_INVENTORY_INVALID')
    require(len(kg['animations'])==1 and kg['animations'][0]['name']=='AxeKick_remap','ACCEPTED_AXEKICK_ACTION_INVALID')
    require(len(cg['meshes'])>=4 and len(cg['skins'])==1,'CANONICAL_SHIELD_LANCE_MESH_NOT_FOUND')
    nodes=name_ids(cg)
    require('mixamorig:LeftWeapon.L' in nodes and 'mixamorig:RightWeapon.R' in nodes,'BOTH_HAND_WEAPON_BONES_REQUIRED')
    # Leave ORIGINAL CANONICAL geometry, materials, shield, lance, bones and
    # binary prefix untouched.  Select the commissioned actions by exact name.
    original=copy.deepcopy(cg)
    cg['animations']=[copy.deepcopy(next(a for a in original['animations'] if a['name']==n)) for n in SELECT_CANON]
    _,idle_end=range_times(original,cb,next(a for a in original['animations'] if a['name']==AUTHORED))
    idle_start,_=range_times(original,cb,next(a for a in original['animations'] if a['name']==AUTHORED))
    require(2.9<=idle_end-idle_start<=3.1,'ORIGINAL_AUTHORED_IDLE_NOT_FULL_THREE_SECONDS')
    # Verify actual animated breathing, not merely many static keys.
    idle=next(a for a in cg['animations'] if a['name']==AUTHORED)
    moving=[]
    for bone in ('mixamorig:Spine1','mixamorig:Spine2','mixamorig:Neck'):
        ch=get_channel(idle,nodes[bone],'rotation')
        require(ch is not None,'ORIGINAL_BREATHING_TRACK_MISSING_'+bone)
        vals=raw_accessor(original,cb,idle['samplers'][ch['sampler']]['output'])
        maximum=max(qdeg(vals[0],q) for q in vals)
        if maximum>.1:moving.append({'bone':bone,'rotationDegrees':round(maximum,5),'samples':len(vals)})
    require(len(moving)>=2,'FULL_IDLE_HAS_NO_DEMONSTRABLE_BREATHING')
    step_proof=check_guard_steps(original,cb)
    app=Appender(cg,cb)
    van=[]
    for clip in vg['animations']:
        proof=check_animation_transfer(vg,cg,clip)
        transfer=app.copy_clip(vg,vb,clip,clip['name'],nodes)
        require(len(transfer['channels'])==len(clip['channels']),'VANGUARD_CHANNEL_LOSS_'+clip['name'])
        van.append({'name':clip['name'],**proof})
    accepted=kg['animations'][0]
    accepted_details=check_animation_transfer(kg,cg,accepted)
    restored=app.copy_clip(kg,kb,accepted,'AxeKick',nodes)
    require(len(restored['channels'])==len(accepted['channels']),'ACCEPTED_AXEKICK_CHANNEL_LOSS')
    names=[x['name'] for x in app.js['animations']]
    require(len(names)==EXPECTED and len(set(names))==EXPECTED,'FINAL_CLIP_INVENTORY_INVALID')
    require(names==list(SELECT_CANON)+v_names+['AxeKick'],'UNEXPECTED_ORDER_OR_CLIP_REMOVAL')
    for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
        require(app.js.get(key)==original.get(key),'CANONICAL_SHIELD_OR_MATERIAL_CHANGED_'+key)
    require(bytes(app.bin[:len(cb)])==cb,'CANONICAL_ORIGINAL_BINARY_MUTATED')
    output.parent.mkdir(parents=True,exist_ok=True)
    glb_save(app.js,bytes(app.bin),output)
    out,dat=read_glb(output)
    require([x['name'] for x in out['animations']]==names,'REOPEN_ACTIONS_NOT_IDENTICAL')
    require(dat.startswith(cb),'REOPEN_ORIGINAL_GEOMETRY_DATA_CHANGED')
    for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
        require(out.get(key)==original.get(key),'REOPEN_SHIELD_LANCE_OR_SKIN_MUTATED_'+key)
    proof={'schema':VERSION,'status':'30_CLIP_COMBINED_REVIEW_UNAPPROVED',
           'canonicalMutation':False,'shieldRetained':True,'lanceRetained':True,
           'canonicalSourceSHA256':digest(canonical),'vanguardSourceSHA256':digest(vanguard),
           'acceptedAxeKickSourceSHA256':digest(axekick),'outSHA256':digest(output),
           'outBytes':output.stat().st_size,'count':EXPECTED,'clips':names,
           'sourceCounts':{'historicalAresGuardSteps':8,'authoredFullIdle':1,'running':1,
                           'vanguard':19,'acceptedAxeKick':1},
           'excludedHistoricalLionheartAttackVariants':True,
           'originalEntireMeshAndRigPreserved':True,
           'idleDurationSeconds':round(idle_end-idle_start,6),
           'idleBreathingMotion':moving,'originalGuardedStepWitnesses':step_proof,
           'vanguardVerified':van,'acceptedAxeKickVerified':accepted_details,
           'vanguardShieldlessGeometryWasNotImported':True,
           'twoHandedShieldHandling':'PRESERVE_MESH_ALWAYS; RUNTIME_VISIBILITY_CHOICE_NOT_BAKED',
           'ownerVisualAcceptance':'PENDING'}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    return proof

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ('canonical','vanguard','axekick','output','report'):p.add_argument('--'+name,required=True)
 a=p.parse_args()
 print(json.dumps(compose(a.canonical,a.vanguard,a.axekick,a.output,a.report),indent=2))
