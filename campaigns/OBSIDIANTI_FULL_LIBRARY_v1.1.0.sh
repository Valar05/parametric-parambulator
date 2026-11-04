#!/data/data/com.termux/files/usr/bin/bash
# Versioned self-locating, packet-verified Termux Git execution entrypoint.
set -euo pipefail
CAMPAIGN=OBSIDIANTI_FULL_LIBRARY_v1.1.0
SELF="$(realpath "${BASH_SOURCE[0]}")"
HERE="$(dirname "$SELF")"
PACKET="$(dirname "$HERE")"
[ -f "$PACKET/manifest.json" ] || { echo 'BLOCKED:PACKET_ROOT_NOT_FOUND'; exit 2; }
printf 'CAMPAIGN=%s\nSCRIPT=%s\n' "$CAMPAIGN" "$SELF"
exec python3 "$HERE/OBSIDIANTI_FULL_LIBRARY_RUN_v1.1.0.py" "$PACKET"
