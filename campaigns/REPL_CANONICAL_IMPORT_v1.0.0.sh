#!/data/data/com.termux/files/usr/bin/bash
# REPL_CANONICAL_IMPORT v1.0.0
# ONE-TIME ORIGINAL SOURCE IMPORT ONLY. This does not pretend the source
# contains later accepted mane/tail controls or update their separate trials.
# The *only* production GLB output is assets/repl/Repl.glb in the remote repo.
set -Eeuo pipefail
export GIT_TERMINAL_PROMPT=0
CAMPAIGN='REPL_CANONICAL_IMPORT'
VERSION='1.0.0'
REPO_NAME='Valar05/parametric-parambulator'
REPO_URL='https://github.com/Valar05/parametric-parambulator.git'
BRANCH='main'
CANONICAL='assets/repl/Repl.glb'
SOURCE_SHA256='d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f'
SOURCE_BLOB='02840305b7a71356839294e376c6c166ae98a9fc'
SOURCE_SIZE='6352596'
PACKET_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$PACKET_ROOT/asset/Repl.glb"
SCRIPT="$PACKET_ROOT/campaign/termux_import.sh"
STATE="$HOME/.local/share/parametric-parambulator/canonical-import-v1.0.0"
CHECKOUT="$STATE/checkout"
DOWNLOADS="$HOME/storage/downloads"
[ -d "$DOWNLOADS" ] || DOWNLOADS="$HOME/Downloads"
RECEIPT="$DOWNLOADS/REPL_CANONICAL_IMPORT_v1.0.0_RECEIPT.txt"

say(){ printf '%s\n' "$*"; }
block(){ say "CAMPAIGN_STATUS=BLOCKED" "REASON=$1" "SOURCE_MODIFIED=NO" "REMOTE_CANONICAL_IMPORT=NOT_VERIFIED"; exit 2; }
shat(){ sha256sum -- "$1" | cut -d' ' -f1; }
command -v git >/dev/null || block 'GIT_UNAVAILABLE_IN_TERMUX'
command -v python3 >/dev/null || block 'PYTHON3_UNAVAILABLE_IN_TERMUX'
command -v sha256sum >/dev/null || block 'SHA256SUM_UNAVAILABLE_IN_TERMUX'
command -v mktemp >/dev/null || block 'MKTEMP_UNAVAILABLE_IN_TERMUX'
say "CAMPAIGN=$CAMPAIGN" "VERSION=$VERSION" "EXECUTION_LANE=TERMUX_GIT" "REPO=$REPO_NAME" "CANONICAL_PATH=$CANONICAL" \
    "IMPORT_SCRIPT=$SCRIPT" "IMPORT_SCRIPT_SHA256=$(shat "$SCRIPT")" \
    "PAYLOAD_PATH=$SOURCE" "PAYLOAD_EXPECTED_SHA256=$SOURCE_SHA256"
[ -f "$SOURCE" ] || block 'GLB_MISSING_FROM_VERIFIED_ZIP'
[ "$(stat -c %s -- "$SOURCE")" = "$SOURCE_SIZE" ] || block 'GLB_LENGTH_MISMATCH'
[ "$(shat "$SOURCE")" = "$SOURCE_SHA256" ] || block 'GLB_SOURCE_SHA256_MISMATCH'
[ "$(git hash-object --no-filters -- "$SOURCE")" = "$SOURCE_BLOB" ] || block 'GLB_GIT_BLOB_MISMATCH'
[ -f "$PACKET_ROOT/campaign/manifest.json" ] || block 'PACKET_MANIFEST_MISSING'
python3 - "$PACKET_ROOT/campaign/manifest.json" "$SOURCE_SHA256" "$SOURCE_BLOB" <<'PY' || exit 2
import json,sys
p=json.load(open(sys.argv[1],encoding='utf8'))
assert p['campaign']=='REPL_CANONICAL_IMPORT' and p['version']=='1.0.0'
assert p['source']['sha256']==sys.argv[2] and p['source']['git_blob_sha1']==sys.argv[3]
assert p['target']['repo']=='Valar05/parametric-parambulator'
assert p['target']['path']=='assets/repl/Repl.glb'
print('PACKET_MANIFEST=VERIFIED')
PY
say 'SOURCE_ASSET=VERIFIED_ORIGINAL_43_JOINT_BASELINE' \
    'HAIR_MANUAL_ACCEPTANCE=HISTORICAL_NOT_INCLUDED_IN_ORIGINAL' \
    'CANONICAL_GLBS_ALLOWED=ONE'
