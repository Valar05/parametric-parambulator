#!/usr/bin/env python3
"""One-invocation Termux Git campaign: purchased ARP full source library to one review GLB."""
from __future__ import annotations
import datetime,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,time,uuid,traceback
V='OBSIDIANTI_VANGUARD_RIGIFY_ARP_v2.0.17'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BASE='3501004150ac2db37a2609872004827427d2b126' # v214 source is verified by GIT readback
AGENTS='547c2af52303f4efb718bbf8f82a698110c7bfca'
CANON='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
VANGUARD='ca91335b8f4d5dc7d89267c18eff8740652e2bfc90710cebe6997d29caa1e541'

ARPZIP='2b377bbc5d81dfcef4209971e332a8bcb402ed44605e5ed0cddc2e90fafebf28'
TARGET='assets/obsidianti/Obsidianti.glb'
LOCKED=[TARGET,'assets/repl/Repl.glb',
        'diagnostics/obsidianti/arp-interactive-review-v2.0.13/runs/20261107T021037Z-2edec0d5/AxeKick/ARP_AxeKick_REVIEW.glb']
OLDTRIAL='campaigns/OBSIDIANTI_ARP_BLENDER5_ISOLATED_v2.0.12_blender_trial.py'
OLDEXPORT='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_export.py'
OLDVIEW='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_viewer.html'
OLDSERVER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_server.py'
OLDHELPER='campaigns/OBSIDIANTI_ARP_INTERACTIVE_REVIEW_v2.0.13_driver.py'
VANGUARD_CLIPS=['0T-Pose','ClubIdle','Idle','Jump','JumpCrouch','JumpForward','Land',
 'LedgeClimb','LedgeGrab','LedgeGrabHang','Midair','MidairSwordAttack1',
 'MidairSwordAttack2','RunForwardOld','SpinAttack','SwordAttack1','SwordAttack2',
 'SwordAttack4','SwordAttack5']
REL='diagnostics/obsidianti/vanguard-rigify-arp-v2.0.17/runs/'
SOURCES={
 'campaigns/'+V+'_LAUNCH.sh':'LAUNCHER',
 'campaigns/'+V+'_driver.py':'driver.py',
 'campaigns/'+V+'_merge.py':'merge.py',
 'campaigns/'+V+'_blender_trial.py':'blender_trial.py',
 'campaigns/'+V+'_viewer.html':'viewer.html',
 'campaigns/'+V+'_server.py':'server.py',
 'campaigns/'+V+'.contract.json':'contract.json',
 'tests/'+V+'_TEST.py':'test_driver.py',
 'campaigns/'+V+'_source_audit.py':'source_audit.py'}

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for buf in iter(lambda:f.read(1048576),b''):h.update(buf)
 return h.hexdigest()

def command(argv,timeout=500,check=True,env=None):
 argv=[str(x) for x in argv]
 p=subprocess.run(argv,capture_output=True,text=True,errors='replace',stdin=subprocess.DEVNULL,timeout=timeout,env=env)
 if check and p.returncode:raise RuntimeError('COMMAND_FAILED_'+str(p.returncode)+' '+repr(argv[:5])+' '+p.stderr[-600:]+' '+p.stdout[-250:])
 return p

def git(repo,*a,timeout=400,check=True):return command(['git','-C',repo,*a],timeout=timeout,check=check)
def g(repo,*a):return git(repo,*a).stdout.strip()
def write_json(p,value):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_name('.'+p.name+'.'+uuid.uuid4().hex[:8]+'.tmp')
 tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(tmp,p)
def copy_new(a,b):
 a=pathlib.Path(a);b=pathlib.Path(b)
 if not a.is_file() or a.is_symlink():raise RuntimeError('SOURCE_NOT_REGULAR_'+str(a))
 if b.exists():
  if b.is_file() and not b.is_symlink() and digest(b)==digest(a):return
  raise RuntimeError('DESTINATION_COLLISION_'+str(b))
 b.parent.mkdir(parents=True,exist_ok=True)
 temp=b.with_name('.'+b.name+'.'+uuid.uuid4().hex[:8])
 shutil.copy2(a,temp)
 if digest(a)!=digest(temp):raise RuntimeError('COPY_HASH_MISMATCH')
 os.replace(temp,b)
def require(expr,label):
 if not expr:raise RuntimeError(label)
def patch_one(s,old,new):
 n=s.count(old)
 if n!=1:raise RuntimeError('SOURCE_PATCH_PRECONDITION_'+str(n)+'_'+old[:70])
 return s.replace(old,new,1)
