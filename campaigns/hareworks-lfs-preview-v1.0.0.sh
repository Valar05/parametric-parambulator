#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
CAMPAIGN='hareworks-lfs-preview-v1.0.0'
REPO='Valar05/parametric-parambulator'
EXPECTED_HEAD='e84bc6f95b8b03ddb640426f9a224e545851c935'
EXPECTED_SHA='4ee555a0e416e3b2d03290fea85fa5306f894b9b4a5e8feb3f41078d5eb7d828'
EXPECTED_BYTES=6484280
SOURCE="$HOME/storage/downloads/Meshy_AI_Hareworks_Field_Engineer_20261120_animated_mixamo_All_animation (2).glb"
DEST='assets/hareworks/Hareworks.glb'
STATE="$HOME/.local/state/hareworks/$CAMPAIGN"
mkdir -p "$STATE"
LOG="$STATE/run.log"; exec > >(tee -a "$LOG") 2>&1
step='preflight'; trap 'rc=$?; echo "BLOCKED step=$step rc=$rc line=$LINENO"; exit "$rc"' ERR
fail(){ echo "BLOCKED step=$step reason=$*"; exit 1; }
retry(){ local n=0; until "$@"; do n=$((n+1)); [ "$n" -lt 3 ] || return 1; sleep $((n*3)); done; }
step=dependencies
command -v git >/dev/null || fail 'git unavailable'
command -v python3 >/dev/null || fail 'python3 unavailable'
command -v git-lfs >/dev/null || { command -v pkg >/dev/null && pkg install -y git-lfs; }
command -v git-lfs >/dev/null || fail 'git-lfs unavailable'
command -v sha256sum >/dev/null || fail 'sha256sum unavailable'
step=source
[ -f "$SOURCE" ] || fail "source missing: $SOURCE"
[ "$(wc -c < "$SOURCE" | tr -d ' ')" = "$EXPECTED_BYTES" ] || fail 'source size mismatch'
[ "$(sha256sum "$SOURCE" | cut -d' ' -f1)" = "$EXPECTED_SHA" ] || fail 'source SHA mismatch'
python3 - "$SOURCE" <<'PY'
import sys,json,struct
b=open(sys.argv[1],'rb').read(); assert b[:4]==b'glTF'; assert struct.unpack_from('<I',b,8)[0]==len(b)
n=struct.unpack_from('<I',b,12)[0]; assert b[16:20]==b'JSON'; j=json.loads(b[20:20+n]); assert len(j['skins'][0]['joints'])==74
names=[a['name'] for a in j['animations']]
assert names==['Running','Walking','Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace','Walk_Backward','Walking_Woman','slide_right'],names
print('GLB_SOURCE_VALIDATED=YES 74_JOINTS 7_CLIPS')
PY
step=checkout
WORK="$STATE/work"
if [ -d "$WORK/.git" ]; then
  [ -z "$(git -C "$WORK" status --porcelain)" ] || fail 'existing campaign checkout dirty'
  [ "$(git -C "$WORK" remote get-url origin)" = "https://github.com/$REPO.git" ] || fail 'existing checkout origin differs'
else
  [ ! -e "$WORK" ] || fail 'work path occupied by non-repository'
  retry env GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "https://github.com/$REPO.git" "$WORK" || fail 'clone failed; check Termux GitHub authentication'