mkdir -p -- "$STATE"
# A separate, fixed, script-owned checkout avoids overwriting a dirty
# user repository and never uses Pose Lab.
if [ ! -d "$CHECKOUT/.git" ]; then
    [ ! -e "$CHECKOUT" ] || block 'ISOLATED_CHECKOUT_PATH_COLLISION'
    TEMP_CHECKOUT="$(mktemp -d "$STATE/.clone.XXXXXXXX")"
    git clone --quiet --branch "$BRANCH" --single-branch "$REPO_URL" "$TEMP_CHECKOUT" || block 'REPO_CLONE_FAILED'
    mv -- "$TEMP_CHECKOUT" "$CHECKOUT" || block 'ATOMIC_CHECKOUT_PUBLISH_FAILED'
fi
[ "$(git -C "$CHECKOUT" remote get-url origin 2>/dev/null)" = "$REPO_URL" ] || block 'REMOTE_IDENTITY_CHANGED'
git -C "$CHECKOUT" fetch --quiet origin "$BRANCH" || block 'REMOTE_FETCH_FAILED'
# Never reset or clean even the isolated checkout. Diagnose safely.
if [ -n "$(git -C "$CHECKOUT" status --porcelain=v1 --untracked-files=all)" ]; then
    # Only a previous interrupted attempt may be resumed, not an
    # unexplained manual or unrelated change.
    CHANGED="$(git -C "$CHECKOUT" status --porcelain=v1 --untracked-files=all | cut -c4-)"
    while IFS= read -r path; do
        [ -n "$path" ] || continue
        case "$path" in
            "$CANONICAL"|'assets/repl/CANONICAL_MODEL.json'|'campaigns/REPL_CANONICAL_IMPORT_v1.0.0.sh'|'README.md') : ;;
            *) block "UNRELATED_CHECKOUT_CHANGE:$path";;
        esac
    done <<< "$CHANGED"
fi
# Remote branch must be the base or an ancestor of our clean, unpushed
# local import commit. Never overwrite or force-push anyone else's work.
REMOTE_BEFORE="$(git -C "$CHECKOUT" rev-parse refs/remotes/origin/$BRANCH)"
LOCAL_BEFORE="$(git -C "$CHECKOUT" rev-parse HEAD)"
if ! git -C "$CHECKOUT" merge-base --is-ancestor "$REMOTE_BEFORE" "$LOCAL_BEFORE"; then
    # A remote import may have won a race: inspect it instead of rebasing.
    if git -C "$CHECKOUT" cat-file -e "refs/remotes/origin/$BRANCH:$CANONICAL" 2>/dev/null; then
        REMOTE_BLOB="$(git -C "$CHECKOUT" rev-parse "refs/remotes/origin/$BRANCH:$CANONICAL")"
        [ "$REMOTE_BLOB" = "$SOURCE_BLOB" ] || block 'CANONICAL_MODEL_ALREADY_EXISTS_WITH_DIFFERENT_BYTES'
        say 'REMOTE_MODEL_PRESENT=ORIGINAL_SOURCE_HASH_MATCHES' 'GIT_BRANCH_HAS_ADVANCED=YES'
        say 'RESUME=Use fresh checkout if local state is irrelevant; no files overwritten'
    fi
    block 'REMOTE_ADVANCED_RELATIVE_TO_ISOLATED_CHECKOUT_NO_FORCE_PUSH'
fi
# Prohibit any other tracked GLB, even outside the intended model path.
TRACKED_GLBS="$(git -C "$CHECKOUT" ls-tree -r --name-only HEAD | grep -Ei '\.glb$' || true)"
if [ -n "$TRACKED_GLBS" ] && [ "$TRACKED_GLBS" != "$CANONICAL" ]; then
    say "EXISTING_GLB_PATHS=$TRACKED_GLBS"
    block 'REPOSITORY_HAS_MULTIPLE_OR_UNEXPECTED_GLB_FILES'
fi
if git -C "$CHECKOUT" cat-file -e "HEAD:$CANONICAL" 2>/dev/null; then
    OLD_BLOB="$(git -C "$CHECKOUT" rev-parse "HEAD:$CANONICAL")"
    [ "$OLD_BLOB" = "$SOURCE_BLOB" ] || block 'CANONICAL_GLB_ALREADY_DIFFERENT_PRESERVE_OWNER_MODEL'
    say 'BASELINE_ALREADY_PRESENT=YES'
else
    mkdir -p -- "$CHECKOUT/assets/repl"
    # This is the only GLB materialized into the intended Git checkout.
    cp -- "$SOURCE" "$CHECKOUT/$CANONICAL" || block 'CANONICAL_COPY_FAILED'
    [ "$(shat "$CHECKOUT/$CANONICAL")" = "$SOURCE_SHA256" ] || block 'CANONICAL_WORKTREE_READBACK_FAILED'
    say 'CANONICAL_SOURCE_COPY=HASH_VERIFIED'