def import_path(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod

def verify_pinned_ancestry(repo,base,head):
 """Prove the pinned base is truly in the history of the checked-out main.

 A depth-one clone has no parent for HEAD. Fetching only the BASE object does
 not restore HEAD's parent links; the old campaign falsely rejected valid Git.
 Deepen the TRACKED main history, not just the pinned commit object. The full
 history fallback is bounded and never changes the checked-out revision.
 """
 if git(repo,'merge-base','--is-ancestor',base,head,check=False).returncode==0:
  return {'base':base,'head':head,'method':'ALREADY_COMPLETE','isAncestor':True}
 observed=[]
 for stage,flags in [('DEEPEN_16',['--deepen=16']),('DEEPEN_128',['--deepen=128']),
                     ('DEEPEN_512',['--deepen=512']),('UNSHALLOW',['--unshallow'])]:
  if g(repo,'rev-parse','--is-shallow-repository')!='true':break
  last=None
  for attempt in range(2):
   p=git(repo,'fetch','--no-tags',*flags,'origin','main',timeout=1000,check=False)
   observed.append({'stage':stage,'attempt':attempt+1,'returnCode':p.returncode})
   last=p
   if p.returncode==0:break
   time.sleep(attempt+1)
  if last is None or last.returncode!=0:
   raise RuntimeError('GIT_MAIN_HISTORY_FETCH_FAILED_'+stage+'_rc='+str(last.returncode if last else 'NONE')+
                      '_'+str(last.stderr[-450:] if last else ''))
  require(g(repo,'rev-parse','HEAD')==head,'GIT_HISTORY_FETCH_CHANGED_CHECKED_OUT_HEAD')
  if git(repo,'merge-base','--is-ancestor',base,head,check=False).returncode==0:
   print('GIT_SHALLOW_ANCESTRY_RECOVERED='+stage+' BASE='+base+' HEAD='+head,flush=True)
   return {'base':base,'head':head,'method':stage,'attempts':observed,'isAncestor':True}
 # Do not silently accept an unrelated, rewritten branch. An unshallowed Git
 # graph with no ancestor relationship is a real divergence and is a hard stop.
 raise RuntimeError('PINNED_GIT_BASE_NOT_ANCESTOR_AFTER_VERIFIED_MAIN_HISTORY_FETCH '+
                    'base='+base+' head='+head+' shallow='+g(repo,'rev-parse','--is-shallow-repository'))

def checkout(root):
 repo=root/'repo'
 env=dict(os.environ,GIT_LFS_SKIP_SMUDGE='1',GIT_TERMINAL_PROMPT='0')
 command(['git','clone','--quiet','--depth=1','--branch=main','--single-branch',REMOTE,repo],timeout=1200,env=env)
 require(g(repo,'remote','get-url','origin').removesuffix('.git')==REMOTE.removesuffix('.git'),'WRONG_REMOTE')
 head=g(repo,'rev-parse','HEAD')
 ancestry=verify_pinned_ancestry(repo,BASE,head)
 require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'AGENTS_CHANGED_RULES_READ_BLOCKED')
 for p,sha in ((TARGET,CANON),):
  require('oid sha256:'+sha in git(repo,'show','HEAD:'+p).stdout,'PINNED_LFS_POINTER_CHANGED_'+p)
 require(not g(repo,'status','--porcelain'),'ISOLATED_CHECKOUT_NOT_CLEAN')
 return repo,head,ancestry

def hydrate(repo,paths):
 git(repo,'lfs','install','--local',timeout=100)
 for path,expected in paths.items():
  if (repo/path).is_file() and digest(repo/path)==expected:continue
  git(repo,'lfs','pull','--include='+path,'--exclude=','origin',timeout=2000,check=False)
  git(repo,'lfs','fetch','--include='+path,'--exclude=','origin','HEAD',timeout=2000,check=False)
  git(repo,'lfs','checkout',path,timeout=450,check=False)
  require((repo/path).is_file() and digest(repo/path)==expected,'VERIFIED_LFS_OBJECT_UNAVAILABLE_'+path)
  print('INPUT_VERIFIED='+path+' SHA256='+expected,flush=True)

def source_vanguard(downloads):
 search_roots=[downloads,downloads.parent/'Documents',downloads.parent/'Movies',downloads.parent/'Models',downloads.parent]
 # File already uploaded by owner; inspect ONLY Vanguard*.glb, never select by filename alone.
 seen=set()
 for folder in search_roots:
  if not folder.is_dir():continue
  for p in sorted(folder.glob('Vanguard*.glb')):
   if str(p) in seen:continue
   seen.add(str(p))
   if p.is_file() and not p.is_symlink() and digest(p)==VANGUARD:
    return p
 raise RuntimeError('VANGUARD_EXACT_GLB_NOT_ON_PHONE_SHA_'+VANGUARD+'; download owner-uploaded Vanguard.glb to Android Downloads')

def vendor(downloads):
 archive=downloads/'auto_rig_pro_3.79.17.zip'
 require(archive.is_file() and digest(archive)==ARPZIP,'PURCHASED_ARP_ZIP_MISSING_OR_CHANGED')
 private=pathlib.Path.home()/'.local/share/obsidianti-arp-purchased/3.79.17'/ARPZIP[:16]/'modules'
 require(private.is_dir() and len([p for p in private.iterdir() if p.is_dir() and (p/'__init__.py').is_file()])==1,
         'PURCHASED_ARP_PRIVATE_MODULE_MISSING')
 return private

