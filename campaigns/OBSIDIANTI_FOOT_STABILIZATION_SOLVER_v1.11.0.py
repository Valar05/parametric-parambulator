"""Obsidianti v1.11.0: isolated candidate, sample actual edited FK action, contact-aware correction.

Never overwrites uploaded reference or original actions. Exports only candidate/review actions.
"""
import bpy,sys,math,json,pathlib,statistics,traceback
from mathutils import Vector, Matrix
src,out,reportfile=sys.argv[sys.argv.index('--')+1:]
MOVES=('Heavy1','Heavy2','Heavy3')
RIG='OBSIDIANTI_SPARSE_FK_EDITABLE_UNAPPROVED'
RIGHT=('mixamorig:RightUpLeg','mixamorig:RightLeg','mixamorig:RightFoot')
LEFT=('mixamorig:LeftUpLeg','mixamorig:LeftLeg','mixamorig:LeftFoot')
R={'status':'STARTED','source':src,'actions':{},'sourceUnchanged':True,'approved':False,'method':'TEMPORARY_TWO_BONE_IK_FK_BAKE'}
def save():pathlib.Path(reportfile).write_text(json.dumps(R,indent=2,sort_keys=True)+'\n')
def frame(t):
 k=math.floor(t);bpy.context.scene.frame_set(k,subframe=t-k);bpy.context.view_layer.update()
def xyz(v):return [round(float(x),8) for x in v]
def dist(a,b):return (a-b).length
def worldpoint(ob,pb):return ob.matrix_world@pb.head
def quat_diff(a,b):return math.degrees(a.rotation_difference(b).angle)
def setup_action(arm,act):
 arm.animation_data_create();arm.animation_data.action=act
 for tr in arm.animation_data.nla_tracks:tr.mute=True

def contact_runs(samples,side):
 # Source actual foot trajectories; require low height and nearly stationary horizontal speed.
 heights=[p[side]['foot'].z for p in samples]
 ground=min(heights)
 span=max(heights)-ground
 limit=ground+max(.012,min(.045,span*.18))
 horizontal=[]
 for i,p in enumerate(samples):
  a=samples[max(0,i-1)][side]['foot'];b=samples[min(len(samples)-1,i+1)][side]['foot']
  horizontal.append(math.hypot(b.x-a.x,b.y-a.y)/max(1,min(len(samples)-1,i+1)-max(0,i-1)))
 # Tolerate slight authored jitter while excluding obvious swings.
 speeds=sorted(horizontal)
 threshold=max(.012,min(.065,statistics.median(speeds)*1.65+.005))
 flags=[h<=limit and v<=threshold for h,v in zip(heights,horizontal)]
 runs=[];start=None
 for i,on in enumerate(flags+[False]):
  if on and start is None:start=i
  if not on and start is not None:
   if i-start>=3:runs.append((start,i-1))
   start=None
 return runs,{'groundEstimate':ground,'heightThreshold':limit,'horizontalThresholdPerFrame':threshold,'ranges':runs}

def keycopy_act(action,name):
 dup=action.copy();dup.name=name
 return dup

def clear_bone_quaternion_fcurves(act,bones):
 try:fc=list(act.fcurves)
 except Exception:raise RuntimeError('ANIMATION_FCURVES_UNSUPPORTED_SAFE_STOP')
 for f in fc:
  if any(f.data_path=='pose.bones["'+b+'"].rotation_quaternion' for b in bones):act.fcurves.remove(f)

