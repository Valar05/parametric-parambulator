#!/usr/bin/env python3
"""Non-destructive glTF2 animation variant authoring: geometry-driven toe-roll IK and AxeKick sole grounding.
Original 20 animation samplers, skin, meshes, nodes and BIN prefix are byte-identical.
No ARP call. This is an owner-requested experimental post-retarget fix, not generic automatic cleanup.
"""
from __future__ import annotations
import argparse,bisect,copy,hashlib,json,math,pathlib,struct

LION=['Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp']
SHOE_LENGTH={'Left':{'donor':.220,'target':.142},'Right':{'donor':.216,'target':.145}}
AXE='AxeKick'
DIMS={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
F={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def load(path):
 b=pathlib.Path(path).read_bytes()
 if len(b)<32 or b[:4]!=b'glTF':raise ValueError('NOT_GLB_2')
 magic,version,total=struct.unpack_from('<4sII',b)
 if version!=2 or total!=len(b):raise ValueError('BAD_GLB_HEADER')
 jlen,jtype=struct.unpack_from('<I4s',b,12)
 if jtype!=b'JSON' or jlen>30000000:raise ValueError('BAD_GLB_JSON')
 js=json.loads(b[20:20+jlen]);idx=20+jlen
 blen,btype=struct.unpack_from('<I4s',b,idx)
 if btype!=b'BIN\0' or idx+8+blen!=len(b):raise ValueError('BAD_GLB_BIN')
 return js,bytearray(b[idx+8:])
def assemble(js,blob,path):
 js['buffers'][0]['byteLength']=len(blob)
 doc=json.dumps(js,separators=(',',':'),ensure_ascii=False).encode('utf8');doc+=b' '*((-len(doc))%4)
 data=bytes(blob);data+=b'\0'*((-len(data))%4)
 size=12+8+len(doc)+8+len(data)
 pathlib.Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,size)+struct.pack('<I4s',len(doc),b'JSON')+doc+struct.pack('<I4s',len(data),b'BIN\0')+data)

def acc(js,blob,idx):
 a=js['accessors'][idx]
 if 'bufferView' not in a or a.get('sparse'):raise ValueError('SPARSE_OR_MISSING_ACCESSOR_'+str(idx))
 view=js['bufferViews'][a['bufferView']]
 if view.get('buffer',0)!=0:raise ValueError('MULTIBUFFER_UNSUPPORTED')
 comps=DIMS[a['type']];code=F[a['componentType']];esize=struct.calcsize('<'+code)
 stride=view.get('byteStride',comps*esize);offset=view.get('byteOffset',0)+a.get('byteOffset',0)
 if stride<comps*esize or offset+stride*(a['count']-1)+comps*esize>len(blob):raise ValueError('ACCESSOR_OVERRUN')
 rows=[list(struct.unpack_from('<'+code*comps,blob,offset+i*stride)) for i in range(a['count'])]
 if a.get('normalized') and a['componentType']!=5126:
  typ=a['componentType'];mx={5121:255,5123:65535,5120:127,5122:32767}.get(typ)
  if mx is None:raise ValueError('UNSUPPORTED_NORMALIZED_ACCESSOR')
  rows=[[max(-1.,x/mx) for x in row] for row in rows]
 return rows

def new_accessor(js,blob,ref,rows):
 src=js['accessors'][ref];comps=DIMS[src['type']]
 if src['componentType']!=5126:raise ValueError('NEW_TRACK_REQUIRES_FLOAT32')
 if any(len(v)!=comps or any(not math.isfinite(x) for x in v) for v in rows):raise ValueError('NONFINITE_OR_BAD_NEW_KEYS')
 if len(rows)!=src['count']:raise ValueError('ACCESSOR_COUNT_CHANGED')
 while len(blob)%4:blob.append(0)
 off=len(blob)
 for v in rows:blob.extend(struct.pack('<'+'f'*comps,*v))
 view={'buffer':0,'byteOffset':off,'byteLength':len(rows)*comps*4}
 js['bufferViews'].append(view)
 a=copy.deepcopy(src);a['bufferView']=len(js['bufferViews'])-1;a['byteOffset']=0
 for fld in ('min','max','normalized'):a.pop(fld,None)
 js['accessors'].append(a)
 return len(js['accessors'])-1