def create_sources(repo,packet):
 src=(repo/OLDTRIAL).read_text()
 # Source is the user's original Vanguard GLB. Import on every disposable trial;
 # preserve the entire original Rigify hierarchy, map only selected ORG joints.
 source_block="""  bpy.ops.wm.open_mainfile(filepath=args.source,load_ui=False)
  source_candidates=[o for o in bpy.data.objects if o.type=='ARMATURE' and all('mixamorig:'+p in o.pose.bones for p in MONITOR)]
  if len(source_candidates)!=1:raise RuntimeError('NATIVE_SOURCE_ARMATURE_NOT_UNIQUE '+repr([o.name for o in source_candidates]))
  src=source_candidates[0];action=select_action(src,args.clip)
"""
 new_block="""  bpy.ops.import_scene.gltf(filepath=args.source,import_shading='NORMALS')
  source_candidates=[o for o in bpy.data.objects if o.type=='ARMATURE' and all(n in o.pose.bones for n in SOURCE_BONE_NAMES)]
  if len(source_candidates)!=1:raise RuntimeError('VANGUARD_SOURCE_RIG_NOT_UNIQUE '+repr([o.name for o in source_candidates]))
  src=source_candidates[0]
  originals={x.name for x in src.data.bones}
  if not all(org in originals for org in ORG_TO_MIXAMO):raise RuntimeError('VANGUARD_REQUIRED_ORG_BONE_MISSING')
  if any(dst in originals for dst in ORG_TO_MIXAMO.values()):raise RuntimeError('VANGUARD_ALREADY_HAS_TARGET_BONE_NAMES')
  for org,dst in ORG_TO_MIXAMO.items():src.data.bones[org].name=dst
  # Blender normally updates paths on a bone rename. Verify/repair imported
  # layered Action FCurves explicitly; don't mistake empty tracks for success.
  patched=0
  for act in bpy.data.actions:
   for layer in act.layers:
    for strip in layer.strips:
     for slot in act.slots:
      if slot.target_id_type!='OBJECT':continue
      try:bag=strip.channelbag(slot,ensure=False)
      except (AttributeError,TypeError,RuntimeError):bag=None
      if not bag:continue
      for fc in bag.fcurves:
       path=fc.data_path
       for org,dst in ORG_TO_MIXAMO.items():
        if ('"'+org+'"') in path:path=path.replace('"'+org+'"','"'+dst+'"')
       if path!=fc.data_path:fc.data_path=path;patched+=1
  action=select_action(src,args.clip)
  result['vanguardRigify']={'originalJoints':len(originals),'mappedORG':dict(ORG_TO_MIXAMO),
      'otherJointsPreservedAsSourceOnly':len(originals)-len(ORG_TO_MIXAMO),
      'fcurvesPatchedAfterBoneRename':patched,'sourceAnimations':len(bpy.data.actions)}
"""
 src=patch_one(src,source_block,new_block)
 mapping="""ORG_TO_MIXAMO={
 'ORG-hips':'mixamorig:Hips','ORG-spine':'mixamorig:Spine',
 'ORG-chest':'mixamorig:Spine2','ORG-neck':'mixamorig:Neck','ORG-head':'mixamorig:Head',
 'ORG-shoulder.L':'mixamorig:LeftShoulder','ORG-upper_arm.L':'mixamorig:LeftArm',
 'ORG-forearm.L':'mixamorig:LeftForeArm','ORG-hand.L':'mixamorig:LeftHand',
 'ORG-shoulder.R':'mixamorig:RightShoulder','ORG-upper_arm.R':'mixamorig:RightArm',
 'ORG-forearm.R':'mixamorig:RightForeArm','ORG-hand.R':'mixamorig:RightHand',
 'ORG-thigh.L':'mixamorig:LeftUpLeg','ORG-shin.L':'mixamorig:LeftLeg',
 'ORG-foot.L':'mixamorig:LeftFoot','ORG-toe.L':'mixamorig:LeftToeBase',
 'ORG-thigh.R':'mixamorig:RightUpLeg','ORG-shin.R':'mixamorig:RightLeg',
 'ORG-foot.R':'mixamorig:RightFoot','ORG-toe.R':'mixamorig:RightToeBase'}
SOURCE_BONE_NAMES=set(ORG_TO_MIXAMO)
"""
 src=patch_one(src,"MONITOR=('LeftUpLeg'",mapping+"MONITOR=('LeftUpLeg'")
 # Select populated Blender 5 glTF action slot; ignore unused rig-control slots.
 old="""def select_action(src,clip):
 acts=[a for a in bpy.data.actions if a.name==clip]
 if len(acts)!=1:raise RuntimeError('NATIVE_SOURCE_ACTION_MISSING '+clip)
 ad=src.animation_data_create();ad.use_nla=False
 for t in ad.nla_tracks:t.mute=True
 ad.action=acts[0]
 if hasattr(ad,'action_slot') and ad.action_slot is None and hasattr(acts[0],'slots'):
  for slot in acts[0].slots:ad.action_slot=slot;break
 return acts[0]
"""
 new="""def select_action(src,clip):
 acts=[a for a in bpy.data.actions if a.name==clip]
 if len(acts)!=1:raise RuntimeError('VANGUARD_SOURCE_ACTION_MISSING '+clip)
 action=acts[0];choices=[]
 for slot in getattr(action,'slots',[]):
  if slot.target_id_type!='OBJECT':continue
  count=0;useful=0
  for layer in action.layers:
   for strip in layer.strips:
    try:bag=strip.channelbag(slot,ensure=False)
    except (AttributeError,TypeError,RuntimeError):bag=None
    if not bag:continue
    count+=len(bag.fcurves)
    useful+=sum(1 for f in bag.fcurves if 'mixamorig:' in f.data_path)
  choices.append((useful,count,str(slot.identifier),slot))
 if not choices:raise RuntimeError('VANGUARD_NO_OBJECT_ACTION_SLOTS_'+clip)
 useful,count,label,chosen=max(choices,key=lambda x:(x[0],x[1]))
 if count<25 or useful<12:raise RuntimeError('VANGUARD_SOURCE_ACTION_SLOT_EMPTY_'+clip+'_'+repr([(x[2],x[0],x[1]) for x in choices]))
 ad=src.animation_data_create();ad.use_nla=False
 for tr in ad.nla_tracks:tr.mute=True
 ad.action=action;ad.action_slot=chosen
 if ad.action_slot!=chosen:raise RuntimeError('VANGUARD_ACTION_SLOT_NOT_BOUND_'+clip)
 src['vanguard_source_slot']=label;src['vanguard_source_fcurves']=count
 src['vanguard_mapped_fcurves']=useful
 return action
"""
 src=patch_one(src,old,new)
 src=patch_one(src,"  result['arpSourceAction']=scene.source_action", """  result['arpSourceAction']=scene.source_action
  saved_slot=next((s for s in action.slots if s.identifier==src.get('vanguard_source_slot')),None)
  if saved_slot is None:raise RuntimeError('VANGUARD_ACTION_SLOT_LOST_AFTER_ARP_CALLBACK')
  src.animation_data.action=action;src.animation_data.action_slot=saved_slot
  result['sourceSlot']={'identifier':saved_slot.identifier,
   'fcurves':int(src['vanguard_source_fcurves']),'mappedFcurves':int(src['vanguard_mapped_fcurves'])}""")
 # Static T pose is an explicitly labeled diagnostic, not advertised as movement.
 src=patch_one(src,"  if end-start<5 or end-start>180:raise RuntimeError('NATIVE_ACTION_FRAME_RANGE_UNEXPECTED')", 
 "  if end-start>300:raise RuntimeError('NATIVE_ACTION_FRAME_RANGE_UNEXPECTED')\n  if end-start<5:result['staticTposeOrShortAction']=True;end=start+6")
 src=patch_one(src,"  result['sourceMotion']=motion_stats(witnesses(src,start,end))", 
 "  result['sourceWitness17']=witnesses(src,start,end)\n  result['sourceMotion']=motion_stats(result['sourceWitness17'])")
 src=patch_one(src,"  result['targetMotion']=motion_stats(witnesses(tgt,start,end))", 
 "  result['targetWitness17']=witnesses(tgt,start,end)\n  result['targetMotion']=motion_stats(result['targetWitness17'])")
 # Explicit shield removal by actual target skin weighting; never name-guess.
 needle="""  if not meshes:raise RuntimeError('TARGET_WEIGHTED_SKIN_MISSING')
  tgt.data.pose_position='POSE'
"""
 replacement="""  if not meshes:raise RuntimeError('TARGET_WEIGHTED_SKIN_MISSING')
  def influence_ratio(o,bone):
   groups={g.index:g.name for g in o.vertex_groups}
   total=0.;specific=0.
   for v in o.data.vertices:
    for weight in v.groups:
     total+=weight.weight
     if groups.get(weight.group)==bone:specific+=weight.weight
   return specific/max(total,1.0)
  candidates=[ob for ob in meshes if influence_ratio(ob,'mixamorig:LeftWeapon.L')>.90]
  lance=[ob for ob in meshes if influence_ratio(ob,'mixamorig:RightWeapon.R')>.90]
  if len(candidates)!=1 or len(lance)!=1 or candidates[0]==lance[0]:
   raise RuntimeError('TARGET_SHIELD_AND_LANCE_NOT_DISTINGUISHABLE_BY_SKIN_WEIGHTS '+repr({o.name:round(influence_ratio(o,'mixamorig:LeftWeapon.L'),3) for o in meshes}))
  result['shieldHiddenOnlyInCandidate']={'mesh':candidates[0].name,'leftWeaponWeightFraction':round(influence_ratio(candidates[0],'mixamorig:LeftWeapon.L'),6),
      'lanceMesh':lance[0].name,'lanceWeightFraction':round(influence_ratio(lance[0],'mixamorig:RightWeapon.R'),6)}
  bpy.data.objects.remove(candidates[0],do_unlink=True)
  meshes=[ob for ob in meshes if ob!=candidates[0]]
  tgt.data.pose_position='POSE'
"""
 # After removal Blender RNA pointer reference could throw if used; use stable name.
 replacement=replacement.replace("  bpy.data.objects.remove(candidates[0],do_unlink=True)\n  meshes=[ob for ob in meshes if ob!=candidates[0]]", "  shield_ob=candidates[0]\n  meshes=[ob for ob in meshes if ob!=shield_ob]\n  bpy.data.objects.remove(shield_ob,do_unlink=True)")
 src=patch_one(src,needle,replacement)
 src=patch_one(src,"  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped)}",
 "  result['mapping']={'boneCount':len(active),'mapped':active,'excludedCount':len(dropped),\n   'profile':'VANGUARD_21_ORG_JOINTS_TO_MIXAMO','hipsRoot':True,'hipsLocation':True}")
 # SOURCE BONE MAP after automatic builder, in case Rigify isn't recognized by ARP auto-mapper.
 orig="""  for i in reversed(range(len(mapping))):
   item=mapping[i];source_name=getattr(item,'source_bone','')
   if source_name not in expected:
    dropped.append(source_name);mapping.remove(i);continue
   item.name=source_name
   if item.name!=source_name:raise RuntimeError('ARP_MAPPING_TARGET_ASSIGNMENT_NOT_PRESERVED '+source_name)
   if hasattr(item,'set_as_root'):item.set_as_root=(source_name=='mixamorig:Hips')
   if hasattr(item,'location') and source_name=='mixamorig:Hips':item.location=True
   active.append({'source':source_name,'target':item.name})
"""
 newmap="""  for i in reversed(range(len(mapping))):
   item=mapping[i];source_name=getattr(item,'source_bone','')
   if source_name not in expected:
    dropped.append(source_name);mapping.remove(i);continue
   item.name=source_name
   if item.name!=source_name:raise RuntimeError('ARP_MAPPING_TARGET_ASSIGNMENT_NOT_PRESERVED '+source_name)
   if hasattr(item,'set_as_root'):item.set_as_root=(source_name=='mixamorig:Hips')
   if hasattr(item,'location') and source_name=='mixamorig:Hips':item.location=True
   active.append({'source':source_name,'target':item.name})
  # Auto-map is permitted to miss Rigify names. Explicit mapped ORG joints
  # remain ARP's native mapping controls; we are NOT inventing an IK solver.
  missing=sorted(expected-{x['source'] for x in active})
  for missing_source in missing:
   item=mapping.add()
   if not hasattr(item,'source_bone'):raise RuntimeError('ARP_BONE_MAP_SOURCE_PROPERTY_MISSING')
   item.source_bone=missing_source
   item.name=missing_source
   if hasattr(item,'set_as_root'):item.set_as_root=(missing_source=='mixamorig:Hips')
   if hasattr(item,'location') and missing_source=='mixamorig:Hips':item.location=True
   if item.source_bone!=missing_source or item.name!=missing_source:
    raise RuntimeError('ARP_EXPLICIT_RIGIFY_MAP_WRITE_FAILED_'+missing_source)
   active.append({'source':missing_source,'target':item.name,'addedExplicitly':True})
"""
 src=patch_one(src,orig,newmap)
 # Preserve exact target frame range and original downloaded GLB untouched.
 (packet/'blender_trial.py').write_text(src)
 compile(src,str(packet/'blender_trial.py'),'exec')
 html=(repo/OLDVIEW).read_text()
 display_clips=['SwordAttack1']+[c for c in VANGUARD_CLIPS if c!='SwordAttack1']
 opts=''.join('<option value="Vanguard_'+clip+'">Vanguard '+clip+(' (static reference)' if clip=='0T-Pose' else '')+'</option>' for clip in display_clips)
 html=patch_one(html,'<option value="Heavy1">Heavy1</option><option value="AxeKick">AxeKick</option>',opts)
 html=patch_one(html,"mode==='candidate'?'candidate'+clip:'canonical'","mode==='candidate'?'candidate':'canonical'")
 # Partial runs still load a real successfully exported clip rather than an absent default.
 html=patch_one(html,'manifest=await mr.json();',"""manifest=await mr.json();
const available=new Set(manifest.models.candidate.animations);
for(const option of el('move').options){if(!available.has(option.value))option.disabled=true}
if(!available.has(el('move').value)){const found=[...el('move').options].find(o=>!o.disabled);if(!found)throw Error('NO_REVIEWABLE_VANGUARD_CLIPS');el('move').value=found.value}
""")
 html=html.replace('Obsidianti | ARP live 3D review','Obsidianti | Vanguard sword motion experiment')
 html=html.replace('AxeKick accepted; Heavy1 hip/foot IK under review. Floor guide is visual, not a contact solver.',
   'Vanguard experimental two-handed sword motions on Obsidianti. Shield hidden; lance retained. Grip not corrected. All clips unapproved. Floor guide is visual.')
 html=html.replace('Heavy1 REVIEW | AxeKick OWNER ACCEPTED','VANGUARD EXPERIMENT | NO OWNER ACCEPTANCE')
 html=html.replace('Heavy1 hip/foot IK under review','Vanguard sword grip under review')
 (packet/'viewer.html').write_text(html)
 server=(repo/OLDSERVER).read_text().replace('ObsidiantiARPViewer/2.0.13','ObsidiantiARPViewer/Vanguard-v2.0.17')
 (packet/'server.py').write_text(server)
 return {n:digest(packet/n) for n in ('blender_trial.py','viewer.html','server.py')}

