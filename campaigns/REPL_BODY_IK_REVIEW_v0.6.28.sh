#!/data/data/com.termux/files/usr/bin/bash
# REPL_BODY_IK_REVIEW_v0.6.28, reviewed source only: never commit/deploy GLB.
set -Eeuo pipefail
printf '%s\n' 'CAMPAIGN=REPL_BODY_IK_REVIEW_v0.6.28' 'AUTHORITY=TERMUX_GIT_SOURCE_ONLY' 'CANONICAL_GLB_MUTATION=FORBIDDEN'
command -v python3 >/dev/null || { echo 'BLOCKED: python3 missing';exit 2; }
command -v sha256sum >/dev/null || { echo 'BLOCKED: sha256sum missing';exit 2; }
echo "LAUNCHER_SHA256=$(sha256sum "$0" | awk '{print $1}')"
TMP_ROOT="${TMPDIR:-${PREFIX:+$PREFIX/tmp}}"
TMP_ROOT="${TMP_ROOT:-/tmp}"
mkdir -p "$TMP_ROOT"
TMPDIR_REPL="$(mktemp -d "$TMP_ROOT/repl-body-ik-v0628-XXXXXXXX")"
trap 'rm -rf "$TMPDIR_REPL"' EXIT
export REPL_ENTRY_SCRIPT="$(readlink -f "$0")"
cat > "$TMPDIR_REPL/solver.py" <<'REPL_SOLVER_PY_EOF'
import sys, json, time, struct, hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R

from rig_physics import Rig,accessor
SOURCE=Path(__import__('os').environ['REPL_SOURCE_GLB'])
rig=Rig(SOURCE)
LEG={
'LF':(['Bone_016','Bone_015','Bone_014','Bone_013','Bone_012'],[('Bone_016','xyz'),('Bone_015','xy'),('Bone_014','x')]),
'RF':(['Bone_022','Bone_021','Bone_020','Bone_019','Bone_018'],[('Bone_022','xyz'),('Bone_021','xy'),('Bone_020','x')]),
'LH':(['Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'],[('Bone_027','xyz'),('Bone_026','xy'),('Bone_025','x')]),
'RH':(['Bone_032','Bone_031','Bone_030','Bone_029','Bone_028'],[('Bone_032','xyz'),('Bone_031','xy'),('Bone_030','x')]),
}
# phases in 32 frame period. body rotations remain in source local coordinates, same clips.
def body_angles(f,scale=1.):
 phase=2*np.pi*f/32
 # body weight exchange, pelvic lag, neck recoil. rotations in local axes xyz radians
 return {
 'Bone_000':np.deg2rad([-.5*np.sin(phase+.3), .4*np.sin(phase+.9), .4*np.sin(phase-.3)])*scale,
 'Bone_001':np.deg2rad([.9*np.sin(phase-.7), .8*np.sin(phase+.6),1.3*np.cos(phase-.3)])*scale,
 'Bone_002':np.deg2rad([-3.8*np.sin(phase+.1), 1.0*np.sin(phase+.6),1.4*np.cos(phase)])*scale,
 'Bone_004':np.deg2rad([2.9*np.sin(phase-1.1),1.1*np.cos(phase+.3),1.1*np.sin(phase-1.1)])*scale,
 'Bone_010':np.deg2rad([-2.8*np.sin(phase+.65),.5*np.cos(phase),.5*np.sin(phase+.15)])*scale,
 }
def add_rot(q,angles):return (R.from_quat(q)*R.from_rotvec(angles)).as_quat()
def body_pose(src,frame,scale):
 pose={k:np.array(v).copy() for k,v in src.items()}
 for bone,angle in body_angles(frame,scale).items():
  key=(rig.names[bone],'rotation')
  pose[key]=add_rot(pose.get(key,rig.nodes[rig.names[bone]].get('rotation',[0,0,0,1])),angle)
 return pose

def foot_transform(world,name):
 w=world[rig.names[name]];return w[:3,3],R.from_matrix(w[:3,:3]).as_quat()

def solve_leg(basepose,newpose,worldbase,leg,xinit=None,max_nfev=32):
 bones,active=LEG[leg];end=bones[-1];tip0,q0=foot_transform(worldbase,end)
 vars_=[(rig.names[name],axis) for name,axes in active for axis in axes]
 params=np.zeros(len(vars_)) if xinit is None else xinit
 baseq={n:np.array(basepose[(n,'rotation')]).copy() for n,_ in vars_}
 # 0.30 rad at proximal, 0.24 rad at middle, 0.16 rad near end
 bounds=np.array([.24 if i<3 else (.28 if i<5 else .25) for i in range(len(vars_))]);
 def apply(x):
  corrections={}
  for (node,axis),t in zip(vars_,x):
   corrections.setdefault(node,np.zeros(3))['xyz'.index(axis)]+=t
  for node,val in corrections.items():newpose[(node,'rotation')]=add_rot(baseq[node],val)
 def errors(x):
  apply(x)
  w=rig.world(newpose);tip,q=foot_transform(w,end)
  rot=(R.from_quat(q0).inv()*R.from_quat(q)).as_rotvec()
  # contact matters: foot endpoint mm and hoof orientation radians; small regularizer
  return np.r_[(tip-tip0)*5.0,rot*1.15,x*.015]
 fit=least_squares(errors,params,bounds=(-bounds,bounds),max_nfev=max_nfev,xtol=2e-5,ftol=2e-5,gtol=2e-5)
 apply(fit.x)
 w=rig.world(newpose);tip,q=foot_transform(w,end)
 rot_err=np.linalg.norm((R.from_quat(q0).inv()*R.from_quat(q)).as_rotvec())
 return fit.x, float(np.linalg.norm(tip-tip0)), float(np.rad2deg(rot_err)),fit.nfev

