#!/data/data/com.termux/files/usr/bin/bash
# Exactly one Termux entrypoint, physically inside the single campaign ZIP.
set -Eeuo pipefail
# Every invocation must preserve immutable extracted packet membership.
export PYTHONDONTWRITEBYTECODE=1
VERSION='0.6.19'
CAMPAIGN='REPL_CARTOON_FK_HOOF_WALK'
ZIP="${1:-}"
DOWNLOADS="$HOME/storage/downloads"
STATE="$HOME/.local/share/repl-campaigns/cartoon-fk-hoof-v0.6.19"
PACKET="$STATE/packet"
LOG="$DOWNLOADS/REPL_CARTOON_FK_HOOF_WALK_v0.6.19_OPERATOR.log"
printf 'CAMPAIGN=%s\nVERSION=%s\nLANE=TERMUX_GIT\nZIP=%s\n' "$CAMPAIGN" "$VERSION" "$ZIP"
for cmd in python3 git sha256sum; do
 command -v "$cmd" >/dev/null 2>&1 || { echo "CAMPAIGN_STATUS=BLOCKED";echo "CAUSE=REQUIRED_TERMUX_PROGRAM_MISSING:$cmd";exit 2; }
done
[ -d "$DOWNLOADS" ] || { echo 'CAMPAIGN_STATUS=BLOCKED';echo 'CAUSE=TERMUX_DOWNLOADS_NOT_MOUNTED';exit 2; }
[ -f "$ZIP" ] || { echo 'CAMPAIGN_STATUS=BLOCKED';echo 'CAUSE=ZIP_NOT_FOUND';exit 2; }
case "$ZIP" in "$DOWNLOADS"/*) ;; *) echo 'CAMPAIGN_STATUS=BLOCKED';echo 'CAUSE=ZIP_NOT_IN_ANDROID_DOWNLOADS';exit 2;; esac
printf 'ZIP_SHA256=%s\n' "$(sha256sum "$ZIP" | cut -d' ' -f1)"
mkdir -p "$STATE"
python3 - "$ZIP" "$PACKET" <<'PY'
import hashlib,json,os,pathlib,sys,tempfile,shutil,zipfile
sys.dont_write_bytecode=True
src=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);root='REPL_CARTOON_FK_HOOF_WALK_v0.6.19/'
with zipfile.ZipFile(src) as z:
    bad=z.testzip()
    if bad:raise SystemExit('BLOCKED: ZIP_CORRUPT:'+bad)
    m=json.loads(z.read(root+'manifest.json'))
    if m.get('campaign')!='REPL_CARTOON_FK_HOOF_WALK' or m.get('version')!='0.6.19':
        raise SystemExit('BLOCKED: WRONG_CAMPAIGN_PACKET')
    members=m['sha256']
    expected={root+name for name in members}|{root+'manifest.json'}
    actual={name for name in z.namelist() if not name.endswith('/')}
    if actual!=expected or len(actual)!=len(z.infolist()):
        raise SystemExit('BLOCKED: PACKET_UNEXPECTED_OR_DUPLICATE_MEMBERS')
    payload={}
    for relative,digest in members.items():
        pp=pathlib.PurePosixPath(relative)
        if pp.is_absolute() or '..' in pp.parts:
            raise SystemExit('BLOCKED: MALFORMED_ZIP_PATH')
        data=z.read(root+relative)
        if hashlib.sha256(data).hexdigest()!=digest:
            raise SystemExit('BLOCKED: ZIP_MEMBER_HASH_MISMATCH:'+relative)
        payload[relative]=data
    payload['manifest.json']=z.read(root+'manifest.json')
if out.exists():
    if not out.is_dir():raise SystemExit('BLOCKED: PACKET_PATH_COLLISION')
    if {str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}!=set(payload):
        raise SystemExit('BLOCKED: PREVIOUS_PACKET_FILE_SET_CHANGED')
    for name,data in payload.items():
        p=out/name
        if not p.is_file() or p.read_bytes()!=data:
            raise SystemExit('BLOCKED: PREVIOUS_PACKET_CONTENT_CHANGED:'+name)
    print('PACKET=EXISTING_EXTRACT_VERIFIED',flush=True)
else:
    tmp=pathlib.Path(tempfile.mkdtemp(prefix='.repl-cartoon-fk-hoof-v0618-',dir=out.parent))
    try:
        for name,data in payload.items():
            p=tmp/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(data)
            if p.read_bytes()!=data:raise SystemExit('BLOCKED: PACKET_EXTRACT_READBACK_MISMATCH')
        os.replace(tmp,out)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    print('PACKET=NEW_ATOMIC_EXTRACT_VERIFIED',flush=True)
print('REPO_GLB_POLICY=ONE_CANONICAL_MODEL',flush=True)
PY
echo "FULL_OPERATOR_LOG=$LOG"
set +e
python3 "$PACKET/campaign/selftest.py" 2>&1 | tee -a "$LOG"
code="${PIPESTATUS[0]}"
if [ "$code" -ne 0 ]; then
 echo "CAMPAIGN_STATUS=BLOCKED" | tee -a "$LOG"
 echo "CAUSE=PACKET_STATIC_SELFTEST_FAILED" | tee -a "$LOG"
 exit "$code"
fi
python3 "$PACKET/campaign/driver.py" --packet "$PACKET/campaign" 2>&1 | tee -a "$LOG"
code="${PIPESTATUS[0]}"
if [ "$code" -ne 0 ]; then
 echo "CAMPAIGN_STATUS=BLOCKED_OR_FAILED" | tee -a "$LOG"
 echo "TERMUX_DRIVER_EXIT=$code" | tee -a "$LOG"
 exit "$code"
fi
echo 'CAMPAIGN_STATUS=TERMUX_ENTRYPOINT_COMPLETED_ZERO' | tee -a "$LOG"