def publish(repo,stage,required_protected):
 # Use the existing proved bounded rebase/readback policy, additive-only source files.
 for attempt in range(4):
  want=g(repo,'rev-parse','HEAD')
  result=git(repo,'push','origin','HEAD:refs/heads/main',timeout=800,check=False)
  if result.returncode==0:
   remote=git(repo,'ls-remote','origin','refs/heads/main').stdout.split()
   require(remote and remote[0]==want,'PUSH_REMOTE_HEAD_READBACK_MISMATCH')
   git(repo,'fetch','--quiet','origin','main',timeout=400)
   require(g(repo,'rev-parse','refs/remotes/origin/main')==want,'REMOTE_FETCH_MISMATCH')
   for p,blob in required_protected.items():
    require(g(repo,'rev-parse','HEAD:'+p)==blob,'PROTECTED_BLOB_CHANGED_'+p)
   return want
  if attempt==3:raise RuntimeError('GIT_PUSH_BLOCKED_'+stage+'_'+result.stderr[-650:])
  git(repo,'fetch','--quiet','origin','main',timeout=450)
  for p,blob in required_protected.items():
   require(g(repo,'rev-parse','refs/remotes/origin/main:'+p)==blob,'REMOTE_PROTECTED_ASSET_ADVANCED_STOP')
  git(repo,'rebase','refs/remotes/origin/main',timeout=500)
 raise RuntimeError('PUBLICATION_EXHAUSTED')