def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def scale(a,k):return [x*k for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def length(a):return math.sqrt(dot(a,a))
def unit(a):
 n=length(a)
 if n<1e-10:raise ValueError('DEGENERATE_VECTOR')
 return scale(a,1/n)
def qnorm(q):
 n=length(q)
 if n<1e-12:raise ValueError('ZERO_QUATERNION')
 return [x/n for x in q]
def qinv(a):return [-a[0],-a[1],-a[2],a[3]]
def qmul(a,b):
 x,y,z,w=a;u,v,t,s=b
 return [w*u+x*s+y*t-z*v,w*v-x*t+y*s+z*u,w*t+x*v-y*u+z*s,w*s-x*u-y*v-z*t]
def qrot(q,v):
 x,y,z,w=q
 t=scale(cross([x,y,z],v),2)
 return add(v,add(scale(t,w),cross([x,y,z],t)))
def qslerp(a,b,u):
 a=qnorm(a);b=qnorm(b);c=dot(a,b)
 if c<0:b=scale(b,-1);c=-c
 if c>.9995:return qnorm(add(scale(a,1-u),scale(b,u)))
 th=math.acos(max(-1.,min(1.,c)));s=math.sin(th)
 return qnorm(add(scale(a,math.sin((1-u)*th)/s),scale(b,math.sin(u*th)/s)))
def qarcto(a,b):
 a=unit(a);b=unit(b);d=max(-1.,min(1.,dot(a,b)))
 if d>1-1e-9:return [0.,0.,0.,1.]
 if d<-1+1e-8:
  v=cross(a,[1,0,0] if abs(a[0])<.8 else [0,1,0]);v=unit(v)
  return [*v,0.]
 return qnorm([*cross(a,b),1+d])
def qangle(a,b):return 2*math.acos(min(1,abs(dot(qnorm(a),qnorm(b)))))

def animation_samples(js,blob,anim):
 result={}
 for ch in anim['channels']:
  node=ch['target']['node'];path=ch['target']['path'];s=anim['samplers'][ch['sampler']]
  ts=[r[0] for r in acc(js,blob,s['input'])];vals=acc(js,blob,s['output'])
  if len(ts)!=len(vals) or len(ts)<2 or any(ts[i]>ts[i+1] for i in range(len(ts)-1)):raise ValueError('TRACK_SHAPE_INVALID')
  result[(node,path)]={'times':ts,'values':vals,'interp':s.get('interpolation','LINEAR'),'channel':ch,'sampler':s}
 return result

def sampled(track,t,path):
 ts=track['times'];v=track['values'];idx=bisect.bisect_left(ts,t)
 if idx<=0:return v[0]
 if idx>=len(ts):return v[-1]
 if abs(t-ts[idx])<1e-6:return v[idx]
 dt=ts[idx]-ts[idx-1]
 if dt<=1e-9:return v[idx]
 k=(t-ts[idx-1])/dt
 if track['interp']=='STEP':return v[idx-1]
 if track['interp']!='LINEAR':raise ValueError('CUBIC_SPLINE_NEEDS_EXPLICIT_BAKE')
 return qslerp(v[idx-1],v[idx],k) if path=='rotation' else add(scale(v[idx-1],1-k),scale(v[idx],k))

class Skeleton:
 def __init__(self,js):
  self.nodes=js['nodes'];self.names={n.get('name'):i for i,n in enumerate(self.nodes)}
  self.parents={child:i for i,n in enumerate(self.nodes) for child in n.get('children',[])}
  if any('matrix' in n for n in self.nodes):raise ValueError('MATRIX_TRANSFORM_NODES_NOT_SUPPORTED_IN_THIS_VERIFIED_SKELETON')
 def eval(self,tracks,t):
  ps={};qs={};ss={}
  def rec(i):
   if i in ps:return
   node=self.nodes[i];p=self.parents.get(i)
   if p is not None:rec(p)
   loc=sampled(tracks[(i,'translation')],t,'translation') if (i,'translation') in tracks else node.get('translation',[0,0,0])
   rot=qnorm(sampled(tracks[(i,'rotation')],t,'rotation') if (i,'rotation') in tracks else node.get('rotation',[0,0,0,1]))
   scl=sampled(tracks[(i,'scale')],t,'scale') if (i,'scale') in tracks else node.get('scale',[1,1,1])
   if p is None:ps[i]=list(loc);qs[i]=rot;ss[i]=list(scl)
   else:
    pp=ps[p];pq=qs[p];ps[i]=add(pp,qrot(pq,[loc[j]*ss[p][j] for j in range(3)]))
    qs[i]=qnorm(qmul(pq,rot));ss[i]=[ss[p][j]*scl[j] for j in range(3)]
  for i in range(len(self.nodes)):rec(i)
  return ps,qs,ss

def corrected_leg(scene,positions,quats,side,move):
 # One-step measured two-bone IK. Identical foot orientation; original rest skeleton unchanged.
 names=scene.names;ns=['mixamorig:'+side+x for x in ('UpLeg','Leg','Foot','ToeBase')]
 u,k,f,toe=[names[x] for x in ns];parent=scene.parents[u]
 H,K,A=[positions[i] for i in (u,k,f)];At=add(A,move)
 seg1=sub(K,H);seg2=sub(A,K);l1=length(seg1);l2=length(seg2);v=sub(At,H);d=length(v)
 if d>l1+l2-0.004 or d<abs(l1-l2)+.004:raise ValueError('TARGET_OUTSIDE_TWO_BONE_REACH')
 e=unit(v);a=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-a*a))
 lateral=sub(sub(K,H),scale(e,dot(sub(K,H),e)))
 if length(lateral)<1e-5:raise ValueError('KNEE_BEND_PLANE_UNDEFINED')
 Kt=add(H,add(scale(e,a),scale(unit(lateral),height)))
 qU=qnorm(qmul(qarcto(seg1,sub(Kt,H)),quats[u]))
 qL=qnorm(qmul(qarcto(seg2,sub(At,Kt)),quats[k]))
 qF=quats[f]  # preserve EXACT world foot orientation
 if qangle(qU,quats[u])>.42 or qangle(qL,quats[k])>.56:raise ValueError('SINGLE_FRAME_KNEE_OR_THIGH_ROTATION_TOO_LARGE')
 # New local quaternions; following original glTF hierarchy.
 localU=qnorm(qmul(qinv(quats[parent]),qU))
 localL=qnorm(qmul(qinv(qU),qL))
 localF=qnorm(qmul(qinv(qL),qF))
 # Analytic pose position check using original fixed rest translations.
 lK=scene.nodes[k].get('translation',[0,0,0]);lA=scene.nodes[f].get('translation',[0,0,0])
 Km=add(H,qrot(qU,lK));Am=add(Km,qrot(qL,lA))
 if length(sub(Am,At))>.005:raise ValueError('TWO_BONE_RECONSTRUCTION_PARITY_FAILED_'+str(round(length(sub(Am,At)),5)))
 return {u:localU,k:localL,f:localF}, {'ankleOffsetM':round(length(move),6),'reconstructedErrorM':round(length(sub(Am,At)),6),
   'thighRotationDeg':round(math.degrees(qangle(qU,quats[u])),4),'kneeRotationDeg':round(math.degrees(qangle(qL,quats[k])),4)}

