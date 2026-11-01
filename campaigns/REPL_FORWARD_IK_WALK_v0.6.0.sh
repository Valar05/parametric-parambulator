#!/data/data/com.termux/files/usr/bin/bash
# REPL_FORWARD_IK_WALK v0.6.0 | one-command, one-ZIP, Termux Git lane.
# No direct GitHub API writes. No additional GLB in the repo. No treadmill clips.
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1
export GIT_TERMINAL_PROMPT=0
VERSION='0.6.0'
NAME='REPL_FORWARD_IK_WALK_v0.6.0'
SOURCE_ZIP="${1:-}"
DOWNLOADS="$HOME/storage/downloads"
STATE="$HOME/.local/share/repl-campaigns/forward-ik-v0.6.0"
PACKET="$STATE/packet"
mkdir -p -- "$DOWNLOADS" "$STATE"
LOG="$DOWNLOADS/${NAME}_operator.log"
exec > >(tee "$LOG") 2>&1
printf 'FULL_OPERATOR_LOG=%s\n' "$LOG"
printf 'CAMPAIGN=REPL_FORWARD_FOUR_BEAT_IK_WALK\nVERSION=%s\n' "$VERSION"
printf 'EXECUTION_LANE=TERMUX_GIT\nIN_PLACE_WALK=NEVER\n'
printf 'ZIP=%s\n' "$SOURCE_ZIP"
[ -f "$SOURCE_ZIP" ] || { echo 'STATUS=BLOCKED'; echo 'CAUSE=MISSING_CAMPAIGN_ZIP'; exit 2; }
for cmd in python3 git sha256sum; do
 command -v "$cmd" >/dev/null 2>&1 || {
  printf 'STATUS=BLOCKED\nCAUSE=DEPENDENCY_MISSING:%s\n' "$cmd"; exit 2;
 }
done
python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,10) else 2)' || {
 echo 'STATUS=BLOCKED';echo 'CAUSE=PYTHON_3_10_REQUIRED';exit 2;
}
printf 'ZIP_SHA256=%s\n' "$(sha256sum -- "$SOURCE_ZIP" | cut -d' ' -f1)"
python3 - "$SOURCE_ZIP" "$PACKET" <<'PY'
import json,os,hashlib,sys,zipfile,tempfile,shutil
from pathlib import Path
archive=Path(sys.argv[1]).resolve()
packet=Path(sys.argv[2]).resolve()
root='REPL_FORWARD_IK_WALK_v0.6.0/'
with zipfile.ZipFile(archive) as z:
 info=z.getinfo(root+'manifest.json')
 meta=json.loads(z.read(info))
 expected=meta['files']
 names=set(z.namelist())
 valid={root+'manifest.json'}|{root+name for name in expected}
 if names!=valid:raise SystemExit('BLOCKED: PACKET_EXTRA_OR_MISSING_MEMBERS')
 for filename,h in expected.items():
  if filename.startswith('/') or '..' in Path(filename).parts:
   raise SystemExit('BLOCKED: UNSAFE_PACKET_PATH')
  data=z.read(root+filename)
  if hashlib.sha256(data).hexdigest()!=h:
   raise SystemExit('BLOCKED: ZIP_MEMBER_SHA_MISMATCH:'+filename)
 if packet.exists():
  for filename,h in expected.items():
   p=packet/filename
   if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:
    raise SystemExit('BLOCKED: EXISTING_PACKET_CHECKSUM_MISMATCH:'+filename)
  print('PACKET=EXISTING_IMMUTABLE_PACKET_REVERIFIED',flush=True)
 else:
  packet.parent.mkdir(parents=True,exist_ok=True)
  staging=Path(tempfile.mkdtemp(prefix='.repl-walk-packet.',dir=packet.parent))
  try:
   for filename,h in expected.items():
    p=staging/filename;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(z.read(root+filename))
   (staging/'manifest.json').write_bytes(z.read(root+'manifest.json'))
   if packet.exists():raise SystemExit('BLOCKED: PACKET_COLLISION')
   staging.rename(packet)
  finally:
   if staging.exists():shutil.rmtree(staging)
  print('PACKET=ATOMIC_EXTRACT_AND_HASH_READBACK_PASS',flush=True)
print('PAYLOAD_PYTHON_SHA256='+expected['campaign/driver.py'],flush=True)
PY
python3 "$PACKET/campaign/selftest.py"
# One initial campaign invocation owns research, four legs, groundedness,
# body response, tail/head, real textured evidence, git commit and readback.
python3 "$PACKET/campaign/driver.py" --packet "$PACKET/campaign"
