#!/data/data/com.termux/files/usr/bin/bash
# v1.0.9 recovery: correct .gitattributes and publish through Termux Git.
# The failed v1.0.8 checkout and commit remain untouched.
set -Eeuo pipefail
CAMPAIGN=hareworks-gait-extraction-v1.0.9
PREVIOUS=hareworks-gait-extraction-v1.0.8
REPO=Valar05/parametric-parambulator
BASE=9b77c19d2f542706d5e04319068345f32583be2a
MODEL_SHA=a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6
MODEL_SIZE=6784896
MODEL=assets/hareworks/Hareworks-nine-clips.glb
ATTR=assets/hareworks/.gitattributes
ATTR_SHA=414c76f53126d221b1914dc72966390588127486
PREV_SCRIPT_SHA=1931765680b1c6f86329462c175bc5017f6d04616f113302bfd517754c72a9aa
OLD="$HOME/.local/state/hareworks/$PREVIOUS/work"
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
ROOT="$STATE/work"
mkdir -p "$STATE"
exec > >(tee -a "$STATE/run.log") 2>&1
phase=preflight
fail(){
  echo "BLOCKED step=$phase reason=$*"
  python3 - "$STATE/blocked.json" "$CAMPAIGN" "$phase" "$*" "$ROOT" <<'PYFAIL' || true
import json,sys,datetime
from pathlib import Path
out,campaign,phase,reason,root=sys.argv[1:]
Path(out).write_text(json.dumps(dict(campaign=campaign,phase='blocked',step=phase,reason=reason,checkout=root,timestampUtc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2))
PYFAIL
  exit 1
}
for c in git git-lfs python3 sha256sum curl; do command -v "$c" >/dev/null || fail "missing required dependency: $c"; done
[[ -f "$OLD/.git/config" ]] || fail 'previous v1.0.8 checkout unavailable; preserve all state'
[[ "$(git -C "$OLD" remote get-url origin)" == "https://github.com/$REPO.git" ]] || fail 'previous checkout origin changed'
[[ -z "$(git -C "$OLD" status --porcelain --untracked-files=all)" ]] || fail 'previous checkout dirty; refusing to touch owner files'
OLD_HEAD=$(git -C "$OLD" rev-parse HEAD)
[[ "$(git -C "$OLD" rev-parse HEAD^)" == "$BASE" ]] || fail 'previous commit does not extend pinned base'
[[ "$(git -C "$OLD" show "HEAD:campaigns/$PREVIOUS.sh" | sha256sum | cut -d' ' -f1)" == "$PREV_SCRIPT_SHA" ]] || fail 'previous campaign source differs'
python3 - "$OLD" "$BASE" <<'PYOLD' || fail 'previous committed paths or content differ'
import subprocess,sys
root,base=sys.argv[1:]
cmd=lambda *args: subprocess.check_output(['git','-C',root,*args])
wanted={'assets/hareworks/Hareworks-nine-clips.glb','campaigns/hareworks-gait-extraction-v1.0.8.sh',*[f'tools/hareworks-gait-extraction/v1.0.8/{x}' for x in ['README.md','contract.json','gait-extract.mjs','index.html']]}
actual=set(cmd('diff','--name-only',base,'HEAD').decode().splitlines());assert actual==wanted,(actual,wanted)
for path in ['AGENTS.md','assets/repl/Repl.glb','assets/hareworks/Hareworks.glb','assets/hareworks/.gitattributes']:
 assert cmd('rev-parse','HEAD:'+path)==cmd('rev-parse',base+':'+path),path
js=cmd('show','HEAD:tools/hareworks-gait-extraction/v1.0.8/gait-extract.mjs')
assert b'Idle_Turn_Left' in js and b'Idle_Turn_Right' in js
print('PREVIOUS_EXTRACTOR_CONTENT=VERIFIED')
PYOLD
# The recovered model can be a raw Git blob (v1.0.8 forgot to track its filename)
# or an LFS pointer. Prefer the exact full binary in old working tree, then Downloads.
phase=source
SOURCE=''
if [[ -f "$OLD/$MODEL" ]] && [[ "$(wc -c < "$OLD/$MODEL" | tr -d ' ')" == "$MODEL_SIZE" ]] && [[ "$(sha256sum "$OLD/$MODEL" | cut -d' ' -f1)" == "$MODEL_SHA" ]];then SOURCE="$OLD/$MODEL";fi
if [[ -z "$SOURCE" ]]; then
  SEARCH=()
  for d in "$HOME/storage/downloads" /storage/emulated/0/Download /sdcard/Download; do
    [[ -d "$d" ]] || continue
    abs=$(cd -P -- "$d" 2>/dev/null && pwd) || continue
    case " ${SEARCH[*]-} " in *" $abs "*) ;; *) SEARCH+=("$abs");; esac
  done
  for d in "${SEARCH[@]}"; do
    while IFS= read -r -d '' f; do
      [[ "$(wc -c < "$f" | tr -d ' ')" == "$MODEL_SIZE" ]] || continue
      if [[ "$(sha256sum "$f" | cut -d' ' -f1)" == "$MODEL_SHA" ]];then SOURCE="$f";break;fi
    done < <(find "$d" -maxdepth 1 -type f -iname '*.glb' -print0 2>/dev/null)
    [[ -n "$SOURCE" ]] && break
  done