def ease(x):
 x=max(0.,min(1.,x));return x*x*(3.-2*x)
def interp_contact(rows,phase,side):
 if not rows:raise ValueError('MISSING_DONOR_CONTACT_CURVE')
 z=phase*(len(rows)-1);i=min(int(z),len(rows)-2);v=z-i
 a=rows[i][side];b=rows[i+1][side]
 return {k:a[k]*(1-v)+b[k]*v for k in ('toeZ','ankleZ','idleToeZ','idleHeelAboveToe','ankleToeLength')}

def score_source_contact(item):
 toe=item['toeZ']-item['idleToeZ'];h=(item['ankleZ']-item['toeZ'])-item['idleHeelAboveToe']
 # Actual sampled native donor toe position against its Idle reference;
 # vertical roll amplitude normalized by the measured native toe-bone reach.
 contact=ease((.065-max(0.,toe))/.065)
 sin_roll=max(0.,min(.98,h/max(.08,item['ankleToeLength'])))
 return sin_roll*contact, {'toeGroundDisplacementM':round(toe,5),'heelRiseM':round(h,5),'contactConfidence':round(contact,4), 'sinRoll':round(sin_roll,5)}

def matrix_world(pos,q,s):
 x,y,z,w=q;xx=x*x;yy=y*y;zz=z*z;xy=x*y;xz=x*z;yz=y*z;wx=w*x;wy=w*y;wz=w*z
 return [[(1-2*(yy+zz))*s[0],2*(xy-wz)*s[1],2*(xz+wy)*s[2],pos[0]],
         [2*(xy+wz)*s[0],(1-2*(xx+zz))*s[1],2*(yz-wx)*s[2],pos[1]],
         [2*(xz-wy)*s[0],2*(yz+wx)*s[1],(1-2*(xx+yy))*s[2],pos[2]],
         [0.,0.,0.,1.]]
