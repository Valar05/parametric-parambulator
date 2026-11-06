#!/usr/bin/env python3
"""Termux-Git authority: comparison of original Ares / Lionheart Blender rigs, read-only assets."""
import os,sys,json,pathlib,hashlib,subprocess,shutil,tempfile,datetime,zipfile,traceback
V='OBSIDIANTI_SOURCE_RIG_FORENSICS_v1.0.0'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
REPO='https://github.com/Valar05/parametric-parambulator.git'
SHA={'Ares.blend':'63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a','LionheartLancer (2).blend':'81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'}
SOURCE={'campaigns/OBSIDIANTI_SOURCE_RIG_FORENSICS_v1.0.0_RUN.py':'driver.py','campaigns/OBSIDIANTI_SOURCE_RIG_FORENSICS_v1.0.0_ANALYZE.py':'analyze.py','docs/obsidianti/SOURCE_RIG_FORENSICS_v1.0.0.md':'readme.md'}
OUT='diagnostics/obsidianti/source-rig-forensics-v1.0.0'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def cmd(*a,timeout=300,check=True,env=None):
 p=subprocess.run([str(x) for x in a],capture_output=True,text=True,timeout=timeout,env=env)
 if p.returncode and check:raise RuntimeError('COMMAND_FAILED '+repr(a[:5])+'\n'+p.stdout[-1000:]+'\n'+p.stderr[-1500:])
 return p
def git(repo,*a,**kw):return cmd('git','-C',repo,*a,**kw)
def find_source(filename,expected):
 home=pathlib.Path.home()
 roots=[home/'storage/downloads',home/'storage/documents',home/'storage/shared',home/'storage/shared/Documents',home/'storage/shared/Download']
 seen=set()
 for root in roots:
  if not root.is_dir():continue
  tests=[root/filename,*root.glob('*/'+filename),*root.glob('*/*/'+filename)]
  for p in tests:
   try:
    if p in seen or not p.is_file() or p.stat().st_size>100000000:continue
    seen.add(p)
    if sha(p)==expected:return p
   except (OSError,PermissionError):continue
 return None
