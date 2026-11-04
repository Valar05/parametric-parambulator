#!/data/data/com.termux/files/usr/bin/bash
# Recover completed real trot from v0.6.36 failed publication; preserve actual GLB.
# Git LFS pointer-aware canonical read gate; source-only Git commit via Termux.
set -Eeuo pipefail
CAMPAIGN=REPL_TROT_RECOVER_PUBLISH_v0.6.37
printf 'CAMPAIGN=%s\nAUTHORITY=TERMUX_GIT_SOURCE_ONLY\nCANONICAL_MODEL_MUTATION=FORBIDDEN\n' "$CAMPAIGN"
printf 'LAUNCHER_SHA256=%s\n' "$(sha256sum "$0" | cut -d' ' -f1)"
command -v python3 >/dev/null || { echo 'BLOCKED:PYTHON3_REQUIRED';exit 2; }
command -v git >/dev/null || { echo 'BLOCKED:GIT_REQUIRED';exit 2; }
D="${1:-$HOME/storage/downloads}"
[[ -d "$D" ]] || { echo 'BLOCKED:DOWNLOADS_NOT_FOUND';exit 2; }
T="$(mktemp -d "${TMPDIR:-${PREFIX:-/tmp}/tmp}/repl37-XXXXXXXX")"
trap 'rm -rf "$T"' EXIT
export REPL37_SCRIPT_SHA="$(sha256sum "$0" | cut -d' ' -f1)"
cat > "$T/recover.py" <<'REPL37_RECOVERY_PY'
from __future__ import annotations
import os,sys,glob,json,hashlib,subprocess,tempfile,shutil,time,struct,base64,io,zipfile,re
from pathlib import Path

NAME='REPL_TROT_DIAGONAL_IK_v0.6.36'
MODEL='Repl_TROT_DIAGONAL_IK_v0.6.36.glb'
PREV='REPL_REAR_HOOF_SWING_v0.6.35'
V36_SHA='73c4c0149bd39b3d82c44aa49c9c6c0554a1ba51c90b5d3e173aa5e33de274de'
OBSERVED_SHA='1b6fd6c989af59bef3ce7a8c825bd40cdc847228aa79cb722576c0946b436c29'
CANON_SHA='50d26053027296895fd8853e7337a1fcbfba8e77a63aea095680b19b3d113dd4'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
REPO='https://github.com/Valar05/parametric-parambulator.git'
REPOPATHS={'campaigns/REPL_TROT_DIAGONAL_IK_v0.6.36.sh':'v36','campaigns/REPL_TROT_RECOVER_PUBLISH_v0.6.37.sh':'v37'}
ETIQUETTE='https://docs.google.com/document/d/1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI/edit'
RESEARCH='https://docs.google.com/document/d/1BVoKaIG-ivp7Vl39SmrcEbfdAg-CAePjrd6IoRgEyQA/edit'

def sha(b):return hashlib.sha256(b).hexdigest()
def readsha(p):return sha(Path(p).read_bytes())
def need(x,why):
 if not x:raise RuntimeError('BLOCKED:'+why)
def run(cmd,env=None,timeout=120,binary=False):
 p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 if p.returncode:raise RuntimeError('BLOCKED:COMMAND:'+str(cmd[:5])+':'+p.stderr.decode('utf8','replace')[-700:])
 return p.stdout if binary else p.stdout.decode('utf8','replace').strip()

def readjson(p):return json.loads(Path(p).read_text())

