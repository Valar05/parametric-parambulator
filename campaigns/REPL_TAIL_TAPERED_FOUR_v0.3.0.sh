#!/usr/bin/env bash
# REPL_TAIL_TAPERED_FOUR v0.3.0 | actual direct-download operator file.
# Please leave the accepted mane alone. This campaign edits only a DERIVED GLB.
# It generates four tapering tail controls and a FULL TEXTURED review.
# No body, leg, hoof, source GLB, Repl.blend, or Pose Lab checkout is modified.
set -Eeuo pipefail
CAMPAIGN='REPL_TAIL_TAPERED_FOUR_CONTROLS'
VERSION='0.3.0'
PIN='aec8a743d8fbf6946df64893b7775a7b18bd198b'
ENGINE_BLOB='8c60a5a30d60ea3e016436afc5982404c2339e9d'
PARENT_BLOB='287567d6baf8e8fa415580dc57ee86600772f797'
GRANDPARENT_BLOB='33ca93660f3d5858d4496027902b9b7a7e44d800'
REPO='https://github.com/Valar05/parametric-parambulator.git'
ROOT="$HOME/.local/share/repl-hair-campaigns"
TARGET="$ROOT/repl-v${VERSION}-${PIN:0:12}"
SCRIPT='campaigns/repl_tail_four_controls_v0_3_0.py'
PARENT='campaigns/repl_hair_five_controls_v0_2_0.py'
GRANDPARENT='campaigns/repl_hair_bind_v0_1_0.py'
printf 'CAMPAIGN=%s\nVERSION=%s\nLAUNCHER_PATH=%s\n' "$CAMPAIGN" "$VERSION" "$0"
printf 'LAUNCHER_SHA256=%s\n' "$(sha256sum -- "$0" | cut -d' ' -f1)"
printf 'PINNED_GITHUB_COMMIT=%s\nEXPECTED_ENGINE_BLOB=%s\n' "$PIN" "$ENGINE_BLOB"
for command_name in git python3 sha256sum mktemp; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'STATUS=BLOCKED\nWHY=MISSING_EXECUTABLE:%s\n' "$command_name"
    exit 2
  }
done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 2)' || {
  echo 'STATUS=BLOCKED'; echo 'WHY=PYTHON_3_10_OR_NEWER_REQUIRED'; exit 2;
}
mkdir -p -- "$ROOT"
if [ -e "$TARGET" ]; then
  [ -d "$TARGET/.git" ] || {
    echo 'STATUS=BLOCKED'; echo 'WHY=EXISTING_TARGET_NOT_GIT'; exit 2;
  }
  [ "$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || :)" = "$PIN" ] || {
    echo 'STATUS=BLOCKED'; echo 'WHY=PINNED_REVISION_CONFLICT'; exit 2;
  }
  [ -z "$(git -C "$TARGET" status --porcelain --untracked-files=all)" ] || {
    echo 'STATUS=BLOCKED'; echo 'WHY=CAMPAIGN_CHECKOUT_HAS_UNCOMMITTED_WORK'; exit 2;
  }
else
  STAGING="$(mktemp -d "$ROOT/.repl-v030-clone.XXXXXXXX")"
  cleanup() {
    if [ -n "${STAGING:-}" ] && [ -d "$STAGING" ]; then
      rm -rf -- "$STAGING"
    fi
  }
  trap cleanup EXIT
  git clone --quiet --no-checkout "$REPO" "$STAGING" || {
    echo 'STATUS=BLOCKED'; echo 'WHY=GITHUB_FETCH_FAILED'; exit 2;
  }
  git -C "$STAGING" -c core.autocrlf=false checkout --quiet --detach "$PIN" || {
    echo 'STATUS=BLOCKED'; echo 'WHY=PINNED_CHECKOUT_FAILED'; exit 2;
  }
  [ "$(git -C "$STAGING" rev-parse HEAD)" = "$PIN" ] || {
    echo 'STATUS=BLOCKED'; echo 'WHY=CHECKOUT_COMMIT_MISMATCH'; exit 2;
  }
  mv -- "$STAGING" "$TARGET"
  STAGING=''
  trap - EXIT
fi
verify_blob() {
  local relative="$1" expected="$2" actual
  [ -f "$TARGET/$relative" ] || {
    printf 'STATUS=BLOCKED\nWHY=SOURCE_FILE_MISSING:%s\n' "$relative"; exit 2;
  }
  actual="$(git -C "$TARGET" hash-object -- "$relative")"
  printf 'SOURCE_FILE=%s\nEXPECTED_BLOB=%s\nACTUAL_BLOB=%s\n' \
    "$relative" "$expected" "$actual"
  [ "$actual" = "$expected" ] || {
    echo 'STATUS=BLOCKED'; echo 'WHY=GIT_SOURCE_IDENTITY_MISMATCH'; exit 2;
  }
}
verify_blob "$SCRIPT" "$ENGINE_BLOB"
verify_blob "$PARENT" "$PARENT_BLOB"
verify_blob "$GRANDPARENT" "$GRANDPARENT_BLOB"
echo 'GITHUB_SOURCE_READBACK=VERIFIED'
echo 'ACCEPTED_MANE=LOCKED'
echo 'TAIL_CONTROL_COUNT=4'
echo 'BONE_LENGTHS=TAPERED_TOWARD_TIP'
echo 'REVIEW=FULL_TEXTURED_TRIANGLES_NOT_POINT_DOTS'
echo 'SOURCE_ASSET=SHA256_GUARDED_NOT_OVERWRITTEN'
exec python3 "$TARGET/$SCRIPT" run --revision "$PIN" "$@"