fi
# Keep historical manifest truthful. Do not change any other project state.
MANIFEST="$CHECKOUT/assets/repl/CANONICAL_MODEL.json"
[ -f "$MANIFEST" ] || block 'CANONICAL_REPO_MANIFEST_MISSING'
python3 - "$MANIFEST" "$SOURCE_SHA256" "$SOURCE_BLOB" <<'PY' || block 'MANIFEST_UPDATE_FAILED'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);d=json.loads(p.read_text(encoding='utf8'))
assert d['canonical_glb_path']=='assets/repl/Repl.glb'
assert d['intended_initial_source_sha256']==sys.argv[2]
d['status']='ORIGINAL_SOURCE_BASELINE_IMPORTED__LATER_HAIR_UPDATES_NOT_MIGRATED'
d['initial_import']={
    'source_sha256':sys.argv[2],
    'git_blob_sha1':sys.argv[3],
    'source_size_bytes':6352596,
    'contains_accepted_hair_weights':False,
    'next_step':'Reconcile owner-accepted mane/tail into SAME canonical path'
}
p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf8')
print('CANONICAL_MANIFEST=UPDATED_WITH_NO_FALSE_HAIR_CLAIM')
PY
# Retire the current README's pre-import status in the very same commit.
# Only exact original wording is touched, and a later edited README is left
# alone if it no longer contains that historical line.
README="$CHECKOUT/README.md"
[ -f "$README" ] || block 'REPOSITORY_README_MISSING'
python3 - "$README" <<'PYDOC' || block 'README_CANONICAL_STATUS_UPDATE_FAILED'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text('utf8')
s=s.replace('**It has not yet been imported.**',
            '**The original 43-joint source baseline is committed here; later accepted mane/tail weighting is not yet integrated.**')
s=s.replace('It has not yet been imported.',
            'The original baseline is imported; accepted mane/tail changes remain a separate migration.')
p.write_text(s,encoding='utf8')
print('README_INITIAL_IMPORT_STATE=UPDATED_IF_HISTORICAL_MARKER_PRESENT')
PYDOC
# This script itself becomes the authorized campaign provenance in repo;
# the six-megabyte payload is committed only once as the sole GLB.
mkdir -p -- "$CHECKOUT/campaigns"
cp -- "$SCRIPT" "$CHECKOUT/campaigns/REPL_CANONICAL_IMPORT_v1.0.0.sh" || block 'SCRIPT_PROVENANCE_COPY_FAILED'
for path in "$CANONICAL" 'assets/repl/CANONICAL_MODEL.json' 'campaigns/REPL_CANONICAL_IMPORT_v1.0.0.sh' 'README.md'; do
    git -C "$CHECKOUT" add -- "$path" || block "GIT_STAGE_FAILED:$path"
done
STAGED_BLOB="$(git -C "$CHECKOUT" rev-parse ":$CANONICAL" 2>/dev/null || true)"
[ "$STAGED_BLOB" = "$SOURCE_BLOB" ] || block 'GIT_STAGED_MODEL_BLOB_NOT_LOCKED_SOURCE'
# The only staged paths are the three explicit allowlist entries.
while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
        "$CANONICAL"|'assets/repl/CANONICAL_MODEL.json'|'campaigns/REPL_CANONICAL_IMPORT_v1.0.0.sh'|'README.md') : ;;
        *) block "UNRELATED_STAGED_PATH:$path";;
    esac
done < <(git -C "$CHECKOUT" diff --cached --name-only)
if ! git -C "$CHECKOUT" diff --cached --quiet; then
    AUTHOR_NAME="$(git -C "$CHECKOUT" config user.name || true)"
    AUTHOR_EMAIL="$(git -C "$CHECKOUT" config user.email || true)"
    if [ -n "$AUTHOR_NAME" ] && [ -n "$AUTHOR_EMAIL" ]; then
        git -C "$CHECKOUT" commit --quiet -m 'Import original Repl baseline into one canonical GLB path' || block 'LOCAL_COMMIT_FAILED'
    else
        git -C "$CHECKOUT" -c user.name='Repl Termux Campaign' -c user.email='repl-termux-campaign@users.noreply.github.com' commit --quiet -m 'Import original Repl baseline into one canonical GLB path' || block 'LOCAL_COMMIT_FAILED'
    fi
fi
NEW_HEAD="$(git -C "$CHECKOUT" rev-parse HEAD)"
say "LOCAL_COMMIT=$NEW_HEAD" 'LOCAL_COMMIT_IS_NOT_REMOTE_PROOF=YES'
# Try the operator's existing noninteractive Git credentials, then existing
# gh and SSH identities. No token is printed, copied, or saved to the ZIP.
PUSHED=NO
if git -C "$CHECKOUT" push --quiet origin "HEAD:refs/heads/$BRANCH" >"$STATE/push-origin.log" 2>&1; then
    PUSHED=YES; say 'PUSH_AUTH_LANE=EXISTING_GIT_CREDENTIALS'