def source_chain(downloads):
 a=downloads/PREV;b=downloads/'REPL_BODY_HEAD_STABLE_v0.6.33';c=downloads/'REPL_BODY_IK_REVIEW_v0.6.28'
 for d in (a,b,c):need((d/'receipt.json').is_file(),'MISSING_VERIFIED_RECEIPT:'+d.name)
 ra=readjson(a/'receipt.json');rb=readjson(b/'receipt.json');rc=readjson(c/'receipt.json')
 walk=a/'Repl_REAR_HOOF_REVIEW_v0.6.35.glb';head=b/'Repl_BODY_IK_HEAD_STABLE_v0.6.33.glb';ik=c/'Repl_BODY_IK_UNACCEPTED_v0.6.27.glb'
 for p in (walk,head,ik):need(p.is_file(),'MISSING_VERIFIED_MODEL:'+p.name)
 need(ra.get('campaign')==PREV and rb.get('campaign')=='REPL_BODY_HEAD_STABLE_v0.6.33' and rc.get('campaign')=='REPL_BODY_IK_REVIEW_v0.6.28','PREDECESSOR_ID_MISMATCH')
 need(ra.get('candidate_sha256')==ra.get('files',{}).get(walk.name)==readsha(walk),'WALK_INTEGRITY')
 need(ra.get('source_sha256')==rb.get('candidate_sha256')==readsha(head),'HEAD_INTEGRITY')
 need(rb.get('source_sha256')==rc.get('candidate_sha256')==readsha(ik),'IK_INTEGRITY')
 need(rc.get('input_glb_sha256')=='eb87ae7643e01cb546616d3b3a17dd2936fb00e01c87cc6a996bfebc8e518675','SOURCE_ORIGIN_INTEGRITY')
 need(ra.get('git_mutation') is False and ra.get('canonical_deployment') is False,'PREDECESSOR_NOT_REVIEW')
 print('APPROVED_WALK_VERIFIED='+readsha(walk),flush=True)
 return walk

def glb_doc(p):
 b=Path(p).read_bytes();need(b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b),'INVALID_GLTF_HEADER')
 size,typ=struct.unpack_from('<I4s',b,12);need(typ==b'JSON','MISSING_JSON_CHUNK')
 return json.loads(b[20:20+size])

def check_candidate(folder,walk,expected=None):
 p=folder/MODEL;phys=folder/'physics.json';view=folder/'index.html'
 for q in (p,phys,view):need(q.is_file(),'CANDIDATE_COMPONENT_MISSING:'+q.name)
 j=readjson(phys);sourcehash=readsha(walk)
 need(j['source_sha256']==sourcehash,'PHYSICS_WRONG_WALK')
 digest=readsha(p)
 need(j['result']['candidate_sha256']==digest,'PHYSICS_GLB_HASH_MISMATCH')
 if expected:need(digest==expected,'SOURCE_DEVICE_OUTPUT_MISMATCH')
 d=glb_doc(p);w=glb_doc(walk)
 need(len(d['animations'])==7 and len(w['animations'])==6,'ANIMATION_COUNT_INVALID')
 need(d['animations'][6]['name']=='REPL_TROT_01_DIAGONAL_IK_REVIEW','TROT_CLIP_IDENTITY_INVALID')
 need(d['animations'][:6]==w['animations'],'APPROVED_WALK_ANIMATIONS_CHANGED')
 need(d['meshes']==w['meshes'] and d['skins']==w['skins'],'PROTECTED_SKIN_OR_MESH_CHANGED')
 need('Repl_TROT_DIAGONAL_IK_v0.6.36.glb' in view.read_text(),'VIEWER_TARGET_INVALID')
 need(len(j.get('samples',[]))>=380,'PHYSICAL_VERIFICATION_SAMPLE_COUNT_TOO_LOW')
 need(j.get('bone_preservation')=='ORIGINAL SIX CLIPS AND ALL PREVIOUS BINARY BUFFER BYTES PRESERVED','BONE_PRESERVATION_UNVERIFIED')
 print('TROT_CANDIDATE_VERIFIED='+digest+' SAMPLES='+str(len(j['samples'])),flush=True)
 return digest,j

