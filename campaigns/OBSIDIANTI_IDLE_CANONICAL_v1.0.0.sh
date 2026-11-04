#!/data/data/com.termux/files/usr/bin/bash
# OBSIDIANTI_IDLE_CANONICAL_v1.0.0 — self-locating, pinned-source Termux Git campaign.
# Canonical model path: Valar05/parametric-parambulator:assets/obsidianti/Obsidianti.glb
# Never touches the canonical Repl model. First run imports once; reruns verify/skip.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PACKET="${1:-}"
if [[ -z "$PACKET" ]]; then
  echo "BLOCKED: launch through the matching SHA-verified packet launcher" >&2
  exit 2
fi
PACKET="$(CDPATH='' cd -- "$PACKET" && pwd -P)"
[[ "$HERE" == "$PACKET/campaigns" ]] || { echo "BLOCKED: mismatched campaign and packet roots" >&2; exit 2; }
command -v python3 >/dev/null || { echo "BLOCKED: Python 3 required in Termux" >&2; exit 2; }
command -v git >/dev/null || { echo "BLOCKED: Git required in Termux" >&2; exit 2; }
python3 "$HERE/OBSIDIANTI_IDLE_RUN_v1.0.0.py" "$PACKET"
