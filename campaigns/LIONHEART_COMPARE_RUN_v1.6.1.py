#!/usr/bin/env python3
"""Termux-only Git-authoritative source model exporter and side-by-side viewer."""
from __future__ import annotations
import datetime, hashlib, json, os, pathlib, shutil, socket, subprocess, sys, time, uuid, urllib.request, struct
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler

VER='LIONHEART_SIDE_BY_SIDE_v1.6.1'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
BLEND='assets/obsidianti/source/LionheartLancer.blend'
MODEL='assets/obsidianti/Obsidianti.glb'
BLEND_SHA='81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
AGENTS_SHA='547c2af52303f4efb718bbf8f82a698110c7bfca'
FILES={'campaigns/LIONHEART_COMPARE_EXPORT_v1.6.1.py':'export.py','campaigns/LIONHEART_COMPARE_RUN_v1.6.1.py':'driver.py','review/lionheart-obsidianti-compare-v1.6.1.html':'viewer.html','campaigns/LIONHEART_SIDE_BY_SIDE_v1.6.1_LAUNCH.sh':'launcher.sh'}

class Stop(Exception): pass

def hashfile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
def cmd(a,timeout=300,env=None,check=True,cwd=None):
 p=subprocess.run([str(x) for x in a],capture_output=True,text=True,timeout=timeout,env=env,cwd=cwd)
 if check and p.returncode:raise Stop('COMMAND_FAILED rc='+str(p.returncode)+' '+repr(a[:5])+' '+p.stderr[-1100:]+' '+p.stdout[-600:])
 return p

def glb(path):
 data=path.read_bytes()
 if len(data)<32 or data[:4]!=b'glTF' or struct.unpack_from('<I',data,8)[0]!=len(data):raise Stop('INVALID_GLB '+str(path))
 n=struct.unpack_from('<I',data,12)[0]
 if data[16:20]!=b'JSON':raise Stop('GLB_JSON_CHUNK_MISSING')
 j=json.loads(data[20:20+n]);return {'animations':[a.get('name','unnamed') for a in j.get('animations',[])], 'meshes':len(j.get('meshes',[])), 'skins':len(j.get('skins',[])), 'nodes':len(j.get('nodes',[]))}

def blender_command(repo,work):
 script=repo/'campaigns/LIONHEART_COMPARE_EXPORT_v1.6.1.py'
 src=repo/BLEND
 if shutil.which('blender'):
  return ['blender','--background','--disable-autoexec','--python',script,'--',src,work,BLEND_SHA]
 if not shutil.which('proot-distro'):raise Stop('BLENDER_NOT_AVAILABLE_NATIVE_OR_PROOT_DEBIAN')
 return ['proot-distro','login','debian','--bind',str(repo)+':/mnt/lion-repo','--bind',str(work)+':/mnt/lion-work','--',
         'blender','--background','--disable-autoexec','--python','/mnt/lion-repo/campaigns/LIONHEART_COMPARE_EXPORT_v1.6.1.py',
         '--','/mnt/lion-repo/'+BLEND,'/mnt/lion-work',BLEND_SHA]

def serve(root,port):
 os.chdir(root)
 class Handler(SimpleHTTPRequestHandler):
  def end_headers(self):
   self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
   self.send_header('Pragma','no-cache')
   super().end_headers()
  def log_message(self,fmt,*args):pass
 ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

