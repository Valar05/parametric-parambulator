#!/data/data/com.termux/files/usr/bin/bash
# Self-locating Termux Git recovery, no solver rerun, no unrelated worktree cleanup.
set -euo pipefail
SELF="$(realpath "${BASH_SOURCE[0]}")"
PACKET="$(dirname "$(dirname "$SELF")")"
[ -f "$PACKET/manifest.json" ] || { echo 'BLOCKED:RECOVERY_PACKET_ROOT_MISSING'; exit 2; }
echo 'CAMPAIGN=OBSIDIANTI_PELVIS_WEAPON_RECOVER_v1.2.2'
echo 'LANE=TERMUX_GIT_ONLY; NO_NEW_GLB; NO_RESOLVE'
exec python3 "$PACKET/campaigns/OBSIDIANTI_PELVIS_WEAPON_RECOVER_RUN_v1.2.2.py" "$PACKET"
