import json,struct,sys,base64,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as R,Slerp

WALK='REPL_WALK_03_FORWARD_SECONDARY_INTEGRATED'

def load_glb(p):
 b=Path(p).read_bytes(); assert b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b)
 n,t=struct.unpack_from('<I4s',b,12);assert t==b'JSON';g=json.loads(b[20:20+n]);idx=20+n;ln,tt=struct.unpack_from('<I4s',b,idx);assert tt==b'BIN\0';buf=memoryview(b)[idx+8:idx+8+ln]
 return g,buf

def accessor(g,buf,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];t={5126:np.dtype('<f4'),5123:np.dtype('<u2'),5125:np.dtype('<u4')}[a['componentType']];k={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];o=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',t.itemsize*k)
 if stride==t.itemsize*k:return np.frombuffer(buf,dtype=t,count=a['count']*k,offset=o).reshape(-1,k).astype(float)
 return np.array([np.frombuffer(buf,dtype=t,count=k,offset=o+j*stride) for j in range(a['count'])],dtype=float)

def fit(p,output):
 g,b=load_glb(p);clip=next(a for a in g['animations'] if a['name']==WALK)
 N=512; tracks=[];maxerrors=[];duration=0.;root_name='Bone_000'
 for ch in clip['channels']:
  samp=clip['samplers'][ch['sampler']];t=accessor(g,b,samp['input'])[:,0];duration=max(duration,float(t[-1]))
 print('SOURCE_DURATION',duration,'CHANNELS',len(clip['channels']))
 phases=np.linspace(0,1,N,endpoint=False);pts=phases*duration
 for ch in clip['channels']:
  samp=clip['samplers'][ch['sampler']]; times=accessor(g,b,samp['input'])[:,0]; raw=accessor(g,b,samp['output']);name=g['nodes'][ch['target']['node']].get('name','node_'+str(ch['target']['node']));path=ch['target']['path']
  if path=='rotation':
   rots=R.from_quat(raw);rr=Slerp(times,rots)(np.minimum(pts,times[-1]));bind=R.from_quat(g['nodes'][ch['target']['node']].get('rotation',[0,0,0,1])); v=(bind.inv()*rr).as_rotvec()
  elif path=='translation':
   v=np.column_stack([np.interp(pts,times,raw[:,j]) for j in range(3)])
   if name==root_name:
    # exclude monotonic root advance; fit periodic residual around linear advance.
    delta=raw[-1]-raw[0];v=v-(raw[0]+phases[:,None]*delta);root_advance=delta.tolist();root_start=raw[0].tolist()
  else:continue
  # Adaptive Fourier fit; sample-space RMS; never use original clip in browser runtime.
  best=None
  for harmonics in (4,6,8,10,12,16,20,24):
   cols=[np.ones(N)];
   for k in range(1,harmonics+1):cols.extend([np.cos(2*np.pi*k*phases),np.sin(2*np.pi*k*phases)])
   A=np.stack(cols,axis=1);coef=np.linalg.lstsq(A,v,rcond=None)[0];pred=A@coef;errs=np.linalg.norm(pred-v,axis=1)
   # numeric reference fit, not anatomy guarantee
   if float(errs.max())<(.012 if path=='rotation' else .006) or harmonics==24:best=(harmonics,coef,float(errs.max()),float(np.sqrt(np.mean(errs**2))));break
  harmonics,coef,maxe,rmse=best;maxerrors.append({'name':name,'path':path,'harmonics':harmonics,'max_error':maxe,'rms_error':rmse})
  tracks.append({'node':name,'path':path,'harmonics':harmonics,'coefficients':np.round(coef.T,9).tolist()})
 spec={'format':'REPL_PARAMETRIC_FOURIER_V1','source_clip':WALK,'source_sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest(),'duration':duration,'samples':N,'tracks':tracks,'fit_errors':maxerrors,'root_node':root_name,'root_advance':root_advance if 'root_advance' in locals() else [0,0,0],'root_start':root_start if 'root_start' in locals() else [0,0,0],'bone_names':[n.get('name') for n in g['nodes']]}
 Path(output).write_text(json.dumps(spec,separators=(',',':')))
 print('FIT tracks=',len(tracks),'max_rotation_error=',max((r['max_error'] for r in maxerrors if r['path']=='rotation'),default=0),'harmonics=',{r['harmonics'] for r in maxerrors},'bytes=',Path(output).stat().st_size)
 return spec
if __name__=='__main__':fit(sys.argv[1],sys.argv[2])
