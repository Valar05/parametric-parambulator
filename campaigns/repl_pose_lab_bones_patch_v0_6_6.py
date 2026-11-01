#!/usr/bin/env python3
"""Pure viewer-template transform, no GLB writes, robust anchor guards."""
from __future__ import annotations

VERSION='0.6.6'
CSS='''
/* Repl Pose Lab: mobile-first, keyboard-accessible controls */
#pose-lab{background:#1f3040;border:2px solid #82a2ba;border-radius:12px;margin:12px 0;padding:12px}
#pose-lab h2{margin:0 0 8px}
#pose-lab .pl-hint{color:#d0e2ec;margin:6px 0}
#pose-lab .pl-readout{color:#b8fff0;word-break:break-word;font-weight:600}
#pose-lab .pl-warning{color:#ffe0a2}
#pose-lab .pl-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0}
#pose-lab button,#pose-lab select,#pose-lab input[type=number]{min-height:44px}
#pose-lab select{min-width:96px;max-width:100%}
#pose-lab .pl-locks{border:1px solid #8a9eb2;border-radius:8px;padding:8px;display:flex;gap:14px;flex-wrap:wrap}
#pose-lab .pl-locks legend{padding:0 6px}
#pose-lab input[type=checkbox]{width:19px;height:19px;accent-color:#41e9d1}
#pose-lab #pl-bone-select{width:100%;max-width:380px}
#pose-lab #pl-step{width:65px;background:#111a29;border:1px solid #8a9eb2;color:#fff;border-radius:6px;padding:7px}
#pose-lab #pl-sensitivity{width:130px}
#pose-lab button:disabled{opacity:.55}
#pose-lab #pl-status{min-height:2em;color:#a9f6dd}
#pose-lab .pl-metadata{font-size:.88rem;color:#b6d2dd}
@media(max-width:520px){#pose-lab{padding:10px}#pose-lab .pl-controls{gap:6px}}
'''
PANEL='''
<section id="pose-lab" aria-label="Pose Lab bone manipulation">
<h2>Pose Lab · Bone Controls v0.6.6</h2>
<p class="pl-hint">Tap a visible bone with one finger to select it. Additional taps add bones (or toggle them off).
With bones selected, twist two fingers to rotate them. Double-tap <strong>empty space</strong> to deselect.
This is a reversible pose reference, not a new walk animation.</p>
<div class="pl-controls">
<label><input type="checkbox" id="pl-skeleton" checked>Skeleton overlay</label>
<label><input type="checkbox" id="pl-edit" disabled>Pose Mode (pause walk)</label>
<label><input type="checkbox" id="pl-additive" checked>Additive selection</label>
<button type="button" id="pl-camera">Camera / Orbit</button>
</div>
<div id="pl-selected" class="pl-readout" aria-live="polite">No bones selected</div>
<div class="pl-controls"><label for="pl-bone-select">Accessible bone selector</label><select id="pl-bone-select"><option>Loading…</option></select>
<button type="button" id="pl-clear">Deselect all</button></div>
<div class="pl-controls"><label>Rotate on local axis <select id="pl-axis">
<option value="X" selected>X</option><option value="Y">Y</option><option value="Z">Z</option>
</select></label><span id="pl-delta" aria-live="off">0° X</span></div>
<fieldset class="pl-locks"><legend>Axis locks</legend>
<label><input id="pl-lockX" type="checkbox">Lock X</label>
<label><input id="pl-lockY" type="checkbox" checked>Lock Y</label>
<label><input id="pl-lockZ" type="checkbox" checked>Lock Z</label>
</fieldset>
<div class="pl-controls"><label>Precision <input id="pl-step" type="number" min="0.5" max="25" step="0.5" value="5">°</label>
<button type="button" id="pl-minus">− Rotate</button><button type="button" id="pl-plus">+ Rotate</button>
<label>Twist sensitivity <input id="pl-sensitivity" type="range" min="0.2" max="2" step="0.1" value="1"></label></div>
<div class="pl-controls"><label><input id="pl-tips" type="checkbox" checked>Protect all four tip bones</label>
<span id="pl-protected" class="pl-warning">Protected tips: ON</span></div>
<div class="pl-controls">
<button type="button" id="pl-undo">Undo</button><button type="button" id="pl-redo">Redo</button>
<button type="button" id="pl-reset-selected">Reset selected</button><button type="button" id="pl-reset-all">Reset all</button>
<button type="button" id="pl-export">Save Pose JSON</button></div>
<p id="pl-status" role="status" aria-live="polite">Waiting for Repl…</p>
<p class="pl-metadata">Red markers: suspect hoof-tip controls (protected by default). Cyan: selected bones.
Editing is paused, reversible and <strong>never writes Repl.glb</strong>. Export a Pose JSON and use the viewer's PNG button
for a reference image. The exported pose includes exact bone names, quaternions, source hash, clip and time.
Disable Pose Mode to restore the original animation.</p>
</section>
'''
def only_replace(text,old,new,code):
 if text.count(old)!=1:raise ValueError(f'{code}: expected 1 anchor, found {text.count(old)}')
 return text.replace(old,new,1)

def patch(template: str, js: str, source_sha: str) -> str:
 if 'installReplPoseLab' not in js: raise ValueError('POSE_LAB_SOURCE_INVALID')
 if len(source_sha)!=64 or any(c not in '0123456789abcdef' for c in source_sha):raise ValueError('SOURCE_SHA_INVALID')
 template=only_replace(template,'</style>',CSS+'</style>','CSS_ANCHOR')
 template=only_replace(template,'<div id="footfall"',PANEL+'\n<div id="footfall"','UI_ANCHOR')
 template=only_replace(template,'let neckRoot=null,neckWorld0=null,lastTravel=0;',
                       'let neckRoot=null,neckWorld0=null,lastTravel=0;\nlet poseLab=null;','STATE_ANCHOR')
 template=only_replace(template,'function animate(){',js+'\nfunction animate(){','INSTALL_ANCHOR')
 template=only_replace(template,'syncCamera();reportFootfalls();updateHinges();orbit.update();renderer.render(scene,camera);',
                       'syncCamera();reportFootfalls();updateHinges();poseLab?.update();orbit.update();renderer.render(scene,camera);','FRAME_ANCHOR')
 template=only_replace(template,'  selectClip();\n },error=>',
  "  selectClip();\n  poseLab=installReplPoseLab({root,scene,camera,canvas,orbit,THREE,mixer,restRotations,sourceSha:'"+source_sha+"',\n"+
  "   animation:gltf.animations,getAction:()=>action,getPaused:()=>paused,\n"+
  "   setPaused:v=>{paused=v;get('play').textContent=v?'Play':'Pause';},getStatus:()=>status});\n },error=>",'LOADER_ANCHOR')
 template=only_replace(template,'<h1>Repl · visible four-leg bend correction (forward travel)</h1>',
  '<h1>Repl · Pose Lab bone controls (non-destructive)</h1>','TITLE_ANCHOR')
 template=only_replace(template,'<title>Repl · visible four-leg swing shape v0.6.5</title>',
 '<title>Repl · Pose Lab bone controls v0.6.6</title>','DOC_TITLE_ANCHOR')
 if template.count('installReplPoseLab')!=2:raise ValueError('POSE_LAB_INJECTION_COUNT_MISMATCH')
 return template
