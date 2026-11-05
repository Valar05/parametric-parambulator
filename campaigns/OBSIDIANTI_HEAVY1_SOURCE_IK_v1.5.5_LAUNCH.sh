#!/data/data/com.termux/files/usr/bin/bash
# Obsidianti Heavy1 source-motion independent world targets and knee poles, v1.5.5.
# Authorized body: Termux Git, one invocation, versioned immutable sources.
set -Eeuo pipefail
VERSION='OBSIDIANTI_HEAVY1_SOURCE_IK_v1.5.5'
MODEL_SHA='8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4'
AGENTS_BLOB='547c2af52303f4efb718bbf8f82a698110c7bfca'
SOURCE_COMMIT='c5fe6465be720789b9977bf08dd3acfbef969a82'
FAILURE_COMMIT='b97375ded91228118096d1e825fd12f429ecae81'
REMOTE='https://github.com/Valar05/parametric-parambulator.git'
SELF_REL='campaigns/OBSIDIANTI_HEAVY1_SOURCE_IK_v1.5.5_LAUNCH.sh'
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
p=pathlib.Path(os.environ['HC_RECEIPT']);r={'campaign':'OBSIDIANTI_HEAVY1_SOURCE_IK_v1.5.5','authority':'TERMUX_GIT_ONLY','stage':os.environ['HC_STAGE'],'error':os.environ['HC_ERROR'],'exitCode':int(os.environ['HC_RC']),'launcherSha256':os.environ['HC_SHA'],'sourceCommit':os.environ['HC_COMMIT'],'sourceModelSha256':os.environ['HC_MODEL'],'modelPublication':os.environ['HC_PUBLISHED'],'ownerVisualApproval':False,'operatorLog':os.environ['HC_LOG'],'generatedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
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
root=pathlib.Path(sys.argv[1]);old='v1.5.4';new='v1.5.5'
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
s=src[E]
# Change only the controller retarget and knee pole calculation. Native donor data is
# authoritative; there is no manually authored stance trajectory or FK substitution.
anchor=' def goals(row,hip_pose):'
terminator=' # These empties genuinely drive Blender'
if s.count(anchor)!=1 or s.count(terminator)!=1:raise RuntimeError('GOAL_REGION_DRIFT')
a=s.index(anchor);z=s.index(terminator,a)
newgoals=''' def goals(row,hip_pose):
  # SOURCE_WORLD_CONTROLLER_TARGETS: source world displacement in GLTF basis,
  # anchored at the FIRST validated target pose. Target hip is NEVER used to
  # construct a desired foot/pole position or world foot quaternion.
  output={}
  for side in SIDES:
   controller=row['bones'][side+'Foot.IK']; controller0=frame0[side+'Foot.IK']
   ankle=row['bones'][f'mixamorig:{side}Foot']; ankle0=frame0[f'mixamorig:{side}Foot']
   pole=row['bones'][side+'Knee.IK']; pole0=frame0[side+'Knee.IK']
   knee=row['bones'][f'mixamorig:{side}Leg']; knee0=frame0[f'mixamorig:{side}Leg']
   ratio={'combined':'combinedRatio','thigh':'thighRatio','shin':'shinRatio'}[a.leg_ratio]
   scale=float(calibration['legRatios'][side][ratio])*a.amplitude
   worldDelta=v3(controller['worldPosition'])-v3(controller0['worldPosition'])
   residual=(v3(ankle['worldPosition'])-v3(controller['worldPosition']))-(v3(ankle0['worldPosition'])-v3(controller0['worldPosition']))
   # hip0 is the starting pose only, not the animated hip at this frame.
   ankle0World=(hip0@hipLocal[side]['ankle'])
   ankleGoal=ankle0World+align@(worldDelta+residual)*scale
   # Pole follows the SOURCE knee bending plane, not an FK hip-relative offset.
   # Keep native knee/pole direction and source knee travel. Neither is
   # driven by target hip rotation; genuine Blender IK handles joint movement.
   knee0Target=(hip0@init_inv@mat4(idle_world[ids[f'mixamorig:{side}Leg']])).translation
   nativeKneeDelta=v3(knee['worldPosition'])-v3(knee0['worldPosition'])
   kneeGoal=knee0Target+align@nativeKneeDelta*scale
   nativeKneeToPole=v3(pole['worldPosition'])-v3(knee['worldPosition'])
   basePoleLever=v3(pole0['worldPosition'])-v3(knee0['worldPosition'])
   pole0World=ankle0World+align@(v3(pole0['worldPosition'])-v3(controller0['worldPosition']))*scale
   poleGoal=pole0World+align@(nativeKneeDelta+nativeKneeToPole-basePoleLever)*scale
   source_delta=(q_bl(ankle['worldQuaternion'])@q_bl(ankle0['worldQuaternion']).inverted()).normalized()
   mapped_delta=(align@source_delta.to_matrix()@align.transposed()).to_quaternion()
   foot0World=(hip0.to_quaternion()@hipLocal[side]['foot'].to_quaternion()).normalized()
   footRot=(mapped_delta@foot0World).normalized()
   if a.strategy=='idle':footRot=foot0World
   elif a.strategy=='local':
    hipnow=q_bl(row['bones']['mixamorig:Hips']['worldQuaternion'])
    hipfirst=q_bl(frame0['mixamorig:Hips']['worldQuaternion'])
    footlocal_now=hipnow.inverted()@q_bl(ankle['worldQuaternion'])
    footlocal_first=hipfirst.inverted()@q_bl(ankle0['worldQuaternion'])
    localdelta=(footlocal_first.inverted()@footlocal_now).normalized()
    mappedlocal=(align@localdelta.to_matrix()@align.transposed()).to_quaternion()
    footRot=(foot0World@mappedlocal).normalized()
   output[side]={'ankleWorld':ankleGoal,'poleWorld':poleGoal,'footWorldRot':footRot,
       'kneeGoalWorld':kneeGoal,'sourceDelta':worldDelta.length,
       'poleSeparation':(poleGoal-ankleGoal).length,
       'kneePlaneLeverLength':nativeKneeToPole.length}
  return output

 # Invariance regression: varying only target pelvis pose MUST NOT change any
 # world-space foot/pole target. This would have caught the v1.5.4 regression.
 g0check=goals(source['frames'][0],hip0)
 alteredHip=hip0@Matrix.Rotation(.31,4,'Y')
 for index in (0,7,15,30,45,60):
  rw=source['frames'][index]
  reference=goals(rw,hip0);perturbed=goals(rw,alteredHip)
  for side in SIDES:
   for key in ('ankleWorld','poleWorld','footWorldRot'):
    lhs,rhs=reference[side][key],perturbed[side][key]
    miss=(lhs-rhs).length if key!='footWorldRot' else lhs.rotation_difference(rhs).angle
    if miss>1e-7:raise RuntimeError('HIP_INDEPENDENCE_REGRESSION '+side+' '+key+' '+str(index))
'''
s=s[:a]+newgoals+s[z:]
# Source poles are not static: continue with last frame's evaluated knee branch.
s=one(s,"   out['observed'][s]={'ankleWorld':seq(fkpos),'kneeWorld':seq(glmat[leg].translation),",
      "   out['observed'][s]={'ankleWorld':seq(fkpos),'kneeWorld':seq(glmat[leg].translation),\n      'sourceMappedKneeGoalWorld':seq(gh[s]['kneeGoalWorld']),\n      'kneeGoalMissMetres':float((glmat[leg].translation-gh[s]['kneeGoalWorld']).length),",
      'knee-witness')
s=one(s,"'trajectoryBasis':'SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION',",
      "'trajectoryBasis':'SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS',\n    'hipIndependenceChecks':6,'originalNativeMotionRetained':True,",
      'trajectory-provenance')
src[E]=s
s=src[A]
# Native Blender is an actual solver, not a numerical visual veto. Preserve the
# same physical gates and failed candidate quarantine; add new knee-goal metrics.
s=one(s,"'maxNativeControllerMiss_m':0.,", "'maxNativeControllerMiss_m':0.,'maxMappedKneeGoalMiss_m':0.,",'knee-metric-init')
s=one(s,"    obs.update({'nativeBlenderAnkle_m':target['ankleWorld'],",
      "    scores['maxMappedKneeGoalMiss_m']=max(scores['maxMappedKneeGoalMiss_m'],length(vec(kp,target['sourceMappedKneeGoalWorld'])))\n    obs.update({'mappedKneeGoal_m':target['sourceMappedKneeGoalWorld'],'mappedKneeMiss_m':target['kneeGoalMissMetres']})\n    obs.update({'nativeBlenderAnkle_m':target['ankleWorld'],",'knee-metric-measure')
src[A]=s
s=src[R]
# Source-driven profiles use the same native action, with competing orientation and
# scale mappings. No manual foot translations or baked poses are introduced.
s=one(s,"  profiles=[('native','combined',1.),('idle','combined',1.),('local','combined',1.),\n            ('native','thigh',1.),('idle','thigh',1.),('local','thigh',1.),\n            ('native','shin',1.),('idle','shin',1.),('local','shin',1.),\n            ('idle','combined',.90),('idle','combined',1.08),\n            ('local','combined',.90),('native','combined',.90)]",
      "  profiles=[('native','combined',1.),('local','combined',1.),\n            ('native','thigh',1.),('local','thigh',1.),('native','shin',1.),\n            ('local','shin',1.),('native','combined',.92),('native','combined',1.06)]",
      'adaptive-mapping-profiles')
# On all failure modes, make local preview URL highly visible and user-copyable.
s=one(s,"    print('QUARANTINED_VISUAL_URL='+url,flush=True)","    print('QUARANTINED_VISUAL_URL='+url,flush=True)\n    print('COPY_THIS_URL_IN_PHONE_BROWSER='+url,flush=True)",'plain-url')
src[R]=s
s=src[T]
s=one(s," must('pole_local=target_local+align@poleLever*scale' in s,'pole lever arm not preserved')",
      " must('nativeKneeToPole' in s and 'sourceMappedKneeGoalWorld' in s,'source knee plane not transferred')\n must('HIP_INDEPENDENCE_REGRESSION' in s and 'hipIndependenceChecks' in s,'animated hip target regression missing')",
      'pole-regression-test')
s=one(s," must('SOURCE_WORLD_FOOT_CONTROLLER_DELTA_NO_DONOR_PELVIS_COMPENSATION' in s,'trajectory provenance missing')",
      " must('SOURCE_WORLD_CONTROLLER_TARGETS_INDEPENDENT_OF_TARGET_HIPS' in s,'trajectory provenance missing')",
      'world-target-test')
s=one(s," must('a.strategy' in s and 'a.leg_ratio' in s,'scale/rotation diagnostics missing')",
      " must('a.strategy' in s and 'a.leg_ratio' in s,'scale/rotation diagnostics missing')\n must('maxMappedKneeGoalMiss_m' in a,'independent knee physical witness missing')",
      'mapped-knee-test')
src[T]=s
src[D]+='''\n\n## v1.5.5 source-driven hip-independent IK targets\nBased on owner video feedback: opening frame acceptable; forward foot mainly anchored,\nrear foot mostly translates backward as stance widens; both feet rotate. These\nare source-motion expectations, not manually scripted front/rear trajectories.\nActual Lionheart Foot.IK/Knee.IK/controller bone positions and rotations are\nretargeted into fixed world anchors calibrated from approved initial target Idle.\nNeither animated target hips nor rejected target Heavy1 FK leg tracks create\nworld-space foot targets. Source knee-plane lever and moving knee are retained.\nSix-channel Only: Heavy1 bilateral UpLeg/Leg/Foot rotations, preserve root,\npelvis, skin, all other actions including Repl. Native Blender IK evaluation,\nskinned footwear physical guards, source-space and knee diagnostics, immutable\nversioned packet, Termux Git remote readback, always-on failed-candidate visual\nreview with HTTP identity and copyable URL. Numeric validation and owner visual\napproval remain distinct and both mandatory for accepted animation.\n'''
for a,b in paths:
 data=src[b].replace(old,new)
 if b.endswith('.py'):ast.parse(data,filename=b)
 p=root/b;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
 print('GENERATED='+b+' SHA256='+hashlib.sha256(data.encode()).hexdigest())
print('VERSIONED_SOURCES_GENERATED_AND_PARSE_CHECKED=YES')
PY_GEN
STAGE='TEST_VERSIONED_SOURCE'
python3 -B "$REPO/tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.5.py"
# Test the actual generator twice: a rerun must be byte-idempotent.
python3 -B - "$REPO" <<'PY'
import pathlib,sys,hashlib,ast
r=pathlib.Path(sys.argv[1]); v='v1.5.5'
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
# Allowlist only the six new v1.5.5 sources and the self-contained launcher.
PATHS=(
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_EVAL_v1.5.5.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_APPLY_v1.5.5.py
 campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.5.py
 tests/OBSIDIANTI_HEAVY1_BLENDER_IK_TEST_v1.5.5.py
 docs/obsidianti/HEAVY1_BLENDER_IK_v1.5.5.md
 review/obsidianti-heavy1-blender-ik-v1.5.5.html
 "$SELF_REL"
)
git -C "$REPO" add -- "${PATHS[@]}"
mapfile -t STAGED < <(git -C "$REPO" diff --cached --name-only)
[[ "${#STAGED[@]}" == 7 ]] || { ERR="STAGED_FILE_COUNT_NOT_SEVEN:${#STAGED[@]}";exit 2; }
for n in "${STAGED[@]}";do
 allowed=0;for a in "${PATHS[@]}";do [[ "$n" == "$a" ]] && allowed=1;done
 ((allowed==1)) || { ERR="UNAUTHORIZED_STAGED_FILE:$n";exit 2; }
done
git -C "$REPO" commit -m 'Obsidianti Heavy1: source-driven hip-independent IK v1.5.5 with visual quarantine'
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
(p/'manifest.json').write_text(json.dumps({'campaign':'OBSIDIANTI_HEAVY1_BLENDER_IK_v1.5.5','files':d},sort_keys=True,indent=2)+'\n')
PY
STAGE='RUN_NATIVE_BLENDER_AND_SKINNED_PHYSICAL_GATES'
# v1.5.5 owns source-motion diagnostics and failed-candidate visual evidence; canonical publication still gated.
set +e
python3 -B "$REPO/campaigns/OBSIDIANTI_HEAVY1_BLENDER_IK_RUN_v1.5.5.py" --packet "$PACKET"
RUN_RC=$?
set -e
if ((RUN_RC!=0));then ERR='NATIVE_BLENDER_OR_SKINNED_GATE_FAILED_VISUAL_REVIEW_QUARANTINED_SEE_V155_RECEIPT';exit "$RUN_RC";fi
MODEL_PUBLISHED='RUNNER_REPORTS_SUCCESS_VERIFY_V155_RECEIPT'
STAGE='RUNNER_REPORTED_SUCCESS_VISUAL_VERDICT_PENDING'
echo 'STATUS=REAL_BLENDER_IK_PHYSICAL_GATE_PASSED_RUNNER_RETURNED_SUCCESS'
echo 'OWNER_VISUAL_ACCEPTANCE=PENDING'
RUN_RC=0
