#!/usr/bin/env bash
# REPL_HAIR_FIVE_CONTROLS v0.2.0: one-command Android/Termux launcher.
# Source authored in GitHub first. Never touches existing Pose Lab checkout.
# A linked GitHub source page is NOT this deliverable; this .sh file is.
set -Eeuo pipefail
CAMPAIGN="REPL_HAIR_FIVE_CONTROLS"
VERSION="0.2.0"
PIN="4bdd0954c2843460f52879281ef992bff6e695ad"
PY_BLOB="287567d6baf8e8fa415580dc57ee86600772f797"
ROOT="$HOME/.local/share/repl-hair-campaigns"
SHORT_PIN="$(printf '%s' "$PIN" | cut -c1-12)"
TARGET="$ROOT/repl-v$VERSION-$SHORT_PIN"
REPO="https://github.com/Valar05/parametric-parambulator.git"
SCRIPT="campaigns/repl_hair_five_controls_v0_2_0.py"
printf 'CAMPAIGN=%s\nVERSION=%s\nLAUNCHER=%s\n' "$CAMPAIGN" "$VERSION" "$0"
printf 'LAUNCHER_SHA256=%s\nPINNED_GIT_SHA=%s\n' "$(sha256sum -- "$0" | cut -d' ' -f1)" "$PIN"
printf 'EXPECTED_PYTHON_GIT_BLOB=%s\n' "$PY_BLOB"
for tool in git python3 sha256sum; do
  command -v "$tool" >/dev/null 2>&1 || {
    printf 'CAMPAIGN_STATUS=BLOCKED\nREASON=MISSING_EXECUTABLE:%s\n' "$tool"
    exit 2
  }
done
mkdir -p "$ROOT"
if [ -e "$TARGET" ]; then
  [ -d "$TARGET/.git" ] || {
    echo 'CAMPAIGN_STATUS=BLOCKED'; echo 'REASON=EXISTING_TARGET_NOT_A_REPOSITORY'
    exit 2
  }
  [ "$(git -C "$TARGET" rev-parse HEAD 2>/dev/null || :)" = "$PIN" ] || {
    echo 'CAMPAIGN_STATUS=BLOCKED'; echo 'REASON=PINNED_REVISION_CONFLICT'
    exit 2
  }
  [ -z "$(git -C "$TARGET" status --porcelain --untracked-files=all)" ] || {
    echo 'CAMPAIGN_STATUS=BLOCKED'; echo 'REASON=DIRTY_CAMPAIGN_CHECKOUT'
    exit 2
  }
else
  STAGE="$(mktemp -d "$ROOT/.repl-v020-clone.XXXXXXXX")"
  cleanup() { if [ -n "$STAGE" ] && [ -d "$STAGE" ]; then rm -rf -- "$STAGE"; fi; }
  trap cleanup EXIT
  git clone --quiet --no-checkout "$REPO" "$STAGE" || {
    echo 'CAMPAIGN_STATUS=BLOCKED'; echo 'REASON=GIT_CLONE_FAILED'; exit 2;
  }
  git -C "$STAGE" -c core.autocrlf=false checkout --quiet --detach "$PIN" || {
    echo 'CAMPAIGN_STATUS=BLOCKED'; echo 'REASON=PINNED_CHECKOUT_FAILED'; exit 2;
  }
  [ "$(git -C "$STAGE" rev-parse HEAD)" = "$PIN" ] || {
    echo 'CAMPAIGN_STATUS=BLOCKED'; echo 'REASON=GIT_READBACK_MISMATCH'; exit 2;
  }
  mv -- "$STAGE" "$TARGET"
  STAGE=""
  trap - EXIT
fi
SOURCE_FILE="$TARGET/$SCRIPT"
[ -f "$SOURCE_FILE" ] || { echo 'CAMPAIGN_STATUS=BLOCKED';echo 'REASON=PYTHON_SOURCE_MISSING';exit 2; }
ACTUAL_BLOB="$(git -C "$TARGET" hash-object -- "$SCRIPT")"
printf 'ACTUAL_PYTHON_GIT_BLOB=%s\n' "$ACTUAL_BLOB"
[ "$ACTUAL_BLOB" = "$PY_BLOB" ] || {
  echo 'CAMPAIGN_STATUS=BLOCKED'; echo 'REASON=PYTHON_SOURCE_HASH_MISMATCH';exit 2;
}
printf 'PINNED_CHECKOUT=VERIFIED\nPYTHON_SOURCE=VERIFIED\n'
exec python3 "$SOURCE_FILE" run --revision "$PIN" "$@"