def main():
 if len(sys.argv)>=4 and sys.argv[1]=='--serve':serve(sys.argv[2],int(sys.argv[3]));return 0
 if len(sys.argv)!=3:raise Stop('usage: driver.py <payload_directory> <launcher_sha256>')
 payload=pathlib.Path(sys.argv[1]).resolve(); launcher_sha=sys.argv[2]
 if not os.environ.get('PREFIX','').startswith('/data/data/com.termux/'):raise Stop('TERMUX_REQUIRED')
 downloads=pathlib.Path.home()/'storage/downloads';downloads.mkdir(parents=True,exist_ok=True)
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:7]
 state=pathlib.Path.home()/'.local/state'/VER/runid;state.mkdir(parents=True,exist_ok=False)
 receipt=downloads/(VER+'_'+runid+'_RECEIPT.json')
 report={'campaign':VER,'run':runid,'authority':'TERMUX_GIT_ONLY','status':'RUNNING','stage':'START','launcherSha256':launcher_sha,
  'expectedBlendSha256':BLEND_SHA,'expectedCanonicalModelSha256':MODEL_SHA,'expectedAgentsBlob':AGENTS_SHA,'sourcePublished':False,
  'canonicalModelChanged':False,'viewerStarted':False,'visualOwnerApproved':False}
 def store():
  receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
  print('STAGE='+report['stage']+' STATUS='+report['status'],flush=True)
 store()
 try:
  env=os.environ.copy();env['GIT_LFS_SKIP_SMUDGE']='1';env['GIT_TERMINAL_PROMPT']='0';env['PYTHONDONTWRITEBYTECODE']='1'
  report['stage']='FETCH_ISOLATED_CHECKOUT';store()
  repo=state/'repo'
  # A fresh read-only clone protects the operator's active checkout and any dirty tree.
  cmd(['git','clone','--depth=1','--single-branch','--branch','main',REMOTE,repo],timeout=420,env=env)
  before=cmd(['git','-C',repo,'rev-parse','HEAD']).stdout.strip();report['inputGitHead']=before
  if cmd(['git','-C',repo,'hash-object','AGENTS.md']).stdout.strip()!=AGENTS_SHA:raise Stop('AGENTS_BLOB_CHANGED_FRESH_READ_REQUIRED')
  if cmd(['git','-C',repo,'status','--porcelain']).stdout.strip():raise Stop('ISOLATED_CHECKOUT_NOT_CLEAN')
  for dst,src in FILES.items():
   pp=repo/dst
   if pp.exists() or cmd(['git','-C',repo,'ls-tree','HEAD','--',dst]).stdout.strip():
    raise Stop('DESTINATION_COLLISION '+dst+' USE_NEW_VERSION')
   if not (payload/src).is_file():raise Stop('BUNDLE_FILE_MISSING '+src)
  report['stage']='PUBLISH_SOURCE_FILES_TERMUX_GIT';store()
  for dst,src in FILES.items():
   dest=repo/dst;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(payload/src,dest)
  cmd(['git','-C',repo,'add','--',*FILES.keys()])
  cmd(['git','-C',repo,'diff','--cached','--check'])
  cmd(['git','-C',repo,'-c','user.name=Termux Campaign','-c','user.email=termux-campaign@users.noreply.github.com','commit','-m','Add Lionheart vs Obsidianti synchronized original-mesh viewer'])
  published=cmd(['git','-C',repo,'rev-parse','HEAD']).stdout.strip()
  remotehead=cmd(['git','ls-remote',REMOTE,'refs/heads/main'],timeout=80,env=env).stdout.split()[0]
  if remotehead!=before:raise Stop('PUSH_REFUSED_REMOTE_ADVANCED; source committed only in isolated checkout')
  cmd(['git','-C',repo,'push','origin','HEAD:refs/heads/main'],timeout=240,env=env)
  readback=cmd(['git','ls-remote',REMOTE,'refs/heads/main'],timeout=80,env=env).stdout.split()[0]
  if readback!=published:raise Stop('REMOTE_COMMIT_READBACK_MISMATCH')
  report['sourcePublished']=True;report['sourceCommit']=published;report['sourceCommitReadback']=readback
  print('SOURCE_COMMIT_READBACK='+readback,flush=True)
  report['stage']='FETCH_PINNED_SOURCE_BLENDER_AND_OBSIDIANTI_GLB';store()
  if cmd(['git','lfs','version'],check=False).returncode:raise Stop('GIT_LFS_MISSING')
  cmd(['git','-C',repo,'lfs','pull','--include='+BLEND+','+MODEL,'--exclude='],timeout=1500,env={**env,'GIT_LFS_SKIP_SMUDGE':'0'})
  for path,expected in [(BLEND,BLEND_SHA),(MODEL,MODEL_SHA)]:
   digest=hashfile(repo/path)
   if digest!=expected:raise Stop('EXACT_SOURCE_BYTES_MISMATCH '+path+' expected '+expected+' observed '+digest)
  report['stage']='BLENDER_NATIVE_SOURCE_EXPORT';store()
  work=state/'generated';work.mkdir()
  p=cmd(blender_command(repo,work),timeout=1800)
  (state/'blender.log').write_text(p.stdout+'\n'+p.stderr)
  print(p.stdout[-3000:],flush=True)
  exports=json.loads((work/'source_exports.json').read_text())
  row=exports['model'];fp=work/row['file']
  if hashfile(fp)!=row['sha256']:raise Stop('BLENDER_EXPORT_SHA_MISMATCH')
  info=glb(fp)
  if info['meshes']<1 or info['skins']<1 or len(info['animations'])<2:raise Stop('BLENDER_EXPORT_MESH_OR_ANIMATION_MISSING '+str(info))
  if len(info['animations'])!=len(set(info['animations'])):raise Stop('DUPLICATE_SOURCE_ANIMATION_NAMES')
  row['glbInspection']=info
  # Note: distinct names alone do not establish distinct evaluated motion.
  canonicalInfo=glb(repo/MODEL)
  if not canonicalInfo['animations']:raise Stop('OBSID_CANONICAL_ANIMATIONS_MISSING')
  report['stage']='STAGE_SOURCE_GLBS_AND_SHARED_VIEWER';store()
  public=downloads/(VER+'_'+runid+'_VIEW');public.mkdir()
  shutil.copyfile(work/row['file'],public/row['file'])
  shutil.copyfile(repo/MODEL,public/'Obsidianti.glb')
  shutil.copyfile(repo/'review/lionheart-obsidianti-compare-v1.6.1.html',public/'index.html')
  manifest={'run':runid,'campaign':VER,'sourceCommit':published,'sourceBlendSHA256':BLEND_SHA,'obsidiantiSha256':MODEL_SHA,
            'source':row,'targetGLB':canonicalInfo,'ownerApproval':'PENDING'}
  (public/'manifest.json').write_text(json.dumps(manifest,indent=2))
  if hashfile(public/'Obsidianti.glb')!=MODEL_SHA:raise Stop('PUBLIC_ASSET_HASH_MISMATCH_OBS')
  if hashfile(public/row['file'])!=row['sha256']:raise Stop('PUBLIC_ASSET_HASH_MISMATCH_SOURCE')
  report['stage']='START_VERIFIED_NO_CACHE_PHONE_VIEWER';store()
  with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
   s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  log=open(state/'http-server.log','ab',buffering=0)
  proc=subprocess.Popen([sys.executable,'-B',str(repo/'campaigns/LIONHEART_COMPARE_RUN_v1.6.1.py'),'--serve',str(public),str(port)],
        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
  log.close()
  url=f'http://127.0.0.1:{port}/index.html?run={runid}'
  for attempt in range(50):
   if proc.poll() is not None:raise Stop('HTTP_SERVER_EXITED '+str(proc.returncode))
   try:
    resp=urllib.request.urlopen(f'http://127.0.0.1:{port}/manifest.json',timeout=2)
    received=json.load(resp)
    if received.get('run')!=runid:raise Stop('VIEWER_WRONG_RUN_ID')
    report['httpHeaders']=dict(resp.headers.items());break
   except (OSError,ValueError):time.sleep(.15)
  else:raise Stop('VIEWER_HTTP_NOT_RESPONDING')
  report.update(status='VIEW_READY_PENDING_OWNER_REVIEW',stage='DONE',viewerStarted=True,viewerURL=url,
    viewerPort=port,viewerPID=proc.pid,viewerFolder=str(public),sourceExports=row,
    canonicalModelChanged=False)
  store()
  print('VIEWER_URL='+url+'\nVIEWER_PORT='+str(port)+'\nSERVER_PID='+str(proc.pid)+'\nCANONICAL_MODEL_UNCHANGED=YES\nOWNER_VISUAL_ACCEPTANCE=PENDING',flush=True)
  return 0
 except Exception as e:
  report['status']='BLOCKED';report['error']=str(e);store();print('ERROR='+str(e),flush=True)
  return 2
 finally:
  print('RECEIPT='+str(receipt),flush=True)

if __name__=='__main__':sys.exit(main())