def matvec(m,v):return [sum(m[i][k]*v[k] for k in range(4)) for i in range(4)]
def mat_from_gltf(flat):return [[flat[j*4+i] for j in range(4)] for i in range(4)]
def matmul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def mesh_feet_at(js,blob,scene,anim,t):
 tracks=animation_samples(js,blob,anim);ps,qs,ss=scene.eval(tracks,t)
 skin=js['skins'][0];ibm=acc(js,blob,skin['inverseBindMatrices']);joints=skin['joints']
 jointmats=[matmul(matrix_world(ps[n],qs[n],ss[n]),mat_from_gltf(m)) for n,m in zip(joints,ibm)]
 nm={side:{i for i,n in enumerate(joints) if scene.nodes[n].get('name') in ('mixamorig:'+side+'Foot','mixamorig:'+side+'ToeBase','mixamorig:'+side+'Toe_End')} for side in ('Left','Right')}
 out={side:[] for side in nm}
 for node in scene.nodes:
  if 'mesh' not in node or node.get('skin')!=0:continue
  for prim in js['meshes'][node['mesh']]['primitives']:
   attrs=prim['attributes']
   if not all(k in attrs for k in ('POSITION','JOINTS_0','WEIGHTS_0')):continue
   coords=acc(js,blob,attrs['POSITION']);ids=acc(js,blob,attrs['JOINTS_0']);ws=acc(js,blob,attrs['WEIGHTS_0'])
   for v,jw,weights in zip(coords,ids,ws):
    associated={side for side,bones in nm.items() if any(int(ji) in bones and weight>=.12 for ji,weight in zip(jw,weights))}
    if not associated:continue
    p=[0.,0.,0.];tot=0.
    for ji,w in zip(jw,weights):
     if w<=0:continue
     q=matvec(jointmats[int(ji)],[*v,1.]);p=add(p,scale(q[:3],w));tot+=w
    if tot>.001:
     p=scale(p,1./tot)
     for side in associated:out[side].append(p[1])
 if any(len(out[x])<8 for x in out):raise ValueError('SHOE_SKINNED_VERTICES_MISSING_'+repr({x:len(y) for x,y in out.items()}))
 return {'sideMinY':{x:min(v) for x,v in out.items()},'minY':min(min(v) for v in out.values()),'counts':{x:len(v) for x,v in out.items()}}