def commit(repo,files,stage,protected):
 if any((repo/p).exists() for p in files):raise RuntimeError('VERSIONED_DESTINATION_COLLISION_'+stage)
 for p,f in files.items():copy_new(f,repo/p)
 git(repo,'add','--',*sorted(files))
 staged=set(g(repo,'diff','--cached','--name-only').splitlines())
 require(staged==set(files),'STAGED_PATH_ALLOWLIST_MISMATCH_'+stage)
 if not git(repo,'config','user.name',check=False).stdout.strip():git(repo,'config','user.name','Termux Vanguard ARP')
 if not git(repo,'config','user.email',check=False).stdout.strip():git(repo,'config','user.email','termux-vanguard-arp@users.noreply.github.com')
 git(repo,'commit','-m','Obsidianti: Vanguard Rigify sword-motion ARP '+stage)
 published=publish(repo,stage,protected)
 for path,original in files.items():
  content=git(repo,'show','refs/remotes/origin/main:'+path).stdout
  if path.endswith(('.glb','.blend')):
   require('oid sha256:'+digest(original) in content,'PUBLISHED_BINARY_LFS_POINTER_WRONG_'+path)
  else:require(content==original.read_text(),'PUBLISHED_TEXT_READBACK_WRONG_'+path)
 return published

def retarget(pd,root,private,source,target,clip):
 folder=root/'trials'/clip
 folder.parent.mkdir(exist_ok=True)
 args=pd+['login','obs-arp-blender50',
  '--bind',str(private.resolve())+':/mnt/arp-private',
  '--bind',str(root.resolve())+':/mnt/arp-work',
  '--bind',str(source.parent.resolve())+':/mnt/arp-source',
  '--bind',str(target.parent.resolve())+':/mnt/arp-target','--',
  'blender','--background','--factory-startup','--enable-autoexec','--python',
  '/mnt/arp-work/blender_trial.py','--',
  '--private','/mnt/arp-private','--source','/mnt/arp-source/'+source.name,
  '--source-sha',VANGUARD,'--target','/mnt/arp-target/'+target.name,
  '--target-sha',CANON,'--clip',clip,'--output','/mnt/arp-work/trials/'+clip]
 p=command(args,timeout=3600,check=False)
 (folder.parent/(clip+'_BLENDER.log')).write_text(p.stdout+'\n'+p.stderr)
 rec=folder/'TRIAL.json';r=json.loads(rec.read_text()) if rec.is_file() else {}
 blend=folder/('ARP_'+clip+'_UNAPPROVED.blend')
 require(p.returncode==0 and r.get('stage')=='SAVED_BLEND' and blend.is_file() and r.get('blendSHA256')==digest(blend),
  'VANGUARD_ARP_RETARGET_FAILED_'+clip+'_rc='+str(p.returncode)+' stage='+str(r.get('stage'))+' '+str(r.get('error',p.stderr[-200:]))[:310])
 require(r.get('targetAction')==clip+'_remap','VANGUARD_ARP_TARGET_ACTION_UNEXPECTED_'+clip)
 require('shieldHiddenOnlyInCandidate' in r,'SHIELD_REMOVAL_NOT_CONFIRMED_'+clip)
 require(int(r.get('mapping',{}).get('boneCount',0))>=18,'VANGUARD_LESS_THAN_18_BONE_MAP_'+clip)
 return blend,r

