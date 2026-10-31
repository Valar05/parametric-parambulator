#!/data/data/com.termux/files/usr/bin/bash
# Repl v0.5.1 canonical tail straighten, Termux-first single-ZIP campaign.
# One model in GitHub, one ZIP in Android Downloads, no standalone .sh download.
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1
export GIT_TERMINAL_PROMPT=0
export GIT_LFS_SKIP_SMUDGE=1
CAMPAIGN=REPL_TAIL_CANONICAL_STRAIGHTEN
VERSION=0.5.1
ZIP="${1:?Expected verified campaign ZIP path}"
BUNDLE=REPL_TAIL_CANONICAL_v0.5.1
STATE="$HOME/.local/share/parametric-parambulator/tail-straighten-v0.5.1"
PACKET="$STATE/packet"
DOWNLOADS="$HOME/storage/downloads"

block(){ printf 'CAMPAIGN_STATUS=BLOCKED\nCAUSE=%s\nCANONICAL_GLB_REMOTE_UPDATE=UNVERIFIED\n' "$1"; exit 2; }
sha(){ sha256sum -- "$1" | cut -d' ' -f1; }
for cmd in bash git python3 sha256sum mktemp; do
  command -v "$cmd" >/dev/null 2>&1 || block "TERMUX_COMMAND_MISSING:$cmd"
done
python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,10) else 2)' || block 'PYTHON_3_10_REQUIRED'
[ -d "$DOWNLOADS" ] || block 'TERMUX_DOWNLOADS_MOUNT_MISSING'
[ -f "$ZIP" ] || block 'CAMPAIGN_ZIP_MISSING'
command -v tee >/dev/null 2>&1 || block 'TERMUX_TEE_MISSING'
LOG="$DOWNLOADS/REPL_TAIL_CANONICAL_v0.5.1_operator.log"
exec > >(tee -a "$LOG") 2>&1
printf 'FULL_OPERATOR_LOG=%s\n' "$LOG"
printf 'CAMPAIGN=%s\nVERSION=%s\nLANE=TERMUX_GIT\nZIP=%s\nZIP_SHA256=%s\n' \
  "$CAMPAIGN" "$VERSION" "$ZIP" "$(sha "$ZIP")"
mkdir -p -- "$STATE"
# All payload members are explicit and hashed; no arbitrary archive extraction.
# The ZIP is SHA-checked before invoking this loader by the one-paste command.
python3 - "$ZIP" "$STATE" "$PACKET" "$BUNDLE" <<'PY' || block 'SAFE_ZIP_EXTRACT_OR_READBACK_FAILED'
import hashlib,json,os,pathlib,shutil,sys,tempfile,zipfile
zip_path,state,target,bundle=sys.argv[1:]
state=pathlib.Path(state);target=pathlib.Path(target)
manifest_name=bundle+'/campaign/contract.json'
allowed={bundle+'/README.md',manifest_name}
allowed|={bundle+'/campaign/'+x for x in (
 'run-termux.sh','driver.py','blender_review.py')}
with zipfile.ZipFile(zip_path) as z:
  infos=z.infolist()
  if {i.filename for i in infos}!=allowed or len(infos)!=len(allowed):
    raise SystemExit('ZIP_MEMBER_SET_MISMATCH')
  if any(i.is_dir() or i.flag_bits&1 or i.file_size>400000 or
         ((i.external_attr>>16)&0o170000)==0o120000 for i in infos):
    raise SystemExit('BAD_ZIP_MEMBER_TYPE_OR_SIZE')
  contract=json.loads(z.read(manifest_name))
  if contract.get('campaign')!='REPL_TAIL_CANONICAL_STRAIGHTEN' or contract.get('version')!='0.5.1':
    raise SystemExit('CAMPAIGN_CONTRACT_MISMATCH')
  checks=contract['packageFileSha256']
  for member in allowed:
    data=z.read(member)
    if member==manifest_name:continue
    name=member[len(bundle)+1:]
    if hashlib.sha256(data).hexdigest()!=checks.get(name):
      raise SystemExit('PAYLOAD_SHA256_MISMATCH:'+name)
  if target.exists():
    for member in allowed:
      name=member[len(bundle)+1:]
      path=target/name
      if not path.is_file() or path.read_bytes()!=z.read(member):
        raise SystemExit('PREEXISTING_PACKET_DIRTY_OR_CHANGED:'+name)
    print('PACKET=EXISTING_IDENTICAL_VERSION_VERIFIED')
  else:
    tmp=pathlib.Path(tempfile.mkdtemp(prefix='.extract-v051-',dir=state))
    try:
      for member in allowed:
        p=tmp/member[len(bundle)+1:]
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(z.read(member))
      os.replace(tmp,target)
    finally:
      if tmp.exists():shutil.rmtree(tmp)
    print('PACKET=ATOMIC_EXTRACT_AND_SHA_READBACK_PASS')
PY
printf 'PAYLOAD_PYTHON=%s\n' "$(sha "$PACKET/campaign/driver.py")"
printf 'REVIEW_RENDERER=%s\n' "$(command -v blender || echo NOT_ON_TERMUX_PATH)"
# This single call generates, validates, commits, pushes and reads back ONE
# canonical GLB in the owner's GitHub project. It publishes textured review.
python3 -u "$PACKET/campaign/driver.py" \
  --packet "$PACKET" --state "$STATE" --downloads "$DOWNLOADS" || block 'DRIVER_FAILED__SEE_CAUSE_ABOVE'

# Rendering is evidence, NOT a second model file. Do not redirect execution
# into Pose Lab or use unsupported transport to reach a remote Blender.
CANON="$STATE/repo/assets/repl/Repl.glb"
RENDER="$DOWNLOADS/REPL_TAIL_STRAIGHTEN_v0.5.1_blender_frames"
if command -v blender >/dev/null 2>&1 && [ -f "$CANON" ]; then
  if [ -e "$RENDER" ] && [ ! -d "$RENDER" ]; then
    printf 'BLENDER_REVIEW=BLOCKED_OUTPUT_COLLISION\n'
  else
    mkdir -p -- "$RENDER"
    if blender -b -t 4 --python "$PACKET/campaign/blender_review.py" -- "$CANON" "$RENDER"; then
      printf 'BLENDER_REVIEW=RENDERED_FULL_TEXTURED_FRAMES\n'
      if command -v ffmpeg >/dev/null 2>&1; then
        ffmpeg -hide_banner -loglevel error -y -framerate 2 -pattern_type glob \
          -i "$RENDER/Repl_v0.5.1_side_f*.png" -vf 'fps=10,scale=960:-1:flags=lanczos' \
          "$RENDER/REPL_TAIL_STRAIGHTEN_v0.5.1.gif" \
          && printf 'BLENDER_GIF=RENDERED\n' || printf 'BLENDER_GIF=OPTIONAL_FAILED\n'
      fi
    else
      printf 'BLENDER_REVIEW=FAILED__TEXTURED_BROWSER_REVIEW_STILL_AVAILABLE\n'
    fi
  fi
else
  printf 'BLENDER_REVIEW=NOT_ON_TERMUX_PATH__TEXTURED_BROWSER_REVIEW_AVAILABLE\n'
fi
printf 'CAMPAIGN_TERMINATED=YES\n'
