#!/usr/bin/env python3
"""Lionheart evaluated-source stance IK on the SAME canonical Obsidianti.glb.

Owner-directed: undo the rejected v1.2 pelvis-pitch change using exact historical
v1.1 sampling; keep removal of all inherited weapon translations; use original
Lionheart source ToeBase WORLD trajectories to classify planted/swing/airborne;
solve support legs against actual SKINNED wedge soles with two-link IK; do not
modify any Ares, Meshy, Idle, skeleton, mesh, weights, accessory or scene data.

Runs only on exact source hashes and uses only Python stdlib. Authored outputs
are quarantined candidates until phone viewer and owner approve.
"""
from __future__ import annotations
import argparse, bisect, copy, hashlib, importlib.util, json, math, os, pathlib, struct, sys, tempfile
from collections import defaultdict

CAMPAIGN='OBSIDIANTI_CONTACT_IK_v1.3.0'
CURRENT_SHA='f9fc5cef4d2f0b08f2a74e350d3251bc993a861ecbb6a22eda5267a09e4629e6'
ORIGINAL_SHA='5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0'
HELPER_SHA='dc19a766ce41950c8040a81339d488573f70151910aa3ebf479ab8296484851f'
ACTIONS=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
LEG_PARTS=('UpLeg','Leg','Foot')
WEAPONS={'mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R'}
FLOOR_Y=0.0