def export(pd,root,blend,clip):
 out=root/'exports';out.mkdir(exist_ok=True)
 glb=out/('Vanguard_'+clip+'.glb');receipt=out/('Vanguard_'+clip+'.json')
 args=pd+['login','obs-arp-blender50',
  '--bind',str(blend.parent.resolve())+':/mnt/arp-source',
  '--bind',str(root.resolve())+':/mnt/arp-work','--',
  'blender','--background','--factory-startup','--disable-autoexec',
  '--python','/mnt/arp-work/export.py','--',
  '--source','/mnt/arp-source/'+blend.name,'--sha',digest(blend),
  '--action',clip+'_remap','--output','/mnt/arp-work/exports/'+glb.name,
  '--receipt','/mnt/arp-work/exports/'+receipt.name]
 p=command(args,timeout=2000,check=False)
 (out/('Vanguard_'+clip+'_EXPORT.log')).write_text(p.stdout+'\n'+p.stderr)
 r=json.loads(receipt.read_text()) if receipt.is_file() else {}
 require(p.returncode==0 and r.get('status')=='BLENDER5_SAVED_ARP_ACTION_EXPORTED_GLB' and glb.is_file() and digest(glb)==r.get('glbSHA256'),
  'VANGUARD_EXPORT_FAILED_'+clip+'_rc='+str(p.returncode)+'_'+str(r.get('error',p.stderr[-200:]))[:300])
 return glb,r

