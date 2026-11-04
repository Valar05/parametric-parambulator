#!/data/data/com.termux/files/usr/bin/bash
# One-version Termux entrypoint. Actual source is also committed to parametric-parambulator.
set -euo pipefail
SELF="$(realpath "${BASH_SOURCE[0]}")"
HERE="$(dirname "$SELF")"
PACKET="$(dirname "$HERE")"
[ -f "$PACKET/manifest.json" ] || { echo 'BLOCKED:PACKET_NOT_FOUND'; exit 2; }
printf 'CAMPAIGN=%s\nLANE=%s\n' 'OBSIDIANTI_PELVIS_WEAPON_v1.2.1' 'TERMUX_GIT_ONLY'
exec python3 "$HERE/OBSIDIANTI_PELVIS_WEAPON_RUN_v1.2.1.py" "$PACKET"