def build_candidate(arm,move,source):
 setup_action(arm,source)
 lo,hi=map(int,(math.floor(source.frame_range[0]),math.ceil(source.frame_range[1])))
 times=list(range(lo,hi+1));original=[]
 for t in times:
  frame(t)
  row={}
  for side,bones in (('Right',RIGHT),('Left',LEFT)):
   row[side]={'hip':worldpoint(arm,arm.pose.bones[bones[0]]).copy(),
              'knee':worldpoint(arm,arm.pose.bones[bones[1]]).copy(),
              'foot':worldpoint(arm,arm.pose.bones[bones[2]]).copy(),
              'footM':arm.pose.bones[bones[2]].matrix.copy(),
              'upM':arm.pose.bones[bones[0]].matrix.copy(),
              'shinM':arm.pose.bones[bones[1]].matrix.copy()}
  original.append(row)
 runs,contact=contact_runs(original,'Right')
 record={'sourceAction':source.name,'frameRange':[lo,hi],'contact':contact,'frames':len(times),'editedLeg':'Right', 'sourceReferenceRetained':True}
 if not runs:
  record['status']='NO_CONFIDENT_CONTACT_WINDOWS_NO_SYNTHETIC_FIX';return None,record
 # Work with a source action, compute evaluated IK matrices in-memory, then key onto a fresh FK copy.
 upper,lower,foot=(arm.pose.bones[b] for b in RIGHT)
 target=bpy.data.objects.new('TEMP_OBS_FOOT_TARGET_'+move,None)
 pole=bpy.data.objects.new('TEMP_OBS_KNEE_POLE_'+move,None)
 bpy.context.scene.collection.objects.link(target);bpy.context.scene.collection.objects.link(pole)
 constraint=lower.constraints.new('IK');constraint.name='TEMP_OBS_CONTACT_IK';constraint.target=target;constraint.chain_count=2;constraint.use_stretch=False
 constraint.pole_target=pole;constraint.pole_angle=0.0
 # Use original knee-plane direction for pole, with parent-independent scene coordinates.
 desired_by_frame={}
 for a,b in runs:
  points=[original[i]['Right']['foot'] for i in range(a,b+1)]
  med=Vector(tuple(statistics.median(p[j] for p in points) for j in range(3)))
  # Maintain original contact height: don't invent a floor height, choose lowest stable reference median.
  med.z=statistics.median(p.z for p in points)
  for i in range(a,b+1):desired_by_frame[i]=med.copy()
 # Source action remains untouched; solve at frame only and preserve baseline foot orientation.
 solved={};measure=[]
 for i,t in enumerate(times):
  if i not in desired_by_frame:continue
  frame(t)
  desired=desired_by_frame[i]
  # Select pole in the original bend plane, using a perpendicular toward the FK knee.
  hip=original[i]['Right']['hip'];knee=original[i]['Right']['knee']
  axis=desired-hip
  if axis.length<1e-5:continue
  axis.normalize();off=knee-hip;perp=off-axis*off.dot(axis)
  if perp.length<1e-5:continue
  perp.normalize()
  pole.location=knee+perp*max(.3,(knee-hip).length*3)
  target.location=desired
  constraint.influence=1.0
  bpy.context.view_layer.update()
  ev=arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
  bones={b:ev.pose.bones[b].matrix.copy() for b in RIGHT}
  achieved=ev.matrix_world@ev.pose.bones[RIGHT[2]].head
  knee_actual=ev.matrix_world@ev.pose.bones[RIGHT[1]].head
  error=dist(achieved,desired)
  knee_delta=dist(knee_actual,knee)
  # Hard bound: do not choose geometrically irrational or solver-flipped poses.
  if error<=.01 and knee_delta<=.085:
   solved[t]=bones
  measure.append({'frame':t,'footTargetError_m':round(error,6),'kneeChange_m':round(knee_delta,6),'accepted':t in solved})
 lower.constraints.remove(constraint)
 bpy.data.objects.remove(target,do_unlink=True);bpy.data.objects.remove(pole,do_unlink=True)
 record.update({'solvedFrames':len(solved),'contactCandidateFrames':len(desired_by_frame),'samples':measure})
 if len(solved)<3 or len(solved)<.6*len(desired_by_frame):
  record['status']='IK_GEOMETRY_REJECTED';return None,record
 candidate=keycopy_act(source,'STABILIZED_FK_'+move)
 # Only act on the right leg. Left and body channels are inherited unchanged.
 clear_bone_quaternion_fcurves(candidate,RIGHT)
 setup_action(arm,candidate)
 # Populate a quaternion key at every source frame for stable playback without IK dependencies.
 for i,t in enumerate(times):
  frame(t)
  if t in solved:
   for name in RIGHT:
    pose=arm.pose.bones[name]
    pose.rotation_mode='QUATERNION'
    # Parent-first, assigning evaluated pose matrices to basis without IK.
    pose.matrix=solved[t][name]
    bpy.context.view_layer.update()
    pose.keyframe_insert(data_path='rotation_quaternion',frame=t,group=name)
  else:
   for name in RIGHT:
    pose=arm.pose.bones[name]
    pose.rotation_mode='QUATERNION'
    pose.matrix=original[i]['Right'][{'mixamorig:RightUpLeg':'upM','mixamorig:RightLeg':'shinM','mixamorig:RightFoot':'footM'}[name]]
    bpy.context.view_layer.update()
    pose.keyframe_insert(data_path='rotation_quaternion',frame=t,group=name)
 # Evaluate source vs candidate contact drift at integers and half-frames.
 corrected=[]
 for t in [lo+j*.5 for j in range((hi-lo)*2+1)]:
  frame(t);p=arm.matrix_world@arm.pose.bones[RIGHT[2]].head;corrected.append((t,p.copy()))
 maxjump=max((dist(a[1],b[1]) for a,b in zip(corrected,corrected[1:])),default=0)
 record['maxHalfFrameFootStep_m']=round(maxjump,6)
 baseline_error=[];corrected_error=[]
 for a,b in runs:
  anchor=desired_by_frame[a]
  for i in range(a,b+1):
   baseline_error.append(dist(original[i]['Right']['foot'],anchor))
   frame(times[i]);corrected_error.append(dist(arm.matrix_world@arm.pose.bones[RIGHT[2]].head,anchor))
 before=statistics.mean(baseline_error) if baseline_error else 0
 after=statistics.mean(corrected_error) if corrected_error else 0
 record['meanContactDriftBefore_m']=round(before,7)
 record['meanContactDriftAfter_m']=round(after,7)
 record['improvementFraction']=round((before-after)/before,5) if before>1e-6 else 0
 record['maximumContactDriftAfter_m']=round(max(corrected_error,default=0),6)
 if before<.002 or after>=before*.92 or max(corrected_error,default=0)>.025:
  record['status']='CONTACT_IMPROVEMENT_NOT_PROVEN_REFERENCE_FALLBACK'
  bpy.data.actions.remove(candidate,do_unlink=True)
  return None,record
 record['status']='CANDIDATE_UNAPPROVED'
 return candidate,record

