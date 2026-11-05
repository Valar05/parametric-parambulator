#!/data/data/com.termux/files/usr/bin/bash
# Versioned repository entry for Lionheart / Obsidianti comparison, v1.6.0.
# Launch from the single SHA-verified user packet; no standalone network bootstrap.
set -Eeuo pipefail
[[ $# -eq 1 && -d "$1" ]] || { echo 'Use the verified v1.6.0 Termux campaign packet'; exit 2; }
exec python3 -B "$(dirname "$0")/LIONHEART_COMPARE_RUN_v1.6.0.py" "$1" UNVERIFIED_STANDALONE
