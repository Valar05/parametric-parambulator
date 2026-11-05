#!/data/data/com.termux/files/usr/bin/bash
# Heavy1 v1.5.2 recovery entrypoint. Existing v1.5.1 Blender IK source is immutable.
# Executed only through the owner's Termux Git lane. No direct ChatGPT Git writes.
set -Eeuo pipefail
VERSION='OBSIDIANTI_HEAVY1_BLENDER_IK_RECOVERY_v1.5.2'
BASE='OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.1'
PIN='e5ff174d734fcfdfa9ed6a297e9f5ba56c3587e3'
ROOT_AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
REL='campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RECOVERY_v1.5.2_LAUNCH.sh'
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GIT_LFS_SKIP_SMUDGE=1 GIT_TERMINAL_PROMPT=0
umask 077
[[ -n "${PREFIX:-}" && -x "$PREFIX/bin/bash" ]] || { echo 'BLOCKED_NOT_TERMUX'; exit 2; }
for cmd in git python3 sha256sum; do command -v "$cmd" >/dev/null || { echo "BLOCKED_MISSING_TOOL=$cmd"; exit 2; }; done
SELF="$(readlink -f "${BASH_SOURCE[0]}")"; [[ -f "$SELF" ]] || exit 2
SELF_SHA="$(sha256sum "$SELF" | cut -d' ' -f1)"
RUNID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
STATE="$HOME/.local/state/$VERSION/$RUNID"
mkdir -p "$STATE"
OUT="$HOME/storage/downloads"; [[ -d "$OUT" ]] || OUT="$STATE"
LOG="$OUT/${VERSION}_${RUNID}_OPERATOR.log"
exec > >(tee -a "$LOG") 2>&1
RECEIPT="$OUT/${VERSION}_${RUNID}_RECEIPT.json"
STAGE='BOOT'; ERR=''; RUN_RC=99
REPO="$STATE/repo"; PACKET="$STATE/packet"
receipt() {
  export HC_STAGE="$STAGE" HC_ERROR="$ERR" HC_RC="$RUN_RC" HC_SELF_SHA="$SELF_SHA" HC_RECEIPT="$RECEIPT" HC_RUNID="$RUNID" HC_PIN="$PIN" HC_MODEL_SHA="$MODEL_SHA" HC_LOG="$LOG"
  python3 - <<'PY'
import json,os,pathlib,datetime
p=pathlib.Path(os.environ['HC_RECEIPT']); obj={
 'campaign':'OBSIDIANTI_HEAVY1_BLENDER_IK_RECOVERY_v1.5.2',
 'authority':'TERMUX_GIT_ONLY','stage':os.environ['HC_STAGE'],
 'error':os.environ['HC_ERROR'],'exitCode':int(os.environ['HC_RC']),
 'sourceCommitPinned':os.environ['HC_PIN'],'sourceModelSHA256':os.environ['HC_MODEL_SHA'],
 'launcherSHA256':os.environ['HC_SELF_SHA'],'runId':os.environ['HC_RUNID'],
 'log':os.environ['HC_LOG'],'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'modelPublication':'NOT_VERIFIED_BY_THIS_WRAPPER','ownerVisualApproval':False}
q=p.with_suffix('.tmp');q.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');q.replace(p)
PY
}
on_exit() {
  local rc="$?"
  if (( rc != 0 )); then RUN_RC="$rc"; [[ -n "$ERR" ]] || ERR="FAILED_AT_${STAGE}"; fi
  receipt || true
  echo "RECOVERY_STAGE=$STAGE"
  echo "RECOVERY_ERROR=${ERR:-NONE}"
  echo "OPERATOR_LOG=$LOG"
  echo "RECOVERY_RECEIPT=$RECEIPT"
  echo "RECOVERY_EXIT=$RUN_RC"
}
trap on_exit EXIT
trap 'ERR="INTERRUPTED"; exit 130' INT TERM
printf 'CAMPAIGN=%s\nAUTHORITY=TERMUX_GIT_ONLY\nLAUNCH_SHA256=%s\nRUN_ID=%s\n' "$VERSION" "$SELF_SHA" "$RUNID"
STAGE='PINNED_CLONE'
git clone --depth=50 --branch=main --single-branch --config filter.lfs.smudge= --config filter.lfs.required=false "$REMOTE" "$REPO"
REMOTE_HEAD="$(git -C "$REPO" rev-parse HEAD)"
echo "RESOLVED_REPO=$REPO"
echo "BRANCH=$(git -C "$REPO" branch --show-current)"
echo "HEAD=$REMOTE_HEAD"
[[ "$REMOTE_HEAD" == "$PIN" ]] || { ERR="REMOTE_ADVANCED_REVIEW_REQUIRED:$REMOTE_HEAD"; exit 2; }
[[ "$(git -C "$REPO" rev-parse HEAD:AGENTS.md)" == "$ROOT_AGENTS_BLOB" ]] || { ERR='PINNED_AGENTS_MISMATCH'; exit 2; }
[[ "$(git -C "$REPO" status --porcelain --untracked-files=all)" == '' ]] || { ERR='ISOLATED_CLONE_DIRTY'; exit 2; }
# Confirm the authorized canonical model pointer without downloading or modifying it.
MODEL_POINTER="$(git -C "$REPO" show HEAD:assets/obsidianti/Obsidianti.glb)"
[[ "$MODEL_POINTER" == *"oid sha256:$MODEL_SHA"* ]] || { ERR='CANONICAL_MODEL_POINTER_CHANGED'; exit 2; }
# Preserve immutable original test, Blender and GLB apply code. New entrypoint is the only Git change.
STAGE='PREPUBLICATION_COLLISION_GATE'
[[ ! -e "$REPO/$REL" ]] || { ERR='RECOVERY_ENTRYPOINT_COLLISION'; exit 2; }
mkdir -p "$(dirname "$REPO/$REL")"
cp "$SELF" "$REPO/$REL"
[[ "$(sha256sum "$REPO/$REL"|cut -d' ' -f1)" == "$SELF_SHA" ]] || { ERR='COPIED_ENTRYPOINT_SHA_MISMATCH'; exit 2; }
STAGE='PUBLISH_RECOVERY_ENTRYPOINT'
git -C "$REPO" config user.name "Obsidianti Termux Campaign"
git -C "$REPO" config user.email 'obsidianti-campaign@users.noreply.github.com'
git -C "$REPO" add -- "$REL"
[[ "$(git -C "$REPO" diff --cached --name-only)" == "$REL" ]] || { ERR='UNAUTHORIZED_STAGED_PATH'; exit 2; }
git -C "$REPO" commit -m 'Obsidianti Heavy1: recover clean-source stage with bytecode-disabled Termux runner'
COMMIT="$(git -C "$REPO" rev-parse HEAD)"
git -C "$REPO" push origin HEAD:refs/heads/main || { ERR='GIT_PUSH_REJECTED_NO_FORCE'; exit 2; }
HEAD_READBACK="$(git -C "$REPO" ls-remote origin refs/heads/main | cut -f1)"
[[ "$HEAD_READBACK" == "$COMMIT" ]] || { ERR='GIT_REMOTE_READBACK_MISMATCH'; exit 2; }
echo "RECOVERY_ENTRYPOINT_COMMIT=$COMMIT"
# Generate a valid packet from exact already-published v1.5.1 Git sources.
STAGE='REASSEMBLE_COMMITTED_V151_PACKET'
mkdir -p "$PACKET"
for rel in \
  campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.1.py \
  campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.1.py \
  campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.1.py \
  tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.1.py \
  docs/obsidianti/HEAVY1_BLENDER_IK_v1.5.1.md \
  review/obsidianti-heavy1-blender-ik-v1.5.1.html; do
  [[ -f "$REPO/$rel" ]] || { ERR="SOURCE_FILE_MISSING:$rel"; exit 2; }
  mkdir -p "$(dirname "$PACKET/$rel")"
  cp "$REPO/$rel" "$PACKET/$rel"
done
python3 - "$PACKET" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]); files={}
for x in p.rglob('*'):
 if x.is_file():files[str(x.relative_to(p))]=hashlib.sha256(x.read_bytes()).hexdigest()
(p/'manifest.json').write_text(json.dumps({'campaign':'OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.1','files':files},indent=2,sort_keys=True)+'\n')
assert len(files)==6
PY
# Native IK and real skinned geometry are run by the original committed engine.
# Disabling Python bytecode protects its clean-source gate WITHOUT deleting files.
STAGE='RESUME_ACTUAL_BLENDER_IK'
set +e
python3 "$REPO/campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.1.py" --packet "$PACKET"
RUN_RC=$?
set -e
if (( RUN_RC != 0 )); then ERR='V151_RUNNER_FAILED_SEE_ITS_FULL_RECEIPT';exit "$RUN_RC"; fi
STAGE='RUNNER_COMPLETED_VISUAL_VERDICT_PENDING'
echo 'STATUS=HEAVY1_NATIVE_BLENDER_IK_RUNNER_RETURNED_SUCCESS'
echo 'OWNER_VISUAL_ACCEPTANCE=PENDING'
RUN_RC=0
