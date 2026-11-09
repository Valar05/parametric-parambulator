#!/data/data/com.termux/files/usr/bin/bash
# Full one-shot executable delivered as OBSIDIANTI_IK41_PREVIEW_v1.0.5_LAUNCH.sh
# This repo metadata entry points at the verified independently downloaded campaign launcher.
set -Eeuo pipefail
f="$HOME/storage/downloads/OBSIDIANTI_IK41_PREVIEW_v1.0.5_LAUNCH.sh"
[ -f "$f" ] || { echo 'BLOCKED:VERSIONED_LAUNCHER_NOT_IN_DOWNLOADS'; exit 1; }
bash "$f"