def main(folder,launcher_sha):
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 home=pathlib.Path.home();downloads=home/'storage/downloads';state=home/'.local/state'/V;state.mkdir(parents=True,exist_ok=True)
 receipt=state/(stamp+'_RECEIPT.json');work=pathlib.Path(tempfile.mkdtemp(prefix='obs_rig_forensics_'));repo=work/'repo'
 note={'campaign':V,'status':'STARTED','authority':'TERMUX_GIT_ONLY','authorRules':'AGENTS.md Git blob '+AGENTS_BLOB+'; Campaign Etiquette live read 2026-11-06','sourceSHA256':SHA,'launcherSHA256':launcher_sha,'canonicalGLBUnchanged':True,'originalBlendUnchanged':True,'humanVisualApproval':False,'run':stamp}
 def save():receipt.write_text(json.dumps(note,indent=2,sort_keys=True)+'\n')
 save()
 try:
  sources={name:find_source(name,h) for name,h in SHA.items()}
  for name,p in sources.items():print('SOURCE_'+name.split('.')[0].replace(' ','_').upper()+'='+str(p) if p else 'SOURCE_MISSING='+name+' EXPECTED_SHA256='+SHA[name],flush=True)
  if not all(sources.values()):raise RuntimeError('ORIGINAL_BLEND_NOT_FOUND_IN_PHONE_STORAGE; download original attachments to Android Downloads (or Documents) and rerun exactly the same launcher')
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1'
  cmd('git','clone','-q','--no-checkout',REPO,repo,timeout=600,env=env)
  git(repo,'checkout','-q','main',env=env)
  head=git(repo,'rev-parse','HEAD').stdout.strip();agentblob=git(repo,'rev-parse','HEAD:AGENTS.md').stdout.strip()
  if agentblob!=AGENTS_BLOB:raise RuntimeError('AGENTS_CHANGED '+agentblob)
  note.update(startingHEAD=head,gitAgentsBlob=agentblob);save();print('HEAD='+head+'\nBRANCH=main',flush=True)
  expected=[*SOURCE,OUT+'/ARES.json',OUT+'/LIONHEART.json',OUT+'/COMPARISON.json',OUT+'/FINDINGS.md']
  for rel in expected:
   if git(repo,'ls-tree','-r','--name-only','HEAD','--',rel).stdout.strip() or (repo/rel).exists():raise RuntimeError('DESTINATION_COLLISION '+rel)
  for dest,src in SOURCE.items():
   p=repo/dest;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(folder/src,p)
   if sha(p)!=sha(folder/src):raise RuntimeError('SOURCE_STAGING_HASH_MISMATCH '+dest)
  import py_compile
  for rel in SOURCE:
   if rel.endswith('.py'):py_compile.compile(str(repo/rel),doraise=True)
  git(repo,'add','--',*SOURCE);git(repo,'commit','-m','Obsidianti: original Ares and Lionheart rig forensic analysis source v1.0.0')
  commit=git(repo,'rev-parse','HEAD').stdout.strip();git(repo,'push','origin','HEAD:main',timeout=450)
  if git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]!=commit:raise RuntimeError('SOURCE_REMOTE_READBACK_MISMATCH')
  for rel,src in SOURCE.items():
   if git(repo,'show','HEAD:'+rel).stdout!=(folder/src).read_text():raise RuntimeError('SOURCE_READBACK_CONTENT_MISMATCH '+rel)
  note['sourcePublishedCommit']=commit;save();print('SOURCE_REMOTE_READBACK_VERIFIED=YES '+commit,flush=True)
  for name,path in sources.items():
   label='ARES' if name.startswith('Ares') else 'LIONHEART';out=work/(label+'.json')
   blender=shutil.which('blender');proot=shutil.which('proot-distro')
   if blender:
    argv=[blender,'--background','--disable-autoexec','--python',repo/'campaigns/OBSIDIANTI_SOURCE_RIG_FORENSICS_v1.0.0_ANALYZE.py','--',path,out]
   elif proot:
    argv=[proot,'login','debian','--bind',str(repo)+':/mnt/obs-repo','--bind',str(work)+':/mnt/obs-work','--bind',str(path.parent)+':/mnt/obs-source','--','blender','--background','--disable-autoexec','--python','/mnt/obs-repo/campaigns/OBSIDIANTI_SOURCE_RIG_FORENSICS_v1.0.0_ANALYZE.py','--','/mnt/obs-source/'+path.name,'/mnt/obs-work/'+out.name]
   else:raise RuntimeError('BLENDER_OR_PROOT_RUNTIME_NOT_INSTALLED')
   p=cmd(*argv,check=False,timeout=1600)
   (work/(label+'.log')).write_text(p.stdout+'\n'+p.stderr)
   if p.returncode:raise RuntimeError(label+'_BLENDER_ANALYSIS_FAILED '+p.stderr[-900:])
   data=json.loads(out.read_text())
   if data['status']!='ANALYSIS_COMPLETE':raise RuntimeError(label+'_ANALYSIS_NOT_COMPLETE '+str(data.get('error')))
   print(label+'_ANALYSIS_COMPLETE=YES RIGS='+str(len(data['rigs']))+' ACTIONS='+str(len(data['actions'])),flush=True)
  ar=json.loads((work/'ARES.json').read_text());li=json.loads((work/'LIONHEART.json').read_text())
  def synopsis(d):
   return {'rigs':[{k:x[k] for k in ('name','boneCount','constraintCounts','IKControlCandidates')} for x in d['rigs']], 'actions':[{'rig':x['rig'],'action':x['action'],'stats':x.get('stats'),'activeConstraintsCount':x.get('activeConstraintsCount'),'activeIKConstraintsCount':x.get('activeIKConstraintsCount')} for x in d['actions']],'warnings':d['warnings']}
  combined={'schema':'obsidianti-source-rig-forensics-v1.0.0','originalSources':SHA,'authorRulesRead':'AGENTS.md and Campaign Etiquette','ares':synopsis(ar),'lionheart':synopsis(li),'status':'EVIDENCE_COLLECTED_NOT_CAUSAL_PROOF'}
  (work/'COMPARISON.json').write_text(json.dumps(combined,indent=2,sort_keys=True)+'\n')
  lines=['# Ares vs Lionheart source rig forensics','','This is source evidence, not proof of the original Obsidianti import divergence. No animation or rig was modified.','','Ares original SHA: `'+SHA['Ares.blend']+'`','Lionheart original SHA: `'+SHA['LionheartLancer (2).blend']+'`','']
  for label,data in [('Ares',ar),('Lionheart',li)]:
   lines.append('## '+label)
   for rig in data['rigs']:lines.append('- Rig `'+rig['name']+'`: '+str(rig['boneCount'])+' bones, constraints '+str(rig['constraintCounts']))
   for act in data['actions']:
    lines.append('- Action `'+act['action']+'` active IK constraints '+str(act.get('activeIKConstraintsCount'))+'; max constraint-on/off foot differences '+str({k:v['maxConstraintPositionDelta_m'] for k,v in act.get('stats',{}).items()}))
   for w in data.get('warnings',[]):lines.append('- WARNING: '+str(w))
  lines+=['','## Interpretation gate','If turning off IK changes evaluated foot transforms in source, an FK-only import must bake *evaluated* source motion rather than copying raw deform keys. If source on/off match, investigate rest matrices, pelvis scale and retarget interpolation. The original import stage still requires a separate source/target trajectory comparison.']
  (work/'FINDINGS.md').write_text('\n'.join(lines)+'\n')
  for name in ('ARES.json','LIONHEART.json','COMPARISON.json','FINDINGS.md'):
   rel=OUT+'/'+name;p=repo/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(work/name,p)
  git(repo,'add','--',OUT);git(repo,'commit','-m','Obsidianti: original rig FK/IK evidence v1.0.0')
  ev=git(repo,'rev-parse','HEAD').stdout.strip();git(repo,'push','origin','HEAD:main',timeout=450)
  if git(repo,'ls-remote','origin','refs/heads/main').stdout.split()[0]!=ev:raise RuntimeError('EVIDENCE_REMOTE_READBACK_MISMATCH')
  if git(repo,'show','HEAD:'+OUT+'/COMPARISON.json').stdout!=(work/'COMPARISON.json').read_text():raise RuntimeError('EVIDENCE_BYTES_REMOTE_MISMATCH')
  for name in ('ARES.json','LIONHEART.json','COMPARISON.json','FINDINGS.md'):
   dest=downloads/(V+'_'+stamp+'_'+name);shutil.copyfile(work/name,dest)
   if sha(dest)!=sha(work/name):raise RuntimeError('DOWNLOADS_HASH_MISMATCH '+name)
   print('DOWNLOADS_'+name+'='+str(dest)+' SHA256='+sha(dest),flush=True)
  handoff=downloads/(V+'_'+stamp+'_HANDOFF.zip')
  with zipfile.ZipFile(handoff,'w',zipfile.ZIP_DEFLATED) as z:
   for name in ('ARES.json','LIONHEART.json','COMPARISON.json','FINDINGS.md','ARES.log','LIONHEART.log'):z.write(work/name,arcname=name)
  note.update(status='SOURCE_FORENSICS_DELIVERED',evidenceCommit=ev,evidenceRemoteReadback=True,handoff=str(handoff),handoffSHA256=sha(handoff));save()
  print('REMOTE_READBACK_VERIFIED=YES EVIDENCE_COMMIT='+ev+'\nSTATUS=SOURCE_FORENSICS_DELIVERED\nHANDOFF='+str(handoff)+'\nHANDOFF_SHA256='+sha(handoff),flush=True)
 except Exception as e:
  note.update(status='BLOCKED',error=str(e),traceback=traceback.format_exc()[-2200:]);save()
  print('STATUS=BLOCKED: '+str(e),flush=True)
  raise
 finally:print('RECEIPT='+str(receipt),flush=True)
if __name__=='__main__':main(pathlib.Path(sys.argv[1]),sys.argv[2])