fi
cd "$WORK"
retry git fetch --depth 1 origin main || fail 'fetch failed'
HEAD="$(git rev-parse FETCH_HEAD)"
[ "$HEAD" = "$EXPECTED_HEAD" ] || fail "remote main moved: $HEAD; expected $EXPECTED_HEAD; refresh campaign rather than overwrite"
GIT_LFS_SKIP_SMUDGE=1 git checkout -B "campaign/$CAMPAIGN" "$HEAD" >/dev/null
[ -z "$(git status --porcelain)" ] || fail 'worktree dirty'
step=collision
[ ! -e "$DEST" ] && [ ! -e 'assets/hareworks/SOURCE.json' ] && [ ! -e 'viewer/hareworks/index.html' ] && [ ! -e "campaigns/$CAMPAIGN.sh" ] || fail 'one or more destination paths already exist; no overwrite'
[ ! -e 'assets/hareworks/.gitattributes' ] || fail 'LFS attributes path already exists'
CANONICAL_SHA="$(git rev-parse HEAD:assets/repl/Repl.glb 2>/dev/null || true)"
[ -n "$CANONICAL_SHA" ] || fail 'canonical Repl path missing'
AGENTS_BLOB="$(git rev-parse HEAD:AGENTS.md)"
# Read policy and canonical identity from the exact pinned revision before any mutation.
git show HEAD:AGENTS.md >/dev/null
git show HEAD:assets/repl/CANONICAL_MODEL.json >/dev/null || fail 'canonical model metadata missing'
step=write
mkdir -p assets/hareworks viewer/hareworks campaigns
cp "$SOURCE" "$DEST"
printf '%s\n' 'Hareworks.glb filter=lfs diff=lfs merge=lfs -text' > assets/hareworks/.gitattributes
python3 - <<'PY'
import json
p='assets/hareworks/SOURCE.json'
with open(p,'w') as f: json.dump({'name':'Hareworks Field Engineer','origin':'Meshy/Mixamo user-provided GLB','source_filename':'Meshy_AI_Hareworks_Field_Engineer_20261120_animated_mixamo_All_animation (2).glb','canonical_path':'assets/hareworks/Hareworks.glb','sha256':'4ee555a0e416e3b2d03290fea85fa5306f894b9b4a5e8feb3f41078d5eb7d828','bytes':6484280,'skin_joint_count':74,'animation_names':['Running','Walking','Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace','Walk_Backward','Walking_Woman','slide_right'],'source_status':'original unmodified; no procedural motion applied'},f,indent=2)
PY
cat > viewer/hareworks/index.html <<'HTML'
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hareworks source model review</title><style>html,body{margin:0;height:100%;background:#151b24;color:#f5f5f5;font:15px system-ui}#bar{position:absolute;z-index:2;top:8px;left:8px;right:8px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:#111b;padding:8px;border-radius:8px}button,select{padding:8px;background:#27394c;color:white;border:1px solid #74839a;border-radius:5px}canvas{display:block}#status{font-size:12px}#hint{position:absolute;bottom:10px;left:10px;background:#111b;padding:6px;border-radius:6px}</style><script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script></head><body><div id="bar"><strong>Hareworks • Original GLB</strong><select id="clips" aria-label="Animation"></select><button id="play">Pause</button><button id="camera">Top / 3⁄4</button><span id="status" role="status">Loading…</span></div><div id="hint">Drag to orbit • pinch to zoom • 7 original clips • not procedural IK</div><script type="module">
import * as THREE from 'three';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const status=document.getElementById('status'),sel=document.getElementById('clips'),scene=new THREE.Scene();scene.background=new THREE.Color(0x151b24);const camera=new THREE.PerspectiveCamera(40,innerWidth/innerHeight,.01,200),renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;document.body.appendChild(renderer.domElement);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;scene.add(new THREE.HemisphereLight(0xffffff,0x333844,2));const light=new THREE.DirectionalLight(0xffffff,2.8);light.position.set(4,8,5);scene.add(light);let mixer,actions=[],playing=true,top=false,center=new THREE.Vector3(),radius=1;const clock=new THREE.Clock();
new GLTFLoader().load('../../assets/hareworks/Hareworks.glb',g=>{scene.add(g.scene);g.scene.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(g.scene);box.getCenter(center);radius=Math.max(box.getSize(new THREE.Vector3()).length()*.65,.5);controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(radius*.65,radius*.65,radius*1.2));camera.near=Math.max(.001,radius/1000);camera.far=radius*100;camera.updateProjectionMatrix();controls.update();mixer=new THREE.AnimationMixer(g.scene);actions=g.animations.map((clip,i)=>{sel.add(new Option(clip.name||'Clip '+i,String(i)));return mixer.clipAction(clip)});if(actions.length)actions[0].play();status.textContent='Loaded '+g.animations.length+' clips • '+g.scene.children.length+' root objects';},p=>{status.textContent='Loading '+(p.total?Math.round(p.loaded/p.total*100)+'%':Math.round(p.loaded/1024)+' KB')},e=>{status.textContent='LOAD ERROR: '+e.message;console.error(e)});
sel.onchange=()=>{actions.forEach(a=>a.stop());actions[+sel.value]?.reset().play();playing=true;document.getElementById('play').textContent='Pause'};document.getElementById('play').onclick=()=>{playing=!playing;if(mixer)mixer.timeScale=playing?1:0;document.getElementById('play').textContent=playing?'Pause':'Play'};document.getElementById('camera').onclick=()=>{top=!top;camera.position.copy(center).add(top?new THREE.Vector3(0,radius*1.5,.001):new THREE.Vector3(radius*.65,radius*.65,radius*1.2));controls.update()};addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});function frame(){requestAnimationFrame(frame);const dt=Math.min(clock.getDelta(),.05);if(mixer)mixer.update(dt);controls.update();renderer.render(scene,camera)}frame();
</script></body></html>
HTML
cp "$0" "campaigns/$CAMPAIGN.sh"
step=lfs
git lfs install --local >/dev/null
git add -- assets/hareworks/.gitattributes "$DEST" assets/hareworks/SOURCE.json viewer/hareworks/index.html "campaigns/$CAMPAIGN.sh"
POINTER="$(git show :"$DEST")"
printf '%s' "$POINTER" | grep -q 'version https://git-lfs.github.com/spec/v1' || fail 'GLB not staged as LFS pointer'
printf '%s' "$POINTER" | grep -q "oid sha256:$EXPECTED_SHA" || fail 'LFS pointer OID mismatch'
[ "$(git diff --cached --name-only | wc -l | tr -d ' ')" = 5 ] || fail 'unexpected staged file count'
[ "$(git rev-parse HEAD:assets/repl/Repl.glb)" = "$CANONICAL_SHA" ] || fail 'Repl canonical changed'
step=commit
git -c user.name="Hareworks Campaign" -c user.email="hareworks-campaign@users.noreply.github.com" commit -m "Import Hareworks original seven-clip GLB via LFS and add preview" >/dev/null
NEW_HEAD="$(git rev-parse HEAD)"
step=publish
retry git push origin HEAD:refs/heads/main || fail 'push failed; retained local commit for safe recovery'
retry git fetch origin main || fail 'post-push fetch failed'
[ "$(git rev-parse FETCH_HEAD)" = "$NEW_HEAD" ] || fail 'remote main commit mismatch'
REMOTE_POINTER="$(git show FETCH_HEAD:"$DEST")"
printf '%s' "$REMOTE_POINTER" | grep -q "oid sha256:$EXPECTED_SHA" || fail 'remote LFS pointer mismatch'
[ "$(git rev-parse FETCH_HEAD:assets/repl/Repl.glb)" = "$CANONICAL_SHA" ] || fail 'remote Repl changed'
step=lfs_readback
# Confirm the LFS object can actually be downloaded from GitHub, not merely the pointer.
retry git lfs fetch origin "$NEW_HEAD" || fail 'remote LFS object fetch failed'
git lfs checkout "$DEST" >/dev/null
[ "$(sha256sum "$DEST" | cut -d' ' -f1)" = "$EXPECTED_SHA" ] || fail 'post-publish LFS object bytes mismatch'
step=viewer
PORT="$(python3 - <<'PY'
import socket
s=socket.socket();s.bind(('127.0.0.1',0));print(s.getsockname()[1]);s.close()
PY
)"
nohup python3 -m http.server "$PORT" --bind 127.0.0.1 > "$STATE/server.log" 2>&1 </dev/null & PID=$!
URL="http://127.0.0.1:$PORT/viewer/hareworks/index.html"
python3 - "$PORT" <<'PY'
import urllib.request,sys,time
u=f'http://127.0.0.1:{sys.argv[1]}/viewer/hareworks/index.html'
for _ in range(30):
 try:
  with urllib.request.urlopen(u,timeout=2) as r:
   if b'Hareworks' in r.read():break
 except Exception:time.sleep(.2)
