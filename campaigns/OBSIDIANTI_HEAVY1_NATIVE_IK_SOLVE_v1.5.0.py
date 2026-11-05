#!/usr/bin/env python3
"""Rig-first Lionheart Heavy1 retarget from real native Foot.IK/Knee.IK trajectories.

Only six Heavy1 deform-leg rotation channels may change. No confidence-gated
contact overlay, fallback poses, root/skin/rest edits, or other action writes.
The commit-side runner owns SHA locking and all Git mutations.
"""
from __future__ import annotations
import argparse, bisect, copy, hashlib, importlib.util, json, math, pathlib, struct, sys

VERSION='OBSIDIANTI_HEAVY1_NATIVE_IK_v1.5.0'
SOURCE_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
DONOR_SHA='a14304e455f978fcdbb0607f187a175310e034fdfed7f83176402fd7eb9f1fd4'
CALIB_SHA='b6d23f49c67df7816124362f4b1ee540db5c16a672fbc8c435a7f503ca123336'
MATH_SHA='dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f'
CLIP='Lionheart_Heavy1'
SIDES=('Left','Right')
PARTS=('UpLeg','Leg','Foot')

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def load_math(repo):
 p=pathlib.Path(repo)/'campaigns/OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py'
 if sha(p)!=MATH_SHA:raise RuntimeError('MATH_HELPER_SHA_CHANGED')
 sys.dont_write_bytecode=True
 spec=importlib.util.spec_from_file_location('obs_native_ik_pinned_math',p)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m

