#!/data/data/com.termux/files/usr/bin/bash
# Source-verified, versioned one-entrypoint Termux Git campaign.
set -euo pipefail
SELF="$(realpath "${BASH_SOURCE[0]}")"
ROOT="$(dirname "$(dirname "$SELF")")"
export PYTHONDONTWRITEBYTECODE=1
[ -r "$ROOT/manifest.json" ] || { echo 'BLOCKED:INCOMPLETE_PACKET'; exit 2; }
exec python3 "$ROOT/campaigns/OBSIDIANTI_CONTACT_IK_RUN_v1.3.0.py" "$ROOT"