def read_tool():
 path=pathlib.Path(__file__).with_name('OBSIDIANTI_PELVIS_WEAPON_SOLVE_v1.2.1.py')
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=HELPER_SHA:
  raise RuntimeError('REQUIRED_PINNED_V121_MATH_HELPER_MISSING_OR_CHANGED')
 sys.dont_write_bytecode=True
 spec=importlib.util.spec_from_file_location('obsidianti_v121_math_readonly',path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module
M=None

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def vadd(a,b):return [x+y for x,y in zip(a,b)]
def vsub(a,b):return [x-y for x,y in zip(a,b)]
def vs(a,k):return [x*k for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def vn(a):
 d=norm(a)
 return vs(a,1./d) if d>1e-9 else [0.,0.,0.]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def lerp(a,b,k):return vadd(vs(a,1.-k),vs(b,k))
def smooth(x):
 t=max(0.,min(1.,x));return t*t*(3-2*t)

def from_to(a,b):
 a=vn(a);b=vn(b);c=cross(a,b);d=max(-1.,min(1.,dot(a,b)))
 if d>1.-1e-9:return [0.,0.,0.,1.]
 if d< -1.+1e-9:
  candidate=[1.,0.,0.] if abs(a[0])<.8 else [0.,1.,0.]
  axis=vn(cross(a,candidate));return [*axis,0.]
 return M.unit([*c,1.+d])

def matrix_rot(m):
 # Extract scale-free orthonormal 3x3 quaternion from a row-major affine matrix.
 # Matrices on this source have uniform/positive unit bone scales.
 x=vn([m[0],m[4],m[8]])
 y0=[m[1],m[5],m[9]];y=vn(vsub(y0,vs(x,dot(x,y0))))
 z=vn(cross(x,y));y=vn(cross(z,x))
 a,b,c=x[0],y[0],z[0];d,e,f=x[1],y[1],z[1];g,h,i=x[2],y[2],z[2]
 trace=a+e+i
 if trace>0:
  s=math.sqrt(1+trace)*2;w=s/4;xq=(h-f)/s;yq=(c-g)/s;zq=(d-b)/s
 elif a>e and a>i:
  s=math.sqrt(1+a-e-i)*2;w=(h-f)/s;xq=s/4;yq=(b+d)/s;zq=(c+g)/s
 elif e>i:
  s=math.sqrt(1+e-a-i)*2;w=(c-g)/s;xq=(b+d)/s;yq=s/4;zq=(f+h)/s
 else:
  s=math.sqrt(1+i-a-e)*2;w=(d-b)/s;xq=(c+g)/s;yq=(f+h)/s;zq=s/4
 return M.unit([xq,yq,zq,w])

def matpos(m):return [m[3],m[7],m[11]]

def quatang(a,b):
 return math.degrees(2*math.acos(min(1.,abs(dot(M.unit(a),M.unit(b))))))

def find_track(anim,g,node,path):
 matches=[ch for ch in anim['channels'] if ch['target']['node']==node and ch['target']['path']==path]
 if len(matches)!=1:raise RuntimeError('CHANNEL_NOT_UNIQUE:'+anim['name']+':'+g['nodes'][node].get('name','')+':'+path)
 return matches[0],anim['samplers'][matches[0]['sampler']]

def prepare_old_and_current(new_g,new_b,old_g,old_b):
 if len(new_g['animations'])!=23 or len(old_g['animations'])!=23:raise RuntimeError('CLIP_COUNT_NOT_23')
 for key in ('nodes','skins','meshes','scenes','materials','textures','images'):
  if new_g.get(key)!=old_g.get(key):raise RuntimeError('HISTORICAL_RIG_OR_MATERIAL_DRIFT:'+key)
 if bytes(new_b[:len(old_b)])!=bytes(old_b):raise RuntimeError('V121_INPUT_NOT_AN_EXTENSION_OF_V11_BIN')
 ids={n.get('name'):i for i,n in enumerate(new_g['nodes'])}
 hip=ids['mixamorig:Hips']
 for old,cur in zip(old_g['animations'],new_g['animations']):
  if old['name']!=cur['name']:raise RuntimeError('HISTORICAL_CLIP_SEQUENCE_CHANGED')
  if not old['name'].startswith('Lionheart_') or old['name']=='LionheartIdle_UNREVIEWED':
   if old!=cur:raise RuntimeError('PROTECTED_CLIP_CHANGED_SINCE_V11:'+old['name'])
   continue
  oldchannels={(ch['target']['node'],ch['target']['path']):ch for ch in old['channels']}
  newchannels={(ch['target']['node'],ch['target']['path']):ch for ch in cur['channels']}
  if any(k[0] not in ids.values() for k in newchannels):raise RuntimeError('NODE_OUT_OF_RANGE')
  for key,ch in newchannels.items():
   if key not in oldchannels:raise RuntimeError('UNEXPECTED_NEW_MOTION_CHANNEL:'+old['name']+str(key))
   a=cur['samplers'][ch['sampler']];b=old['samplers'][oldchannels[key]['sampler']]
   if key!=(hip,'rotation') and (a!=b):raise RuntimeError('NONPELVIS_CHANNEL_CHANGED_SINCE_V11:'+old['name']+str(key))
  missing=set(oldchannels)-set(newchannels)
  if any(key[1]!='translation' or new_g['nodes'][key[0]].get('name') not in WEAPONS for key in missing):
   raise RuntimeError('UNEXPECTED_REMOVED_ACTION_CHANNEL:'+old['name']+str(missing))
  if any(key[1]=='translation' and new_g['nodes'][key[0]].get('name') in WEAPONS for key in newchannels):
   raise RuntimeError('REJECTED_WEAPON_TRANSLATION_RETURNED:'+old['name'])
  # Replace output accessor index with exact original historical output, no guess/inverse-angle.
  nc,ns=find_track(cur,new_g,hip,'rotation');oc,osamp=find_track(old,old_g,hip,'rotation')
  if ns['input']!=osamp['input']:raise RuntimeError('HIP_TIMES_DIFFER_FROM_V11')
  ns['output']=osamp['output']
 return ids

def donor_source_height(donor):
 act=donor.get('actions',{})
 if any(x not in act for x in ['Idle',*ACTIONS]):raise RuntimeError('DONOR_ACTIONS_MISSING')
 idle=act['Idle']['frames'][0]['bones']
 for side in ('Left','Right'):
  if 'mixamorig:'+side+'ToeBase' not in idle:raise RuntimeError('SOURCE_IDLE_TOEBASE_MISSING')
 y=min(idle['mixamorig:'+s+'ToeBase']['worldPosition'][1] for s in ('Left','Right'))
 if not -.28<y<.25:raise RuntimeError('SOURCE_FLOOR_ABNORMAL:'+str(y))
 return y

def joint_names(g):
 ids={n.get('name'):i for i,n in enumerate(g['nodes'])}
 chains={side:[ids['mixamorig:'+side+p] for p in LEG_PARTS] for side in ('Left','Right')}
 parents={child:i for i,n in enumerate(g['nodes']) for child in n.get('children',[])}
 for chain in chains.values():
  if parents[chain[1]]!=chain[0] or parents[chain[2]]!=chain[1]:raise RuntimeError('LEG_CHAIN_HIERARCHY_MISMATCH')
 return chains,parents

def source_contact_rows(donor,name,ground):
 rows=donor['actions'][name]['frames']
 if len(rows)<5:raise RuntimeError('INSUFFICIENT_EVALUATED_SOURCE_FRAMES:'+name)
 if any(b['time']<=a['time'] for a,b in zip(rows,rows[1:])):raise RuntimeError('SOURCE_TIME_NOT_MONOTONIC:'+name)
 result=[]
 for row in rows:
  d={'time':float(row['time']),'toe':{},'weight':{}}
  for side in ('Left','Right'):
   bone=row['bones'].get('mixamorig:'+side+'ToeBase')
   if not bone:raise RuntimeError('SOURCE_TOEBASE_MISSING:'+name+':'+side)
   toe=list(bone['worldPosition']);h=toe[1]-ground
   # The source-toe anchor specifies when a contact should exist. No target pose guesses.
   # Negative source toe heights remain ground constraints, but are logged separately.
   weight=1.-smooth((h-.018)/.075)
   d['toe'][side]=toe;d['weight'][side]=weight
  result.append(d)
 return result

def eval_contact(rows,t,side):
 ts=[x['time'] for x in rows]
 if t<=ts[0]:return rows[0]['toe'][side],rows[0]['weight'][side]
 if t>=ts[-1]:return rows[-1]['toe'][side],rows[-1]['weight'][side]
 i=bisect.bisect_right(ts,t)-1;k=(t-ts[i])/(ts[i+1]-ts[i])
 return lerp(rows[i]['toe'][side],rows[i+1]['toe'][side],k),(1-k)*rows[i]['weight'][side]+k*rows[i+1]['weight'][side]

def contact_episodes(rows,side):
 spans=[];start=None
 for i,row in enumerate(rows):
  is_support=row['weight'][side]>=.52
  if is_support and start is None:start=i
  if start is not None and (not is_support or i==len(rows)-1):
   end=i if is_support else i-1
   if end>=start:spans.append((start,end))
   start=None
 return spans

def contact_target(rows,spans,t,side,base_sole,scale):
 if not spans:return None
 ts=[r['time'] for r in rows]
 i=min(range(len(ts)),key=lambda j:abs(ts[j]-t))
 matches=[(s,e) for s,e in spans if s<=i<=e]
 if not matches:return None
 s,e=matches[0]
 reference=rows[s]['toe'][side];toe,_=eval_contact(rows,t,side)
 dx=(toe[0]-reference[0])*scale;dz=(toe[2]-reference[2])*scale
 return [base_sole[0]+dx,FLOOR_Y,base_sole[2]+dz],(s,e)

def shoe_anchor(pts):
 ys=sorted(p[1] for p in pts)
 cutoff=ys[max(0,int(.12*(len(ys)-1)))]
 low=[p for p in pts if p[1]<=cutoff]
 return [sum(p[k] for p in low)/len(low) for k in range(3)]

def generate_fk(g,track,t,witnesses,skin,ibm):
 world=M.global_matrices(g,track,t)
 soles=M.skin_foot_points(witnesses,skin,ibm,world)
 return world,soles

def solve_two_bone(world,chain,parents,goal):
 up,leg,foot=chain
 h=matpos(world[up]);k=matpos(world[leg]);a=matpos(world[foot]);
 l1=norm(vsub(k,h));l2=norm(vsub(a,k));dvec=vsub(goal,h);d=norm(dvec)
 if min(l1,l2,d)<.001:raise RuntimeError('DEGENERATE_TWO_BONE_CHAIN')
 maxreach=l1+l2-.001
 minreach=abs(l1-l2)+.001
 if d>maxreach+.014 or d<minreach-.014:return None,{'targetBeyondReach_m':round(max(0,d-maxreach,minreach-d),5)}
 d1=min(maxreach,max(minreach,d));u=vn(dvec)
 original_dir=vn(vsub(a,h))
 pole=vsub(vsub(k,h),vs(u,dot(vsub(k,h),u)))
 if norm(pole)<.01:
  pole=vsub(vsub(k,h),vs(original_dir,dot(vsub(k,h),original_dir)))
 if norm(pole)<.01:
  z=cross(u,[0.,0.,1.]);pole=z if norm(z)>.02 else cross(u,[1.,0.,0.])
 pole=vn(pole)
 co=max(-1.,min(1.,(l1*l1+d1*d1-l2*l2)/(2*l1*d1)))
 kn=vadd(h,vadd(vs(u,l1*co),vs(pole,l1*math.sqrt(max(0.,1-co*co)))))
 corrected_ankle=vadd(h,vs(u,d1))
 q_upper_delta=from_to(vsub(k,h),vsub(kn,h))
 q_lower_delta=from_to(M.rotate(q_upper_delta,vsub(a,k)),vsub(corrected_ankle,kn))
 r_parent=matrix_rot(world[parents[up]]);ru=matrix_rot(world[up]);rl=matrix_rot(world[leg]);rf=matrix_rot(world[foot])
 ru_new=M.mul(q_upper_delta,ru)
 rl_new=M.mul(q_lower_delta,M.mul(q_upper_delta,rl))
 localup=M.unit(M.mul(M.inv(r_parent),ru_new))
 localleg=M.unit(M.mul(M.inv(ru_new),rl_new))
 localfoot=M.unit(M.mul(M.inv(rl_new),rf))
 return (localup,localleg,localfoot),{'targetBeyondReach_m':round(max(0.,d-maxreach,minreach-d),5), 'ankleGoalError_m':round(norm(vsub(goal,corrected_ankle)),5)}

def make_modified_track(track,chain,poses,t):
 out=dict(track)
 for idx,q in zip(chain,poses):out[(idx,'rotation')]=((t,),(tuple(q),))
 return out

def solve_support_pose(g,track,t,chain,parents,witnesses,skin,ibm,side,target,weight):
 base_world,base_shoe=generate_fk(g,track,t,witnesses,skin,ibm)
 oldsole=shoe_anchor(base_shoe[side]);up,leg,foot=chain
 if not 0<=weight<=1:raise RuntimeError('INVALID_CONTACT_WEIGHT')
 if weight<.001:return [M.sampled(*track[(j,'rotation')],t,True) for j in chain],oldsole,{'status':'not_supported'}
 ankle=matpos(base_world[foot]);aim=vadd(ankle,vsub(target,oldsole))
 if norm(vsub(target,oldsole))>.50:return None,oldsole,{'status':'unreasonable_shift','shift_m':round(norm(vsub(target,oldsole)),4)}
 best=None
 for k in range(4):
  pose,diag=solve_two_bone(base_world,chain,parents,aim)
  if pose is None:return None,oldsole,{'status':'unreachable','detail':diag}
  oldposes=[M.sampled(*track[(j,'rotation')],t,True) for j in chain]
  if max(quatang(a,b) for a,b in zip(pose,oldposes))>95:
   return None,oldsole,{'status':'joint_change_excessive','worst_deg':round(max(quatang(a,b) for a,b in zip(pose,oldposes)),2)}
  qblend=[M.slerp(a,b,weight) for a,b in zip(oldposes,pose)]
  newtrack=make_modified_track(track,chain,qblend,t)
  _,newshoe=generate_fk(g,newtrack,t,witnesses,skin,ibm)
  newsole=shoe_anchor(newshoe[side]);err=vsub(target,newsole);errnorm=norm(err)
  if best is None or errnorm<best[0]:best=(errnorm,qblend,newsole,diag)
  if errnorm<.004 or weight<.35:break
  aim=vadd(aim,vs(err,.85))
 return best[1],best[2],{'status':'IK_APPLIED','finalError_m':round(best[0],5),'detail':best[3]}

def evaluate_motion(g,b,anim,donor_rows,source_floor,side_anchors=None,solve=True,horizontal_scale=1.,root_y_shift=0.,original_anim=None):
 tracks=M.channels(g,b,anim)
 chains,parents=joint_names(g);names={n.get('name'):i for i,n in enumerate(g['nodes'])}
 hip=names['mixamorig:Hips'];hip_times=tracks[hip,'rotation'][0]
 # Bounded translation compensation is considered only if the original-pelvis,
 # no-shift IK solution cannot meet contact gates. Never rotate the pelvis.
 # Fade vertically at original source contacts and at clip boundaries.
 if abs(root_y_shift)>1e-10:
  ht,hv=tracks[hip,'translation']
  shifted=[]
  for t,v in zip(ht,hv):
   confidence=max(eval_contact(donor_rows,t,side)[1] for side in ('Left','Right'))
   edge=smooth((t-ht[0])/.13)*smooth((ht[-1]-t)/.13)
   shifted.append([v[0],v[1]+root_y_shift*confidence*edge,v[2]])
  tracks[(hip,'translation')]=(ht,shifted)
 if len(hip_times)<5:raise RuntimeError('NO_FRAME_SEQUENCE:'+anim['name'])
 wit,skin,ibm=M.foot_witnesses(g,b)
 episodes={side:contact_episodes(donor_rows,side) for side in chains}
 # A foot that never touches the floor in the native source must remain airborne.
 # We must NOT invent stance to satisfy a numeric check.
 # Base reference in original target trajectory at the donor's first planted frame.
 anchors={side:{} for side in chains}
 for side,eps in episodes.items():
  for s,e in eps:
   t=donor_rows[s]['time'];_,pts=generate_fk(g,tracks,t,wit,skin,ibm)
   anchors[side][(s,e)]=shoe_anchor(pts[side])
 scales={}
 for side,chain in chains.items():
  st=donor_rows[0]
  source_start=st['time']
  _,s_shoe=generate_fk(g,tracks,source_start,wit,skin,ibm)
  # Donor has native meter space, scale by target height / original Lionheart height.
  # This fraction remains bounded so it cannot explosively extrapolate footwork.
  scale=1.
  scales[side]=scale
 results={side:{i:[] for i in chain} for side,chain in chains.items()}
 metrics={'clip':anim['name'],'sourceFloor_m':source_floor,'sourceContactSpans':{s:[[round(donor_rows[i]['time'],3),round(donor_rows[j]['time'],3)] for i,j in episodes[s]] for s in chains},'samples':len(hip_times),'rootYShiftCandidate_m':root_y_shift,'samplesSupported':0,'preSoleMin_m':100.,'postSoleMin_m':100.,'maxContactError_m':0.,'meanContactError_m':0.,'maxJointDelta_deg':0.,'IKUnreachable':0,'IKFailures':[]}
 errors=[]
 original_track=tracks
 for t in hip_times:
  wworld,shoes=generate_fk(g,original_track,t,wit,skin,ibm)
  overrides={}
  for side,chain in chains.items():
   toe,contact_conf=eval_contact(donor_rows,t,side)
   # Protect authored Idle end poses and allow contact to fade at beginning/end.
   duration=hip_times[-1]-hip_times[0]
   edge=smooth((t-hip_times[0])/.10)*smooth((hip_times[-1]-t)/.10)
   strength=contact_conf*edge
   oldposes=[M.sampled(*original_track[(j,'rotation')],t,True) for j in chain]
   fallback=oldposes
   target=None
   if strength>.04:
    for (s,e),anchor in anchors[side].items():
     found=contact_target(donor_rows,[(s,e)],t,side,anchor,horizontal_scale*scales[side])
     if found is not None:target,cspan=found;break
   if target is not None:
    # At low-confidence transition frames we avoid claiming the sole is fully planted.
    shifted,sole,info=solve_support_pose(g,original_track,t,chain,parents,wit,skin,ibm,side,target,strength)
    if shifted is None:
     metrics['IKUnreachable']+=1
     if len(metrics['IKFailures'])<24:metrics['IKFailures'].append({'t':round(t,3),'side':side,**info})
     poses=fallback
    else:
     poses=shifted
     newtip=sole
     if strength>.85:
      errors.append(abs(sole[1]));metrics['samplesSupported']+=1
   else:poses=fallback
   for idx,q in zip(chain,poses):results[side][idx].append(q)
   metrics['maxJointDelta_deg']=max(metrics['maxJointDelta_deg'],max(quatang(a,b) for a,b in zip(poses,oldposes)))
 # Validate target actual skinned soles across ALL source contact frames and half-frames.
 combined=dict(tracks)
 for side,chain in chains.items():
  for idx in chain:combined[(idx,'rotation')]=(hip_times,results[side][idx])
 heights=[];clearances=[];bad=[]
 probe=sorted(set([float(x) for x in hip_times]+[(a+b)/2 for a,b in zip(hip_times,hip_times[1:])]))
 for t in probe:
  _,p=generate_fk(g,combined,t,wit,skin,ibm)
  for side in chains:
   _,conf=eval_contact(donor_rows,t,side)
   floor=M.floor_height(p[side]);metrics['postSoleMin_m']=min(metrics['postSoleMin_m'],floor)
   if conf>=.83 and .10<t<hip_times[-1]-.10:
    heights.append(floor)
    if floor<-.033 or floor>.065:bad.append([round(t,3),side,round(floor,4)])
   else:clearances.append(floor)
 # Original sample min floor for diagnostic (not a global clamp).
 for t in hip_times:
  _,p=generate_fk(g,tracks,t,wit,skin,ibm)
  for side in chains:metrics['preSoleMin_m']=min(metrics['preSoleMin_m'],M.floor_height(p[side]))
 if 0<len(heights)<5:raise RuntimeError('TOO_FEW_SUPPORTED_TARGET_FRAMES:'+anim['name'])
 metrics.update({'supportedSoleRMS_m':round(math.sqrt(sum(h*h for h in heights)/len(heights)),5) if heights else 0.,'worstPenetration_m':round(max(0.,-min(heights)),5) if heights else 0.,'worstHover_m':round(max(0.,max(heights)),5) if heights else 0.,'badSupportSamples':len(bad),'badSupportExamples':bad[:12], 'sourceContactSamples':len(heights),'postSoleMin_m':round(metrics['postSoleMin_m'],5),'preSoleMin_m':round(metrics['preSoleMin_m'],5)})
 return combined,results,metrics

def append_accessor(g,b,vals):
 return M.append_accessor(g,b,vals,'VEC4')

def solve_model(current,history,samples,output,check_only=False):
 global M
 M=read_tool()
 if sha(current)!=CURRENT_SHA:raise RuntimeError('CANONICAL_UNEXPECTED_SHA:'+sha(current))
 if sha(history)!=ORIGINAL_SHA:raise RuntimeError('ORIGINAL_HISTORY_SHA_MISMATCH:'+sha(history))
 source=json.loads(pathlib.Path(samples).read_text())
 if source.get('sourceKind')!='lionheart' or source.get('actionCount')!=11:raise RuntimeError('LIONHEART_EVALUATED_SOURCE_REQUIRED')
 donor_floor=donor_source_height(source)
 g,b=M.load_glb(current);g0,b0=M.load_glb(history)
 orig_g=copy.deepcopy(g);original_bytes=bytes(b)
 ids=prepare_old_and_current(g,b,g0,b0)
 # Exact historical pelvis rotation restored in EVERY Lionheart action, regardless
 # of whether old v1.2 pelvis search happened to improve a particular clip.
 report={'campaign':CAMPAIGN,'sourceModelSha256':CURRENT_SHA,'historicalModelSha256':ORIGINAL_SHA,'sourceDonorFrameCount':sum(len(source['actions'][a]['frames']) for a in ACTIONS), 'sourceGroundY_m':donor_floor,'canonical':'assets/obsidianti/Obsidianti.glb','revertedPelvisPitchAllLionheart':True,'weaponPositionTracksRemainRemoved':True,'sourceContactClassifiedFromOriginalBlender':True,'perClip':[],'modelVisuallyApproved':False,'physicsFailures':[]}
 for name in ACTIONS:
  anim=next(a for a in g['animations'] if a['name']=='Lionheart_'+name)
  donor=source_contact_rows(source,name,donor_floor)
  choices=[]
  # Fit horizontal donor stride at original pelvis height first. Explore small,
  # smoothly faded root-Y translation only when physically necessary.
  for hs in (1.,.5,0.):
   tr,rotations,metrics=evaluate_motion(g,b,anim,donor,donor_floor,horizontal_scale=hs)
   score=metrics['supportedSoleRMS_m'] + 2*metrics['worstPenetration_m']+.005*metrics['IKUnreachable']+.002*metrics['badSupportSamples']
   choices.append((score,hs,0.,rotations,metrics,tr))
  choices.sort(key=lambda x:x[0]);score,hs,root_shift,rotations,metrics,tr=choices[0]
  def valid(m):
   return ((m['sourceContactSamples']>=5 or not any(m['sourceContactSpans'].values())) and
     m['supportedSoleRMS_m']<=.055 and m['worstPenetration_m']<=.08 and
     m['IKUnreachable']<=int(len(donor)*.22))
  if not valid(metrics):
   for root in (-.02,.02,-.04,.04,-.07,.07):
    for horizontal in (1.,.5,0.):
     tt,rr,mm=evaluate_motion(g,b,anim,donor,donor_floor,horizontal_scale=horizontal,root_y_shift=root)
     sc=mm['supportedSoleRMS_m']+2*mm['worstPenetration_m']+.005*mm['IKUnreachable']+.002*mm['badSupportSamples']+.1*abs(root)
     choices.append((sc,horizontal,root,rr,mm,tt))
   choices.sort(key=lambda x:x[0])
   # Prefer a valid fitted contact over an invalid lower numeric score.
   eligible=[r for r in choices if valid(r[4])]
   score,hs,root_shift,rotations,metrics,tr=(min(eligible,key=lambda v:v[0]) if eligible else choices[0])
  metrics['horizontalDonorScale']=hs;metrics['rootYShiftApplied_m']=root_shift
  metrics['searchProfiles']=[{'horizontalScale':v,'rootYShift_m':root,'score':round(sc,6),'valid':valid(m)} for sc,v,root,_,m,_ in choices]
  # Don't push a bundle of broken actions; record exact failing physical evidence.
  if not valid(metrics):
   report['physicsFailures'].append({'clip':anim['name'],'reason':'INSUFFICIENT_SOURCE_GROUNDED_IK','evidence':metrics})
   report['perClip'].append(metrics)
   # Continue evaluating the OTHER Lionheart actions, not just this first failure.
   # Do not apply this invalid clip or commit a partially corrected model.
   continue
  # Root correction is a last-resort, CONTACT-GATED, tiny vertical displacement.
  # Existing horizontal pelvis motion and all pelvis rotation tracks remain untouched
  # except for the exact historical v1.1 pitch reversal above.
  if abs(root_shift)>1e-10:
   _,hsampler=find_track(anim,g,ids['mixamorig:Hips'],'translation')
   hsampler['output']=M.append_accessor(g,b,tr[ids['mixamorig:Hips'],'translation'][1],'VEC3')
  # Add only 6 leg-joint rotation accessor updates, leaving weapons and all
  # other author-provided animation records untouched.
  for side,rot in rotations.items():
   for idx,qs in rot.items():
    ch,s=find_track(anim,g,idx,'rotation')
    if len(M.Access(g,b).get(s['input']))!=len(qs):raise RuntimeError('JOINT_SAMPLE_LENGTH_DIFFERENT')
    s['output']=append_accessor(g,b,qs)
  report['perClip'].append(metrics)
 if report['physicsFailures']:
  report['status']='PHYSICAL_CONTACT_PREFLIGHT_FAILED_NO_MODEL_MUTATION'
  report['passedSourceActionCount']=len(ACTIONS)-len(report['physicsFailures'])
  pathlib.Path(output).parent.mkdir(parents=True,exist_ok=True)
  pathlib.Path(output).write_text(json.dumps(report,indent=2)+'\n')
  raise RuntimeError('SOURCE_GROUNDED_IK_FAILED_'+str(len(report['physicsFailures']))+'_CLIPS; REPORT='+str(output))
 # Preserve exact original user-authored non-Lionheart clips and bindings.
 for before,after in zip(orig_g['animations'],g['animations']):
  if not before['name'].startswith('Lionheart_') or before['name']=='LionheartIdle_UNREVIEWED':
   if before!=after:raise RuntimeError('PROTECTED_CLIP_MUTATED:'+before['name'])
 if g['nodes']!=orig_g['nodes'] or g['skins']!=orig_g['skins'] or g['meshes']!=orig_g['meshes'] or g['scenes']!=orig_g['scenes']:
  raise RuntimeError('MESH_OR_RIG_CHANGED')
 blob=M.encode_glb(g,b);n,_,=struct.unpack_from('<I4s',blob,12)
 p=20+n;nb,t=struct.unpack_from('<I4s',blob,p)
 if t!=b'BIN\0' or blob[p+8:p+8+len(original_bytes)]!=original_bytes:raise RuntimeError('ORIGINAL_GLB_BIN_BYTES_MODIFIED')
 afterpath=pathlib.Path(current)
 report['beforeSha256']=CURRENT_SHA;report['candidateByteSha256']=hashlib.sha256(blob).hexdigest();report['clipCount']=len(g['animations']);report['status']='PREFLIGHT_REPORT_UNPUBLISHED' if check_only else 'ONE_CANONICAL_CANDIDATE_VISUAL_REVIEW_PENDING'
 pathlib.Path(output).parent.mkdir(parents=True,exist_ok=True);pathlib.Path(output).write_text(json.dumps(report,indent=2)+'\n')
 if not check_only:
  fd,tmp=tempfile.mkstemp(prefix='.obsidianti-ik-atomic-',suffix='.tmp',dir=str(afterpath.parent))
  try:
   with os.fdopen(fd,'wb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
   os.replace(tmp,afterpath)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
  if sha(afterpath)!=report['candidateByteSha256']:raise RuntimeError('POSTWRITE_MODEL_HASH_MISMATCH')
 print('MODEL_PREVIEW_STATUS='+report['status']+'\nCANDIDATE_SHA256='+report['candidateByteSha256']+'\nIK_CLIPS='+str(len(report['perClip'])),flush=True)
 return report

def cli():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--historical',required=True);p.add_argument('--source',required=True);p.add_argument('--report',required=True);p.add_argument('--check-only',action='store_true');a=p.parse_args()
 solve_model(a.model,a.historical,a.source,a.report,a.check_only)
if __name__=='__main__':cli()
