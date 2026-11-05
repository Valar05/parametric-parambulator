#!/data/data/com.termux/files/usr/bin/bash
# Obsidianti Heavy1 source provenance validator repair, v1.5.6; retain source motion and native Blender IK.
# Authorized body: Termux Git, one invocation, versioned immutable sources.
set -Eeuo pipefail
VERSION='OBSIDIANTI_HEAVY1_VALIDATOR_REPAIR_v1.5.6'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE_COMMIT='122f702845bb7960bce5d08d52fc3fae4886dd6b'
FAILURE_COMMIT='122f702845bb7960bce5d08d52fc3fae4886dd6b'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
SELF_REL='campaigns/OBSIDIANTI_HEAVY1_VALIDATOR_REPAIR_v1.5.6_LAUNCH.sh'
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GIT_LFS_SKIP_SMUDGE=1 GIT_TERMINAL_PROMPT=0
umask 077
[[ -n "${PREFIX:-}" && -x "$PREFIX/bin/bash" ]] || { echo 'BLOCKED_NOT_TERMUX'; exit 2; }
for bin in git python3 sha256sum; do command -v "$bin" >/dev/null || { echo "BLOCKED_DEPENDENCY=$bin"; exit 2; }; done
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
SELF_SHA="$(sha256sum "$SELF"|cut -d' ' -f1)"
RUNID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
STATE="$HOME/.local/state/$VERSION/$RUNID"; mkdir -p "$STATE"
OUT="$HOME/storage/downloads"; [[ -d "$OUT" ]] || OUT="$STATE"
LOG="$OUT/${VERSION}_${RUNID}_OPERATOR.log"
RECEIPT="$OUT/${VERSION}_${RUNID}_RECEIPT.json"
REPO="$STATE/repo"; PACKET="$STATE/packet"
STAGE='BOOT'; ERR=''; RUN_RC=2; REPO_COMMIT=''; MODEL_PUBLISHED='NOT_ESTABLISHED'
exec > >(tee -a "$LOG") 2>&1
receipt(){
 export HC_STAGE="$STAGE" HC_ERROR="$ERR" HC_RC="$RUN_RC" HC_SHA="$SELF_SHA" HC_COMMIT="$REPO_COMMIT" HC_RECEIPT="$RECEIPT" HC_MODEL="$MODEL_SHA" HC_PUBLISHED="$MODEL_PUBLISHED" HC_LOG="$LOG"
 python3 -B - <<'PY'
import os,json,pathlib,datetime
p=pathlib.Path(os.environ['HC_RECEIPT']);r={'campaign':'OBSIDIANTI_HEAVY1_VALIDATOR_REPAIR_v1.5.6','authority':'TERMUX_GIT_ONLY','stage':os.environ['HC_STAGE'],'error':os.environ['HC_ERROR'],'exitCode':int(os.environ['HC_RC']),'launcherSha256':os.environ['HC_SHA'],'sourceCommit':os.environ['HC_COMMIT'],'sourceModelSha256':os.environ['HC_MODEL'],'modelPublication':os.environ['HC_PUBLISHED'],'ownerVisualApproval':False,'operatorLog':os.environ['HC_LOG'],'generatedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
t=p.with_suffix('.tmp');t.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');t.replace(p)
PY
}
on_exit(){
 local rc="$?"
 if ((rc!=0));then RUN_RC="$rc"; [[ -n "$ERR" ]] || ERR="FAILED_AT_${STAGE}";fi
 receipt || true
 echo "STAGE=$STAGE"; echo "ERROR=${ERR:-NONE}"; echo "OPERATOR_LOG=$LOG"; echo "RECEIPT=$RECEIPT"; echo "EXIT=$RUN_RC"
}
trap on_exit EXIT
trap 'ERR="INTERRUPTED";exit 130' INT TERM
printf 'CAMPAIGN=%s\nAUTHORITY=TERMUX_GIT_ONLY\nSELF_SHA256=%s\n' "$VERSION" "$SELF_SHA"
STAGE='PINNED_ISOLATED_GIT_CLONE'
git clone --depth=100 --single-branch --branch main --config filter.lfs.smudge= --config filter.lfs.required=false "$REMOTE" "$REPO"
HEAD="$(git -C "$REPO" rev-parse HEAD)"
echo "RESOLVED_REPO=$REPO";echo "EXECUTION_DIR=$REPO";echo 'BRANCH=main';echo "HEAD=$HEAD"
[[ "$(git -C "$REPO" rev-parse HEAD:AGENTS.md)" == "$AGENTS_BLOB" ]] || { ERR='AGENTS_REVISION_CHANGED';exit 2; }
[[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" ]] || { ERR='DIRTY_ISOLATED_SOURCE';exit 2; }
for commit in "$SOURCE_COMMIT" "$FAILURE_COMMIT"; do
 if ! git -C "$REPO" merge-base --is-ancestor "$commit" HEAD 2>/dev/null; then
  git -C "$REPO" fetch --deepen=150 origin main
  git -C "$REPO" merge-base --is-ancestor "$commit" HEAD || { ERR="MISSING_HISTORICAL_SOURCE:$commit";exit 2; }
 fi
done
[[ "$(git -C "$REPO" show HEAD:assets/obsidianti/Obsidianti.glb)" == *"oid sha256:$MODEL_SHA"* ]] || { ERR='CANONICAL_MODEL_CHANGED_NO_PERMISSION_TO_OVERWRITE';exit 2; }
[[ "$(git -C "$REPO" rev-parse HEAD:assets/repl/Repl.glb)" != '' ]] || { ERR='REPL_LOCK_MISSING';exit 2; }
STAGE='PREPUBLICATION_VERSIONED_PATH_GUARD'
# The code generator inspects all six destination names before writing any source.
# This launcher is itself committed and read back before the physical run.
[[ ! -e "$REPO/$SELF_REL" ]] || { ERR='VERSIONED_LAUNCHER_DESTINATION_COLLISION';exit 2; }
mkdir -p "$(dirname "$REPO/$SELF_REL")"
python3 -B - "$REPO" <<'PY_GEN'
import pathlib,sys,ast,hashlib
root=pathlib.Path(sys.argv[1]);old='v1.5.5';new='v1.5.6'
paths=[('campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_'+k+'_'+old+'.py','campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_'+k+'_'+new+'.py') for k in ('EVAL','APPLY','RUN')]
paths += [('tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_'+old+'.py','tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_'+new+'.py'),('docs/obsidianti/HEAVY1_BLENDER_IK_'+old+'.md','docs/obsidianti/HEAVY1_BLENDER_IK_'+new+'.md'),('review/obsidianti-heavy1-blender-ik-'+old+'.html','review/obsidianti-heavy1-blender-ik-'+new+'.html')]
for a,b in paths:
 if (root/b).exists():raise RuntimeError('VERSIONED_DESTINATION_COLLISION '+b)
 if not (root/a).is_file():raise RuntimeError('SOURCE_NOT_COMMITTED '+a)
src={b:(root/a).read_text() for a,b in paths}
def one(s,a,b,label):
 if s.count(a)!=1:raise RuntimeError('PATCH_DRIFT '+label+' expected exactly once, found '+str(s.count(a)))
 return s.replace(a,b,1)
E,A,R,T,D,H=[b for a,b in paths]
s=src[A]
# Actual failure: evaluator advertises SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS;
# validator still demands the v1.5.4 SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION.
old_provenance="sample.get('trajectoryBasis')!='SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION'"
new_provenance="sample.get('trajectoryBasis')!='SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS'"
s=one(s,old_provenance,new_provenance,'evaluated-sample-provenance')
# Give misleading contract errors their own code to diagnose future schema drift.
s=one(s,"raise RuntimeError('SAMPLES_NOT_ACTUAL_BLENDER_IK')",
      "raise RuntimeError('NATIVE_IK_SAMPLE_PROVENANCE_OR_ENGINE_MISMATCH')",'provenance-error')
src[A]=s
s=src[T]
# Test evaluator/validator contract, and reject old provenance or fake IK engines.
needle=" must('SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS' in s,'trajectory provenance missing')"
replacement=''' must('SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS' in s,'trajectory provenance missing')
 must("sample.get('trajectoryBasis')!='SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS'" in a,
      'evaluator-to-validator provenance contract drift')
 must('NATIVE_IK_SAMPLE_PROVENANCE_OR_ENGINE_MISMATCH' in a,'provenance error missing')
 must("'originalBadFKUsedForLegBasis':False" in s,'actual Blender solver provenance missing')'''
s=one(s,needle,replacement,'interface-regression-test')
src[T]=s
src[D]+='''\n\n## v1.5.6 metadata contract correction\nThe actual v1.5.5 Blender constraints evaluated every sample, but physical APPLY rejected\nthem before skin checks because the evaluator emitted trajectoryBasis=\nSOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS while APPLY expected\nthe old v1.5.4 identifier. Correct only the validator contract and add a\nregression test. Preserve source-driven Blender controls, world target invariance,\nknee pole tracking, six-channel edits, 121 skinned probes, and quarantined visual\noutput even when the numeric physical preflight fails. This is a source interface\nrepair, NOT evidence the motion is valid or visually approved.\n'''
for a,b in paths:
 data=src[b].replace(old,new)
 if b.endswith('.py'):ast.parse(data,filename=b)
 p=root/b;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
 print('GENERATED='+b+' SHA256='+hashlib.sha256(data.encode()).hexdigest())
print('VERSIONED_SOURCES_GENERATED_AND_PARSE_CHECKED=YES')
PY_GEN
STAGE='TEST_VERSIONED_SOURCE'
python3 -B "$REPO/tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.6.py"
# Test the actual generator twice: a rerun must be byte-idempotent.
python3 -B - "$REPO" <<'PY'
import pathlib,sys,hashlib,ast
r=pathlib.Path(sys.argv[1]); v='v1.5.6'
names=[f'campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_{p}_{v}.py' for p in ('EVAL','APPLY','RUN')]+[f'tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_{v}.py']
for n in names:
 t=(r/n).read_text();ast.parse(t,filename=n)
 assert 'v1.5.3' not in t,n
print('NEW_VERSION_PYTHON_AST=PASS')
PY
cp "$SELF" "$REPO/$SELF_REL"
[[ "$(sha256sum "$REPO/$SELF_REL" |cut -d' ' -f1)" == "$SELF_SHA" ]] || { ERR='LAUNCHER_COPY_MISMATCH';exit 2; }
STAGE='COMMIT_AND_READBACK_TERMUX_GIT'
git -C "$REPO" config user.name 'Obsidianti Termux Campaign'
git -C "$REPO" config user.email 'obsidianti-campaign@users.noreply.github.com'
# Allowlist only the six new v1.5.6 sources and the self-contained launcher.
PATHS=(
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.6.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.6.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.6.py
 tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.6.py
 docs/obsidianti/HEAVY1_BLENDER_IK_v1.5.6.md
 review/obsidianti-heavy1-blender-ik-v1.5.6.html
 "$SELF_REL"
)
git -C "$REPO" add -- "${PATHS[@]}"
mapfile -t STAGED < <(git -C "$REPO" diff --cached --name-only)
[[ "${#STAGED[@]}" == 7 ]] || { ERR="STAGED_FILE_COUNT_NOT_SEVEN:${#STAGED[@]}";exit 2; }
for n in "${STAGED[@]}";do
 allowed=0;for a in "${PATHS[@]}";do [[ "$n" == "$a" ]] && allowed=1;done
 ((allowed==1)) || { ERR="UNAUTHORIZED_STAGED_FILE:$n";exit 2; }
done
git -C "$REPO" commit -m 'Obsidianti Heavy1: repair native IK sample provenance contract v1.5.6'
REPO_COMMIT="$(git -C "$REPO" rev-parse HEAD)"
[[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" ]] || { ERR='NEW_SOURCE_COMMIT_DIRTY';exit 2; }
git -C "$REPO" push origin HEAD:refs/heads/main || { ERR='REMOTE_ADVANCED_OR_PUSH_REJECTED_NO_FORCE';exit 2; }
[[ "$(git -C "$REPO" ls-remote origin refs/heads/main|cut -f1)" == "$REPO_COMMIT" ]] || { ERR='REMOTE_SOURCE_READBACK_FAILED';exit 2; }
echo "SOURCE_COMMIT_READBACK=$REPO_COMMIT"
STAGE='ASSEMBLE_EXACT_COMMITTED_PACKET'
mkdir -p "$PACKET"
for rel in "${PATHS[@]:0:6}";do
 mkdir -p "$(dirname "$PACKET/$rel")"
 git -C "$REPO" show "$REPO_COMMIT:$rel" > "$PACKET/$rel"
 cmp "$REPO/$rel" "$PACKET/$rel" || { ERR="PACKET_MISMATCH:$rel";exit 2; }
done
python3 -B - "$PACKET" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]);d={}
for f in p.rglob('*'):
 if f.is_file():d[f.relative_to(p).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
assert len(d)==6
(p/'manifest.json').write_text(json.dumps({'campaign':'OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.6','files':d},sort_keys=True,indent=2)+'\n')
PY
STAGE='RUN_NATIVE_BLENDER_AND_SKINNED_PHYSICAL_GATES'
# v1.5.6 owns source-motion diagnostics and failed-candidate visual evidence; canonical publication still gated.
set +e
python3 -B "$REPO/campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.6.py" --packet "$PACKET"
RUN_RC=$?
set -e
if ((RUN_RC!=0));then ERR='NATIVE_BLENDER_OR_SKINNED_GATE_FAILED_SEE_V156_RECEIPT_AND_VISUAL';exit "$RUN_RC";fi
MODEL_PUBLISHED='RUNNER_REPORTS_SUCCESS_VERIFY_V156_RECEIPT'
STAGE='RUNNER_REPORTED_SUCCESS_VISUAL_VERDICT_PENDING'
echo 'STATUS=REAL_BLENDER_IK_PHYSICAL_GATE_PASSED_RUNNER_RETURNED_SUCCESS'
echo 'OWNER_VISUAL_ACCEPTANCE=PENDING'
RUN_RC=0
