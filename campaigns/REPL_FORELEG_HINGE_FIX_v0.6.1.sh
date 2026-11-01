#!/data/data/com.termux/files/usr/bin/bash
# Termux launcher inside the single v0.6.1 campaign ZIP.
# No GitHub connector writes. One canonical in-repo GLB. No in-place walk.
set -Eeuo pipefail
VERSION='0.6.1'
CAMPAIGN='REPL_FORELEG_HINGE_FIX'
ZIP="${1:-}"
DOWNLOADS="$HOME/storage/downloads"
STATE="$HOME/.local/share/repl-campaigns/foreleg-ik-v0.6.1"
PACKET="$STATE/packet"
LOG="$DOWNLOADS/REPL_FORELEG_HINGE_FIX_v0.6.1_OPERATOR.log"
echo "CAMPAIGN=$CAMPAIGN"
echo "VERSION=$VERSION"
echo "EXECUTION_LANE=TERMUX_GIT"
echo "ZIP=$ZIP"
for cmd in python3 git sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "CAMPAIGN_STATUS=BLOCKED";echo "CAUSE=REQUIRED_TERMUX_PROGRAM_MISSING:$cmd";exit 2;
  }
done
[ -d "$DOWNLOADS" ] || { echo 'CAMPAIGN_STATUS=BLOCKED';echo 'CAUSE=TERMUX_SHARED_DOWNLOADS_MISSING';exit 2; }
[ -f "$ZIP" ] || { echo 'CAMPAIGN_STATUS=BLOCKED';echo 'CAUSE=ZIP_NOT_FOUND';exit 2; }
case "$ZIP" in
  "$DOWNLOADS"/*) ;;
  *) echo 'CAMPAIGN_STATUS=BLOCKED';echo 'CAUSE=ZIP_NOT_IN_ANDROID_DOWNLOADS';exit 2;;
esac
printf 'ZIP_SHA256=%s\n' "$(sha256sum "$ZIP" | cut -d' ' -f1)"
mkdir -p "$STATE"
# Verify complete contents against the immutable packet manifest and extract
# atomically. Never overwrite an old or modified user-owned campaign packet.
python3 - "$ZIP" "$PACKET" <<'PY'
from __future__ import annotations
import hashlib,json,os,pathlib,sys,tempfile,shutil,zipfile
sys.dont_write_bytecode=True
src=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);root='REPL_FORELEG_HINGE_FIX_v0.6.1/'
with zipfile.ZipFile(src) as z:
    bad=z.testzip()
    if bad:raise SystemExit('BLOCKED: ZIP_CORRUPT:'+bad)
    m=json.loads(z.read(root+'manifest.json'))
    if m.get('campaign')!='REPL_FORELEG_HINGE_FIX' or m.get('version')!='0.6.1':
        raise SystemExit('BLOCKED: WRONG_CAMPAIGN_PACKET')
    members=m['sha256']
    expected=set(root+k for k in members)|{root+'manifest.json'}
    found=set(n for n in z.namelist() if not n.endswith('/'))
    if found!=expected:
        raise SystemExit('BLOCKED: PACKET_UNEXPECTED_FILES')
    payload={}
    for relative,digest in members.items():
        if pathlib.PurePosixPath(relative).is_absolute() or '..' in pathlib.PurePosixPath(relative).parts:
            raise SystemExit('BLOCKED: MALFORMED_ZIP_PATH')
        data=z.read(root+relative)
        if hashlib.sha256(data).hexdigest()!=digest:
            raise SystemExit('BLOCKED: ZIP_MEMBER_HASH_MISMATCH:'+relative)
        payload[relative]=data
    payload['manifest.json']=z.read(root+'manifest.json')
if out.exists():
    if not out.is_dir():raise SystemExit('BLOCKED: PACKET_PATH_COLLISION')
    for name,data in payload.items():
        f=out/name
        if not f.is_file() or f.read_bytes()!=data:
            raise SystemExit('BLOCKED: PREVIOUS_EXTRACTED_PACKET_CHANGED:'+name)
    print('PACKET=VERIFIED_EXISTING_EXTRACT',flush=True)
else:
    temp=pathlib.Path(tempfile.mkdtemp(prefix='.repl-packet-v061-',dir=out.parent))
    try:
        for name,data in payload.items():
            f=temp/name;f.parent.mkdir(parents=True,exist_ok=True)
            f.write_bytes(data)
            if f.read_bytes()!=data:raise SystemExit('BLOCKED: PACKET_EXTRACT_READBACK_MISMATCH')
        os.replace(temp,out)
    finally:
        if temp.exists():shutil.rmtree(temp)
    print('PACKET=NEW_ATOMIC_EXTRACT_VERIFIED',flush=True)
print('NO_EXTRA_GLB=ONE_CANONICAL_GIT_MODEL',flush=True)
PY
# One operator invocation, with a complete readable log in public Downloads.
# A failed pipeline cannot accidentally report success because pipefail is set.
echo "FULL_OPERATOR_LOG=$LOG"
set +e
python3 "$PACKET/campaign/selftest.py" 2>&1 | tee -a "$LOG"
status="${PIPESTATUS[0]}"
if [ "$status" -ne 0 ]; then
  echo "CAMPAIGN_STATUS=BLOCKED" | tee -a "$LOG"
  echo "CAUSE=PACKET_SOURCE_SELFTEST_FAILED" | tee -a "$LOG"
  exit "$status"
fi
python3 "$PACKET/campaign/driver.py" --packet "$PACKET/campaign" 2>&1 | tee -a "$LOG"
status="${PIPESTATUS[0]}"
if [ "$status" -ne 0 ]; then
  echo "CAMPAIGN_STATUS=BLOCKED_OR_FAILED" | tee -a "$LOG"
  echo "TERMUX_DRIVER_EXIT=$status" | tee -a "$LOG"
  exit "$status"
fi
echo 'CAMPAIGN_STATUS=OPERATOR_SCRIPT_EXITED_ZERO' | tee -a "$LOG"