else:raise SystemExit('VIEWER_SERVER_NOT_RESPONDING')
PY
export STATE CAMPAIGN EXPECTED_SHA EXPECTED_HEAD NEW_HEAD CANONICAL_SHA AGENTS_BLOB URL PID PORT
python3 - <<'PY'
import os,json,datetime
v={k:os.environ[k] for k in ('CAMPAIGN','EXPECTED_SHA','EXPECTED_HEAD','NEW_HEAD','CANONICAL_SHA','AGENTS_BLOB','URL','PID','PORT')};v.update({'status':'REMOTE_VERIFIED_VIEWER_HTTP_READY_OWNER_VISUAL_PENDING','repo':'Valar05/parametric-parambulator','model_path':'assets/hareworks/Hareworks.glb','lfs':True,'rules_read':'GitHub AGENTS.md and Home Center Campaign Etiquette read by campaign author; pinned AGENTS.md read at execution','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});p=os.path.join(os.environ['STATE'],'receipt.json');open(p,'w').write(json.dumps(v,indent=2));print('RECEIPT='+p)
PY
printf 'REMOTE_COMMIT=%s\nLFS_SHA256=%s\nGAME_VIEWER_URL=%s\nVIEWER_PID=%s\n' "$NEW_HEAD" "$EXPECTED_SHA" "$URL" "$PID"
command -v termux-open-url >/dev/null && termux-open-url "$URL" || true