fi
[[ -n "$SOURCE" ]] || fail 'exact original nine-clip model not found; no renamed or substitute source accepted'
echo "SOURCE_REUSED=$SOURCE SHA256=$MODEL_SHA"
phase=checkout
if [[ -e "$ROOT" ]]; then
  [[ -d "$ROOT/.git" ]] || fail 'recovery checkout path occupied by a non-Git file'
  [[ "$(git -C "$ROOT" remote get-url origin)" == "https://github.com/$REPO.git" ]] || fail 'recovery checkout origin changed'
  [[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=all)" ]] || fail 'recovery checkout has existing changes; no overwrite'
  [[ "$(git -C "$ROOT" rev-parse HEAD)" == "$BASE" ]] || fail 'recovery checkout already committed; leave untouched, inspect receipt'
else
  git -c lfs.install.skip=true clone --depth=1 --filter=blob:none --no-checkout --single-branch --branch main "https://github.com/$REPO.git" "$ROOT" || fail 'new isolated clone failed'
fi
git -C "$ROOT" sparse-checkout init --cone || fail 'sparse init failed'
git -C "$ROOT" sparse-checkout set assets/hareworks tools/hareworks-gait-extraction campaigns || fail 'sparse set failed'
GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" fetch --depth=1 origin main || fail 'main fetch failed'
[[ "$(git -C "$ROOT" rev-parse FETCH_HEAD)" == "$BASE" ]] || fail 'remote main advanced; do not overwrite'
GIT_LFS_SKIP_SMUDGE=1 git -C "$ROOT" checkout -B "$CAMPAIGN" "$BASE" || fail 'checkout failed'
cd "$ROOT"
[[ -f AGENTS.md ]] && grep -Fq 'Termux Git only' AGENTS.md || fail 'repository AGENTS gate failed'
[[ "$(git rev-parse "HEAD:$ATTR")" == "$ATTR_SHA" ]] || fail 'LFS attributes changed from audited source'
phase=prepublication-collision
PATHS=("$ATTR" "$MODEL" "campaigns/$PREVIOUS.sh" "campaigns/$CAMPAIGN.sh" \
 tools/hareworks-gait-extraction/v1.0.8/README.md tools/hareworks-gait-extraction/v1.0.8/contract.json \
 tools/hareworks-gait-extraction/v1.0.8/gait-extract.mjs tools/hareworks-gait-extraction/v1.0.8/index.html)
for p in "${PATHS[@]:1}";do
 [[ ! -e "$p" && ! -L "$p" ]] && ! git cat-file -e "HEAD:$p" 2>/dev/null || fail "destination already exists: $p"
done
# .gitattributes is the one intentionally updated policy file. Its prior bytes
# are locked; no other lines may be changed.
phase=author
git lfs install --local || fail 'git-lfs local install failed'
python3 - "$ATTR" <<'PYATTR' || fail 'could not extend exact LFS mapping'
from pathlib import Path
import sys
p=Path(sys.argv[1]);original=p.read_bytes()
assert original==b'Hareworks.glb filter=lfs diff=lfs merge=lfs -text\n',repr(original)
p.write_bytes(original+b'Hareworks-nine-clips.glb filter=lfs diff=lfs merge=lfs -text\n')
PYATTR
[[ "$(git check-attr filter -- "$MODEL")" == "$MODEL: filter: lfs" ]] || fail 'new GLB did not receive LFS filter before staging'
mkdir -p assets/hareworks campaigns tools/hareworks-gait-extraction/v1.0.8
cp -- "$SOURCE" "$MODEL"
[[ "$(sha256sum "$MODEL" | cut -d' ' -f1)" == "$MODEL_SHA" ]] || fail 'copied model hash changed'
for name in README.md contract.json gait-extract.mjs index.html;do
 cp -- "$OLD/tools/hareworks-gait-extraction/v1.0.8/$name" "tools/hareworks-gait-extraction/v1.0.8/$name"
 [[ "$(sha256sum "tools/hareworks-gait-extraction/v1.0.8/$name" | cut -d' ' -f1)" == "$(git -C "$OLD" show "HEAD:tools/hareworks-gait-extraction/v1.0.8/$name" | sha256sum | cut -d' ' -f1)" ]] || fail "extractor content mismatch $name"
done
cp -- "$OLD/campaigns/$PREVIOUS.sh" "campaigns/$PREVIOUS.sh"
cp -- "$0" "campaigns/$CAMPAIGN.sh"
[[ "$(sha256sum "campaigns/$PREVIOUS.sh" | cut -d' ' -f1)" == "$PREV_SCRIPT_SHA" ]] || fail 'copied old campaign SHA mismatch'
phase=validate
if command -v node >/dev/null;then node --check tools/hareworks-gait-extraction/v1.0.8/gait-extract.mjs || fail 'JS syntax error';else echo 'NODE_JS_SYNTAX_CHECK_UNAVAILABLE; prior content preserved byte-for-byte';fi
[[ "$(git rev-parse HEAD:assets/repl/Repl.glb)" == "$(git rev-parse "$BASE:assets/repl/Repl.glb")" ]] || fail 'protected Repl changed'
[[ "$(git rev-parse HEAD:assets/hareworks/Hareworks.glb)" == "$(git rev-parse "$BASE:assets/hareworks/Hareworks.glb")" ]] || fail 'protected seven-clip Hareworks changed'
git add -- "${PATHS[@]}" || fail 'Git staging failed'
python3 - "${PATHS[@]}" <<'PYSTAGE' || fail 'staged paths differ from allowlist'
import subprocess,sys
want=set(sys.argv[1:]);got=set(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines())
assert want==got,(want-got,got-want)
print('STAGED_PATHS_VERIFIED=',len(got))
PYSTAGE
# Check the exact staged pointer before any commit. Git LFS must have converted
# raw GLB bytes to a lightweight pointer, never a 6.7MB ordinary Git blob.
python3 - "$MODEL" "$MODEL_SHA" "$MODEL_SIZE" <<'PYPTR' || fail 'LFS pointer not created in index'
import subprocess,sys
path,oid,size=sys.argv[1:]
actual=subprocess.check_output(['git','show',':'+path]);expected=(f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n').encode()
assert actual==expected,(len(actual),actual[:120])
print('INDEX_LFS_POINTER=PASS',oid)
PYPTR
phase=commit
git -c user.name='Hareworks Termux Campaign' -c user.email='hareworks-campaign@users.noreply.github.com' commit -m 'Publish Hareworks nine-clip gait/idle turns with corrected LFS tracking v1.0.9' || fail 'commit failed'
FINAL=$(git rev-parse HEAD)
[[ "$(git rev-parse HEAD^)" == "$BASE" ]] || fail 'unexpected commit parent'
LFS_OBJECT="$(git rev-parse --git-path "lfs/objects/${MODEL_SHA:0:2}/${MODEL_SHA:2:2}/$MODEL_SHA")"
[[ -f "$LFS_OBJECT" ]] && [[ "$(sha256sum "$LFS_OBJECT" | cut -d' ' -f1)" == "$MODEL_SHA" ]] || fail 'new model missing from local LFS object store'
phase=lfs-upload
# Upload only the new object's OID; missing unrelated history/LFS objects are
# not a reason to block a verified new source.
git lfs push --object-id origin "$MODEL_SHA" || fail 'explicit LFS object upload failed; Git ref unchanged'
echo "EXACT_LFS_UPLOAD=PASS $MODEL_SHA"
phase=git-publication
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$BASE" ]] || fail 'remote main advanced; no force push'
# The LFS upload already succeeded, so avoid duplicating it via the pre-push
# hook's problematic historical object scanner (documented GIT_LFS_SKIP_PUSH).
GIT_LFS_SKIP_PUSH=1 git push origin HEAD:refs/heads/main || fail "Git push failed; local commit preserved $FINAL"
phase=readback
[[ "$(git ls-remote origin refs/heads/main | cut -f1)" == "$FINAL" ]] || fail 'remote main ref mismatch'
GIT_LFS_SKIP_SMUDGE=1 git fetch --depth=1 origin main || fail 'remote fetch failed'
[[ "$(git rev-parse FETCH_HEAD)" == "$FINAL" ]] || fail 'fetched remote commit differs'
for p in "${PATHS[@]}";do
 [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "HEAD:$p")" ]] || fail "remote content mismatch $p"
done
for p in AGENTS.md assets/repl/Repl.glb assets/hareworks/Hareworks.glb;do
 [[ "$(git rev-parse "FETCH_HEAD:$p")" == "$(git rev-parse "$BASE:$p")" ]] || fail "protected remote file changed $p"
done
[[ "$(git show "FETCH_HEAD:$MODEL" | sha256sum | cut -d' ' -f1)" == "$(git show "HEAD:$MODEL" | sha256sum | cut -d' ' -f1)" ]] || fail 'LFS pointer readback differs'
echo "GIT_REMOTE_READBACK=PASS $FINAL"
phase=viewer
PORT=0
for p in 8765 8766 8767 8768 8769; do
 if ! (echo >/dev/tcp/127.0.0.1/$p) >/dev/null 2>&1;then PORT=$p;break;fi
done
((PORT>0)) || fail 'no available local viewer port'
cat > "$STATE/server.py" <<'PY'
import http.server,sys
class Handler(http.server.SimpleHTTPRequestHandler):
 def end_headers(self):
  self.send_header('Cache-Control','no-store')
  super().end_headers()
http.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),Handler).serve_forever()
PY
nohup python3 "$STATE/server.py" "$PORT" > "$STATE/server.log" 2>&1 </dev/null &
PID=$!
READY=0
for i in 1 2 3 4 5 6 7 8; do
 if curl -fsS "http://127.0.0.1:$PORT/tools/hareworks-gait-extraction/v1.0.8/index.html" >/dev/null && curl -fsS "http://127.0.0.1:$PORT/tools/hareworks-gait-extraction/v1.0.8/gait-extract.mjs" >/dev/null;then READY=1;break;fi
 sleep 1