def make(js,blob,contacts,report,output):
 src_j=copy.deepcopy(js);src_blob=bytes(blob);src_json=copy.deepcopy(src_j)
 scene=Skeleton(js);original_names=[a['name'] for a in js['animations']]
 required=['Lionheart_'+c for c in LION]
 if any(n not in original_names for n in required+[AXE]):raise ValueError('REQUIRED_ORIGINAL_ACTIONS_MISSING')
 initial_anim_count=len(js['animations']);stats={};prev_animation_count=initial_anim_count
 for clip in required:
  anim=next(a for a in js['animations'][:initial_anim_count] if a['name']==clip)
  tracks=animation_samples(js,blob,anim)
  all_ids=[scene.names['mixamorig:'+side+part] for side in ('Left','Right') for part in ('UpLeg','Leg','Foot')]
  times_by=[]
  for node in all_ids:
   tr=tracks.get((node,'rotation'))
   if tr is None:raise ValueError('MISSING_LEG_ROTATION_TRACK_'+clip+'_'+str(node))
   times_by.append(tr['times'])
  if any(len(t)!=len(times_by[0]) or any(abs(a-b)>1e-5 for a,b in zip(t,times_by[0])) for t in times_by):
   raise ValueError('LEG_ROTATION_KEY_TIME_GRID_MISMATCH_'+clip)
  times=times_by[0];end=max(times[-1]-times[0],1e-8)
  src=contacts['actions'].get(clip)
  if not src or len(src)<5:raise ValueError('SOURCE_DONOR_CONTACT_SAMPLES_MISSING_'+clip)
  variant=copy.deepcopy(anim);variant['name']=clip+'_ToeRoll'
  pernode={n:[] for n in all_ids};changes=[];rejected=[];surface=[]
  for ti,t in enumerate(times):
   ps,qs,ss=scene.eval(tracks,t)
   phase=(t-times[0])/end
   frame={'index':ti,'time':round(t,6),'sides':{}}
   for side in ('Left','Right'):
    contact=interp_contact(src,phase,side);sinweighted,src_metrics=score_source_contact(contact)
    L=SHOE_LENGTH[side];diff=L['donor']-L['target']
    # Conservative length-based compensation: original donor toe-to-ankle arc
    # minus target arc. The flat-footed baseline has ZERO correction.
    sinroll=max(0.,min(.98,src_metrics['sinRoll']));confidence=src_metrics['contactConfidence']
    vertical=-diff*sinroll*confidence
    fore=-diff*(1-math.sqrt(max(0.,1-sinroll*sinroll)))*confidence
    ankle=scene.names['mixamorig:'+side+'Foot'];toe=scene.names['mixamorig:'+side+'ToeBase']
    fwd=sub(ps[toe],ps[ankle]);fwd[1]=0.
    if length(fwd)>1e-8:fwd=unit(fwd)
    else:fwd=[0.,0.,1.]
    requested=add([0.,vertical,0.],scale(fwd,fore))
    nodequats={n:qnorm(sampled(tracks[(n,'rotation')],t,'rotation')) for n in [scene.names['mixamorig:'+side+x] for x in ('UpLeg','Leg','Foot')]}
    accepted=None;measure=None;applied=0
    # Adaptive bounded reach reduction: preserve current FK pose if a target
    # is unreachable or violates the anatomical-rotation guard.
    for factor in (1.,.8,.6,.4,.2,.1,.0):
     if factor==0:break
     try:
      new,measure=corrected_leg(scene,ps,qs,side,scale(requested,factor));accepted=new;applied=factor;break
     except ValueError:pass
    if accepted is None:accepted=nodequats
    for n in nodequats:pernode[n].append(accepted[n])
    if applied:changes.append({'frame':ti,'side':side,'offsetM':round(length(scale(requested,applied)),6),'factor':applied,'details':measure})
    elif length(requested)>.0005:rejected.append({'frame':ti,'side':side,'requestedM':round(length(requested),5),'reason':'REACH_OR_POSE_GUARD'})
    frame['sides'][side]={**src_metrics,'requestedOffsetM':round(length(requested),6),'appliedFactor':applied}
   surface.append(frame)
  # Record EXACT existing animation channel IDs; the candidate replaces ONLY
  # six rotation outputs (two legs x upper/lower/foot), not pelvis or any mesh.
  for ch in variant['channels']:
   node=ch['target']['node'];axis=ch['target']['path']
   if node not in pernode or axis!='rotation':continue
   original=anim['samplers'][ch['sampler']]
   oldaccessor=original['output'];newaccessor=new_accessor(js,blob,oldaccessor,pernode[node])
   # Animation deep copy has a unique sampler per channel in verified source.
   variant['samplers'][ch['sampler']]['output']=newaccessor
  js['animations'].append(variant)
  stats[clip]={'variant':variant['name'],'frames':len(times),'correctedSamples':len(changes),
   'maxOffsetM':max([x['offsetM'] for x in changes],default=0.),'rejected':rejected,
   'changedSampleDetails':changes,'sourceContactSamples':surface}
 # AxeKick: floor first frame by actual evaluated skinned weighted shoes.
 ax=next(a for a in js['animations'][:initial_anim_count] if a['name']==AXE)
 before=mesh_feet_at(src_j,src_blob,scene,ax,0.)
 shift=-before['minY']
 if not -1.2<shift<1.2:raise ValueError('AXEKICK_FLOOR_SHIFT_ABNORMAL_'+str(shift))
 var=copy.deepcopy(ax);var['name']='AxeKick_Floor'
 hips=scene.names['mixamorig:Hips'];match=[ch for ch in var['channels'] if ch['target']=={'node':hips,'path':'translation'}]
 if len(match)!=1:raise ValueError('NO_UNIQUE_AXEKICK_HIP_TRANSLATION')
 sample=var['samplers'][match[0]['sampler']];old=sample['output'];rows=acc(src_j,src_blob,old)
 # Parent SmartRigArmature is identity in the verified skinning coordinate system.
 parent=scene.parents[hips]
 pnode=scene.nodes[parent]
 if any(abs(x)>1e-6 for x in pnode.get('translation',[0,0,0])) or any(abs(x-y)>1e-6 for x,y in zip(pnode.get('rotation',[0,0,0,1]),[0,0,0,1])):
  raise ValueError('AXEKICK_HIPS_PARENT_NOT_WORLD_IDENTITY')
 shifted=[[v[0],v[1]+shift,v[2]] for v in rows]
 sample['output']=new_accessor(js,blob,old,shifted)
 js['animations'].append(var)
 # Original action bytes are identical; only animation extension and new output
 # accessor BIN suffix differ. No old sampler, skin or mesh was overwritten.
 if bytes(blob[:len(src_blob)])!=src_blob:raise ValueError('ORIGINAL_BIN_PREFIX_MUTATED')
 if js['animations'][:initial_anim_count]!=src_json['animations']:raise ValueError('ORIGINAL_ACTION_METADATA_CHANGED')
 for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
  if js.get(key)!=src_json.get(key):raise ValueError('ORIGINAL_MODEL_TOPOLOGY_CHANGED_'+key)
 assemble(js,blob,output)
 newj,newbin=load(output)
 if len(newj['animations'])!=initial_anim_count+len(required)+1:raise ValueError('VARIANT_COUNT_INCORRECT')
 floor_check=mesh_feet_at(newj,newbin,scene,var,0.)
 if abs(floor_check['minY'])>.002:raise ValueError('AXEKICK_FLOOR_MESH_PARITY_FAILED_'+str(floor_check['minY']))
 out={'schema':'OBSIDIANTI_TOE_ROLL_POST_ARP_v2.0.19','status':'UNAPPROVED_EXPERIMENT','sourceGLBSHA256':sha(report['input']),
      'outputSHA256':sha(output),'inputAnimations':initial_anim_count,'newAnimations':len(required)+1,
      'originalSampleBufferPreserved':True,'noReretarget':True,'noCanonicalChange':True,
      'ankleToeMeshLengths':SHOE_LENGTH,'lionheart':stats,'axeKick':{'originalPreserved':True,
      'shiftM':round(shift,7),'before':before,'after':floor_check,'variant':'AxeKick_Floor',
      'onlyHipTranslationAltered':True},
      'clipNames':[x['name'] for x in newj['animations']]}
 pathlib.Path(report['output']).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 return out

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--contacts',required=True);ap.add_argument('--output',required=True);ap.add_argument('--report',required=True);a=ap.parse_args()
 js,blob=load(a.source);contacts=json.loads(pathlib.Path(a.contacts).read_text())
 r=make(js,blob,contacts,{'input':a.source,'output':a.report},a.output)
 print('POST_ARP_TOE_CANDIDATE='+a.output+' SHA256='+r['outputSHA256']+' CLIPS='+str(len(r['clipNames'])),flush=True)
 print('AXEKICK_GROUND_OFFSET_M='+str(r['axeKick']['shiftM']),flush=True)
 for clip in LION:print('TOE_CORRECTED='+clip+' SAMPLES='+str(r['lionheart']['Lionheart_'+clip]['correctedSamples']),flush=True)