def patch(source,out,clip_results):
 import copy
 doc=copy.deepcopy(rig.doc); raw=rig.raw
 b=bytearray(raw)
 changes=[]
 for clip,result in clip_results.items():
  for ch in doc['animations'][clip]['channels']:
   tgt=ch['target'];name=rig.nodes[tgt['node']].get('name')
   if tgt['path']!='rotation' or name not in result:continue
   sample=doc['animations'][clip]['samplers'][ch['sampler']];ac=doc['accessors'][sample['output']];bv=doc['bufferViews'][ac['bufferView']]
   arr=result[name];assert arr.shape==(97,4)
   off=bv['byteOffset']+ac.get('byteOffset',0)
   old=b[off:off+arr.nbytes];b[off:off+arr.nbytes]=arr.astype('<f4').tobytes()
   if old!=b[off:off+arr.nbytes]:changes.append((clip,name))
  # New barrel rotation track (only clips 4+5), rest poses and all other clips preserved
  arr=result['Bone_001'];offset=len(b);b.extend(arr.astype('<f4').tobytes())
  bvi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':arr.nbytes})
  aci=len(doc['accessors']);doc['accessors'].append({'bufferView':bvi,'componentType':5126,'count':97,'type':'VEC4'})
  anim=doc['animations'][clip];time_ac=anim['samplers'][0]['input']
  spi=len(anim['samplers']);anim['samplers'].append({'input':time_ac,'output':aci,'interpolation':'LINEAR'})
  anim['channels'].append({'sampler':spi,'target':{'node':rig.names['Bone_001'],'path':'rotation'}})
  changes.append((clip,'Bone_001'))
 doc['buffers'][0]['byteLength']=len(b)
 text=json.dumps(doc,separators=(',',':')).encode('utf8');text+=b' '*((-len(text))%4)
 binary=bytes(b)+b'\0'*((-len(b))%4)
 header=struct.pack('<4sII',b'glTF',2,12+8+len(text)+8+len(binary))
 Path(out).write_bytes(header+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary)
 return changes

def solve(scale=1.,out='/mnt/data/repl_ik_candidate.glb'):
 start=time.time();result={};metrics={}
 for clip in (4,5):
  result[clip]={};stats=[]
  keys=[key for key in rig.anims[clip] if key[1]=='rotation']
  for frame in range(33):
   basepose=rig.sampled(clip,frame=frame)
   worldbase=rig.world(basepose)
   pose=body_pose(basepose,frame,scale)
   for leg in LEG:
    x,dis,rot,nfev=solve_leg(basepose,pose,worldbase,leg)
    stats.append(dict(f=frame,leg=leg,position_error=dis,rotation_error_deg=rot,nfev=nfev,max_delta_deg=float(np.rad2deg(np.max(abs(x))))))
   result[clip].setdefault('Bone_001',np.empty((97,4),dtype='<f4'))
   for i in (frame,frame+32,frame+64):
    if i<=96:result[clip]['Bone_001'][i]=pose[(rig.names['Bone_001'],'rotation')]
   for (node,path) in keys:
    name=rig.nodes[node].get('name')
    if path!='rotation' or (name not in body_angles(frame) and name not in [b for _,act in LEG.values() for b,_ in act]):continue
    result[clip].setdefault(name,np.empty((97,4),dtype='<f4'))
    for i in (frame, frame+32,frame+64):
     if i<=96:result[clip][name][i]=pose[(node,'rotation')]
  metrics[clip]={k:float(max(s[k] for s in stats)) for k in ('position_error','rotation_error_deg','max_delta_deg')}
  print('CLIP',clip,metrics[clip],'time',round(time.time()-start,1),flush=True)
 changes=patch(SOURCE,Path(out),result)
 print('OUTPUT',out,'sha',hashlib.sha256(Path(out).read_bytes()).hexdigest(),'changes',len(changes),flush=True)
 return metrics


REPL_SOLVER_PY_EOF
cat > "$TMPDIR_REPL/validator.py" <<'REPL_VALIDATOR_PY_EOF'
import sys, json, hashlib, numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation as R
from rig_physics import Rig, parse, accessor

def require(ok, reason):
 if not ok:raise RuntimeError('PHYSICAL_GATE_FAILED:'+reason)