def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mulv(a,s):return [x*s for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def length(a):return math.sqrt(dot(a,a))
def normalize(a):
 d=length(a)
 return mulv(a,1/d) if d>1e-10 else [0.,0.,0.]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def clamp(x,a,b):return max(a,min(b,x))
def xyz(m):return [m[3],m[7],m[11]]
def rot_of(M,m):
 x=normalize([m[0],m[4],m[8]])
 yy=[m[1],m[5],m[9]];y=normalize(sub(yy,mulv(x,dot(x,yy))))
 z=normalize(cross(x,y));y=normalize(cross(z,x))
 a,b,c=x[0],y[0],z[0];d,e,f=x[1],y[1],z[1];g,h,i=x[2],y[2],z[2];tr=a+e+i
 if tr>0:
  t=math.sqrt(1+tr)*2;q=[(h-f)/t,(c-g)/t,(d-b)/t,t/4]
 elif a>e and a>i:
  t=math.sqrt(1+a-e-i)*2;q=[t/4,(b+d)/t,(c+g)/t,(h-f)/t]
 elif e>i:
  t=math.sqrt(1+e-a-i)*2;q=[(b+d)/t,t/4,(f+h)/t,(c-g)/t]
 else:
  t=math.sqrt(1+i-a-e)*2;q=[(c+g)/t,(f+h)/t,t/4,(d-b)/t]
 return M.unit(q)

def from_to(M,a,b):
 aa=normalize(a);bb=normalize(b);v=cross(aa,bb);w=clamp(dot(aa,bb),-1.,1.)
 if w>1.-1e-9:return [0.,0.,0.,1.]
 if w < -1.+1e-9:
  c=[1.,0.,0.] if abs(aa[0])<.8 else [0.,1.,0.]
  return [*normalize(cross(aa,c)),0.]
 return M.unit([v[0],v[1],v[2],1+w])

def quatangle(M,a,b):
 aa=M.unit(a);bb=M.unit(b)
 return math.degrees(2*math.acos(clamp(abs(dot(aa,bb)),0,1)))

def yaw(M,q,v):
 return M.rotate(q,v)

def yrot(angle):return [0,math.sin(angle/2),0,math.cos(angle/2)]

def path_for(side,part):return 'mixamorig:'+side+part

def frame_goal(M,frame,idle,calib,tgt_idleref,modelhiprot,modelhippos,scale,yaw_deg,side):
 hip=frame['bones']['mixamorig:Hips'];hip0=idle['bones']['mixamorig:Hips']
 def in_hip(bone,hipbone):
  return M.rotate(M.inv(hipbone['worldQuaternion']),sub(bone['worldPosition'],hipbone['worldPosition']))
 def ctrl_rot_in_hip(bone,hipbone):return M.unit(M.mul(M.inv(hipbone['worldQuaternion']),bone['worldQuaternion']))
 src=frame['bones'][side+'Foot.IK'];src0=idle['bones'][side+'Foot.IK']
 pole=frame['bones'][side+'Knee.IK'];pole0=idle['bones'][side+'Knee.IK']
 srcdelta=sub(in_hip(src,hip),in_hip(src0,hip0))
 # Preserve the native constraint's evaluated ankle-to-controller residual.
 # Even if an IK goal is out of donor reach, the donor's real deforming ankle
 # is the physically authored endpoint; never silently replace it with the
 # unachieved IK target or raw joint quaternion.
 ankle=frame['bones']['mixamorig:'+side+'Foot'];ankle0=idle['bones']['mixamorig:'+side+'Foot']
 residual=sub(sub(in_hip(ankle,hip),in_hip(src,hip)),
              sub(in_hip(ankle0,hip0),in_hip(src0,hip0)))
 srcdelta=add(srcdelta,residual)
 poledelta=sub(in_hip(pole,hip),in_hip(pole0,hip0))
 rot=yrot(math.radians(yaw_deg))
 ankle_base=tgt_idleref['anklePelvisLocal']
 knee_base=tgt_idleref['kneePelvisLocal']
 ankle_local=add(ankle_base,yaw(M,rot,mulv(srcdelta,scale)))
 pole_local=add(knee_base,yaw(M,rot,mulv(poledelta,scale)))
 target=add(modelhippos,M.rotate(modelhiprot,ankle_local))
 pole_target=add(modelhippos,M.rotate(modelhiprot,pole_local))
 # Donor Foot.IK roll is expressed in the donor pelvis frame, then transferred
 # relative to the donor Idle roll onto the approved target Idle ankle roll.
 qsrc0=ctrl_rot_in_hip(ankle0,hip0);qsrc=ctrl_rot_in_hip(ankle,hip)
 qfoot0=tgt_idleref['footPelvisLocalRot']
 qfoot_local=M.mul(qfoot0,M.mul(M.inv(qsrc0),qsrc))
 qfoot_world=M.unit(M.mul(modelhiprot,qfoot_local))
 return target,pole_target,qfoot_world,srcdelta

def one_frame(M,g,base_tracks,t,frames,calib,refs,chains,parents,scale_adjust,yaw_deg):
 world=M.global_matrices(g,base_tracks,t)
 hips=refs['hipNode'];hiprot=rot_of(M,world[hips]);hippos=xyz(world[hips])
 row=interpolate_source(frames,t)
 begin=frames[0]
 ret={};errors={};goals={};pole_dirs={}
 for side in SIDES:
  chain=chains[side];up,leg,foot=chain
  wup=world[up];wleg=world[leg];wfoot=world[foot]
  H=xyz(wup);K=xyz(wleg);A=xyz(wfoot)
  s=calib['legRatios'][side]['combinedRatio']*scale_adjust
  goal,pole,qfoot,srcdelta=frame_goal(M,row,begin,calib,refs['targetIdle'][side],hiprot,hippos,s,yaw_deg,side)
  L1=length(sub(K,H));L2=length(sub(A,K));dist=length(sub(goal,H))
  if min(L1,L2,dist)<.001:raise RuntimeError('DEGENERATE_LEG_GEOMETRY:'+side)
  miss=max(0.,dist-(L1+L2-.0005),abs(L1-L2)+.0005-dist)
  # A tiny reach overflow is projected to the true two-bone envelope, but
  # its unprojected error is always recorded and physically gated afterward.
  u=normalize(sub(goal,H));dd=clamp(dist,abs(L1-L2)+.0005,L1+L2-.0005)
  x=(L1*L1+dd*dd-L2*L2)/(2*dd)
  h=math.sqrt(max(0,L1*L1-x*x))
  pk=sub(pole,H);perp=sub(pk,mulv(u,dot(pk,u)))
  if length(perp)<.001:
   pk=sub(K,H);perp=sub(pk,mulv(u,dot(pk,u)))
  if length(perp)<.001:
   c=cross(u,[0.,0.,1.]);perp=c if length(c)>.001 else cross(u,[1.,0.,0.])
  kk=add(H,add(mulv(u,x),mulv(normalize(perp),h)))
  ankle_clamped=add(H,mulv(u,dd))
  qu=from_to(M,sub(K,H),sub(kk,H))
  rot_up_old=rot_of(M,wup);rot_leg_old=rot_of(M,wleg)
  rot_up_new=M.unit(M.mul(qu,rot_up_old))
  ankle_after_upper=add(kk,M.rotate(qu,sub(A,K)))
  ql=from_to(M,sub(ankle_after_upper,kk),sub(ankle_clamped,kk))
  rot_leg_new=M.unit(M.mul(ql,M.mul(qu,rot_leg_old)))
  parentrot=rot_of(M,world[parents[up]])
  qs={up:M.unit(M.mul(M.inv(parentrot),rot_up_new)),
      leg:M.unit(M.mul(M.inv(rot_up_new),rot_leg_new)),
      foot:M.unit(M.mul(M.inv(rot_leg_new),qfoot))}
  for idx,q in qs.items():
   if not all(math.isfinite(v) for v in q):raise RuntimeError('NONFINITE_QUATERNION')
  ret[side]=qs;errors[side]={'reachMiss_m':miss,'goalTravelFromAnkle_m':length(sub(goal,A)),'sourceDeltaPelvisLocal_m':srcdelta}
  goals[side]=goal;pole_dirs[side]=normalize(sub(kk,H))
 return ret,errors,goals,pole_dirs

def interpolate_source(frames,t):
 times=[r['timeSeconds'] for r in frames]
 if t<=times[0]:return frames[0]
 if t>=times[-1]:return frames[-1]
 i=bisect.bisect_right(times,t)-1
 if abs(t-times[i])<1e-7:return frames[i]
 k=(t-times[i])/(times[i+1]-times[i])
 a=frames[i]['bones'];b=frames[i+1]['bones'];bones={}
 for key in ('mixamorig:Hips','mixamorig:LeftFoot','mixamorig:RightFoot','LeftFoot.IK','RightFoot.IK','LeftKnee.IK','RightKnee.IK'):
  bones[key]={
    'worldPosition':[a[key]['worldPosition'][n]*(1-k)+b[key]['worldPosition'][n]*k for n in range(3)],
    'worldQuaternion':_quat_slerp(a[key]['worldQuaternion'],b[key]['worldQuaternion'],k)}
 return {'timeSeconds':t,'bones':bones}

def _quat_slerp(a,b,k):
 d=dot(a,b)
 if d<0:b=[-x for x in b];d=-d
 d=clamp(d,-1,1)
 if d>.9995:
  v=[x*(1-k)+y*k for x,y in zip(a,b)];n=length(v);return mulv(v,1/n)
 theta=math.acos(d);s=math.sin(theta)
 return [(a[j]*math.sin((1-k)*theta)+b[j]*math.sin(k*theta))/s for j in range(4)]

def make_target_reference(M,g,b,tracks,idle_anim):
 ids={n.get('name'):i for i,n in enumerate(g['nodes'])}
 if 'mixamorig:Hips' not in ids:raise RuntimeError('HIPS_NODE_MISSING')
 idle_tracks=M.channels(g,b,idle_anim)
 world=M.global_matrices(g,idle_tracks,0.)
 hip=ids['mixamorig:Hips'];P=xyz(world[hip]);Q=rot_of(M,world[hip]);invQ=M.inv(Q)
 target={};chains={};parents={c:i for i,n in enumerate(g['nodes']) for c in n.get('children',[])}
 for side in SIDES:
  chain=[ids[path_for(side,p)] for p in PARTS];chains[side]=chain
  if parents[chain[1]]!=chain[0] or parents[chain[2]]!=chain[1]:raise RuntimeError('LEG_PARENT_CHAIN_MISMATCH')
  target[side]={
    'anklePelvisLocal':M.rotate(invQ,sub(xyz(world[chain[2]]),P)),
    'kneePelvisLocal':M.rotate(invQ,sub(xyz(world[chain[1]]),P)),
    'footPelvisLocalRot':M.unit(M.mul(invQ,rot_of(M,world[chain[2]])))}
 return {'hipNode':hip,'targetIdle':target,'ids':ids},chains,parents

def candidate(M,g,b,source,calib,amp,yaw_deg,probe_only=False):
 anim=next((a for a in g['animations'] if a.get('name')==CLIP),None)
 idle=next((a for a in g['animations'] if a.get('name')=='LionheartIdle_UNREVIEWED'),None)
 if not anim or not idle:raise RuntimeError('HEAVY1_OR_APPROVED_IDLE_MISSING')
 original=M.channels(g,b,anim);refs,chains,parents=make_target_reference(M,g,b,original,idle)
 hip=refs['hipNode'];ts=original[(hip,'rotation')][0]
 frames=source['frames']
 if len(frames)!=61 or frames[-1]['timeSeconds']<.999:raise RuntimeError('SOURCE_HEAVY1_FRAME_COUNT_NOT_61')
 # Source archive is already exactly whole-and-half frames at 60Hz.
 # New animation sampling is at the same times; no gating based on contact.
 times=[float(row['timeSeconds']) for row in frames]
 if abs(ts[0]-times[0])>.003 or abs(ts[-1]-times[-1])>.003:raise RuntimeError('MODEL_SOURCE_DURATION_MISMATCH')
 accum={side:{idx:[] for idx in chains[side]} for side in SIDES}
 maxreach=0.;frame_records=[];maxchange=0.
 for t in times:
  poses,errs,goals,poles=one_frame(M,g,original,t,frames,calib,refs,chains,parents,amp,yaw_deg)
  fullrow={'timeSeconds':round(t,8),'sides':{}}
  for side in SIDES:
   err=errs[side];maxreach=max(maxreach,err['reachMiss_m'])
   for idx,quat in poses[side].items():
    accum[side][idx].append(quat)
    oq=M.sampled(*original[(idx,'rotation')],t,True)
    maxchange=max(maxchange,quatangle(M,quat,oq))
   fullrow['sides'][side]={**err,'ankleTargetWorld_m':[round(x,6) for x in goals[side]],'kneeDirection':poles[side]}
  frame_records.append(fullrow)
 new=dict(original)
 for side in SIDES:
  for idx,qq in accum[side].items():new[(idx,'rotation')]=(times,qq)
 # Check actual target skinned heel/toe and both ankle trajectories at every
 # half and QUARTER source frame, including transitions between baked keys.
 witnesses,skin,ibm=M.foot_witnesses(g,b)
 checktimes=sorted(set(round(t,9) for t in (times+[(a+b)/2 for a,b in zip(times,times[1:])])))
 report=[];maxerr=0.;minfloor=1e12;maxquaternion=0.;maxfootjump=0.;maxkneeflip=0.
 previous={};sole_prev={};knee_prev={}
 for t in checktimes:
  world=M.global_matrices(g,new,t);soles=M.skin_foot_points(witnesses,skin,ibm,world)
  # Expected continuous goal sampled from source native controller matrices.
  oldworld=M.global_matrices(g,original,t);ph=rot_of(M,oldworld[hip]);pp=xyz(oldworld[hip])
  row=interpolate_source(frames,t)
  one={'time':round(t,7)}
  for side in SIDES:
   goal,_,_,_=frame_goal(M,row,frames[0],calib,refs['targetIdle'][side],ph,pp,calib['legRatios'][side]['combinedRatio']*amp,yaw_deg,side)
   ankle=xyz(world[chains[side][-1]]);e=length(sub(ankle,goal));maxerr=max(maxerr,e)
   floor=min(p[1] for p in soles[side]);minfloor=min(minfloor,floor)
   shoe_center=[sum(p[k] for p in soles[side])/len(soles[side]) for k in range(3)]
   if side in previous:
    maxfootjump=max(maxfootjump,length(sub(ankle,previous[side])))
    prevs=sole_prev[side];maxfootjump=max(maxfootjump,length(sub(shoe_center,prevs)))
    kp=normalize(sub(xyz(world[chains[side][1]]),xyz(world[chains[side][0]])))
    maxkneeflip=max(maxkneeflip,math.degrees(math.acos(clamp(dot(kp,knee_prev[side]),-1,1))))
   previous[side]=ankle;sole_prev[side]=shoe_center;knee_prev[side]=normalize(sub(xyz(world[chains[side][1]]),xyz(world[chains[side][0]])))
   if not probe_only or t in (0.,.25,.5,.75,1.):
    one[side]={'ankleWorld_m':[round(x,6) for x in ankle],
      'originalAnkleWorld_m':[round(x,6) for x in xyz(oldworld[chains[side][-1]])],
      'goalError_m':round(e,6),'lowestSkinnedSoleY_m':round(floor,6),
      'controllerDesiredWorld_m':[round(x,6) for x in goal]}
  report.append(one)
 for side in SIDES:
  for idx,qq in accum[side].items():
   for a,c in zip(qq,qq[1:]):maxquaternion=max(maxquaternion,quatangle(M,a,c))
 minfloor_error=max(0.,-minfloor)
 # Do NOT silently exempt the bad frames the user previously found. These
 # are hard clip-wide tests of physical mesh and joint continuity.
 metrics={'amplitude':amp,'yaw_deg':yaw_deg,'reachExcess_m':round(maxreach,6),
          'maxAnkleGoalError_m':round(maxerr,6),
          'maxSolePenetration_m':round(minfloor_error,6),
          'maxFootStepAtQuarterFrame_m':round(maxfootjump,6),
          'maxKneeVectorDeltaQuarterFrame_deg':round(maxkneeflip,4),
          'maxBakedJointDeltaHalfFrame_deg':round(maxquaternion,4),
          'worstJointCorrectionFromPublished_deg':round(maxchange,4),
          'sampleFrames':len(times),'physicalProbeCount':len(checktimes),
          'sourceControllerAnchor':'NATIVE_BLENDER_EVALUATED_ALL_FRAMES',
          'groundingClaim':'NO_DONOR_SOLE_SAMPLE'}
 valid=(maxreach<=.008 and maxerr<=.009 and minfloor_error<=.015 and maxfootjump<=.060
        and maxkneeflip<=25 and maxquaternion<=25 and maxchange<=140)
 metrics['physicalGatePassed']=valid
 metrics['score']=(maxerr*30+maxreach*100+minfloor_error*55+maxfootjump*4
             +maxkneeflip*.003+maxquaternion*.002+abs(amp-1)*.11+abs(yaw_deg)*.004)
 return metrics,new,frame_records,report

def append_times(g,b,times):
 import struct
 if not all(math.isfinite(t) for t in times):raise RuntimeError('BAD_SAMPLE_TIME')
 if any(y<=x for x,y in zip(times,times[1:])):raise RuntimeError('NONMONOTONE_TIME')
 while len(b)%4:b.append(0)
 off=len(b);b.extend(struct.pack('<'+'f'*len(times),*times));k=len(g['bufferViews'])
 g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(times)*4})
 i=len(g['accessors'])
 g['accessors'].append({'bufferView':k,'componentType':5126,'count':len(times),'type':'SCALAR',
                        'min':[min(times)],'max':[max(times)]})
 return i