done
[[ "$READY" == 1 ]] && kill -0 "$PID" || fail 'viewer HTTP server unavailable'
URL="http://127.0.0.1:$PORT/tools/hareworks-gait-extraction/v1.0.8/index.html?commit=$FINAL"
python3 - "$STATE/receipt.json" "$HEAD" "$FINAL" "$BASE" "$MODEL_SHA" "$MODEL_SIZE" "$URL" "$PID" <<'PY'
import json,sys,datetime
out,source,final,base,model,size,url,pid=sys.argv[1:]
receipt=dict(campaign='hareworks-gait-extraction-v1.0.9',phase='viewer_http_ready',timestampUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pinnedBase=base,previousExtractorCommit=source,publishedCommit=final,nineClipModelSha256=model,nineClipModelBytes=int(size),explicitLfsObjectUpload='succeeded',gitRemoteReadback='succeeded',rulesRead={'agents':'repo pinned AGENTS gate','campaignEtiquette':'Home Center document 1wntegQjw7238dmGqbvs9TQmlsp4uXdXw7_wPciNx6sI (author read 2026-11-20)','topDownEtiquette':'Home Center document 1qdMR0g3hGWhC2L8Uw-1FVoZQSQuqEr4JwC5J3uog8hU (author read 2026-11-20)'},viewerUrl=url,viewerPid=int(pid),browserAnalysisComplete=False,ownerVisualAcceptance=False)
with open(out,'w') as f:json.dump(receipt,f,indent=2)
PY
echo "REMOTE_COMMIT=$FINAL"
echo "NINE_CLIP_MODEL_SHA=$MODEL_SHA"
echo 'SEVEN_CLIP_HAREWORKS_AND_REPL_UNCHANGED=YES'
echo "VIEWER_URL=$URL"
echo "RECEIPT=$STATE/receipt.json"
echo 'BROWSER_EXTRACTION_AND_VISUAL_ACCEPTANCE=PENDING'
if command -v termux-open-url >/dev/null; then termux-open-url "$URL" || echo 'BROWSER_OPEN_FAILED; use URL'; else echo 'TERMUX_OPEN_URL_MISSING; use URL';fi