def main(source, candidate, output):
 src=Rig(source);new=Rig(candidate)
 assert len(src.doc['animations'])==len(new.doc['animations'])==6
 require(len(src.nodes)==len(new.nodes)==53,'NODE_COUNT')
 require(len(src.joints)==len(new.joints)==50,'SKIN_COUNT')
 for x in ['meshes','skins','materials','textures','images','nodes']:
  require(src.doc[x]==new.doc[x],'PROTECTED_METADATA_'+x)
 # Original buffer bytes identical except the explicitly permitted rotation accessors.
 require(new.raw[:len(src.raw)] != src.raw,'NO_ANIMATION_CHANGE')
 old=np.frombuffer(src.raw,dtype=np.uint8);updated=np.frombuffer(new.raw[:len(src.raw)],dtype=np.uint8)
 allowed=np.zeros(len(src.raw),dtype=bool)
 legs={'LF':(['Bone_015','Bone_014','Bone_013','Bone_012'],8), 'RF':(['Bone_021','Bone_020','Bone_019','Bone_018'],24), 'LH':(['Bone_026','Bone_025','Bone_024','Bone_023'],0), 'RH':(['Bone_031','Bone_030','Bone_029','Bone_028'],16)}
 body={'Bone_000','Bone_002','Bone_004','Bone_010','Bone_001'}
 mutable=body|{b for n,_ in legs.values() for b in n[:3]}|{'Bone_016','Bone_022','Bone_027','Bone_032'}
 changes=[]
 for clip in range(6):
  a=src.doc['animations'][clip];b=new.doc['animations'][clip]
  if clip<=3:require(a==b,'PRESERVE_ORIGINAL_ANIM_'+str(clip))
  new_channels=[]
  for ch in b['channels']:
   name=new.doc['nodes'][ch['target']['node']].get('name')
   if name=='Bone_001' and clip in (4,5) and ch['target']['path']=='rotation':new_channels.append(ch)
  require(len(new_channels)==(1 if clip in (4,5) else 0),'NEW_BARREL_TRACK')
  for ch in a['channels']:
   target=ch['target'];name=src.doc['nodes'][target['node']]['name'];kind=target['path']
   require(ch in b['channels'],'EXISTING_CHANNEL_REMOVED')
   ac=src.doc['accessors'][a['samplers'][ch['sampler']]['output']];bv=src.doc['bufferViews'][ac['bufferView']]
   off=bv['byteOffset']+ac.get('byteOffset',0);n=ac['count']*4*{'SCALAR':1,'VEC3':3,'VEC4':4}.get(ac['type'],1)
   if clip in (4,5) and kind=='rotation' and name in mutable:
    allowed[off:off+n]=True
    if not np.array_equal(old[off:off+n],updated[off:off+n]):changes.append([clip,name])
   else:require(np.array_equal(old[off:off+n],updated[off:off+n]),'LOCKED_TRACK_CHANGED_'+str((clip,name,kind)))
 require(np.array_equal(old[~allowed],updated[~allowed]),'NONCHANNEL_BYTES_MODIFIED')
 require(len(changes)>=20,'COMPENSATING_IK_TRACKS_NOT_PRESENT')
 # Exact source skinning rather than theoretical IK target positions.
 patches={};mesh=src.mesh[0]
 for leg,(names,start) in legs.items():
  ji=[src.joints.index(src.names[n]) for n in names[-2:]]
  w=np.where(np.isin(mesh['J'],ji),mesh['W'],0).sum(axis=1)
  ids=np.where(w>.1)[0];p,_=src.skin(src.sampled(5,frame=start+4));floor=p[ids,1].min()
  ids=ids[p[ids,1]<floor+.055];require(len(ids)>=35,'TOO_FEW_FOOT_PATCH_VERTICES_'+leg);patches[leg]=ids
 def skin_patch(r,w,leg):
  ids=patches[leg];m=r.mesh[0];mat=w[r.joints]@r.invbind;v=np.c_[m['xyz'][ids],np.ones(len(ids))];p=np.zeros((len(ids),3))
  for j in range(4):p+=np.einsum('nij,nj->ni',mat[m['J'][ids,j]],v)[:,:3]*m['W'][ids,j,None]
  return p
 report={'source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),'samples':0,'changes':changes,'per_leg':{},'status':'PHYSICAL_PASS_HUMAN_REVIEW_PENDING'}
 for clip in (4,5):
  b={l:[] for l in legs};a={l:[] for l in legs}
  for half in range(193):
   t=half*.02
   w0=src.world(src.sampled(clip,time=t));w1=new.world(new.sampled(clip,time=t))
   for leg in legs:
    a[leg].append(skin_patch(src,w0,leg));b[leg].append(skin_patch(new,w1,leg));report['samples']+=1
  for leg,(_,start) in legs.items():
   va=np.asarray(a[leg]);vb=np.asarray(b[leg]);f=np.arange(193)*.5
   phase=(f-start)%32;stance=(phase>=3)&(phase<=18);swing=(phase>=21)&(phase<=30)
   sole=vb[:,:,1].min(axis=1);drift=np.linalg.norm(va-vb,axis=2)
   mx=float(drift[stance].max());span=0.
   for cyc in range(3):
    selected=(f-start-32*cyc>=3)&(f-start-32*cyc<=18)
    if np.sum(selected)>3:span=max(span,float(np.ptp(vb[selected,:,2].mean(axis=1))))
   met={'stance_patch_delta_max':mx,'stance_z_spread_max':span,'stance_sole_min':float(sole[stance].min()),'stance_sole_max':float(sole[stance].max()),'swing_sole_min':float(sole[swing].min()),'patch_vertices':len(patches[leg])}
   report['per_leg'][str(clip)+'_'+leg]=met
   require(mx<=.009,'STANCE_PATCH_DELTA_'+str((clip,leg,mx)))
   require(span<=.013,'STANCE_Z_SLIP_'+str((clip,leg,span)))
   require(met['stance_sole_min']>=-.006 and met['stance_sole_max']<=.015,'GROUND_PLANE_'+str((clip,leg)))
   require(met['swing_sole_min']>=.012,'SWING_CLEARANCE_'+str((clip,leg)))
 # Preserve cycle continuity and avoid introducing implausible new angular steps.
 for clip in (4,5):
  for k,d in new.anims[clip].items():
   if k[1]!='rotation':continue
   q=d['v'];cur=(R.from_quat(q[:-1]).inv()*R.from_quat(q[1:])).magnitude()
   if k in src.anims[clip]:
    oldq=src.anims[clip][k]['v'];base=(R.from_quat(oldq[:-1]).inv()*R.from_quat(oldq[1:])).magnitude()
    require(float(np.max(cur-base))<=np.deg2rad(6.1),'JOINT_STEP_REGRESSION_'+new.nodes[k[0]]['name'])
  for key,d in new.anims[clip].items():
   if key[1]=='rotation':require(float(np.max(np.abs(d['v'][0]-d['v'][32])))<1e-5 and float(np.max(np.abs(d['v'][0]-d['v'][64])))<1e-5,'CYCLIC_ROTATION_'+new.nodes[key[0]]['name'])
 # Verify material body displacement, not just rotation key presence.
 weighted={}
 for name in ['Bone_001','Bone_002','Bone_004','Bone_010']:
  ji=src.joints.index(src.names[name]);w=(mesh['W']*(mesh['J']==ji)).sum(axis=1);ids=np.where(w>.25)[0]
  if len(ids)<10:continue
  vals=[]
  for frame in (6,14,22,30):
   p0,_=src.skin(src.sampled(5,frame=frame));p1,_=new.skin(new.sampled(5,frame=frame))
   vals.append(float(np.median(np.linalg.norm(p1[ids]-p0[ids],axis=1))))
  weighted[name]=max(vals)
 report['body_median_vertex_displacement_peak']=weighted
 require(weighted['Bone_002']>.018 and weighted['Bone_004']>.018 and weighted['Bone_001']>.004,'TORSO_MOVEMENT_TOO_SMALL')
 require(report['samples']==1544,'WRONG_SAMPLE_COUNT')
 Path(output).write_text(json.dumps(report,indent=2)+'\n')
 print('REAL_SKINNED_IK_VALIDATION=PASS; HALF_FRAME_SAMPLES='+str(report['samples']),flush=True)
 return report
if __name__=='__main__':main(*sys.argv[1:4])

REPL_VALIDATOR_PY_EOF
cat > "$TMPDIR_REPL/review_renderer.py" <<'REPL_REVIEW_RENDERER_PY_EOF'
import numpy as np, io, sys
from PIL import Image,ImageDraw
from rig_physics import Rig

def texture(r,idx):
  img=r.doc['images'][idx];bv=r.doc['bufferViews'][img['bufferView']];return Image.open(io.BytesIO(r.raw[bv['byteOffset']:bv['byteOffset']+bv['byteLength']])).convert('RGB')

def render(r,frame,clip=5,output='/tmp/repl.png',width=850,height=590,clay=False):
  zbuf=np.ones((height,width),dtype=np.float32)*-9999
  rgb=np.full((height,width,3),235,dtype=np.uint8)
  images=[np.asarray(texture(r,j)) for j in range(len(r.doc['images']))]
  for mi,m in enumerate(r.mesh):
    v,world=r.skin(r.sampled(clip,frame=frame),mesh_i=mi)
    # True world-space UV projected from the exact skinned mesh, no invented geometry.
    pix=np.stack([(v[:,2]-0.36)*200+width*.5,height*.90-v[:,1]*206],axis=1)
    tri=m['tri'];p=pix[tri];vv=v[tri]
    cross=(p[:,1,0]-p[:,0,0])*(p[:,2,1]-p[:,0,1])-(p[:,1,1]-p[:,0,1])*(p[:,2,0]-p[:,0,0])
    n=np.cross(vv[:,1]-vv[:,0],vv[:,2]-vv[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]+1e-10
    light=np.array([.6,.75,.58]);light/=np.linalg.norm(light)
    shade=.52+.48*np.maximum(0,n@light)
    mat=r.doc['materials'][r.doc['meshes'][mi]['primitives'][0]['material']]
    texid=r.doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    tex=images[texid];th,tw=tex.shape[:2];uv=m['uv'][tri]
    depth=vv[:,:,0] # camera looks from +X
    for i in range(len(tri)):
      if abs(cross[i])<.05:continue
      x0,y0=p[i,0];x1,y1=p[i,1];x2,y2=p[i,2]
      xmin=max(0,int(np.floor(min(x0,x1,x2))));xmax=min(width-1,int(np.ceil(max(x0,x1,x2))))
      ymin=max(0,int(np.floor(min(y0,y1,y2))));ymax=min(height-1,int(np.ceil(max(y0,y1,y2))))
      if xmax<xmin or ymax<ymin:continue
      yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1];fx=xx+.5;fy=yy+.5
      den=cross[i]
      w1=((fx-x0)*(y2-y0)-(fy-y0)*(x2-x0))/den
      w2=((x1-x0)*(fy-y0)-(y1-y0)*(fx-x0))/den
      w0=1-w1-w2
      inside=(w0>=-1.e-5)&(w1>=-1.e-5)&(w2>=-1.e-5)
      d=w0*depth[i,0]+w1*depth[i,1]+w2*depth[i,2]
      zlocal=zbuf[ymin:ymax+1,xmin:xmax+1]
      mask=inside&(d>zlocal)
      if not np.any(mask):continue
      ix=xx[mask];iy=yy[mask]
      zbuf[iy,ix]=d[mask]
      u=w0[mask]*uv[i,0,0]+w1[mask]*uv[i,1,0]+w2[mask]*uv[i,2,0]
      vv1=w0[mask]*uv[i,0,1]+w1[mask]*uv[i,1,1]+w2[mask]*uv[i,2,1]
      tx=np.minimum(tw-1,np.maximum(0,np.rint(u*(tw-1)).astype(int)))
      ty=np.minimum(th-1,np.maximum(0,np.rint((1-vv1)*(th-1)).astype(int)))
      color=(np.full((len(tx),3),[0.67,0.73,0.80],dtype=np.float32) if clay else tex[ty,tx].astype(np.float32)/255)
      # Exposure applied only for inspection, preserving original texels in source assets
      color=np.power(np.clip(color*1.3*shade[i],0,1),.78)*255
      rgb[iy,ix,:]=np.clip(color,0,255).astype(np.uint8)
  img=Image.fromarray(rgb)
  img.save(output)
  return output

REPL_REVIEW_RENDERER_PY_EOF
cat > "$TMPDIR_REPL/viewer.html" <<'REPL_VIEWER_HTML_EOF'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Repl body + IK · synchronized textured review</title>
<style>:root{color-scheme:dark;background:#0e1420;color:#eff4ff;font:16px system-ui,sans-serif}*{box-sizing:border-box}body{margin:0}header,footer,.toolbar{padding:10px 14px}h1{font-size:1.2rem;margin:3px 0}p{margin:4px 0;color:#cad5e5}button,select,input{font:inherit;min-height:40px}button,select{background:#26354b;color:white;border:1px solid #8aa3c5;border-radius:7px;padding:6px 10px}button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid #efcb6e}.toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.toolbar label{display:flex;gap:7px;align-items:center}#timeline{min-width:130px;flex:1}#viewport{width:100%;height:68vh;min-height:420px;display:block;touch-action:none;background:#d6dde5}#status{font-weight:600;color:#92e8cf;min-height:24px}.labels{display:grid;grid-template-columns:1fr 1fr;background:#111a28;font-weight:bold;text-align:center}.labels>span{padding:8px}.labels>span:first-child{border-right:1px solid #657387}.legend{font-size:.89rem}small{color:#bcd0e3}</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script></head><body>
<header><h1>Repl · full-rate body / IK inspection</h1><p>Actual original textures and skinned geometry. Synchronized before/after at the full display refresh rate, no contact-sheet sampling.</p><div id="status" role="status" aria-live="polite">Loading exact source GLBs…</div></header>
<div class="toolbar"><label>Clip <select id="clip"><option value="5" selected>Integrated traveling walk</option><option value="4">Body transfer walk</option><option value="3">Leg gait (unchanged)</option></select></label><label>View <select id="view"><option value="side" selected>Side</option><option value="three">Three-quarter</option><option value="front">Front</option><option value="rear">Rear</option><option value="top">Top</option></select></label><label>Speed <select id="speed"><option value=".25">¼×</option><option value=".5">½×</option><option value="1" selected>1×</option><option value="1.5">1½×</option></select></label><button id="play">Pause</button><button id="restart">Restart</button><label><input type="checkbox" id="follow" checked>Follow traveling horse</label></div>
<div class="toolbar"><label>Time <span id="timelabel">0.00s</span></label><input id="timeline" aria-label="Animation timeline" type="range" min="0" max="3.84" step=".005" value="0"><button id="frame">Save full-resolution PNG</button><button id="record">Record 30 FPS WebM</button></div>
<div class="labels"><span>BEFORE · v0.6.24</span><span>AFTER · body + compensated IK (NOT APPROVED)</span></div>
<canvas id="viewport" role="img" aria-label="Two synchronized interactive textured 3D horses; orbit with touch, pinch to zoom, and scrub timeline"></canvas>
<footer><p class="legend">One-finger drag: orbit both cameras. Pinch or mouse wheel: zoom. The same pose time and camera apply to both sides. Both GLBs preserve the original 2048 × 2048 texture images. Camera and lighting are identical for fair comparison.</p><small>Review only: neither model changes the GitHub canonical Repl.glb. Playback renders every display frame in your browser. Video recording runs at 30 FPS when supported.</small></footer>
<script type="module">
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $=id=>document.getElementById(id),canvas=$('viewport'),status=$('status');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
const scenes=[],cameras=[],mixers=[],actions=[],models=[];let duration=3.84,time=0,playing=true,last=performance.now(),followZ=0,recorder=null,parts=[];
for(let i=0;i<2;i++){let scene=new THREE.Scene();scene.background=new THREE.Color(0xd5dce5);scene.add(new THREE.HemisphereLight(0xffffff,0x63768b,2.3));let a=new THREE.DirectionalLight(0xfff1db,3);a.position.set(3,6,6);scene.add(a);let b=new THREE.DirectionalLight(0xd6e5ff,1.1);b.position.set(-4,4,-5);scene.add(b);let ground=new THREE.GridHelper(10,40,0x7f8c9e,0xb7c3cd);ground.position.y=-.003;scene.add(ground);scenes.push(scene);cameras.push(new THREE.PerspectiveCamera(38,1,.02,100));}
const orbit=new OrbitControls(cameras[0],canvas);orbit.enableDamping=true;orbit.enablePan=true;orbit.minDistance=.3;orbit.maxDistance=25;
function syncCameras(){cameras[1].position.copy(cameras[0].position);cameras[1].quaternion.copy(cameras[0].quaternion);cameras[1].projectionMatrix.copy(cameras[0].projectionMatrix);cameras[1].projectionMatrixInverse.copy(cameras[0].projectionMatrixInverse);}
function resize(){const w=Math.max(2,canvas.clientWidth),h=Math.max(2,canvas.clientHeight);renderer.setSize(w,h,false);for(const c of cameras){c.aspect=w/2/h;c.updateProjectionMatrix()}syncCameras();}
window.addEventListener('resize',resize);resize();
function viewPreset(){if(!models.length)return;const bounds=new THREE.Box3().setFromObject(models[0]);let center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());let r=Math.max(2.6,size.length()*.75);let vectors={side:[1.8,.2,.06],three:[1.3,.5,1.3],front:[.05,.3,1.9],rear:[.05,.3,-1.9],top:[.08,2.2,.15]};let v=vectors[$('view').value];orbit.target.copy(center);cameras[0].position.set(center.x+v[0]*r,center.y+v[1]*r,center.z+v[2]*r);cameras[0].lookAt(orbit.target);orbit.update();syncCameras();followZ=0;}
function selectClip(){if(models.length!==2)return;let idx=Number($('clip').value);for(let i=0;i<2;i++){mixers[i].stopAllAction();actions[i]=mixers[i].clipAction(models[i].animations[idx]);actions[i].reset();actions[i].setLoop(THREE.LoopOnce,1);actions[i].clampWhenFinished=true;actions[i].play();}time=0;duration=Math.min(models[0].animations[idx].duration,models[1].animations[idx].duration);$('timeline').max=duration;playing=true;$('play').textContent='Pause';viewPreset();seek(0);}
function seek(t){time=Math.max(0,Math.min(duration,t));for(const m of mixers)m.setTime(time);$('timeline').value=time;$('timelabel').textContent=time.toFixed(2)+'s';}
$('clip').addEventListener('change',selectClip);$('view').addEventListener('change',viewPreset);$('play').addEventListener('click',()=>{if(time>=duration-.001)seek(0);playing=!playing;$('play').textContent=playing?'Pause':'Play';});$('restart').addEventListener('click',()=>{seek(0);playing=true;$('play').textContent='Pause';});$('timeline').addEventListener('input',()=>{playing=false;$('play').textContent='Play';seek(Number($('timeline').value));});
$('frame').addEventListener('click',()=>{draw();const a=document.createElement('a');a.download='Repl_IK_before_after_'+time.toFixed(2)+'s.png';a.href=canvas.toDataURL('image/png');document.body.append(a);a.click();a.remove();});
$('record').addEventListener('click',()=>{if(recorder&&recorder.state==='recording'){recorder.stop();return}if(!window.MediaRecorder||!canvas.captureStream){status.textContent='This browser does not support video recording';return}let types=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'];let mime=types.find(t=>MediaRecorder.isTypeSupported(t));if(!mime){status.textContent='No supported WebM recorder';return}seek(0);playing=true;parts=[];recorder=new MediaRecorder(canvas.captureStream(30),{mimeType:mime,videoBitsPerSecond:6000000});recorder.ondataavailable=e=>{if(e.data.size)parts.push(e.data)};recorder.onstop=()=>{let blob=new Blob(parts,{type:mime});let u=URL.createObjectURL(blob);let a=document.createElement('a');a.href=u;a.download='Repl_Body_IK_30fps_before_after.webm';a.click();setTimeout(()=>URL.revokeObjectURL(u),6000);$('record').textContent='Record 30 FPS WebM'};recorder.start(200);$('record').textContent='Stop and save recording';status.textContent='Recording synchronized 30 FPS comparison';});
function draw(){let w=canvas.width,h=canvas.height,half=Math.floor(w/2);renderer.setScissorTest(true);for(let i=0;i<2;i++){renderer.setViewport(i*half,0,i===0?half:w-half,h);renderer.setScissor(i*half,0,i===0?half:w-half,h);renderer.render(scenes[i],cameras[i]);}renderer.setScissorTest(false);}
function frame(t){requestAnimationFrame(frame);const dt=Math.min((t-last)/1000,.05);last=t;if(models.length!==2)return;if(playing){let next=time+dt*Number($('speed').value);seek(next);if(next>=duration){playing=false;$('play').textContent='Replay';if(recorder&&recorder.state==='recording')recorder.stop();}}
 orbit.update();if($('follow').checked){let z=0;const body=models[0].scene.getObjectByName('Bone_000');if(body){body.updateWorldMatrix(true,false);z=body.getWorldPosition(new THREE.Vector3()).z;}let diff=z-followZ;orbit.target.z+=diff;cameras[0].position.z+=diff;followZ=z;}
 syncCameras();draw();}
async function load(path){return await new GLTFLoader().loadAsync(path)}
try{const files=['./Repl_body_v0.6.24_before.glb','./Repl_BODY_IK_UNACCEPTED_v0.6.27.glb'];const loaded=await Promise.all(files.map(load));for(let i=0;i<2;i++){let g=loaded[i];models.push(g);scenes[i].add(g.scene);g.scene.traverse(o=>{if(o.isSkinnedMesh||o.isMesh)o.frustumCulled=false;});mixers.push(new THREE.AnimationMixer(g.scene));}selectClip();status.textContent='Both genuine textured GLBs loaded. Full-rate 3D review ready.';requestAnimationFrame(frame);}catch(e){status.textContent='Unable to load comparison GLBs: '+String(e);console.error(e)}
</script></body></html>

REPL_VIEWER_HTML_EOF
cat > "$TMPDIR_REPL/driver.py" <<'REPL_DRIVER_PY_EOF'
import os,sys,hashlib,json,zipfile,tempfile,shutil,subprocess,time
from pathlib import Path
from PIL import Image,ImageDraw
PREFIX='REPL_BODY_ENGAGEMENT_v0.6.24/'
ZIP_SHA='0b306b7038b7c642f348ab38543541cd01292302cf173c4ae2a81a48f79c5f86'
BODY_SHA='eb87ae7643e01cb546616d3b3a17dd2936fb00e01c87cc6a996bfebc8e518675'
GAIT_SHA='ba06833ee321d5f0b95498f6f58a0d5939a512048a43ef7524a7910d6506bfcc'
HEAD='27854f5ecbdb3ec2f11a16877d5e8a723f144ddd'
CANON='50d26053027296895fd8853e7337a1fcbfba8e77a63aea095680b19b3d113dd4'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
CAMPAIGN='REPL_BODY_IK_REVIEW_v0.6.28'

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def need(ok,msg):
 if not ok:raise RuntimeError('BLOCKED:'+msg)
def run(args,**kwargs):
 return subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kwargs)

def publish_source(script,receipt):
 """Publish ONLY this immutable review source from a fresh isolated checkout.
 A new remote HEAD is normal; governing AGENTS and canonical asset identity
 are the actual hard gates. On concurrent non-fast-forward updates retry safely.
 """
 if os.environ.get('REPL_HOST_TEST')=='1':return {'state':'HOST_TEST_NO_REMOTE_MUTATION'}
 need(shutil.which('git'),'GIT_NOT_INSTALLED_FOR_SOURCE_PUBLICATION')
 remote='https://github.com/Valar05/parametric-parambulator.git'
 env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0'
 last_error='UNATTEMPTED'
 for attempt in range(1,4):
  with tempfile.TemporaryDirectory(prefix='repl-ik-git-') as temp:
   gitdir=Path(temp)/'repository'
   cp=run(['git','-c','core.autocrlf=false','clone','--depth','1','--filter=blob:none','--branch','main',remote,str(gitdir)],env=env,timeout=150)
   need(cp.returncode==0,'GIT_ISOLATED_CLONE:'+cp.stdout[-350:])
   current=run(['git','-C',str(gitdir),'rev-parse','HEAD'],env=env)
   need(current.returncode==0,'GIT_HEAD_READ')
   remotehead=current.stdout.strip()
   target=gitdir/'campaigns'/script.name
   if target.exists():
    if sha(target)==sha(script):
     receipt['source_git_commit']=remotehead
     print('GIT_SOURCE_ALREADY_PRESENT_AND_VERIFIED='+remotehead,flush=True)
     return {'state':'SOURCE_ONLY_ALREADY_PUBLISHED','commit':remotehead,'model_deployed':False}
    raise RuntimeError('BLOCKED:CAMPAIGN_FILENAME_COLLISION_DIFFERENT_BYTES')
   # File-level authority checks, not exact HEAD equality.
   ag=gitdir/'AGENTS.md';need(ag.exists(),'AGENTS_FILE_MISSING')
   agsha=run(['git','-C',str(gitdir),'hash-object','AGENTS.md'],env=env)
   need(agsha.returncode==0 and agsha.stdout.strip()==AGENTS_BLOB,'AGENTS_REVISION_CHANGED')
   manifest=json.loads((gitdir/'assets/repl/CANONICAL_MODEL.json').read_text())
   need(manifest['active_model']['sha256']==CANON,'CANONICAL_MANIFEST_HASH_CHANGED')
   model_blob=run(['git','-C',str(gitdir),'rev-parse','HEAD:assets/repl/Repl.glb'],env=env)
   need(model_blob.returncode==0 and model_blob.stdout.strip()==manifest['active_model']['git_blob_sha1'],
        'CANONICAL_MODEL_BLOB_CHANGED')
   receipt['publication_source_head']=remotehead
   print('REMOTE_HEAD='+remotehead+'; GOVERNING_RULES_AND_CANONICAL_MODEL=UNCHANGED',flush=True)
   target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(script.read_bytes());need(sha(target)==sha(script),'SCRIPT_COPY_HASH')
   cp=run(['git','-C',str(gitdir),'add','--',str(target.relative_to(gitdir))],env=env)
   need(cp.returncode==0,'GIT_ADD:'+cp.stdout[-250:])
   staged=run(['git','-C',str(gitdir),'diff','--cached','--name-only'],env=env)
   need(staged.stdout.strip()==str(target.relative_to(gitdir)),'STAGED_FILE_SCOPE')
   cp=run(['git','-C',str(gitdir),'commit','-m','Add Repl v0.6.28 full-frame IK review and interactive viewer campaign'],env=env)
   need(cp.returncode==0,'GIT_COMMIT:'+cp.stdout[-350:])
   commit=run(['git','-C',str(gitdir),'rev-parse','HEAD'],env=env).stdout.strip()
   cp=run(['git','-C',str(gitdir),'push','origin','HEAD:refs/heads/main'],env=env,timeout=150)
   if cp.returncode:
    last_error=cp.stdout[-400:]
    print('GIT_PUSH_RETRY_ATTEMPT='+str(attempt)+' '+last_error,flush=True)
    # Reclone and revalidate all authority and asset gates. Never force push.
    continue
   read=run(['git','ls-remote',remote,'refs/heads/main'],env=env,timeout=60)
   need(read.returncode==0 and read.stdout.split()[0]==commit,'REMOTE_COMMIT_READBACK')
   # Verify immutable source against the actual remote branch after push.
   cp=run(['git','-C',str(gitdir),'fetch','-q','origin','main'],env=env,timeout=60)
   need(cp.returncode==0,'REMOTE_FETCH_AFTER_PUSH')
   readback=run(['git','-C',str(gitdir),'show','FETCH_HEAD:'+str(target.relative_to(gitdir))],env=env)
   need(readback.returncode==0 and hashlib.sha256(readback.stdout.encode()).hexdigest()==sha(script),'REMOTE_SOURCE_READBACK')
   receipt['source_git_commit']=commit
   return {'state':'SOURCE_ONLY_PUBLISHED','commit':commit,'model_deployed':False}
 raise RuntimeError('BLOCKED:GIT_PUSH_RETRIES_EXHAUSTED_LOCAL_WORK_PRESERVED:'+last_error)

def main():
 import numpy,scipy,PIL
 script=Path(os.environ['REPL_ENTRY_SCRIPT']).resolve()
 downloads=Path(sys.argv[1]) if len(sys.argv)>1 else Path.home()/'storage'/'downloads'
 need(downloads.is_dir(),'SHARED_DOWNLOADS_NOT_FOUND')
 matches=[]
 for p in sorted(downloads.glob('REPL_BODY_ENGAGEMENT_v0.6.24*.zip')):
  if p.is_file() and sha(p)==ZIP_SHA:matches.append(p)
 need(matches,'REQUIRED_V0624_PACKET_MISSING_OR_HASH_WRONG')
 source=matches[0];out=downloads/CAMPAIGN
 if out.exists():
  receipt=out/'receipt.json'
  if receipt.exists():
   r=json.loads(receipt.read_text())
   if r.get('zip_sha256')==ZIP_SHA and all((out/n).is_file() and sha(out/n)==h for n,h in r.get('outputs',{}).items()):
    print('VERIFIED_EXISTING_REVIEW='+str(out));print('STATUS=REVIEW_REUSED_NO_MODEL_DEPLOYMENT');return
  raise RuntimeError('DESTINATION_COLLISION_NO_OVERWRITE:'+str(out))
 stage=Path(tempfile.mkdtemp(prefix='.'+CAMPAIGN+'-',dir=str(downloads)))
 try:
  with tempfile.TemporaryDirectory(prefix='repl-ik-scratch-') as tmp:
   priv=Path(tmp)
   with zipfile.ZipFile(source) as archive:
    files={'payload/Repl_body_candidate.glb':'Repl_body_candidate.glb','payload/Repl_approved_gait.glb':'Repl_approved_gait.glb','campaign/rig_physics.py':'rig_physics.py'}
    for member,name in files.items():
     with archive.open(PREFIX+member) as inp,open(priv/name,'wb') as dest:shutil.copyfileobj(inp,dest)
   need(sha(priv/'Repl_body_candidate.glb')==BODY_SHA,'SOURCE_GLB_SHA')
   need(sha(priv/'Repl_approved_gait.glb')==GAIT_SHA,'APPROVED_GAIT_SHA')
   # source script imports the authentic skinner from the verified original packet.
   sys.path.insert(0,str(priv));os.environ['REPL_SOURCE_GLB']=str(priv/'Repl_body_candidate.glb')
   import solver, validator,review_renderer
   candidate=priv/'Repl_BODY_IK_UNACCEPTED.glb'
   solve_stats=solver.solve(1.,str(candidate))
   physical=validator.main(str(priv/'Repl_body_candidate.glb'),str(candidate),str(stage/'physics.json'))
   from rig_physics import Rig
   before=Rig(priv/'Repl_body_candidate.glb');after=Rig(candidate)
   for idx,im in enumerate(before.doc['images']):
    need(im['mimeType']=='image/png','TEXTURE_PNG_EXPECTED')
   # The actual source GLBs are served to Three.js and rendered on every browser
   # animation frame at full canvas/texture resolution. No low-FPS GIF substitution.
   review_renderer.render(before,14,5,str(priv/'before.png'),900,620,False)
   review_renderer.render(after,14,5,str(priv/'after.png'),900,620,False)
   still=Image.new('RGB',(1800,650),(232,232,232))
   still.paste(Image.open(priv/'before.png'),(0,30));still.paste(Image.open(priv/'after.png'),(900,30))
   d=ImageDraw.Draw(still);d.rectangle((0,0,1800,29),fill=(20,24,31))
   d.text((12,9),'BEFORE v0.6.24',fill=(255,255,255));d.text((920,9),'AFTER IK · NOT APPROVED',fill=(255,255,255))
   still.save(stage/'textured_still.png')
   review_renderer.render(before,14,5,str(priv/'before.png'),900,620,True)
   review_renderer.render(after,14,5,str(priv/'after.png'),900,620,True)
   clay=Image.new('RGB',(1800,620),(232,232,232));clay.paste(Image.open(priv/'before.png'),(0,0));clay.paste(Image.open(priv/'after.png'),(900,0));clay.save(stage/'clay_still.png')
   viewer=Path(os.environ['REPL_VIEWER_HTML']).read_bytes()
   need(b'full-rate body' in viewer and b'GLTFLoader' in viewer,'VIEWER_SOURCE_IDENTITY')
   (stage/'index.html').write_bytes(viewer)
   shutil.copyfile(priv/'Repl_body_candidate.glb',stage/'Repl_body_v0.6.24_before.glb')
   need(sha(stage/'Repl_body_v0.6.24_before.glb')==BODY_SHA,'REVIEW_BEFORE_GLB_SHA')
   # Review-only GLB, never assets/repl/Repl.glb or any repo asset path.
   candidate_name='Repl_BODY_IK_UNACCEPTED_v0.6.27.glb';shutil.copyfile(candidate,stage/candidate_name)
   need(sha(stage/candidate_name)==sha(candidate),'CANDIDATE_READBACK_HASH')
   receipt={'campaign':CAMPAIGN,'rules_read':{'agents_blob':AGENTS_BLOB,'campaign_etiquette':'https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit','read_date':'2026-11-03'},'source_head_at_author_read':HEAD,'remote_canonical_sha256_at_author_read':CANON,'source_zip':source.name,'zip_sha256':ZIP_SHA,'input_glb_sha256':BODY_SHA,'candidate_sha256':sha(candidate),'result':'SKINNED_PHYSICS_PASS_OWNER_VISUAL_ACCEPTANCE_PENDING','ik_compensation':'ALL_FOUR_LEGS; ROOT_TRAVEL_PROTECTED; PROTECTED_HOOF/TOE_CHANNELS_UNCHANGED','review_frame_count':'browser_refresh_rate','live_threejs_full_frame_rate':True,'source_git_commit':'NOT_YET_VERIFIED','model_deployed':False,'statistics':physical,'solver':solve_stats,'outputs':{}}
   for p in stage.iterdir():
    if p.is_file():receipt['outputs'][p.name]=sha(p)
   # Source-only Git publication is optional on a host test but mandatory on the user lane.
   published=publish_source(script,receipt)
   receipt['git_source_publication']=published
   (stage/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
  need(not out.exists(),'PUBLICATION_COLLISION');stage.rename(out)
  print('REVIEW_ARTIFACTS='+str(out))
  print('REVIEW_GLB_SHA256='+sha(out/'Repl_BODY_IK_UNACCEPTED_v0.6.27.glb'))
  print('NO_CANONICAL_GLB_DEPLOYMENT=TRUE')
  print('STATUS=PHYSICAL_PASS_VISUAL_REVIEW_REQUIRED')
 except Exception:
  print('PRIVATE_FAILURE_EVIDENCE_DIR='+str(stage),file=sys.stderr)
  raise
if __name__=='__main__':
 try:main()
 except Exception as e:print('STATUS=BLOCKED '+str(e),file=sys.stderr);sys.exit(2)

REPL_DRIVER_PY_EOF
export REPL_VIEWER_HTML="$TMPDIR_REPL/viewer.html"
PYTHONPATH="$TMPDIR_REPL" python3 "$TMPDIR_REPL/driver.py" "${1:-$HOME/storage/downloads}"

# Serve the SAME generated real GLBs and full-rate review page on phone loopback.
# A terminal-session exit must not kill the review; all streams are detached.
REVIEW_DIR="${1:-$HOME/storage/downloads}/REPL_BODY_IK_REVIEW_v0.6.28"
[[ -f "$REVIEW_DIR/receipt.json" && -f "$REVIEW_DIR/index.html" ]] || { echo 'BLOCKED: verified review output missing';exit 2; }
export REPL_REVIEW_DIR="$REVIEW_DIR"
python3 - <<'PY'
import json,hashlib,os,pathlib,sys
p=pathlib.Path(os.environ['REPL_REVIEW_DIR']);j=json.loads((p/'receipt.json').read_text())
for f,digest in j['outputs'].items():
 path=p/f
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
  sys.exit('BLOCKED: review output collision / changed bytes '+f)
if j.get('model_deployed') is not False:sys.exit('BLOCKED: unexpected model deployment status')
print('REVIEW_OUTPUT_SHA_READBACK=PASS',len(j['outputs']))
PY
PORT="$(python3 - <<'PY'
import socket
for port in range(8765,8790):
 with socket.socket() as s:
  try:s.bind(('127.0.0.1',port))
  except OSError:continue
  print(port);break
else:raise SystemExit('BLOCKED: all review ports busy')
PY
)"
LOG="$REVIEW_DIR/server.log"
if command -v setsid >/dev/null; then
 setsid python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$REVIEW_DIR" > "$LOG" 2>&1 < /dev/null &
else
 nohup python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$REVIEW_DIR" > "$LOG" 2>&1 < /dev/null &
fi
SERVER_PID=$!
python3 - "$PORT" <<'PY'
import sys,urllib.request,time
url='http://127.0.0.1:'+sys.argv[1]+'/index.html'
for attempt in range(30):
 try:
  with urllib.request.urlopen(url,timeout=2) as resp:body=resp.read()
  if b'full-rate body' in body and b'GLTFLoader' in body:
   print('HTTP_VIEWER_VERIFIED='+url);break
 except Exception:pass
 time.sleep(.2)
else:raise SystemExit('BLOCKED: loopback HTTP server failed readback')
PY
URL="http://127.0.0.1:$PORT/index.html"
echo "SERVER_PID=$SERVER_PID"
echo "INTERACTIVE_3D_VIEWER=$URL"
echo 'PLAYBACK=FULL_BROWSER_REFRESH_RATE; RECORDING=30FPS_WHEN_SUPPORTED'
echo 'ANIMATION=EVERY_BROWSER_FRAME; NO_LOW_FPS_THUMBNAIL_GIF'
echo 'CANONICAL_GLB_DEPLOYED=NO'
if command -v termux-open-url >/dev/null 2>&1;then
 termux-open-url "$URL" && echo 'BROWSER_OPEN_REQUESTED=YES' || echo 'BROWSER_OPEN_REQUESTED=FAILED'
else
 echo 'BROWSER_OPEN_REQUESTED=NO_TERMUX_OPEN_URL; open the printed local URL in your Android browser'
fi