def recover_or_regenerate(downloads,walk,v36):
 final=downloads/NAME
 if final.exists():
  need((final/'receipt.json').is_file(),'OUTPUT_COLLISION_NO_RECEIPT')
  old=readjson(final/'receipt.json');digest,_=check_candidate(final,walk)
  need(old.get('candidate_sha256')==digest and old.get('source_sha256')==readsha(walk),'EXISTING_RECEIPT_WRONG_SOURCE')
  for n,h in old.get('files',{}).items():need((final/n).is_file() and readsha(final/n)==h,'EXISTING_REVIEW_FILE_CHANGED:'+n)
  print('REUSED_VERIFIED_COMPLETE_REVIEW='+str(final),flush=True)
  return final
 candidates=sorted(downloads.glob('.'+NAME+'-*'),key=lambda p:p.stat().st_mtime,reverse=True)
 for c in candidates:
  try:
   digest,j=check_candidate(c,walk,OBSERVED_SHA)
   need(not final.exists(),'OUTPUT_COLLISION')
   files={p.name:readsha(p) for p in c.iterdir() if p.is_file() and p.name!='server.log'}
   receipt={'campaign':NAME,'source_campaign':PREV,'source_sha256':readsha(walk),'candidate_sha256':digest,'files':files,'model_deployed':False,'git_mutation':False,'recovered_by':'REPL_TROT_RECOVER_PUBLISH_v0.6.37','recovery_origin':'verified complete v0.6.36 private failure evidence','physics_summary':j.get('validation',{}),'original_six_animations_preserved':True,'visual_acceptance':'PENDING','status':'TROT_REVIEW_RECOVERED_AND_PHYSICS_VERIFIED'}
   (c/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
   c.rename(final)
   print('RECOVERED_COMPLETED_20_SECOND_SOLVE_WITHOUT_RERUN='+str(final),flush=True)
   return final
  except Exception as e:
   print('RECOVERY_CANDIDATE_REJECTED='+str(c)+':'+str(e),flush=True)
 # Regenerate using the **exact v36 embedded code**, source-verified; this is bounded fallback.
 print('NO_VALID_FAILURE_CANDIDATE:REGENERATING_ONCE_WITH_VERIFIED_V36_ENGINE',flush=True)
 data=v36.read_text();match=re.search(r"b64='''(.*?)'''",data,re.S)
 need(match is not None,'V36_EMBEDDED_PAYLOAD_MISSING')
 payload=zipfile.ZipFile(io.BytesIO(base64.b64decode(''.join(match.group(1).split()))))
 manifest=json.loads(payload.read('manifest.json'))
 with tempfile.TemporaryDirectory(prefix='repl37-regenerate-') as td:
  t=Path(td)
  for n,digest in manifest.items():
   need('/' not in n and '..' not in n,'EMBEDDED_PATH_INVALID')
   b=payload.read(n);need(sha(b)==digest,'EMBEDDED_PAYLOAD_INVALID:'+n)
   (t/n).write_bytes(b)
  env=os.environ.copy();env.update({'REPL_HOST_TEST':'1','REPL_SCRIPT':str(v36),'REPL_TROT_VIEWER':str(t/'viewer.html'),'PYTHONPATH':td})
  run([sys.executable,str(t/'driver.py'),str(downloads)],env=env,timeout=600)
 return recover_or_regenerate(downloads,walk,v36)

def git_publish(v36,v37):
 env=os.environ.copy();env.update({'GIT_LFS_SKIP_SMUDGE':'1','GIT_TERMINAL_PROMPT':'0'})
 for attempt in range(3):
  with tempfile.TemporaryDirectory(prefix='repl37-source-') as td:
   repo=Path(td)/'repo'
   try:
    run(['git','-c','core.autocrlf=false','clone','--depth','1','--filter=blob:none','--branch','main',REPO,str(repo)],env=env,timeout=150)
    need(run(['git','-C',str(repo),'hash-object','AGENTS.md'],env=env)==AGENTS_BLOB,'REMOTE_AGENTS_CHANGED_REVIEW_REQUIRED')
    meta=readjson(repo/'assets/repl/CANONICAL_MODEL.json')['active_model']
    need(meta['sha256']==CANON_SHA,'CANONICAL_MANIFEST_CHANGED')
    ptr=run(['git','-C',str(repo),'show','HEAD:assets/repl/Repl.glb'],env=env,binary=True)
    if ptr.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
     lines=ptr.decode().splitlines();oid=next((x.split(':',1)[1] for x in lines if x.startswith('oid sha256:')),None)
     size=next((int(x.split()[1]) for x in lines if x.startswith('size ')),None)
     need(oid==meta['sha256'] and size is not None and size>1000000,'CANONICAL_LFS_POINTER_DOES_NOT_MATCH_MANIFEST')
     print('CANONICAL_LFS_POINTER_OID_VERIFIED='+oid+' SIZE='+str(size),flush=True)
    else:
     need(sha(ptr)==meta['sha256'],'CANONICAL_DIRECT_BLOB_MISMATCH')
    before=run(['git','-C',str(repo),'rev-parse','HEAD'],env=env)
    before_model_blob=run(['git','-C',str(repo),'rev-parse','HEAD:assets/repl/Repl.glb'],env=env)
    changed=[]
    for path,src in [(list(REPOPATHS)[0],v36),(list(REPOPATHS)[1],v37)]:
     dst=repo/path
     if dst.exists():need(readsha(dst)==readsha(src),'REMOTE_SOURCE_FILENAME_COLLISION:'+path)
     else:
      dst.parent.mkdir(exist_ok=True,parents=True);dst.write_bytes(src.read_bytes());changed.append(path)
    if changed:
     run(['git','-C',str(repo),'add','--',*changed],env=env)
     staged=run(['git','-C',str(repo),'diff','--cached','--name-only'],env=env).splitlines()
     need(sorted(staged)==sorted(changed),'GIT_STAGED_UNEXPECTED_FILES')
     run(['git','-C',str(repo),'-c','user.name=Repl Termux Campaign','-c','user.email=repl-campaign@localhost','commit','-m','Recover Repl trot and verify canonical LFS pointer v0.6.37'],env=env)
     commit=run(['git','-C',str(repo),'rev-parse','HEAD'],env=env)
     try:run(['git','-C',str(repo),'push','origin','HEAD:refs/heads/main'],env=env,timeout=100)
     except RuntimeError as e:
      if attempt<2:
       print('GIT_PUSH_RETRY='+str(attempt+1)+':'+str(e)[-300:],flush=True);continue
      raise
    else:commit=before
    remote=run(['git','ls-remote',REPO,'refs/heads/main'],env=env).split()[0]
    need(remote==commit,'REMOTE_HEAD_READBACK_NOT_COMMIT')
    run(['git','-C',str(repo),'fetch','--depth','1','origin','main'],env=env,timeout=90)
    for path,src in [(list(REPOPATHS)[0],v36),(list(REPOPATHS)[1],v37)]:
     rb=run(['git','-C',str(repo),'show','FETCH_HEAD:'+path],env=env,binary=True)
     need(sha(rb)==readsha(src),'REMOTE_FILE_HASH_READBACK:'+path)
    need(run(['git','-C',str(repo),'rev-parse','FETCH_HEAD:assets/repl/Repl.glb'],env=env)==before_model_blob,'CANONICAL_MODEL_BLOB_CHANGED_AFTER_PUBLICATION')
    print('GITHUB_SOURCE_COMMIT_AND_EXACT_READBACK='+commit,flush=True)
    return {'state':'COMMITTED_AND_READ_BACK' if changed else 'ALREADY_COMMITTED_AND_READ_BACK','commit':commit,'canonical_model_sha256':CANON_SHA,'agents_md_blob':AGENTS_BLOB,'campaign_etiquette':ETIQUETTE,'research':RESEARCH}
   except RuntimeError:
    raise
 raise RuntimeError('BLOCKED:SOURCE_PUBLICATION_ATTEMPTS_EXHAUSTED')

def main():
 downloads=Path(sys.argv[1]);v37=Path(sys.argv[2]);need(downloads.is_dir(),'DOWNLOADS_UNAVAILABLE')
 matches=[p for p in downloads.glob('REPL_TROT_DIAGONAL_IK_v0.6.36*.sh') if p.is_file() and readsha(p)==V36_SHA]
 need(len(matches)>0,'ORIGINAL_V36_SCRIPT_NOT_FOUND_BY_EXACT_HASH')
 v36=matches[0];need(readsha(v37)==os.environ['REPL37_SCRIPT_SHA'],'RECOVERY_SCRIPT_CHANGED')
 walk=source_chain(downloads)
 dest=recover_or_regenerate(downloads,walk,v36)
 pub=git_publish(v36,v37)
 receipt=dest/'receipt.json';a=readjson(receipt)
 a['git_source_publication']=pub;a['recovered_by']='REPL_TROT_RECOVER_PUBLISH_v0.6.37';a['git_mutation']=False
 # receipt only, never modify approved GLB or previously rendered outputs
 receipt.write_text(json.dumps(a,indent=2)+'\n')
 print('TROT_REVIEW_DIR='+str(dest),flush=True)
 print('TROT_OUTPUT_SHA256='+a['candidate_sha256'],flush=True)
 print('TROT_SOURCE_GIT_PUBLICATION='+pub['state'],flush=True)
 print('CANONICAL_MODEL_AND_APPROVED_WALK_UNCHANGED=YES',flush=True)

if __name__=='__main__':
 try:main()
 except Exception as e:print('STATUS='+str(e),file=sys.stderr);sys.exit(2)
REPL37_RECOVERY_PY
python3 "$T/recover.py" "$D" "$(readlink -f "$0")"
REVIEW="$D/REPL_TROT_DIAGONAL_IK_v0.6.36"
[[ -f "$REVIEW/receipt.json" && -f "$REVIEW/index.html" ]] || { echo 'BLOCKED:RECOVERED_REVIEW_MISSING';exit 2; }
PORT="$(python3 - "$REVIEW" <<'PORT_REUSE'
import sys,urllib.request,pathlib
p=pathlib.Path(sys.argv[1]);ref=(p/'receipt.json').read_bytes()
for port in range(8765,8830):
 try:
  with urllib.request.urlopen('http://127.0.0.1:%d/receipt.json'%port,timeout=.25) as r:b=r.read()
  if b==ref:print(port);break
 except Exception:pass
PORT_REUSE
)"
if [[ -z "$PORT" ]];then
 PORT="$(python3 - <<'FREE_PORT'