def main():
 bpy.ops.wm.open_mainfile(filepath=src,load_ui=False)
 arm=bpy.data.objects.get(RIG)
 if arm is None or arm.type!='ARMATURE':raise RuntimeError('EXACT_AUTHOR_RIG_MISSING')
 reference=bpy.data.objects.get('OBSIDIANTI_FK_REFERENCE_DO_NOT_EDIT')
 if reference is None:raise RuntimeError('REFERENCE_RIG_MISSING')
 if not all(x in arm.pose.bones for x in RIGHT):raise RuntimeError('RIGHT_LEG_BONES_MISSING')
 originals={m:bpy.data.actions.get('SPARSE_FK_'+m) for m in MOVES}
 if not all(originals.values()):raise RuntimeError('EDITED_SPARSE_ACTIONS_MISSING')
 baseline_names=[a.name for a in bpy.data.actions]
 results={}
 for move,source in originals.items():
  cand,record=build_candidate(arm,move,source)
  R['actions'][move]=record
  results[move]=cand
  save();print('STABILIZATION_'+move+'='+record['status']+' SOLVED='+str(record.get('solvedFrames',0)),flush=True)
 # Reviewable cases receive both BEFORE and AFTER if corrected, or an explicit source fallback.
 review=[]
 for m in MOVES:
  before=originals[m].copy();before.name='BEFORE_EDITED_'+m;review.append(before)
  if results[m] is not None:review.append(results[m])
  else:
   fallback=originals[m].copy();fallback.name='FALLBACK_UNCHANGED_'+m;review.append(fallback)
 arm.animation_data_create();arm.animation_data.action=None
 for t in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(t)
 for action in review:
  tr=arm.animation_data.nla_tracks.new();tr.name=action.name
  strip=tr.strips.new(action.name,int(action.frame_range[0]),action);strip.blend_type='REPLACE';strip.influence=1.0;tr.mute=False
 meshes=[]
 for ob in bpy.data.objects:
  if ob.type=='MESH' and ob.name.startswith('SPARSE_EDIT_') and (ob.parent==arm or any(m.type=='ARMATURE' and m.object==arm for m in ob.modifiers)):meshes.append(ob)
 if not meshes:raise RuntimeError('SKINNED_MESH_MISSING')
 for ob in bpy.context.selected_objects:ob.select_set(False)
 for ob in bpy.data.objects:
  if ob.type in {'MESH','ARMATURE'}:
   ob.hide_set(False);ob.hide_render=False;ob.select_set(ob==arm or ob in meshes)
 bpy.context.view_layer.objects.active=arm;frame(1)
 opts={'filepath':out,'export_format':'GLB','use_selection':True,'export_animations':True,'export_nla_strips':True,'export_yup':True,'export_lights':False,'export_cameras':False}
 prop=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
 if 'export_selected' in prop:opts['export_selected']=opts.pop('use_selection')
 if 'export_animation_mode' in prop:opts['export_animation_mode']='NLA_TRACKS'
 if 'export_force_sampling' in prop:opts['export_force_sampling']=True
 for k in list(opts):
  if k not in prop:opts.pop(k)
 z=bpy.ops.export_scene.gltf(**opts)
 if 'FINISHED' not in z or pathlib.Path(out).stat().st_size<20000:raise RuntimeError('GLB_EXPORT_FAILED')
 blend=str(pathlib.Path(out).with_suffix('.blend'));bpy.ops.wm.save_as_mainfile(filepath=blend)
 R.update({'status':'REVIEW_READY_UNAPPROVED','reviewClips':[a.name for a in review],'candidateCount':sum(x is not None for x in results.values()),'exportGLB':out,'exportBlend':blend})
 save();print('REVIEW_EXPORT_READY='+out+' CANDIDATES='+str(R['candidateCount']),flush=True)
try:main()
except Exception as e:
 R.update(status='BLOCKED',error=type(e).__name__+': '+str(e));save();traceback.print_exc();raise
