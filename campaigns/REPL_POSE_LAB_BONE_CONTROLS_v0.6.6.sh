#!/data/data/com.termux/files/usr/bin/bash
# First invocation: bash <this-packet/run-termux.sh> ~/storage/downloads/REPL_POSE_LAB_BONE_CONTROLS_v0.6.6.zip
# Actually delivered launcher: one pasted Python ZIP-SHA verification/extract/exec command.
# Repl source of truth: Valar05/parametric-parambulator; never Pose Lab workspace.
set -Eeuo pipefail
VERSION=0.6.6
NAME=REPL_POSE_LAB_BONE_CONTROLS
ZIP="${1:-}"
DOWNLOADS="$HOME/storage/downloads"
PRIVATE="$HOME/.local/share/repl-campaigns/pose-lab-bones-v0.6.6"
PACKET="$PRIVATE/packet"
LOG="$DOWNLOADS/${NAME}_v${VERSION}_OPERATOR.log"
if [[ ! -d "$DOWNLOADS" || ! -f "$ZIP" ]]; then
  printf 'CAMPAIGN_STATUS=BLOCKED\nCAUSE=TERMUX_DOWNLOADS_OR_VERSIONED_ZIP_MISSING\n' >&2
  exit 2
fi
mkdir -p "$PRIVATE"
# A single immutable durable log, shown live as the campaign proceeds.
exec > >(tee -a "$LOG") 2>&1
printf 'CAMPAIGN=%s\nVERSION=%s\nLANE=TERMUX_GIT_ONLY\n' "$NAME" "$VERSION"
printf 'VERSIONED_ZIP=%s\n' "$ZIP"
printf 'VERSIONED_ZIP_SHA256=%s\n' "$(sha256sum "$ZIP" | awk '{print $1}')"
printf 'OPERATOR_LOG=%s\n' "$LOG"
python3 - "$ZIP" "$PRIVATE" <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,sys,tempfile,zipfile
file=Path(sys.argv[1]);root=Path(sys.argv[2]);final=root/'packet'
prefix='REPL_POSE_LAB_BONE_CONTROLS_v0.6.6/'
with zipfile.ZipFile(file) as z:
 names=z.namelist()
 if len(names)!=len(set(names)) or not names or any(not x.startswith(prefix) or
     x.startswith('/') or '\\' in x or '..' in Path(x).parts for x in names):
  raise SystemExit('CAMPAIGN_STATUS=BLOCKED:ZIP_PATH_OR_DUPLICATE_ENTRY_UNSAFE')
 m=json.loads(z.read(prefix+'manifest.json'))
 expected=set(m['files'])
 got={n[len(prefix):] for n in names if not n.endswith('/') and n!=prefix+'manifest.json'}
 if got!=expected:raise SystemExit('CAMPAIGN_STATUS=BLOCKED:PACKET_FILE_SET_MISMATCH')
 for name,meta in m['files'].items():
  b=z.read(prefix+name)
  if hashlib.sha256(b).hexdigest()!=meta['sha256'] or len(b)!=meta['bytes']:
   raise SystemExit('CAMPAIGN_STATUS=BLOCKED:PACKET_HASH_MISMATCH:'+name)
 if final.exists():
  for name,meta in m['files'].items():
   dst=final/name
   if not dst.is_file() or hashlib.sha256(dst.read_bytes()).hexdigest()!=meta['sha256']:
    raise SystemExit('CAMPAIGN_STATUS=BLOCKED:EXISTING_PACKET_CHANGED:'+name)
  print('PACKET=EXISTING_READBACK_VERIFIED',flush=True)
 else:
  tmp=Path(tempfile.mkdtemp(prefix='.packet-v066-',dir=root))
  try:
   for name in expected:
    dst=tmp/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(z.read(prefix+name))
   (tmp/'manifest.json').write_bytes(z.read(prefix+'manifest.json'))
   os.replace(tmp,final)
  finally:
   if tmp.exists():shutil.rmtree(tmp)
  print('PACKET=NEW_ATOMIC_EXTRACT_VERIFIED',flush=True)
 print('PACKET_FILES_SHA_VERIFIED='+str(len(expected)),flush=True)
PY
python3 "$PACKET/campaign/selftest.py" --packet "$PACKET"
python3 "$PACKET/campaign/driver.py" --packet "$PACKET/campaign"
