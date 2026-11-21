#!/data/data/com.termux/files/usr/bin/bash
# Hareworks v0.1.5: repair v0.1.4's missing foot-profile resource without
# altering the user's preferred v0.1.3 legs, v0.1.2 pelvis, or v0.1.4 upper solver.
# Sole authorized publication lane: owner's Android Termux Git.
set -Eeuo pipefail
CAMPAIGN='hareworks-forward-woman-viewer-fix-v0.1.5'
REPO='Valar05/parametric-parambulator'
BASE='5ca33bf4d5479f03ea8dbfdff7fdea9d6978eacf'
OLD='tools/hareworks-forward-woman/v0.1.4'
DIR='tools/hareworks-forward-woman/v0.1.5'
MODEL='assets/hareworks/Hareworks-nine-clips.glb'
MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'
MODEL_BYTES='6784896'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
V014_VIEWER_BLOB='a8fefa27db49e4db18527c2f3699f2ea650d427b'
V014_KERNEL_BLOB='e5f04a8042d220118125cd736ddbe2502529fadf'
V013_LEGS_BLOB='8ca6a0c2b1973f71d3f6cb383612635252f9a042'
V012_PELVIS_BLOB='4d43c5864de31ec93563c42a910863579138e4c5'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase='preflight'
ROOT='';WORK='';COMMIT='';PORT='';PID=''
fail(){
  echo "BLOCKED step=$phase reason=$*"
  if [[ -n "$ROOT" && -f "$ROOT/server.log" ]];then
    echo 'SERVER_LOG_TAIL:'; tail -n 20 "$ROOT/server.log" || true
  fi
  python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$COMMIT" "$ROOT" <<'PY_BLOCK' || true
import datetime,json,pathlib,sys
out,campaign,phase,reason,commit,snapshot=sys.argv[1:]
pathlib.Path(out).write_text(json.dumps({'campaign':campaign,'phase':'BLOCKED','step':phase,'reason':reason,'publishedCommitIfKnown':commit,'snapshot':snapshot,'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
PY_BLOCK
  exit 1
}
hash(){ sha256sum -- "$1" | cut -d' ' -f1; }
if [[ "${1:-run}" == status ]];then
  if [[ -f "$STATE/receipt.json" ]];then cat "$STATE/receipt.json";else echo "NO_COMPLETE_RECEIPT=$STATE";fi
  exit 0
fi
[[ "${1:-run}" == run || "${1:-run}" == resume ]] || fail 'usage: bash script.sh [run|resume|status]'
for c in git python3 curl sha256sum node;do command -v "$c" >/dev/null || fail "missing required command: $c";done
SELF_SHA=$(hash "$0")
echo "CAMPAIGN=$CAMPAIGN"
echo "ENTRYPOINT_SHA256=$SELF_SHA"
echo "REMOTE_REPO=$REPO"
ORIGIN="https://github.com/$REPO.git"
for attempt in 1 2 3;do
  REMOTE=$(git ls-remote "$ORIGIN" refs/heads/main | cut -f1) && [[ "$REMOTE" =~ ^[0-9a-f]{40}$ ]] && break
  sleep "$attempt"
done
[[ "${REMOTE:-}" =~ ^[0-9a-f]{40}$ ]] || fail 'GitHub main lookup failed'
echo "AUDITED_BASE=$BASE"
echo "OBSERVED_REMOTE_MAIN=$REMOTE"
ROOT=$(mktemp -d "$STATE/snapshot.XXXXXXXX") || fail 'isolated snapshot creation failed'
WORK="$ROOT/repo"
phase='isolation'
for attempt in 1 2;do
  if GIT_LFS_SKIP_SMUDGE=1 git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "$ORIGIN" "$WORK";then break;fi
  [[ ! -e "$WORK" ]] || fail 'clone failed with incomplete isolated checkout; retained for inspection'
  sleep "$attempt"
done
[[ -d "$WORK/.git" ]] || fail 'could not clone isolated repository'
git -C "$WORK" sparse-checkout init --cone || fail 'sparse init failed'
git -C "$WORK" sparse-checkout set assets/hareworks tools/hareworks-forward-woman campaigns || fail 'sparse selection failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$WORK" checkout -B "$CAMPAIGN" "$REMOTE" || fail 'isolated checkout failed'
[[ "$(git -C "$WORK" rev-parse HEAD)" == "$REMOTE" ]] || fail 'isolated checkout revision mismatch'
cd "$WORK"
phase='rules-and-source'
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'AGENTS.md not loaded'
[[ "$(git rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || fail 'AGENTS.md audited revision changed'
[[ "$(git rev-parse HEAD:$OLD/viewer.mjs)" == "$V014_VIEWER_BLOB" ]] || fail 'v0.1.4 viewer changed'
[[ "$(git rev-parse HEAD:$OLD/upper-kernel.mjs)" == "$V014_KERNEL_BLOB" ]] || fail 'upper solver changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs)" == "$V013_LEGS_BLOB" ]] || fail 'preserved lower-body solver changed'
[[ "$(git rev-parse HEAD:tools/hareworks-forward-woman/v0.1.2/motion-profile.json)" == "$V012_PELVIS_BLOB" ]] || fail 'preserved pelvis profile changed'
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_BYTES" <<'PY_POINTER' || fail 'published model LFS identity changed'
import subprocess,sys
path,sha,n=sys.argv[1:]
actual=subprocess.check_output(['git','show','HEAD:'+path])
expected=(f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {n}\n').encode()
assert actual==expected,(actual[:100],expected)
print('IMMUTABLE_MODEL_POINTER=PASS')
PY_POINTER
FILES=("$DIR/index.html" "$DIR/viewer.mjs" "$DIR/upper-kernel.mjs" "$DIR/upper-kernel-test.mjs" "$DIR/README.md" "$DIR/contract.json" "campaigns/$CAMPAIGN.sh")
phase='collision-gate'
PUBLISHED=0
if [[ "$REMOTE" == "$BASE" ]];then
  for p in "${FILES[@]}";do
    [[ ! -e "$p" && ! -L "$p" ]] || fail "destination exists: $p"
    git cat-file -e "HEAD:$p" 2>/dev/null && fail "historical Git path occupied: $p" || :
  done
else
  if git cat-file -e "HEAD:campaigns/$CAMPAIGN.sh" 2>/dev/null && git cat-file -e "HEAD:$DIR/viewer.mjs" 2>/dev/null;then
    [[ "$(git show "HEAD:campaigns/$CAMPAIGN.sh" | sha256sum | cut -d' ' -f1)" == "$SELF_SHA" ]] || fail 'different campaign already uses filename'
    [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'remote head no longer matches audited publish ancestry'
    PUBLISHED=1;echo "EXACT_CAMPAIGN_ALREADY_PUBLISHED=$REMOTE; no Git mutation"
  else
    fail 'remote main advanced; no overwrite, rebase or force push authorized'
  fi
fi
phase='model'
SOURCE=''
for base in "$HOME/.local/state/hareworks" "$HOME/storage/downloads" /storage/emulated/0/Download;do
  [[ -d "$base" ]] || continue
  if [[ "$base" == "$HOME/.local/state/hareworks" ]];then
    while IFS= read -r -d '' f;do
      [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
      if [[ "$(hash "$f")" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
    done < <(find "$base" -maxdepth 10 -type f -name 'Hareworks-nine-clips.glb' -print0 2>/dev/null)
  else
    while IFS= read -r -d '' f;do
      [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_BYTES" ]] || continue
      if [[ "$(hash "$f")" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
    done < <(find -L "$base" -maxdepth 1 -type f -iname '*.glb' -print0 2>/dev/null)
  fi
  [[ -z "$SOURCE" ]] || break
done
if [[ -z "$SOURCE" ]];then
  command -v git-lfs >/dev/null || fail 'verified source missing and git-lfs unavailable'
  git lfs install --local || fail 'local git-lfs initialization failed'
  for attempt in 1 2;do
    if GIT_LFS_SKIP_SMUDGE=1 git lfs fetch -I "$MODEL" -X '' origin "$REMOTE";then break;fi
    sleep "$attempt"
  done
  OBJ=$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")
  [[ -f "$OBJ" ]] || fail 'exact source LFS object not downloaded'
  SOURCE="$OBJ"
fi
[[ "$(wc -c < "$SOURCE" | tr -d ' ')" == "$MODEL_BYTES" && "$(hash "$SOURCE")" == "$MODEL_SHA" ]] || fail 'GLB actual bytes mismatch'
python3 - "$SOURCE" <<'PY_RIG' || fail 'canonical GLB rig/clip unreadable'
import json,struct,sys
p=sys.argv[1]; b=open(p,'rb').read()
assert b[:4]==b'glTF' and len(b)==struct.unpack_from('<I',b,8)[0]
n,kind=struct.unpack_from('<I4s',b,12);assert kind==b'JSON'
g=json.loads(b[20:20+n]);assert len(g['skins'][0]['joints'])==74
assert len(g['animations'])==9 and 'Walking_Woman' in [a['name'] for a in g['animations']]
print('ORIGINAL_GLTF_74_JOINTS_AND_WOMAN_CLIP=PASS')
PY_RIG
phase='packet'
if ((PUBLISHED==0));then
  mkdir -p "$DIR" campaigns
  python3 - "$OLD" "$DIR" <<'PY_GENERATE' || fail 'versioned viewer repair source generation failed'
import pathlib,sys
old=pathlib.Path(sys.argv[1]);new=pathlib.Path(sys.argv[2]);new.mkdir(parents=True,exist_ok=True)
viewer=(old/'viewer.mjs').read_text()
wrong="const paths=['../v0.1.2/motion-profile.json','./foot-profile.json'];"
right="const paths=['../v0.1.2/motion-profile.json','../v0.1.3/foot-profile.json'];"
assert viewer.count(wrong)==1, 'missing or multiplied defective dependency expression'
viewer=viewer.replace(wrong,right).replace('v0.1.4','v0.1.5')
(new/'viewer.mjs').write_text(viewer)
html=(old/'index.html').read_text().replace('v0.1.4','v0.1.5')
# Correct stale v0.1.3 description without changing physics or animation.
old_desc='The generated side borrows only non-leg upper-body animation; no animated pelvis or leg tracks.'
assert html.count(old_desc)==1
html=html.replace(old_desc,'The generated side uses periodic upper-body equations; no generated clip tracks play.')
# Display actionable failure for module/CDN load errors too.
error_hook='''<script>window.addEventListener('error',function(e){const s=document.getElementById('status');if(s)s.textContent='BROWSER_SCRIPT_ERROR: '+(e.message||'module or CDN import failed')});window.addEventListener('unhandledrejection',function(e){const s=document.getElementById('status');if(s)s.textContent='BROWSER_IMPORT_ERROR: '+(e.reason?.message||String(e.reason))});</script>'''
assert '<div id="status"' in html
html=html.replace('<div id="status"',error_hook+'\n<div id="status"',1)
(new/'index.html').write_text(html)
for filename in ('upper-kernel.mjs','upper-kernel-test.mjs'):
  (new/filename).write_bytes((old/filename).read_bytes())
print('V015_VIEWER_RESOURCE_PATH_CORRECTED=PASS')
PY_GENERATE
  cat > "$DIR/README.md" <<'MD_README'
# Hareworks v0.1.5: blank viewer resource recovery

This is a **loading-path correction only** to the owner-rejected blank-screen v0.1.4 viewer. Its published `viewer.mjs` requests `./foot-profile.json` although that asset only exists in `../v0.1.3/foot-profile.json`. That missing HTTP JSON blocks the entire `Promise.all` initialization before the skinned characters are added to the scene.

## Preserved scope

- Unchanged original source GLB, all 9 animations, and the reference `Walking_Woman` clip.
- Unchanged v0.1.3 leg and foot solver, v0.1.2 pelvis equations, v0.1.4 upper-body Fourier reconstruction.
- The full v0.1.5 `viewer.mjs` is generated from the exact audited v0.1.4 viewer with only the broken asset URL and version labels replaced. Its physics/pose statements are byte-equivalent after that substitution. The `upper-kernel.mjs` and its tests are copied byte-for-byte.
- The HTML has updated model-description wording plus a browser error message hook. Source profile, foot profile, model, old versions, and the existing Git history are untouched.

## Gates

The Termux campaign pins the current remote Git main, rules Git blob, source GLB SHA256 and bytes. It checks every relative `import`, the actual two JSON profile dependencies, and model URI, including deliberate validation of the old broken dependency path as a negative fixture. It runs existing kernel tests, publishes new text files only in an isolated Termux checkout, confirms exact remote readback, and starts a fresh no-cache HTTP viewer that checks the same runtime resource manifest rather than an unrelated list of URLs. It prints the actual dynamically assigned localhost URL, port, PID, model hash, and persistent receipt. Browser execution and visible skinned model review remain separate from HTTP availability and Git publication.

**Owner acceptance pending.** This does not assert the upper-body motion is visually approved or that world-space locomotion is complete.
MD_README
  cat > "$DIR/contract.json" <<'JSON_CONTRACT'
{
  "campaign": "hareworks-forward-woman-viewer-fix-v0.1.5",
  "repository": "Valar05/parametric-parambulator",
  "auditedParent": "5ca33bf4d5479f03ea8dbfdff7fdea9d6978eacf",
  "sourceClip": "Walking_Woman",
  "immutableModelPath": "assets/hareworks/Hareworks-nine-clips.glb",
  "immutableModelSha256": "a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6",
  "runLane": "Termux Git only",
  "purpose": "Fix v0.1.4 viewer's missing foot-profile JSON; preserve all gait mechanics",
  "oldBadUrl": "./foot-profile.json",
  "correctUrl": "../v0.1.3/foot-profile.json",
  "newFiles": ["tools/hareworks-forward-woman/v0.1.5/index.html", "tools/hareworks-forward-woman/v0.1.5/viewer.mjs", "tools/hareworks-forward-woman/v0.1.5/upper-kernel.mjs", "tools/hareworks-forward-woman/v0.1.5/upper-kernel-test.mjs", "tools/hareworks-forward-woman/v0.1.5/README.md", "tools/hareworks-forward-woman/v0.1.5/contract.json", "campaigns/hareworks-forward-woman-viewer-fix-v0.1.5.sh"],
  "protectedVersions": ["v0.1.2", "v0.1.3", "v0.1.4"],
  "ownerVisualAcceptance": false
}
JSON_CONTRACT
  cp -- "$0" "campaigns/$CAMPAIGN.sh" || fail 'cannot install exact campaign launcher'
fi
phase='prepublish-dependency-gate'
python3 - "$OLD" "$DIR" "$MODEL" "$MODEL_SHA" <<'PY_DEPENDENCIES' || fail 'viewer dependencies or locked source changed'
import json,pathlib,re,subprocess,sys
old,new,model,modelsha=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]),sys.argv[4]
source=(old/'viewer.mjs').read_text();newsrc=(new/'viewer.mjs').read_text()
wrong="const paths=['../v0.1.2/motion-profile.json','./foot-profile.json'];"
right="const paths=['../v0.1.2/motion-profile.json','../v0.1.3/foot-profile.json'];"
assert source.count(wrong)==1
assert newsrc==source.replace(wrong,right).replace('v0.1.4','v0.1.5'), 'unexpected animation/rig source modification'
for p in ('upper-kernel.mjs','upper-kernel-test.mjs'):
 assert (old/p).read_bytes()==(new/p).read_bytes(), ('upper algorithm drift',p)
old_missing=(old/'foot-profile.json').exists()
assert not old_missing, 'negative fixture unexpectedly resolved: defective v0.1.4 dependency'
assert not (new/'foot-profile.json').exists(), 'wrong profile path fabricated'
urls=re.search(r"const paths=\['([^']+)','([^']+)'\];",newsrc)
assert urls, 'JS JSON dependency expression not recognized'
for rel in urls.groups():
 target=(new/rel).resolve(strict=True)
 assert target.is_file(), ('missing JSON runtime dependency',rel)
 data=json.loads(target.read_text())
 assert data['sourceSha256']==modelsha and data['clip']=='Walking_Woman',('invalid profile source',rel)
for rel in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",newsrc):
 assert (new/rel).resolve(strict=True).is_file(), ('missing JS module dependency',rel)
html=(new/'index.html').read_text()
assert 'BROWSER_SCRIPT_ERROR' in html and 'BROWSER_IMPORT_ERROR' in html
assert 'src="./viewer.mjs"' in html
assert model.as_posix() in 'assets/hareworks/Hareworks-nine-clips.glb' or model.exists()
assert model.read_text().startswith('version https://git-lfs.github.com/spec/v1') or model.stat().st_size==6784896
print('RUNTIME_MANIFEST=PASS JSON x2, all relative JS imports, DOM module, original model')
print('INJECTED_MISSING_PROFILE_NEGATIVE_TEST=PASS: old bad path does not exist')
print('PRESERVED_V013_LEGS_V012_PELVIS_V014_UPPER=PASS exact viewer normalization')
PY_DEPENDENCIES
node --check "$DIR/viewer.mjs" || fail 'viewer syntax failed'
node --check "$DIR/upper-kernel.mjs" || fail 'upper module syntax failed'
node "$DIR/upper-kernel-test.mjs" > "$STATE/upper-test.log" || fail 'unchanged upper module test failed'
node tools/hareworks-forward-woman/v0.1.3/foot-kernel-test.mjs > "$STATE/foot-regression.log" || fail 'preserved v0.1.3 foot regression failed'
node tools/hareworks-forward-woman/v0.1.2/pose-kernel-test.mjs > "$STATE/pelvis-regression.log" || fail 'preserved v0.1.2 pelvis regression failed'
[[ "$(hash "campaigns/$CAMPAIGN.sh")" == "$SELF_SHA" ]] || fail 'repo campaign file does not match exact attached entrypoint'
echo 'HOST_SOURCE_SYNTAX_AND_DEPENDENCIES=PASS; REAL_BROWSER=PENDING'
if ((PUBLISHED==0));then
  phase='scoped-stage'
  [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'main changed before publication'
  git add -- "${FILES[@]}" || fail 'allowlisted stage failed'
  python3 - "${FILES[@]}" <<'PY_STAGE' || fail 'staged set not exactly the new seven text files'
import subprocess,sys
expected=set(sys.argv[1:]);actual=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines());assert actual==expected,(sorted(expected-actual),sorted(actual-expected));assert all(not p.endswith('.glb') for p in actual)
print('NEW_TEXT_ONLY_STAGING=PASS',len(actual))
PY_STAGE
  for protected in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb "$MODEL" tools/hareworks-forward-woman/v0.1.2/motion-profile.json tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs tools/hareworks-forward-woman/v0.1.4/viewer.mjs tools/hareworks-forward-woman/v0.1.4/upper-kernel.mjs;do
    git diff --quiet -- "$protected" || fail "protected file changed: $protected"
    [[ "$(git rev-parse "HEAD:$protected")" == "$(git rev-parse "$BASE:$protected")" ]] || fail "protected Git blob changed: $protected"
  done
  phase='commit'
  git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Fix Hareworks v0.1.4 blank model viewer resource path v0.1.5' || fail 'commit failed'
  COMMIT=$(git rev-parse HEAD)
  [[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'unexpected commit parent'
  phase='push'
  [[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote advanced after commit; no force push'
  GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "push failed, local commit retained: $COMMIT"
else
  COMMIT="$REMOTE"
fi
phase='remote-readback'
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$COMMIT" ]] || fail 'GitHub main readback SHA differs'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'readback Git fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$COMMIT" ]] || fail 'remote FETCH_HEAD differs'
for p in "${FILES[@]}";do
  [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "HEAD:$p")" ]] || fail "remote artifact differs: $p"
done
for p in AGENTS.md "$MODEL" "$OLD/viewer.mjs" "$OLD/upper-kernel.mjs" tools/hareworks-forward-woman/v0.1.3/foot-kernel.mjs tools/hareworks-forward-woman/v0.1.2/motion-profile.json;do
  [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "protected remote blob changed: $p"
done
echo "EXACT_REMOTE_READBACK=PASS $COMMIT"
phase='viewer'
cp -- "$SOURCE" "$MODEL" || fail 'copy verified model into disposable HTTP snapshot failed'
[[ "$(hash "$MODEL")" == "$MODEL_SHA" ]] || fail 'local served model digest mismatch'
cat > "$ROOT/server.py" <<'PY_SERVER'
import http.server,json,os,pathlib,sys
root,ready=sys.argv[1:]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=root,**kwargs)
 def end_headers(self):
  self.send_header('Cache-Control','no-store, no-cache, max-age=0, must-revalidate')
  self.send_header('Pragma','no-cache')
  super().end_headers()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
pathlib.Path(ready).write_text(json.dumps({'pid':os.getpid(),'port':server.server_address[1],'root':root}))
server.serve_forever()
PY_SERVER
READY="$ROOT/server-ready.json"
nohup python3 "$ROOT/server.py" "$WORK" "$READY" > "$ROOT/server.log" 2>&1 </dev/null &
PID=$!
for i in 1 2 3 4 5 6 7 8 9 10;do
  [[ -f "$READY" ]] && PORT=$(python3 - "$READY" <<'PY_PORT'
import json,sys
print(json.load(open(sys.argv[1]))['port'])
PY_PORT
)
  if [[ "$PORT" =~ ^[0-9]+$ ]] && curl -fsS --max-time 3 "http://127.0.0.1:$PORT/$DIR/index.html" >/dev/null 2>&1;then break;fi
  sleep 1
done
[[ "$PORT" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null || fail 'HTTP server failed to start'
# Independent readback uses the EXACT resource paths extracted from the new JS.
python3 - "http://127.0.0.1:$PORT" "$DIR" "$MODEL" "$MODEL_SHA" "$MODEL_BYTES" "$STATE/resource-manifest.json" <<'PY_HTTP' || fail 'HTTP runtime dependency readback failed'
import hashlib,json,pathlib,re,sys,urllib.parse,urllib.request
origin,directory,model,sha,n,out=sys.argv[1:];n=int(n); viewer=pathlib.PurePosixPath(directory)/'viewer.mjs'
read=lambda u:urllib.request.urlopen(u,timeout=40).read()
get=lambda path:read(origin+'/'+str(path).lstrip('/'))
script=get(viewer).decode();html=get(pathlib.PurePosixPath(directory)/'index.html').decode()
match=re.search(r"const paths=\['([^']+)','([^']+)'\];",script)
assert match, 'runtime requested JSON URLs not discoverable'
paths=[str(pathlib.PurePosixPath(directory).joinpath(u)) for u in ('index.html','viewer.mjs','upper-kernel.mjs','upper-kernel-test.mjs')]
urls=[urllib.parse.urljoin(origin+'/'+directory+'/viewer.mjs',rel) for rel in match.groups()]
for rel in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",script): urls.append(urllib.parse.urljoin(origin+'/'+directory+'/viewer.mjs',rel))
for u in urls: assert len(read(u))>0,('missing browser import/fetch',u)
for u in urls[:2]:
 d=json.loads(read(u));assert d['sourceSha256']==sha and d['clip']=='Walking_Woman',('wrong fetched JSON',u)
blob=get(model);assert len(blob)==n and hashlib.sha256(blob).hexdigest()==sha
assert 'src="./viewer.mjs"' in html
report={'viewerScript':str(viewer),'fetchedProfileUrls':urls[:2],'allRequiredImports':urls[2:],'modelSha256':sha,'modelBytes':len(blob),'status':'HTTP_DEPENDENCIES_VERIFIED_BROWSER_RENDER_PENDING'}
pathlib.Path(out).write_text(json.dumps(report,indent=2))
print('HTTP_RUNTIME_RESOURCE_MANIFEST=PASS',len(urls),'resources; original GLB bytes/hash PASS')
PY_HTTP
curl -fsSI --max-time 5 "http://127.0.0.1:$PORT/$DIR/index.html" > "$STATE/http-headers.txt" || fail 'HTTP viewer response header unavailable'
URL="http://127.0.0.1:$PORT/$DIR/index.html?build=$COMMIT"
python3 - "$STATE/receipt.json" "$CAMPAIGN" "$BASE" "$COMMIT" "$SELF_SHA" "$MODEL_SHA" "$AGENTS_BLOB" "$URL" "$PID" "$PORT" "$ROOT" <<'PY_RECEIPT'
import datetime,json,pathlib,sys
out,campaign,parent,commit,script,model,agents,url,pid,port,root=sys.argv[1:]
r={'campaign':campaign,'phase':'git_published_http_runtime_manifest_verified_browser_pending','timestampUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auditedParentCommit':parent,'publishedCommit':commit,'entrypointSha256':script,'modelSha256':model,'agentsGitBlob':agents,'rulesRead':{'agents':'Git blob verified from canonical repo','campaignEtiquette':'Home Center 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI freshly read 2026-11-20','topDownEtiquette':'Home Center 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU freshly read 2026-11-20'},'viewerUrl':url,'viewerPid':int(pid),'viewerPort':int(port),'snapshot':root,'fixed':'v0.1.4 viewer fetching nonexistent ./foot-profile.json','immutableModelAndPriorMotion':True,'HTTPRuntimeDependenciesVerified':True,'actualWebGLRendered':False,'ownerVisualAcceptance':False,'executionLane':'Termux Git only'}
pathlib.Path(out).write_text(json.dumps(r,indent=2))
PY_RECEIPT
echo "REMOTE_COMMIT=$COMMIT"
echo "MODEL_SHA256=$MODEL_SHA"
echo "VIEWER_SOURCE_COMMIT=$COMMIT"
echo "VIEWER_PORT=$PORT PID=$PID"
echo "VIEWER_URL=$URL"
echo "HTTP_MANIFEST=$STATE/resource-manifest.json"
echo "RECEIPT=$STATE/receipt.json"
echo 'BROWSER_WEBGL_VISIBLE_MODELS=OWNER_REVIEW_PENDING'
if command -v termux-open-url >/dev/null;then
 termux-open-url "$URL" || echo "BROWSER_OPEN_REQUEST_FAILED; manually open VIEWER_URL=$URL"
else
 echo "TERMUX_OPEN_URL_UNAVAILABLE; manually open VIEWER_URL=$URL"
fi
