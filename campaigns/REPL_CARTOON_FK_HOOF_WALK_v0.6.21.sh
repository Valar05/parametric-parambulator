#!/data/data/com.termux/files/usr/bin/bash
# Repl v0.6.21 exact-binary, visually reviewed, anatomically corrected walk.
# The operator only runs this Termux entrypoint; all Git writes stay in Termux.
set -Eeuo pipefail
CAMPAIGN='REPL_CARTOON_FK_HOOF_WALK'
VERSION='0.6.21'
EXPECTED_HEAD='d0f3d99717a4e83d15d43fb8818786ecc21057ab'
EXPECTED_SOURCE='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
EXPECTED_MODEL='50d26053027296895fd8853e7337a1fcbfba8e77a63aea095680b19b3d113dd4'
EXPECTED_AGENTS_BLOB='4be065f641da680a932af891fa1d697cc6d48bbd'
MODEL_PATH='assets/repl/Repl.glb'
META_PATH='assets/repl/CANONICAL_MODEL.json'
SCRIPT_PATH='campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.21.sh'
ZIP="${1:?Please pass the downloaded SHA-checked v0.6.21 ZIP}"
DOWNLOADS="$HOME/storage/downloads"
BASE="$HOME/.local/share/repl-campaigns/cartoon-fk-hoof-v0.6.21"
CACHE="$HOME/.local/share/repl-campaigns/cartoon-fk-hoof-v0.6.20/repo"
REPO="$BASE/repo"
LOG="$DOWNLOADS/REPL_CARTOON_FK_HOOF_WALK_v0.6.21_OPERATOR.log"
mkdir -p "$DOWNLOADS" "$BASE"
exec > >(tee -a "$LOG") 2>&1
status='BLOCKED_OR_FAILED'
trap 'rc=$?; if ((rc != 0)); then echo "CAMPAIGN_STATUS=$status"; echo "TERMUX_DRIVER_EXIT=$rc"; echo "FULL_OPERATOR_LOG=$LOG"; fi' EXIT
fail(){ echo "BLOCKED=$*"; exit 2; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
echo "CAMPAIGN=$CAMPAIGN"
echo "VERSION=$VERSION"
echo 'LANE=TERMUX_GIT_ONLY'
echo "ZIP=$ZIP"
echo "ZIP_SHA256=$(sha "$ZIP")"
echo "EXPECTED_CANONICAL_SOURCE=$EXPECTED_SOURCE"
echo "EXPECTED_CANDIDATE=$EXPECTED_MODEL"
echo "FULL_OPERATOR_LOG=$LOG"

# Atomic private extraction; exact manifest members only; no folder traversal.
PACKET="$BASE/verified_packet"
if [[ ! -e "$PACKET" ]]; then
  TMP="$BASE/packet.stage.$$"; mkdir -p "$TMP"
  python3 - "$ZIP" "$TMP" <<'PY'
import hashlib,json,sys,zipfile,pathlib
z=zipfile.ZipFile(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);prefix='REPL_CARTOON_FK_HOOF_WALK_v0.6.21/'
manifest=json.loads(z.read(prefix+'manifest.json'))
assert set(z.namelist())=={prefix+'manifest.json'}|{prefix+name for name in manifest['members']},'ZIP_MEMBER_SET'
for name,digest in manifest['members'].items():
    assert name and not name.startswith('/') and '..' not in pathlib.PurePosixPath(name).parts,'ZIP_PATH'
    b=z.read(prefix+name);assert hashlib.sha256(b).hexdigest()==digest,'MEMBER_SHA:'+name
    p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PACKET_MEMBER_HASHES=PASS',len(manifest['members']))
PY
  mv "$TMP" "$PACKET"
fi
# Reruns must independently recheck the packet directory, not blindly trust it.
python3 - "$PACKET" <<'PY'
import sys,json,hashlib,pathlib
p=pathlib.Path(sys.argv[1]);m=json.loads((p/'manifest.json').read_text())
for name,h in m['members'].items():
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==h,'CACHE_MEMBER_MISMATCH:'+name
print('PACKET_READBACK_HASHES=PASS')
PY
[[ "$(sha "$PACKET/payload/Repl.glb")" == "$EXPECTED_MODEL" ]] || fail 'CANDIDATE_MODEL_SHA'

# Safe, isolated, source-verified checkout; never touch the operator's working tree.
if [[ ! -e "$REPO/.git" ]]; then
  [[ ! -e "$REPO" ]] || fail 'CHECKOUT_PATH_COLLISION'
  if [[ -d "$CACHE/.git" && -z "$(git -C "$CACHE" status --porcelain)" ]]; then
    ORIGIN="$(git -C "$CACHE" remote get-url origin)" || fail 'CACHE_HAS_NO_ORIGIN'
    git clone --quiet --no-hardlinks "$CACHE" "$REPO" || fail 'VERIFIED_CACHE_CLONE'
    git -C "$REPO" remote set-url origin "$ORIGIN"
    echo 'CHECKOUT=VERIFIED_CACHE_CLONE'
  else
    fail 'NO_VERIFIED_V0620_CACHE; refusing to modify user checkout'
  fi
fi
[[ -z "$(git -C "$REPO" status --porcelain)" ]] || fail 'DIRTY_ISOLATED_CHECKOUT'
for attempt in 1 2 3; do
 if git -C "$REPO" fetch --quiet origin main; then break; fi
 if ((attempt==3)); then fail 'GIT_FETCH_ORIGIN_AFTER_RETRIES'; fi
 sleep "$attempt"
done
HEAD="$(git -C "$REPO" rev-parse HEAD)"
ORIGIN_MAIN="$(git -C "$REPO" rev-parse refs/remotes/origin/main)"
echo "CHECKOUT_HEAD=$HEAD"
echo "ORIGIN_MAIN=$ORIGIN_MAIN"
# For a resumed launch after a push, explicitly recognize success by remote bytes.
if [[ "$ORIGIN_MAIN" != "$EXPECTED_HEAD" ]]; then
  if [[ "$(git -C "$REPO" show "origin/main:$MODEL_PATH" | sha256sum | awk '{print $1}')" == "$EXPECTED_MODEL" ]] && \
     git -C "$REPO" show 'origin/main:AGENTS.md' | grep -q 'Repl owner-authorized anatomical front-cannon gait correction'; then
    echo "REMOTE_READBACK_SHA=$ORIGIN_MAIN"
    echo 'REMOTE_MODEL_SHA256=PASS'
    echo 'CAMPAIGN_STATUS=CANONICAL_ASSET_UPDATED_AWAITING_OWNER_VISUAL_ACCEPTANCE'
    status='SUCCESS';exit 0
  fi
  fail 'REMOTE_MAIN_HAS_NEW_UNKNOWN_WORK; source review needed'
fi
[[ "$HEAD" == "$EXPECTED_HEAD" ]] || fail 'CACHE_HEAD_STALE_OR_DIVERGED'
[[ "$(sha "$REPO/$MODEL_PATH")" == "$EXPECTED_SOURCE" ]] || fail 'WRONG_CANONICAL_MODEL'
[[ "$(git -C "$REPO" rev-parse HEAD:AGENTS.md)" == "$EXPECTED_AGENTS_BLOB" ]] || fail 'AGENTS_REVISION_MISMATCH'
[[ ! -e "$REPO/$SCRIPT_PATH" ]] || fail 'VERSIONED_SCRIPT_NAME_COLLISION'
# The binary validator runs on the *exact* binary that was geometrically checked and rendered.
python3 "$PACKET/campaign/verify_structure.py" "$REPO/$MODEL_PATH" "$PACKET/payload/Repl.glb" || fail 'STRUCTURAL_GATE'
# When existing scientific packages are available, replay true-skinned half-frame physics on this device.
if python3 -c 'import numpy, scipy' >/dev/null 2>&1; then
  python3 "$PACKET/campaign/verify_physics.py" "$REPO/$MODEL_PATH" "$PACKET/payload/Repl.glb" "$BASE/physical_check.json" || fail 'PHYSICS_GATE'
  echo 'DEVICE_PHYSICS=FULL_SKINNED_HALF_FRAME_VERIFIED'
else
  # We do not install dependencies or claim this gate ran. Exact binary SHA
  # pins the candidate to the author's completed 768-sample physical audit.
  python3 - "$PACKET/review/local_physics_receipt.json" <<'PY'
import json,sys
j=json.load(open(sys.argv[1]));assert j['source_sha256']=='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1';assert j['candidate_sha256']=='50d26053027296895fd8853e7337a1fcbfba8e77a63aea095680b19b3d113dd4';assert j['half_frame_samples']>=768 and j['full_trajectory_samples']>=1158
print('HOST_REAL_GLB_GEOMETRY_EVIDENCE=SHA_PINNED')
PY
  echo 'DEVICE_PHYSICS=NOT_RERUN_NUMPY_SCIPY_UNAVAILABLE'
fi

# All changes are scoped to one existing canonical GLB, its metadata, AGENTS,
# and one NEW versioned campaign source. Nothing touches any other project.
mkdir -p "$REPO/campaigns"
cp "$PACKET/campaigns/REPL_CARTOON_FK_HOOF_WALK_v0.6.21.sh" "$REPO/$SCRIPT_PATH"
python3 - "$REPO/AGENTS.md" "$PACKET/AGENTS_ADDENDUM.md" "$REPO/$META_PATH" <<'PY'
import sys,json,pathlib
agents,add,meta=map(pathlib.Path,sys.argv[1:]);base=agents.read_text();note=add.read_text()
assert '## 2026-11-02 — Repl owner-authorized anatomical front-cannon gait correction' not in base
agents.write_text(base.rstrip()+'\n'+note)
m=json.loads(meta.read_text());old=m['active_model'];oldsha=old['sha256']
assert oldsha=='c6dc250356248e5860e5919568e4103d6c1d2cb6e071e7bb9a0f7ce1f42ee4c1'
m['prior_accepted_motion_snapshot']={'version':old['version'],'sha256':oldsha,'git_blob_sha1':old.get('git_blob_sha1'),'review':'BEST_YET_NOT_VISUALLY_APPROVED'}
m['active_model']={
 'version':'0.6.21','path':'assets/repl/Repl.glb','campaign':'REPL_CARTOON_FK_HOOF_WALK',
 'sha256':'50d26053027296895fd8853e7337a1fcbfba8e77a63aea095680b19b3d113dd4',
 'source_sha256':oldsha,'git_blob_sha1':'92b7cd8b9e8385372ccd1b0121a5a948a5fceabd','animations':6,'joint_count':50,'node_count':53,
 'controlled_bones':['Bone_013','Bone_014','Bone_015','Bone_019','Bone_020','Bone_021'],
 'preserved_hoof_end_bones':['Bone_012','Bone_018'],
 'all_non_walk_tracks':'BYTE_IDENTICAL_TO_v0.6.17',
 'root_hindlegs_mane_tail_skin_mesh':'UNCHANGED_FROM_v0.6.17',
 'physical_check':'FULL_SKINNED_HALF_FRAME_VERIFIED_ON_EXACT_SOURCE_AND_CANDIDATE',
 'owner_visual_acceptance':'PENDING'}
m['status']='MODEL_PUBLISHED_PENDING_OWNER_VISUAL_ACCEPTANCE'
meta.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
PY
# Atomic replacement of only the canonical asset. Git history retains the baseline.
TEMP_MODEL="$REPO/assets/repl/.Repl.v0.6.21.stage.$$.glb"
cp "$PACKET/payload/Repl.glb" "$TEMP_MODEL"
[[ "$(sha "$TEMP_MODEL")" == "$EXPECTED_MODEL" ]] || fail 'STAGED_MODEL_SHA'
mv "$TEMP_MODEL" "$REPO/$MODEL_PATH"
[[ "$(sha "$REPO/$MODEL_PATH")" == "$EXPECTED_MODEL" ]] || fail 'CANONICAL_MODEL_READBACK_SHA'
# Before staging, enforce exact approved path list; never commit unrelated files.
git -C "$REPO" add -- AGENTS.md "$META_PATH" "$MODEL_PATH" "$SCRIPT_PATH"
python3 - "$REPO" "$META_PATH" "$MODEL_PATH" "$SCRIPT_PATH" <<'PY'
import subprocess,sys
repo,meta,model,script=sys.argv[1:];p=subprocess.run(['git','-C',repo,'diff','--cached','--name-only'],capture_output=True,text=True,check=True)
expected={'AGENTS.md',meta,model,script};actual=set(p.stdout.splitlines())
assert actual==expected,('STAGED_PATH_SCOPE',actual,expected)
print('GIT_STAGED_EXACT_ALLOWED_PATHS=PASS')
PY
if ! git -C "$REPO" config user.email >/dev/null; then git -C "$REPO" config user.email 'repl-termux@localhost';fi
if ! git -C "$REPO" config user.name >/dev/null; then git -C "$REPO" config user.name 'Repl Termux Campaign';fi
git -C "$REPO" commit --quiet -m 'Improve Repl foreleg support, level hoof and natural swing v0.6.21'
NEW_HEAD="$(git -C "$REPO" rev-parse HEAD)"
echo "MODEL_COMMIT=$NEW_HEAD"
if ! git -C "$REPO" push origin HEAD:refs/heads/main; then
  REMOTE_NOW="$(git -C "$REPO" ls-remote origin refs/heads/main | awk '{print $1}')"
  [[ "$REMOTE_NOW" == "$NEW_HEAD" ]] || fail 'GIT_PUSH_FAILED_NEW_LOCAL_COMMIT_PRESERVED'
fi
# Read back the remote commit and exact canonical Git blob, not merely push exit.
for attempt in 1 2 3; do
 git -C "$REPO" fetch --quiet origin main || true
 SEEN="$(git -C "$REPO" ls-remote origin refs/heads/main | awk '{print $1}')"
 if [[ "$SEEN" == "$NEW_HEAD" ]]; then break;fi
 sleep "$attempt"
done
[[ "$SEEN" == "$NEW_HEAD" ]] || fail 'REMOTE_MAIN_READBACK_MISMATCH'
LOCAL_BLOB="$(git -C "$REPO" rev-parse HEAD:"$MODEL_PATH")"
REMOTE_BLOB="$(git -C "$REPO" rev-parse origin/main:"$MODEL_PATH")"
[[ "$LOCAL_BLOB" == "$REMOTE_BLOB" ]] || fail 'REMOTE_MODEL_GIT_BLOB_MISMATCH'
[[ "$(git -C "$REPO" show origin/main:"$MODEL_PATH" | sha256sum | awk '{print $1}')" == "$EXPECTED_MODEL" ]] || fail 'REMOTE_CANONICAL_MODEL_SHA'
echo "REMOTE_READBACK_SHA=$SEEN"
echo "REMOTE_MODEL_GIT_BLOB=$REMOTE_BLOB"
echo "REMOTE_MODEL_SHA256=$EXPECTED_MODEL"
# Review image is published to Downloads without requiring another ferry task.
REVIEW="$DOWNLOADS/Repl-v0.6.21-before-after.png"
if [[ ! -f "$REVIEW" ]]; then cp "$PACKET/review/Repl_before_after.png" "$REVIEW";fi
[[ "$(sha "$REVIEW")" == "$(sha "$PACKET/review/Repl_before_after.png")" ]] || fail 'REVIEW_IMAGE_READBACK_SHA'
command -v termux-media-scan >/dev/null && termux-media-scan "$REVIEW" >/dev/null 2>&1 || true
echo "REVIEW_IMAGE=$REVIEW"
echo 'MODEL_UPDATED=YES'
echo 'OWNER_VISUAL_ACCEPTANCE=PENDING'
echo 'CAMPAIGN_STATUS=CANONICAL_ASSET_UPDATED_AWAITING_OWNER_VISUAL_ACCEPTANCE'
status='SUCCESS'
