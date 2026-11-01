#!/data/data/com.termux/files/usr/bin/bash
# Repl v0.5.2. One ZIP, one Termux invocation, one real GitHub canonical GLB.
# Correct body/tail socket pivot and re-key 14-second straightening.
set -Eeuo pipefail
export PYTHONDONTWRITEBYTECODE=1
export GIT_TERMINAL_PROMPT=0
export GIT_LFS_SKIP_SMUDGE=1
CAMPAIGN=REPL_TAIL_PIVOT_ANCHOR
VERSION=0.5.2
ZIP="${1:?Pass exact verified owner ZIP}"
BUNDLE=REPL_TAIL_PIVOT_ANCHOR_v0.5.2
STATE="$HOME/.local/share/parametric-parambulator/tail-pivot-v0.5.2"
PACKET="$STATE/packet"
DOWNLOADS="$HOME/storage/downloads"
block(){ printf 'STATUS=BLOCKED\nCAUSE=%s\nREMOTE_CANONICAL_UPDATE=NOT_CONFIRMED\n' "$1"; exit 2; }
sha(){ sha256sum -- "$1" | cut -d ' ' -f 1; }
for name in bash git python3 sha256sum mktemp tee; do
 command -v "$name" >/dev/null 2>&1 || block "REQUIRED_TERMUX_COMMAND_MISSING:$name"
done
python3 -c 'import sys;sys.exit(0 if sys.version_info >= (3,10) else 2)' || block 'PYTHON_3_10_REQUIRED'
[ -d "$DOWNLOADS" ] || block 'TERMUX_DOWNLOADS_NOT_MOUNTED'
[ -f "$ZIP" ] || block 'VERIFIED_ZIP_NOT_FOUND'
mkdir -p -- "$STATE"
LOG="$DOWNLOADS/REPL_TAIL_PIVOT_v0.5.2_operator.log"
exec > >(tee -a "$LOG") 2>&1
printf 'CAMPAIGN=%s\nVERSION=%s\nLANE=TERMUX_GIT\n' "$CAMPAIGN" "$VERSION"
printf 'OPERATOR_LOG=%s\nZIP_PATH=%s\nZIP_SHA256=%s\n' "$LOG" "$ZIP" "$(sha "$ZIP")"
printf 'OUTPUT_GLB_COUNT_REQUIRED=1\nDESTINATION=assets/repl/Repl.glb\n'
# The outer one-paste command verifies the entire ZIP SHA. This extractor
# separately validates the contract, members, SHA of every payload and
# preexisting versioned extracted packet before launching anything.
python3 - "$ZIP" "$STATE" "$PACKET" "$BUNDLE" <<'PY' || block 'PAYLOAD_EXTRACT_OR_READBACK_FAILED'
import hashlib,json,os,pathlib,shutil,sys,tempfile,zipfile
zipfile_path,state_dir,target_dir,bundle=sys.argv[1:]
state=pathlib.Path(state_dir);target=pathlib.Path(target_dir)
files={'README.md','campaign/contract.json','campaign/run-termux.sh',
       'campaign/driver.py','campaign/model.py','campaign/blender_review.py'}
expected={bundle+'/'+x for x in files}
with zipfile.ZipFile(zipfile_path) as z:
    infos=z.infolist()
    if len(infos)!=len(expected) or {i.filename for i in infos}!=expected:
        raise SystemExit('ZIP_EXACT_MEMBER_SET_MISMATCH')
    if any(i.is_dir() or i.flag_bits&1 or i.file_size>300000 or
           ((i.external_attr>>16)&0o170000)==0o120000 or
           '..' in pathlib.PurePosixPath(i.filename).parts
           for i in infos):
        raise SystemExit('UNSAFE_ZIP_ENTRY_OR_UNBOUNDED_SIZE')
    contract=json.loads(z.read(bundle+'/campaign/contract.json'))
    if contract.get('campaign')!='REPL_TAIL_PIVOT_ANCHOR' or contract.get('version')!='0.5.2':
        raise SystemExit('WRONG_CAMPAIGN_CONTRACT')
    for name,digest in contract['sha256_payloads'].items():
        if name not in files or name=='campaign/contract.json':
            raise SystemExit('UNEXPECTED_CONTRACT_FILE')
        if hashlib.sha256(z.read(bundle+'/'+name)).hexdigest()!=digest:
            raise SystemExit('PAYLOAD_HASH_MISMATCH:'+name)
    if set(contract['sha256_payloads'])!=files-{'campaign/contract.json'}:
        raise SystemExit('PAYLOAD_LIST_NOT_COMPLETE')
    if target.exists():
        for relative in files:
            p=target/relative
            if not p.is_file() or p.read_bytes()!=z.read(bundle+'/'+relative):
                raise SystemExit('EXTRACTED_PACKET_DIRTY_OR_OTHER_VERSION:'+relative)
        print('EXTRACTED_PACKET=ALREADY_VERIFIED_IDENTICAL',flush=True)
    else:
        tmp=pathlib.Path(tempfile.mkdtemp(prefix='.extract-v052-',dir=state))
        try:
            for relative in files:
                path=tmp/relative
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(z.read(bundle+'/'+relative))
            os.replace(tmp,target)
        finally:
            if tmp.exists():shutil.rmtree(tmp)
        print('EXTRACTED_PACKET=ATOMIC_SHA_VERIFIED',flush=True)
PY
printf 'MODEL_REPAIR_PAYLOAD_SHA256=%s\n' "$(sha "$PACKET/campaign/model.py")"
printf 'BLENDER_ON_TERMUX_PATH=%s\n' "$(command -v blender || echo NO)"
# The only production mutation occurs now, through the owner's TERMUX Git.
# No direct ChatGPT GitHub write APIs; no script fishing expedition.
python3 -u "$PACKET/campaign/driver.py" \
 --packet "$PACKET" --state "$STATE" --downloads "$DOWNLOADS" \
 || block 'DRIVER_FAILED__SEE_EXPLICIT_CAUSE_IN_LOG'
# The GLB remains ONLY in the repo. Render optional full textures, no GLB exports.
CANON="$STATE/repo/assets/repl/Repl.glb"
RENDER="$DOWNLOADS/REPL_TAIL_PIVOT_v0.5.2_blender_frames"
if command -v blender >/dev/null 2>&1 && [ -f "$CANON" ]; then
 if [ -e "$RENDER" ] && [ ! -d "$RENDER" ]; then
  echo 'BLENDER_REVIEW=BLOCKED_OUTPUT_FILENAME_COLLISION'
 else
  mkdir -p -- "$RENDER"
  if blender -b -t 4 --python "$PACKET/campaign/blender_review.py" -- "$CANON" "$RENDER"; then
   echo 'BLENDER_REVIEW=FULL_TEXTURED_FRAMES_PUBLISHED'
   if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -hide_banner -loglevel error -y -framerate 2 -pattern_type glob \
     -i "$RENDER/Repl_v0.5.2_side_f*.png" \
     -vf 'fps=10,scale=960:-1:flags=lanczos' \
     "$RENDER/REPL_TAIL_PIVOT_v0.5.2.gif" \
     && echo 'GIF=FULL_TEXTURED_RENDERED' || echo 'GIF=OPTIONAL_RENDER_FAILED'
   fi
  else
   echo 'BLENDER_REVIEW=FAILED_BROWSER_REVIEW_REMAINS_AVAILABLE'
  fi
 fi
else
 echo 'BLENDER_REVIEW=NOT_ON_TERMUX_PATH__REAL_GLB_TEXTURED_BROWSER_AVAILABLE'
fi
echo 'CAMPAIGN_TERMINATED=YES'