def main(packet,launcher,expected):
 packet=pathlib.Path(packet).resolve();launcher=pathlib.Path(launcher).resolve()
 require(launcher.is_file() and digest(launcher)==expected,'LAUNCHER_SHA_MISMATCH')
 manifest=json.loads((packet/'manifest.json').read_text())
 wanted={'driver.py','merge.py','source_audit.py','contract.json','test_driver.py'}
 require(set(manifest)==wanted and all(digest(packet/n)==s for n,s in manifest.items()),'PAYLOAD_MANIFEST_SHA_MISMATCH')
 contract=json.loads((packet/'contract.json').read_text())
 require(contract['schema']==V and contract['authority']=='TERMUX_GIT_ONLY' and contract['vanguardSHA256']==VANGUARD
  and sorted(contract['sourceMutablePaths'])==sorted(SOURCES),'CONTRACT_SCOPE_INVALID')
 for n in ('driver.py','merge.py','source_audit.py','test_driver.py'):
  command(['python3','-m','py_compile',str(packet/n)])
 command(['python3',str(packet/'test_driver.py'),str(packet/'merge.py')],timeout=180)
 downloads=pathlib.Path.home()/'storage/downloads';require(downloads.is_dir(),'ANDROID_DOWNLOADS_MOUNT_MISSING')
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 root=pathlib.Path.home()/'.local/state'/V/runid;root.mkdir(parents=True,exist_ok=False)
 receipt=root/'RECEIPT.json'
 state={'schema':V,'runId':runid,'status':'BOOT','stage':'BOOT','authority':'TERMUX_GIT_ONLY',
  'launcherSHA256':expected,'rulesBlob':AGENTS,'pinnedGitBase':BASE,'canonicalSHA256':CANON,
  'canonicalModified':False,'axeKickModified':False,'userVisualAcceptance':'PENDING',
  'vendorSourcePublished':False,'sourceGlbPublished':False,
  'etiquetteRead':'CHATGPT_LIVE_2026-11-06', 'mission':'Vanguard Rigify ORG source to Obsidianti via purchased ARP, experimental sword-to-lance; shield removed candidate only; no cleanup',
  'expectedActions':VANGUARD_CLIPS}
 def mark(stage):state['stage']=stage;write_json(receipt,state);print('STAGE='+stage,flush=True)
 mark('BOOT')
 try:
  source=source_vanguard(downloads);private=vendor(downloads)
  audit=import_path(packet/'source_audit.py','vanguard_source_verifier')
  verified=audit.inspect(source)
  write_json(root/'SOURCE_AUDIT.json',verified)
  state['vanguardSourcePath']=str(source);state['vanguardSHA256']=digest(source)
  print('VANGUARD_SOURCE_VERIFIED='+VANGUARD+' ACTIONS='+str(len(VANGUARD_CLIPS)),flush=True)
  mark('VANGUARD_ORIGINAL_SOURCE_AUDITED')
  repo,head,ancestry=checkout(root);state['inputHead']=head;state['gitAncestryProof']=ancestry
  protected={p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED};state['protectedBefore']=protected
  require(g(repo,'rev-parse','HEAD:AGENTS.md')==AGENTS,'RULES_READ_BLOCKED')
  mark('PINNED_REPO_AND_RULES_VERIFIED')
  for ref in (OLDTRIAL,OLDEXPORT,OLDVIEW,OLDSERVER,OLDHELPER):require((repo/ref).is_file(),'REQUIRED_VERIFIED_BASELINE_MISSING_'+ref)
  derived=create_sources(repo,packet);state['derivedSourceSHA256']=derived
  for n in ('blender_trial.py','viewer.html','server.py'):require((packet/n).is_file(),'DERIVED_SOURCE_NOT_CREATED_'+n)
  # Static derived source code is committed through Termux Git before execution.
  source_files={k:(launcher if v=='LAUNCHER' else packet/v) for k,v in SOURCES.items()}
  source_commit=commit(repo,source_files,'SOURCE',protected)
  state['sourceCommit']=source_commit;mark('SOURCE_PUBLISHED_REMOTE_READBACK')
  old=import_path(repo/OLDHELPER,'verified_v213_blender_runtime')
  pd=old.private_pd();state['blenderRuntime']=old.ensure_container(pd)
  hydrate(repo,{TARGET:CANON})
  require(digest(repo/TARGET)==CANON,'TARGET_CANONICAL_LFS_NOT_HYDRATED')
  for name,f in (('blender_trial.py',packet/'blender_trial.py'),('export.py',repo/OLDEXPORT)):
   copy_new(f,root/name)
  mark('PURCHASED_ARP_AND_CANONICAL_TARGET_VERIFIED')
  trials={};outputs={};errors={}
  for clip in VANGUARD_CLIPS:
   state['currentAction']=clip;mark('RETARGET_VANGUARD_'+clip)
   key='Vanguard_'+clip
   try:
    blend,r=retarget(pd,root,private,source,repo/TARGET,clip)
    if clip!='0T-Pose':
     require(verified['actionEvidence'][clip]['movingMappedBoneCount']>0,
      'VANGUARD_SOURCE_AUDIT_MOTION_MISSING_'+clip)
     # Do not reject legitimate subtle Idle/Midair motions at an arbitrary 5-degree threshold.
     rows=r.get('targetWitness17',[])
     turn=max((max(z.get('rotationDeltaDeg',{}).values(),default=0.) for z in rows),default=0.)
     hip0=(rows[0]['jointWorld']['Hips'] if rows else [0,0,0])
     travel=max((sum((a-b)**2 for a,b in zip(z['jointWorld']['Hips'],hip0))**.5 for z in rows),default=0.)
     require(turn>0.2 or travel>0.003,'VANGUARD_ARP_TARGET_ANIMATION_STATIC_'+clip+'_ANGLE='+str(turn)+'_HIP='+str(round(travel,4)))
    glb,exp=export(pd,root,blend,clip)
    # Confirm the actual GLB contains one clip, armature, target mesh and no shield.
    evidence=audit.verify_target_candidate(glb)
    trials[key]={'status':'EXPORTED','sourceMotion':r.get('sourceMotion'),
     'targetMotion':r.get('targetMotion'),'sourceWitness17':r.get('sourceWitness17'),
     'targetWitness17':r.get('targetWitness17'),'targetAction':r.get('targetAction'),
     'mapping':r.get('mapping'),'sourceSlot':r.get('sourceSlot'),
     'sourceRigify':r.get('vanguardRigify'),
     'shieldRemoved':r.get('shieldHiddenOnlyInCandidate'),
     'exportedGLBSHA256':exp['glbSHA256'],'targetGeometryAudit':evidence}
    outputs[key]=glb
    print('VANGUARD_ACTION_EXPORTED='+key+' GLB_SHA256='+digest(glb),flush=True)
   except BaseException as e:
    errors[key]=str(e)[:900];trials[key]={'status':'FAILED','error':errors[key]}
    print('VANGUARD_ACTION_FAILED='+key+' '+errors[key],flush=True)
   state['completedActions']={k:v['status'] for k,v in trials.items()};mark('ACTION_CHECKPOINT_'+clip)
  state['succeededActionCount']=len(outputs);state['actionErrors']=errors
  if not outputs:raise RuntimeError('NO_VANGUARD_ACTION_EXPORTED; inspect preserved individual BLENDER logs; no placeholder GLB')
  merged_inputs=[{'name':key,'path':str(outputs[key])} for key in ['Vanguard_'+c for c in VANGUARD_CLIPS] if key in outputs]
  merge=import_path(packet/'merge.py','vanguard_verified_animation_merger')
  combined=root/(V+'_'+runid+'_REVIEW_LIBRARY.glb');keys=root/'KEYS.json'
  merge_result=merge.merge(merged_inputs,combined,keys)
  require(merge_result['merged']['clips']==len(merged_inputs),'MERGE_WRONG_ANIMATION_COUNT')
  geometry=audit.verify_target_candidate(combined)
  state['geometryAudit']=geometry
  output_download=downloads/combined.name
  copy_new(combined,output_download)
  require(digest(output_download)==merge_result['merged']['sha256'],'DOWNLOADS_COMBINED_GLB_CHANGED')
  state['combinedGLB']=str(output_download);state['combinedSHA256']=digest(output_download)
  mark('VANGUARD_REVIEW_GLB_VERIFIED_AND_COPIED_DOWNLOADS')
  diagnostics={'schema':V,'inputVanguardSHA256':VANGUARD,
   'rigifyMapping':'21 ORG bones renamed to Mixamo names within disposable imported source',
   'shield':'Deleted in candidate Blender scenes by LeftWeapon.L skin weights; canonical unchanged',
   'lance':'Retained original target RightWeapon.R mesh; NO grip alignment',
   'actions':trials,'failures':errors}
  write_json(root/'TRAJECTORIES.json',diagnostics)
  for fn in ('KEYS.json','TRAJECTORIES.json','SOURCE_AUDIT.json'):
   dest=downloads/(V+'_'+runid+'_'+fn)
   copy_new(root/fn,dest);require(digest(dest)==digest(root/fn),'DOWNLOAD_DIAGNOSTIC_HASH_CHANGED_'+fn)
   print('DOWNLOAD_DIAGNOSTIC='+str(dest)+' SHA256='+digest(dest),flush=True)
  token=hashlib.sha256((runid+source_commit+expected+digest(output_download)).encode()).hexdigest()[:24]
  viewer={'schema':V,'runId':runid,'buildToken':token,'launcherSHA256':expected,
   'sourceCommit':source_commit,'htmlPath':str(repo/('campaigns/'+V+'_viewer.html')),
   'models':{'candidate':{'sha256':digest(output_download),'bytes':output_download.stat().st_size,
     'url':'/models/candidate.glb','animations':merge_result['merged']['names']}},
   'modelPaths':{'candidate':str(output_download)},'canonicalModelSHA256':CANON,
   'mode':'VANGUARD_21_ORG_RIGIFY_JOINTS_PURCHASED_ARP_LANCE_SHIELD_HIDDEN'}
  old.V=V;ticket=old.start_server(root,repo,viewer)
  state['viewerURL']=ticket['url'];state['serverPID']=ticket['pid'];state['serverPort']=ticket['port']
  mark('VERIFIED_HTTP_VIEWER')
  print('VIEWER_URL='+ticket['url'],flush=True)
  print('BROWSER_OPEN_INTENT_SENT='+str(old.open_browser(ticket['url'])).upper(),flush=True)
  evidence={'schema':V,'runId':runid,'sourceCommit':source_commit,'baseGitHead':head,
   'authority':'TERMUX_GIT_ONLY','rulesBlob':AGENTS,'inputVanguardSHA256':VANGUARD,
   'purchasedARPZipSha256':ARPZIP,'canonicalModelSHA256':CANON,
   'canonicalModified':False,'axeKickModified':False,'acceptedPriorAnimationsModified':False,
   'sourceGLBPublished':False,'vendorSourcePublished':False,
   'shieldHiddenOnlyInCandidate':True,'lanceRetained':True,'gripAdjusted':False,
   'sourceAnimations':len(VANGUARD_CLIPS),'exportedAnimations':len(outputs),
   'errors':errors,'resultSHA256':digest(output_download),'resultBytes':output_download.stat().st_size,
   'resultPath':str(output_download),'viewerURL':ticket['url'],'viewerHTTPVerified':True,
   'ownerVisualAcceptance':'PENDING','protectedBefore':protected,
   'protectedAfter':{p:g(repo,'rev-parse','HEAD:'+p) for p in LOCKED},
   'sourceAudit':verified,'targetGeometryAudit':geometry,'gitAncestryProof':ancestry}
  require(evidence['protectedAfter']==protected,'PROTECTED_MODEL_OR_AXEKICK_BLOB_CHANGED')
  write_json(root/'EVIDENCE.json',evidence)
  report=root/'REPORT.md'
  report.write_text('# Vanguard 2H Sword → Obsidianti Lance | purchased ARP v2.0.17\n\n'
   +'**Status:** '+('ALL_REAL_VANGUARD_CLIPS_EXPORTED' if not errors else 'PARTIAL_UNAPPROVED_EXPERIMENT')+'; canonical Obsidianti/AxeKick unchanged.\n\n'
   +'## Experiment\n\nOriginal 437-joint Rigify-style Vanguard.glb; 21 mapped ORG deformation/control bones renamed on an isolated imported copy; ARP native remap with source/target scaling and translating Hips; no custom kinematic fixes, no forced weapon grip. '
   +'The shield mesh was identified by LeftWeapon.L weights and removed from the candidate **only**; lance RightWeapon.R retained.\n\n'
   +'## Output\n\n'+output_download.name+'\n\nSHA256 `'+digest(output_download)+'`\n\nViewer: '+ticket['url']+'\n\n'
   +'19 source actions including one static 0T-Pose reference. Animations exported: '+str(len(outputs))+'.\n\n'
   +'## Per-action results\n\n'+''.join('- '+key+': '+trials[key]['status']+'\n' for key in trials)
   +'\n## Human acceptance\n\nUnapproved. Two-handed sword motion on lance may require independent hand and weapon grip edits. Source character, original target, and existing animation library have not been modified.\n')
  dest=REL+runid+'/'
  files={dest+'REPORT.md':report,dest+'KEYS.json':keys,dest+'TRAJECTORIES.json':root/'TRAJECTORIES.json',
   dest+'SOURCE_AUDIT.json':root/'SOURCE_AUDIT.json',dest+'EVIDENCE.json':root/'EVIDENCE.json',
   dest+'OBSIDIANTI_VANGUARD_ARP_EXPERIMENT_UNAPPROVED.glb':output_download}
  require('lfs' in git(repo,'check-attr','filter','--',dest+'OBSIDIANTI_VANGUARD_ARP_EXPERIMENT_UNAPPROVED.glb').stdout,
   'CANDIDATE_GLB_NOT_GIT_LFS_TRACKED')
  evidence_commit=commit(repo,files,'EVIDENCE',protected)
  state['evidenceCommit']=evidence_commit
  state['status']='VANGUARD_ARP_REVIEW_READY_UNAPPROVED' if not errors else 'VANGUARD_ARP_PARTIAL_REVIEW_ERRORS_RECORDED'
  mark('REMOTE_EVIDENCE_PUBLISHED')
  print('VANGUARD_REVIEW_GLB='+str(output_download),flush=True)
  print('VANGUARD_REVIEW_SHA256='+digest(output_download),flush=True)
  print('EVIDENCE_URL=https://github.com/Valar05/parametric-parambulator/blob/'+evidence_commit+'/'+dest+'REPORT.md',flush=True)
  print('CANONICAL_AND_AXEKICK_UNCHANGED=YES',flush=True)
  print('STATUS='+state['status'],flush=True)
 except BaseException as e:
  state['status']='BLOCKED';state['errorType']=type(e).__name__;state['error']=str(e)[:1300]
  state['traceback']=traceback.format_exc()[-2900:];write_json(receipt,state)
  print('STATUS=BLOCKED '+state['error'],flush=True)
  raise
 finally:
  write_json(receipt,state)
  print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':
 if len(sys.argv)!=4:raise SystemExit('usage driver.py PACKET LAUNCHER SHA256')
 main(sys.argv[1],sys.argv[2],sys.argv[3])