import socket
for port in range(8765,8830):
 with socket.socket() as s:
  try:s.bind(('127.0.0.1',port))
  except OSError:continue
  print(port);break
else:raise SystemExit('BLOCKED:NO_FREE_VIEWER_PORT')
FREE_PORT
)"
 if command -v setsid >/dev/null;then
  setsid python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$REVIEW" > "$REVIEW/server.log" 2>&1 </dev/null &
 else
  nohup python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$REVIEW" > "$REVIEW/server.log" 2>&1 </dev/null &
 fi
 printf 'VIEWER_SERVER_PID=%s\n' "$!"
fi
python3 - "$PORT" "$REVIEW" <<'VERIFY_HTTP'
import sys,time,json,hashlib,urllib.request,pathlib
port=sys.argv[1];root=pathlib.Path(sys.argv[2]);receipt=json.loads((root/'receipt.json').read_text())
for n in range(35):
 try:
  for name in ['index.html','Repl_TROT_DIAGONAL_IK_v0.6.36.glb']:
   with urllib.request.urlopen('http://127.0.0.1:'+port+'/'+name,timeout=3) as r:b=r.read()
   assert hashlib.sha256(b).hexdigest()==receipt['files'][name],name
  print('HTTP_REAL_VIEWER_AND_REAL_GLB_SHA_READBACK=PASS');break
 except Exception:
  if n==34:raise
  time.sleep(.3)
VERIFY_HTTP
URL="http://127.0.0.1:$PORT/index.html"
echo "TROT_REVIEW_URL=$URL"
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" && echo 'ANDROID_BROWSER_OPEN_REQUESTED=YES' || echo 'ANDROID_BROWSER_OPEN_REQUESTED=FAILED'
fi
echo 'STATUS=TROT_CANDIDATE_RECOVERED; GIT_SOURCE_VERIFIED; OWNER_VISUAL_ACCEPTANCE_PENDING; CANONICAL_UNCHANGED'