fi
if [ "$PUSHED" = NO ] && command -v gh >/dev/null 2>&1 && gh auth status -h github.com >/dev/null 2>&1; then
    if git -C "$CHECKOUT" -c credential.helper='!gh auth git-credential' push --quiet origin "HEAD:refs/heads/$BRANCH" >"$STATE/push-gh.log" 2>&1; then
        PUSHED=YES; say 'PUSH_AUTH_LANE=EXISTING_GH_AUTH'
    fi
fi
if [ "$PUSHED" = NO ] && command -v ssh >/dev/null 2>&1; then
    if GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=8' git -C "$CHECKOUT" push --quiet "git@github.com:$REPO_NAME.git" "HEAD:refs/heads/$BRANCH" >"$STATE/push-ssh.log" 2>&1; then
        PUSHED=YES; say 'PUSH_AUTH_LANE=EXISTING_SSH_IDENTITY'
    fi
fi
[ "$PUSHED" = YES ] || block 'REMOTE_PUSH_AUTH_OR_POLICY_FAILED__LOCAL_COMMIT_PRESERVED_FOR_RESUME'
say 'GITHUB_PUSH=REPORTED_SUCCESS_VERIFYING_REMOTE'
# Require a fresh GitHub server ref query. A local commit is not proof.
REMOTE_HEAD="$(git -C "$CHECKOUT" ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')"
[ "$REMOTE_HEAD" = "$NEW_HEAD" ] || block 'REMOTE_GITHUB_HEAD_READBACK_MISMATCH'
git -C "$CHECKOUT" fetch --quiet origin "$BRANCH" || block 'REMOTE_REFETCH_FAILED'
REMOTE_BLOB="$(git -C "$CHECKOUT" rev-parse "refs/remotes/origin/$BRANCH:$CANONICAL")"
[ "$REMOTE_BLOB" = "$SOURCE_BLOB" ] || block 'REMOTE_CANONICAL_GIT_BLOB_MISMATCH'
REMOTE_BYTES="$(git -C "$CHECKOUT" show "refs/remotes/origin/$BRANCH:$CANONICAL" | sha256sum | awk '{print $1}')"
[ "$REMOTE_BYTES" = "$SOURCE_SHA256" ] || block 'REMOTE_CANONICAL_SHA256_MISMATCH'
# Verify all GLBs in remote commit: exactly one, at the owner-defined path.
REMOTE_GLBS="$(git -C "$CHECKOUT" ls-tree -r --name-only "refs/remotes/origin/$BRANCH" | grep -Ei '\.glb$' || true)"
[ "$REMOTE_GLBS" = "$CANONICAL" ] || block 'REMOTE_MULTIPLE_MODELS_DETECTED'
mkdir -p -- "$(dirname "$RECEIPT")"
TMP_RECEIPT="$RECEIPT.tmp.$$"
cat > "$TMP_RECEIPT" <<EOF
CAMPAIGN=REPL_CANONICAL_IMPORT
VERSION=1.0.0
EXECUTION_LANE=TERMUX_GIT
REPOSITORY=$REPO_NAME
REMOTE_BRANCH=$BRANCH
REMOTE_HEAD=$REMOTE_HEAD
REMOTE_CANONICAL_PATH=$CANONICAL
REMOTE_CANONICAL_SIZE=$SOURCE_SIZE
REMOTE_CANONICAL_SHA256=$REMOTE_BYTES
REMOTE_GIT_BLOB_SHA1=$REMOTE_BLOB
REMOTE_GLB_COUNT=1
ORIGINAL_SOURCE_IMPORTED=YES
V0_2_V0_3_MANUAL_HAIR_ACCEPTANCE=HISTORICAL_ONLY_NOT_CLAIMED_INSTALLED
NO_POSE_LAB=YES
STATUS=REMOTE_GITHUB_READBACK_VERIFIED
EOF
mv -- "$TMP_RECEIPT" "$RECEIPT"
say 'CAMPAIGN_STATUS=REMOTE_GITHUB_READBACK_VERIFIED' "RECEIPT=$RECEIPT" \
    "REMOTE_HEAD=$REMOTE_HEAD" "REMOTE_GLB_SHA256=$REMOTE_BYTES" \
    'CANONICAL_GLB_FILES_IN_REPO=1' 'HUMAN_HAIR_VISUAL_VERDICT=NOT_PART_OF_THIS_IMPORT'