def append_rotations(M,g,b,anim,origtracks,corrected):
 # Mutate exactly six rotation outputs (new immutable accessor data), nothing else.
 ids={n.get('name'):i for i,n in enumerate(g['nodes'])}
 named={(ch['target']['node'],ch['target']['path']):anim['samplers'][ch['sampler']] for ch in anim['channels']}
 keys=set()
 for side in SIDES:
  for part in PARTS:
   key=(ids[path_for(side,part)],'rotation');keys.add(key)
   if key not in named:raise RuntimeError('EXPECTED_ROTATION_CHANNEL_MISSING:'+str(key))
   t,qs=corrected[key]
   if len(t)!=61 or len(qs)!=61:raise RuntimeError('MISSING_61_ROTATION_SAMPLES')
   if any(not math.isfinite(x) for q in qs for x in q):raise RuntimeError('NONFINITE_NEW_ROTATION')
   sampler=named[key]
   # Preserve other animation track inputs and buffer data; new sampler only for chosen channel.
   sampler['input']=append_times(g,b,t)
   sampler['output']=M.append_accessor(g,b,qs,'VEC4')
   sampler['interpolation']='LINEAR'
 assert len(keys)==6
 return keys

def solve(path,repo,source_path,calib_path,report_path,preview_path=None,write=False):
 p=pathlib.Path(path);repo=pathlib.Path(repo)
 if sha(p)!=SOURCE_SHA:raise RuntimeError('MODEL_LFS_SOURCE_SHA_MISMATCH')
 if sha(source_path)!=DONOR_SHA:raise RuntimeError('HEAVY1_NATIVE_SAMPLES_SHA_MISMATCH')
 if sha(calib_path)!=CALIB_SHA:raise RuntimeError('CALIBRATION_SHA_MISMATCH')
 M=load_math(repo)
 source=json.loads(pathlib.Path(source_path).read_text());calib=json.loads(pathlib.Path(calib_path).read_text())
 if source['action']!='Heavy1' or source['frameCount']!=61:raise RuntimeError('WRONG_SOURCE_ACTION')
 if calib['modelSha256']!=SOURCE_SHA:raise RuntimeError('CALIBRATION_MODEL_HASH_MISMATCH')
 g,b=M.load_glb(path);srcg=copy.deepcopy(g);srcbin=bytes(b)
 target=next((a for a in g['animations'] if a.get('name')==CLIP),None)
 if target is None:raise RuntimeError('HEAVY1_CLIP_MISSING')
 clips=[a['name'] for a in g['animations']]
 choices=[]
 # Adaptive coarse-to-fine exploration of physically sensible profile scales;
 # no hardcoded single-shot answer. Numeric candidate never replaces owner review.
 for amplitude in (1.,.95,1.05,.9,1.1,.925,1.075,.875):
  for yaw_deg in (0.,-4.,4.,-8.,8.):
   try:
    stats,tracks,records,probe=candidate(M,g,b,source,calib,amplitude,yaw_deg,probe_only=True)
    choices.append((stats['score'],stats,tracks,records,probe))
   except Exception as ex:
    choices.append((float('inf'),{'amplitude':amplitude,'yaw_deg':yaw_deg,'error':str(ex),'physicalGatePassed':False},None,None,None))
 choices.sort(key=lambda t:t[0]);ok=[c for c in choices if c[1].get('physicalGatePassed')]
 final=None
 if ok:
  coarse=ok[0][1]
  # Bounded local refinement; repeat actual full skinned validation for every profile.
  extras=[]
  for a in (coarse['amplitude']-.025,coarse['amplitude']+.025,coarse['amplitude']-.0125,coarse['amplitude']+.0125):
   if not .875<=a<=1.10:continue
   for yaw_deg in (coarse['yaw_deg']-2,coarse['yaw_deg'],coarse['yaw_deg']+2):
    try:
     stats,tracks,records,probe=candidate(M,g,b,source,calib,a,yaw_deg,probe_only=True)
     extras.append((stats['score'],stats,tracks,records,probe))
    except Exception as ex:extras.append((float('inf'),{'amplitude':a,'yaw_deg':yaw_deg,'error':str(ex),'physicalGatePassed':False},None,None,None))
  choices+=extras;choices.sort(key=lambda t:t[0]);ok=[c for c in choices if c[1].get('physicalGatePassed')]
  if ok:
   s=ok[0][1];st,tracks,records,probe=candidate(M,g,b,source,calib,s['amplitude'],s['yaw_deg'],probe_only=False)
   if st['physicalGatePassed']:final=(st,tracks,records,probe)
 report={'schema':'obsidianti-heavy1-native-ik-candidate-v1','version':VERSION,
         'status':'CANDIDATE_QUARANTINED_VISUAL_PENDING' if final else 'PHYSICAL_PREFLIGHT_FAILED_MODEL_UNCHANGED',
         'sourceModelSha256':SOURCE_SHA,'nativeHeavy1Sha256':DONOR_SHA,
         'rulesMathHelperSha256':MATH_SHA,'sourceSamples':61,
         'protectedClips':[n for n in clips if n!=CLIP],
         'searchProfilesEvaluated':len(choices),
         'searchTop12':[x[1] for x in choices[:12]],
         'unmodifiedModel':not bool(write and final),
         'selectedProfile':final[0] if final else None}
 pathlib.Path(report_path).parent.mkdir(parents=True,exist_ok=True)
 if final:
  st,newtracks,records,probes=final
  if preview_path:
   pathlib.Path(preview_path).write_text(json.dumps({'source':SOURCE_SHA,'selected':st,'frames':records,'probes':probes},indent=2)+'\n')
  append_rotations(M,g,b,target,M.channels(g,b,target),newtracks)
  for a,old in zip(g['animations'],srcg['animations']):
   if old['name']!=CLIP and a!=old:raise RuntimeError('OTHER_ANIMATION_MODIFIED:'+old['name'])
  for fld in ('nodes','skins','meshes','scenes','materials','textures','images','bufferViews'):
   if fld!='bufferViews' and g.get(fld)!=srcg.get(fld):raise RuntimeError('NONANIMATION_CHANGED:'+fld)
  if not bytes(b).startswith(srcbin):raise RuntimeError('BIN_PREFIX_CHANGED')
  blob=M.encode_glb(g,b)
  report['candidateSha256']=hashlib.sha256(blob).hexdigest()
  report['changedTracks']=['mixamorig:'+side+part+'/rotation' for side in SIDES for part in PARTS]
  if write:
   # Only after all checks in read-only preflight. Caller owns atomic installation.
   dst=pathlib.Path(path)
   dst.write_bytes(blob)
   if sha(dst)!=report['candidateSha256']:raise RuntimeError('WRITTEN_MODEL_SHA_MISMATCH')
 pathlib.Path(report_path).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 if not final:raise RuntimeError('NO_PHYSICALLY_VALID_HEAVY1_IK_PROFILE')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--repo',required=True)
 p.add_argument('--source',required=True);p.add_argument('--calibration',required=True)
 p.add_argument('--report',required=True);p.add_argument('--preview');p.add_argument('--write',action='store_true');a=p.parse_args()
 report=solve(a.model,a.repo,a.source,a.calibration,a.report,a.preview,a.write)
 print('HEAVY1_NATIVE_IK_STATUS='+report['status'],flush=True)
 print('CANDIDATE_SHA256='+report['candidateSha256'],flush=True)
if __name__=='__main__':main()
