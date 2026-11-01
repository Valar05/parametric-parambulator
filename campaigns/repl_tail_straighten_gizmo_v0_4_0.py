#!/usr/bin/env python3
"""REPL v0.4.0: a slow tail straightening review and opt-in pivot gizmo.

This is a successor to v0.3.0, NOT a rewrite. Its sole geometry input
is the exact original Repl.glb. The accepted v0.3.0 four-tail-joint
candidate is regenerated in memory, then a separate slow-straighten
animation is appended. Original mane and tail weights, pivots, body,
textures and both old animation clips remain byte-for-byte unchanged
inside the new GLB's existing buffer prefix.

The gizmo is in the full-textured viewer, OFF by default; dragging it
does not change the rig or apply a new pivot. Save JSON to propose one.
No moving hooves, gait, cloth, wind shader or new bones.
"""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback

VERSION="0.4.0"
CAMPAIGN="REPL_TAIL_SLOW_STRAIGHTEN_AND_OPTIONAL_GIZMO"
PREDECESSOR="repl_tail_four_controls_v0_3_0.py"
PREDECESSOR_BLOB_SHA="8c60a5a30d60ea3e016436afc5982404c2339e9d"
GIZMO_JS="repl_tail_gizmo_v0_4_0.js"
GIZMO_JS_BLOB_SHA="1b4396ed0027a0a75baed840d7ed741e57c58a92"
SOURCE_SHA256="d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f"
REVIEW_DURATION=14.0
FRAME_STEP=0.25
TARGET_TAIL_ELEVATION_DEG=-8.0
TERMINAL_ADJUST_DEG=8.0
TARGET_JOINTS=50
TARGET_NODES=53
TAIL_NAMES=("REPL_TAIL_BASE","REPL_TAIL_TIP",
            "REPL_TAIL_NEAR_TIP","REPL_TAIL_TERMINAL")
OUTPUT_FOLDER="Repl_TailStraighten_Gizmo_v0.4.0"
OUT_GLB="Repl_TailStraighten_Gizmo_v0.4.0.glb"
OUT_HTML="Repl_TailStraighten_Gizmo_v0.4.0_textured.html"
OUT_REPORT="Repl_TailStraighten_Gizmo_v0.4.0_report.json"
OUT_RECEIPT="RECEIPT_v0.4.0.json"
CLIP_NAME="REPL_TAIL_SLOW_STRAIGHTEN_14S_FOUR_JOINTS"
SAMPLE_TIMES=tuple(i*FRAME_STEP for i in range(int(REVIEW_DURATION/FRAME_STEP)+1))


class Blocked(RuntimeError):
    pass


def guard(ok, reason):
    if not ok:
        raise Blocked(reason)


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def load_engines():
    path=Path(__file__).with_name(PREDECESSOR)
    guard(path.is_file(),"LOCKED_V030_ENGINE_NOT_IN_GIT_CHECKOUT")
    guard(git_blob_sha(path.read_bytes())==PREDECESSOR_BLOB_SHA,
          "V030_PREDECESSOR_BLOB_MISMATCH")
    spec=importlib.util.spec_from_file_location("repl_tail_v030",path)
    prev=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prev)
    guard(prev.VERSION=="0.3.0" and prev.SOURCE_SHA256==SOURCE_SHA256,
          "V030_PREDECESSOR_IDENTITY_CHANGED")
    old,v010=prev.load_predecessor()
    guard(old.VERSION=="0.2.0" and v010.VERSION=="0.1.0",
          "V020_OR_V010_PREDECESSOR_MISMATCH")
    gizmo=Path(__file__).with_name(GIZMO_JS)
    guard(gizmo.is_file(),"GIZMO_SOURCE_MISSING_FROM_PINNED_CHECKOUT")
    data=gizmo.read_bytes()
    guard(git_blob_sha(data)==GIZMO_JS_BLOB_SHA,
          "GIZMO_MODULE_BLOB_MISMATCH")
    return prev,old,v010,data.decode("utf8")


def ease(t):
    t=max(0.0,min(1.0,float(t)))
    return t*t*t*(t*(t*6-15)+10)


def slow_progress(t, joint):
    """14s natural sequential unfurl, hold, then return to original rest."""
    guard(0<=joint<4,"TAIL_CONTROL_PHASE_OUT_OF_RANGE")
    raise_start=0.25+joint*.45
    raise_end=5.85+joint*.45
    lower_start=9.00+(3-joint)*.22
    lower_end=13.30+(3-joint)*.13
    if t<=raise_start:return 0.0
    if t<raise_end:return ease((t-raise_start)/(raise_end-raise_start))
    if t<lower_start:return 1.0
    if t<lower_end:return 1.0-ease((t-lower_start)/(lower_end-lower_start))
    return 0.0


def rest_link_angles(prev):
    """Measure named-tail joint pivot coordinates, not mesh bounding boxes."""
    pivots=prev.TAIL_PIVOTS
    guard(len(pivots)==4,"EXISTING_TAIL_PIVOTS_CHANGED")
    values=[]
    for a,b in zip(pivots,pivots[1:]):
        dx=b[0]-a[0]; dy=b[1]-a[1]; dz=b[2]-a[2]
        guard(abs(dx)<1e-4 and dz<-.001,
              "TAIL_REST_CHAIN_NOT_IN_EXPECTED_SAGITTAL_PLANE")
        values.append(math.degrees(math.atan2(dy,-dz)))
    guard(all(math.isfinite(x) for x in values),
          "NONFINITE_REST_SEGMENT_ANGLES")
    return values


def target_corrections(prev):
    angles=rest_link_angles(prev)
    # World X rotations to align three existing link directions with a
    # common gently descending, rear-facing axis. Descendant local
    # corrections subtract the parent change to avoid over-rotating.
    target=TARGET_TAIL_ELEVATION_DEG
    absolute=[target-a for a in angles]
    local=[
        absolute[0],
        absolute[1]-absolute[0],
        absolute[2]-absolute[1],
        TERMINAL_ADJUST_DEG
    ]
    guard(max(abs(x) for x in local)<45,
          "STRAIGHTEN_CORRECTION_WOULD_BE_EXCESSIVE")
    return angles,local


def tail_joint_map(doc):
    nodes=doc["nodes"]
    result={node.get("name"):(i,node) for i,node in enumerate(nodes)}
    guard(all(name in result for name in TAIL_NAMES),
          "EXPECTED_FOUR_TAIL_CONTROLS_MISSING")
    return {name:result[name][0] for name in TAIL_NAMES}


def local_axis_for_world_x(world_matrix):
    """Rest world +X axis mapped to a bone's local frame (no shear)."""
    values=(world_matrix[0],world_matrix[1],world_matrix[2])
    scale=math.sqrt(sum(x*x for x in values))
    guard(scale>1e-6,"DEGENERATE_BONE_AXIS")
    return tuple(v/scale for v in values)


def add_slow_straighten_clip(doc, binary, prev, base):
    guard(len(doc.get("animations",[]))==2,
          "LOCKED_PREDECESSOR_REVIEW_CLIP_COUNT_CHANGED")
    old_clips=json.dumps(doc["animations"],sort_keys=True)
    name_map=tail_joint_map(doc)
    rest_world=base.world_matrices(doc,{})
    angles,corrections=target_corrections(prev)
    names=list(TAIL_NAMES)
    axes={name:local_axis_for_world_x(rest_world[name_map[name]])
          for name in names}
    times_acc=base.emit_accessor(
        doc,binary,[(float(t),) for t in SAMPLE_TIMES],5126,"SCALAR")
    samplers=[];channels=[];keys={}
    for i,name in enumerate(names):
        nodeid=name_map[name]
        q0=base.node_rotation(doc["nodes"][nodeid])
        rotations=[]
        for t in SAMPLE_TIMES:
            deg=corrections[i]*slow_progress(t,i)
            q=base.qmul(q0,base.axisq(axes[name],deg))
            scale=math.sqrt(sum(x*x for x in q))
            rotations.append(tuple(x/scale for x in q))
        guard(all(abs(a-b)<1e-6 for a,b in zip(rotations[0],rotations[-1])),
              "STRAIGHTEN_CLIP_MUST_END_AT_ORIGINAL_REST")
        target_acc=base.emit_accessor(doc,binary,rotations,5126,"VEC4")
        samplers.append({"input":times_acc,"output":target_acc,
                         "interpolation":"LINEAR"})
        channels.append({"sampler":i,"target":{
            "node":nodeid,"path":"rotation"}})
        keys[nodeid]=rotations
    doc["animations"].append({
        "name":CLIP_NAME,
        "samplers":samplers,"channels":channels,
        "extras":{
            "duration_seconds":REVIEW_DURATION,
            "semantics":"gradual 4-joint unfurl, extended hold, ease to neutral",
            "original_mane_untouched":True,
            "body_and_hooves_motion_channels":0,
            "gizmo":"OFF_BY_DEFAULT_NON_MUTATING",
            "owner_acceptance":"PENDING"
        }})
    guard(json.dumps(doc["animations"][:2],sort_keys=True)==old_clips,
          "OLD_ACCEPTED_ANIMATION_CLIPS_MODIFIED")
    return keys,name_map,{
        "measured_named_rest_joint_angles_degrees":angles,
        "target_world_elevation_deg":TARGET_TAIL_ELEVATION_DEG,
        "local_joint_corrections_deg":corrections,
        "local_world_x_axes":axes,
        "sampled_frames":len(SAMPLE_TIMES),
        "duration_seconds":REVIEW_DURATION
    }


def matrices_at(base,doc,binary,overrides):
    return base.skin_matrices(doc,binary,base.world_matrices(doc,overrides))


def validate_straighten(doc,binary,base,positions,keys,name_map,
                        previous_hair_joints,previous_hair_weights):
    skin=doc["skins"][0]
    guard(len(skin["joints"])==TARGET_JOINTS
          and len(doc["nodes"])==TARGET_NODES,
          "DERIVED_50_JOINT_IDENTITY_CHANGED")
    hair=doc["meshes"][1]["primitives"][0]
    actual_hj=base.accessor(doc,binary,hair["attributes"]["JOINTS_0"])
    actual_hw=base.accessor(doc,binary,hair["attributes"]["WEIGHTS_0"])
    guard(actual_hj==previous_hair_joints
          and actual_hw==previous_hair_weights,
          "EXISTING_V030_HAIR_WEIGHT_VALUES_CHANGED")
    body=doc["meshes"][0]["primitives"][0]
    bp=base.accessor(doc,binary,body["attributes"]["POSITION"])
    bj=base.accessor(doc,binary,body["attributes"]["JOINTS_0"])
    bw=base.accessor(doc,binary,body["attributes"]["WEIGHTS_0"])
    guard(len(bp)==6082 and len(positions)==1819,
          "ORIGINAL_GEOMETRY_COUNT_CHANGED")
    old_expected=base.EXPECTED_JOINTS
    try:
        base.EXPECTED_JOINTS=TARGET_JOINTS
        rest=matrices_at(base,doc,binary,{})
        hooves=[i for i,p in enumerate(bp) if p[1]<.12]
        mane=[i for i,p in enumerate(positions) if p[2]>=-.65]
        tail=[i for i,p in enumerate(positions) if p[2]<-.65]
        guard(len(hooves)>50 and len(mane)>600 and len(tail)>900,
              "ANATOMICAL_REGION_COVERAGE_CHANGED")
        hoof_orig=[
            base.deform_vertex(bp[i],bj[i],bw[i],rest)
            for i in hooves]
        mane_orig=[
            base.deform_vertex(positions[i],actual_hj[i],actual_hw[i],rest)
            for i in mane]
        tail_orig=[
            base.deform_vertex(positions[i],actual_hj[i],actual_hw[i],rest)
            for i in tail]
        maximum_hoof=0.0;maximum_mane=0.0;maximum_body=0.0
        maximum_tail=0.0;sampled=0
        midpoint_index=0
        for f,t in enumerate(SAMPLE_TIMES):
            pose={node:rotations[f] for node,rotations in keys.items()}
            matrices=matrices_at(base,doc,binary,pose)
            for i,ref in zip(hooves,hoof_orig):
                p=base.deform_vertex(bp[i],bj[i],bw[i],matrices)
                maximum_hoof=max(maximum_hoof,math.dist(p,ref))
            for i,ref in zip(mane,mane_orig):
                p=base.deform_vertex(
                    positions[i],actual_hj[i],actual_hw[i],matrices)
                maximum_mane=max(maximum_mane,math.dist(p,ref))
            for i in range(0,len(bp),12):
                a=base.deform_vertex(bp[i],bj[i],bw[i],rest)
                b=base.deform_vertex(bp[i],bj[i],bw[i],matrices)
                maximum_body=max(maximum_body,math.dist(a,b))
            for i,ref in zip(tail,tail_orig):
                p=base.deform_vertex(
                    positions[i],actual_hj[i],actual_hw[i],matrices)
                guard(all(math.isfinite(v) for v in p),
                      "NONFINITE_TAIL_VERTEX_DURING_STRAIGHTEN")
                maximum_tail=max(maximum_tail,math.dist(p,ref))
            sampled+=1
        guard(maximum_hoof<1e-6,"HOOF_MOVED_DURING_TAIL_ONLY_REVIEW")
        guard(maximum_body<1e-6,"BODY_MOVED_DURING_TAIL_ONLY_REVIEW")
        guard(maximum_mane<1e-6,"ACCEPTED_MANE_MOVED_DURING_TAIL_ONLY_REVIEW")
        guard(.08<maximum_tail<.8,
              "TAIL_STRAIGHTEN_INVISIBLE_OR_EXPLOSIVE")
        # Validate actual FK control chain at a time when all 4 are extended.
        peak_index=min(range(len(SAMPLE_TIMES)),
                       key=lambda i:abs(SAMPLE_TIMES[i]-8.0))
        peak_pose={node:rotations[peak_index]
                   for node,rotations in keys.items()}
        worlds=base.world_matrices(doc,peak_pose)
        positions_of_bones=[
            tuple(worlds[name_map[n]][k] for k in (3,7,11))
            for n in TAIL_NAMES]
        elevations=[]
        for a,b in zip(positions_of_bones,positions_of_bones[1:]):
            dy=b[1]-a[1];dz=b[2]-a[2]
            guard(dz<0,"TAIL_POINTED_TOWARD_RUMP_AT_FULL_EXTENSION")
            elevations.append(math.degrees(math.atan2(dy,-dz)))
        max_alignment=max(
            abs(x-TARGET_TAIL_ELEVATION_DEG) for x in elevations)
        guard(max_alignment<8.0,
              "TAIL_FK_NOT_ACTUALLY_STRAIGHT:"+str(elevations))
        return {
            "sampled_frames":sampled,
            "maximum_hoof_displacement":maximum_hoof,
            "maximum_body_displacement":maximum_body,
            "maximum_accepted_mane_displacement":maximum_mane,
            "maximum_tail_vertex_displacement":maximum_tail,
            "peak_joint_segment_angles_deg":elevations,
            "maximum_peak_alignment_error_deg":max_alignment,
            "body_or_hoof_animation_channels":0,
            "original_two_animation_clips":"PRESERVED",
            "four_tail_control_channels":4,
            "owner_visual_review":"PENDING"
        }
    finally:
        base.EXPECTED_JOINTS=old_expected


HTML_TEMPLATE=r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Repl v0.4 · Tail straighten + optional pivot gizmo</title>
<style>
:root{color-scheme:dark;--bg:#161921;--text:#f2f2f3;--muted:#c6c7d1;--line:#4b5265}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.48 system-ui,sans-serif}
main{max-width:1280px;margin:auto;padding:12px}
h1{font-size:1.32rem;margin:0 0 4px}
h2{font-size:1.05rem;margin:8px 0}
p{color:var(--muted);margin:8px 0}
#stage{width:100%;height:68vh;min-height:410px;touch-action:none;display:block;
background:#d9dadc;border:1px solid var(--line);border-radius:12px}
.controls{display:flex;align-items:center;flex-wrap:wrap;gap:9px;margin:8px 0 12px}
.control{display:inline-flex;align-items:center;gap:7px}
button,select,input{font:inherit}
button,select{padding:9px;border:1px solid #65728a;border-radius:7px;
color:#fff;background:#333c50}
input[type="range"]{width:min(440px,75vw)}
button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #8fe7e0}
fieldset{border:1px solid var(--line);border-radius:8px}
#status{min-height:1.5em;font-weight:600;color:#9bead8}
#gizmo-panel{background:#242b39;border:1px solid #616b7b;
border-radius:10px;padding:12px;margin:12px 0}
#gizmo-panel[hidden]{display:none}
.gizmo-fields{display:grid;grid-template-columns:repeat(3,minmax(80px,1fr));gap:9px}
.gizmo-fields input{width:100%;padding:8px;background:#141d2b;color:#fff;border:1px solid #748098;border-radius:6px}
.gizmo-rows{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:9px 0}
#gizmo-coordinates{width:100%;padding:10px;color:#fff;background:#141d2b;
border:1px solid #68778a;border-radius:6px}
.note{font-size:.89rem;color:var(--muted)}
</style>
<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}
</script></head>
<body><main><h1>Repl · Four-bone slow tail straightening</h1>
<p>The original mane, tail pivots, skin weights, textures and body are preserved.
The new 14-second motion unfurls the tail gradually, holds, then returns.
The separate pivot gizmo is an optional NON-MUTATING guide.</p>
<div id="status" role="status" aria-live="polite">Loading original textured GLB and animation…</div>
<div class="controls">
<label class="control">Animation
<select id="clip">
<option value="straight">Slow straightening · 14 s</option>
<option value="sway">Original four-bone sway</option>
<option value="neck">Accepted neck and mane review</option>
</select></label>
<label class="control">Camera
<select id="view"><option value="three">3/4</option><option value="side">Side</option>
<option value="rear">Rear</option><option value="front">Front</option>
<option value="top">Top</option></select></label>
<button id="pause">Pause</button>
<label class="control">Speed
<select id="speed"><option value=".25">0.25×</option>
<option value=".5">0.5×</option><option value="1" selected>1×</option>
<option value="2">2×</option></select></label>
<button id="save-frame">Save full-resolution PNG</button>
<button id="save-views">Save 3-view contact sheet</button>
</div>
<div class="controls">
<label class="control" for="timeline">Frame</label>
<input type="range" id="timeline" min="0" max="14" value="0" step=".01">
<span id="time" aria-live="off">0.00 s</span>
</div>
<canvas id="stage" aria-label="Interactive full-resolution textured Repl model"></canvas>
<div class="controls">
<label class="control"><input type="checkbox" id="gizmo-enable">
Enable optional tail-pivot gizmo (OFF by default)</label>
</div>
<section id="gizmo-panel" hidden aria-label="Optional tail attachment guide">
<h2>Tail pivot, original GLB world coordinates</h2>
<p class="note">This tool moves a visible marker only; it cannot secretly
change the pivot, rig, motion, or saved model. Orange = v0.3 root.
Cyan = your movable guide. Geometry intersection estimate is NOT exact.</p>
<div class="gizmo-fields">
<label>X<input id="pivotX" type="number" step=".001"></label>
<label>Y<input id="pivotY" type="number" step=".001"></label>
<label>Z<input id="pivotZ" type="number" step=".001"></label>
</div>
<div class="gizmo-rows">
<button id="gizmo-original">Current v0.3 root</button>
<button id="gizmo-arc-estimate">Open-arc estimate (uncertain)</button>
<button id="gizmo-focus">Close-up camera</button>
<button id="gizmo-reset-camera">Whole model</button>
</div>
<div class="gizmo-rows">
<label class="control"><input id="gizmo-xray" type="checkbox" checked>Translucent body</label>
<label class="control"><input id="gizmo-wire" type="checkbox">Body wireframe</label>
<label class="control"><input id="gizmo-ring" type="checkbox" checked>Guide ring</label>
<label class="control"><input id="gizmo-show-original" type="checkbox" checked>Old pivot marker</label>
</div>
<div class="gizmo-rows">
<label>Ring radius <span id="gizmo-radius-value">.027</span>
<input id="gizmo-radius" type="range" min=".005" max=".08" step=".001" value=".027"></label>
<label>Ring tilt <span id="gizmo-tilt-value">-38</span>°
<input id="gizmo-tilt" type="range" min="-85" max="85" value="-38" step="1"></label>
</div>
<input id="gizmo-coordinates" type="text" readonly aria-label="Copyable pivot coordinates">
<div id="gizmo-status" aria-live="polite"></div>
<div class="gizmo-rows">
<button id="gizmo-copy">Copy coordinates</button>
<button id="gizmo-export">Save pivot selection JSON</button>
</div></section>
<p>Use drag/touch to orbit and pinch to zoom; try the full textured side and
rear views. All four hooves remain completely stationary in both tail-only
clips. The preview and gizmo are diagnostics, not an automatic owner verdict.</p>
<p class="note">The GLB bytes are embedded in this HTML. Three.js and its
add-ons load from a pinned public CDN, so opening the HTML requires network
access for the renderer. The downloadable GLB has its own original materials.</p>
<script type="module">
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {TransformControls} from 'three/addons/controls/TransformControls.js';
__GIZMO_MODULE__
const get=id=>document.getElementById(id);
const canvas=get('stage'),status=get('status');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.20;
const scene=new THREE.Scene();scene.background=new THREE.Color(0xd8dadb);
const camera=new THREE.PerspectiveCamera(38,1,.01,100);
scene.add(new THREE.HemisphereLight(0xffffff,0x66676a,2.65));
const key=new THREE.DirectionalLight(0xfff6e8,3.1);key.position.set(4,9,5);scene.add(key);
const rim=new THREE.DirectionalLight(0xffdddd,1.55);rim.position.set(-5,5,-6);scene.add(rim);
const grid=new THREE.GridHelper(4,20,0xb1b1b1,0xd4d4d4);grid.position.y=-.01;scene.add(grid);
const orbit=new OrbitControls(camera,canvas);orbit.enableDamping=true;orbit.enablePan=true;
const clock=new THREE.Clock();
let gltf=null,root=null,mixer=null,action=null,gizmo=null,paused=false;
const restRotations=new Map();
let currentDuration=14;
function resize(){const w=Math.max(200,canvas.clientWidth),h=Math.max(300,canvas.clientHeight);
renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(canvas);resize();
function cameraPreset(){
  if(!root)return;
  const bounds=new THREE.Box3().setFromObject(root);
  const center=bounds.getCenter(new THREE.Vector3());
  const extent=bounds.getSize(new THREE.Vector3()).length();
  const r=Math.max(extent*.74,1.5);
  const offsets={three:[1,.5,-1],side:[1,.16,0],rear:[0,.16,-1],
    front:[0,.16,1],top:[0,1.5,-.1]};
  const o=offsets[get('view').value]||offsets.three;
  camera.position.set(center.x+o[0]*r*1.8,center.y+o[1]*r*1.8,center.z+o[2]*r*1.8);
  orbit.target.copy(center);camera.lookAt(orbit.target);orbit.update();
}
function selectClip(){
  if(!mixer||!gltf)return;
  mixer.stopAllAction();
  for(const [bone,q] of restRotations)bone.quaternion.copy(q);
  const pick=get('clip').value;
  const find=phrase=>gltf.animations.find(a=>a.name.includes(phrase));
  const clip=pick==='straight'?find('SLOW_STRAIGHTEN'):
    pick==='sway'?find('EXPRESSIVE_SWAY'):find('NECK_REVIEW');
  if(!clip){status.textContent='Requested animation missing from GLB';return;}
  action=mixer.clipAction(clip);action.reset();action.setLoop(THREE.LoopRepeat,Infinity);action.play();
  currentDuration=clip.duration;get('timeline').max=String(currentDuration);
  mixer.setTime(0);get('timeline').value=0;get('time').textContent='0.00 s';
  status.textContent='Showing real textured GLB: '+clip.name+
    '. Optional gizmo '+(gizmo?.enabled?'ON':'OFF')+'.';
}
get('clip').addEventListener('change',selectClip);
get('view').addEventListener('change',cameraPreset);
get('pause').addEventListener('click',()=>{
  paused=!paused;get('pause').textContent=paused?'Play':'Pause';});
get('timeline').addEventListener('input',e=>{
  if(!mixer)return;
  paused=true;get('pause').textContent='Play';
  mixer.setTime(Number(e.target.value));
  get('time').textContent=Number(e.target.value).toFixed(2)+' s';
});
function capture(){
  renderer.render(scene,camera);
  return canvas.toDataURL('image/png');
}
function downloadUrl(url,name){
  const link=document.createElement('a');link.href=url;link.download=name;
  document.body.appendChild(link);link.click();link.remove();
}
get('save-frame').addEventListener('click',()=>{
  downloadUrl(capture(),'Repl_TailStraighten_v0.4.0_frame.png');});
get('save-views').addEventListener('click',()=>{
  const originalPosition=camera.position.clone(),originalTarget=orbit.target.clone();
  const last=get('view').value;
  const views=['three','side','rear'];
  const sheet=document.createElement('canvas');
  sheet.width=canvas.width*3;sheet.height=canvas.height;
  const ctx=sheet.getContext('2d');
  for(let i=0;i<3;i++){
    get('view').value=views[i];cameraPreset();renderer.render(scene,camera);
    ctx.drawImage(canvas,i*canvas.width,0,canvas.width,canvas.height);
  }
  get('view').value=last;
  camera.position.copy(originalPosition);orbit.target.copy(originalTarget);orbit.update();
  renderer.render(scene,camera);
  downloadUrl(sheet.toDataURL('image/png'),
    'Repl_TailStraighten_v0.4.0_three_views.png');
});
function frame(){
  requestAnimationFrame(frame);
  const delta=Math.min(clock.getDelta(),.05);
  if(mixer&&!paused){
    mixer.update(delta*Number(get('speed').value));
    if(action) {
      get('timeline').value=(action.time%currentDuration).toFixed(3);
      get('time').textContent=action.time.toFixed(2)+' s';
    }
  }
  orbit.update();renderer.render(scene,camera);
}
frame();
try {
  const encoded='__EMBEDDED_GLB_BASE64__';
  const bytes=Uint8Array.from(atob(encoded),v=>v.charCodeAt(0));
  new GLTFLoader().parse(bytes.buffer,'',model=>{
    gltf=model;root=model.scene;scene.add(root);
    root.traverse(o=>{
      if(o.isMesh)o.frustumCulled=false;
      if(o.isBone)restRotations.set(o,o.quaternion.clone());
    });
    mixer=new THREE.AnimationMixer(root);
    gizmo=installTailPivotGizmo({
      scene,camera,canvas,orbit,renderer,root,THREE,TransformControls,status});
    cameraPreset();selectClip();
  },error=>{status.textContent='GLB parse failed: '+String(error);});
} catch(e){status.textContent='Viewer failed: '+String(e);}
</script></main></body></html>"""


def make_artifacts(source,prev,old,base,gizmo_js):
    previous_glb,prev_report,_html=prev.make_artifacts(source,old,base)
    doc,bin_bytes=prev.read_glb_bytes(previous_glb)
    guard(len(doc["nodes"])==TARGET_NODES and
          len(doc["skins"][0]["joints"])==TARGET_JOINTS,
          "V030_ACCEPTED_FOUR_TAIL_JOINT_RIG_CHANGED")
    body_before=json.dumps(doc["meshes"][0],sort_keys=True)
    hair_before=json.dumps(doc["meshes"][1],sort_keys=True)
    nodes_before=json.dumps(doc["nodes"],sort_keys=True)
    skin_joints_before=json.dumps(doc["skins"][0],sort_keys=True)
    animations_before=json.dumps(doc["animations"],sort_keys=True)
    binary_hash=sha(bin_bytes)
    hair=doc["meshes"][1]["primitives"][0]
    positions=base.accessor(doc,bin_bytes,hair["attributes"]["POSITION"])
    original_j=base.accessor(doc,bin_bytes,hair["attributes"]["JOINTS_0"])
    original_w=base.accessor(doc,bin_bytes,hair["attributes"]["WEIGHTS_0"])
    added=bytearray(bin_bytes)
    keys,name_map,motion=add_slow_straighten_clip(doc,added,prev,base)
    guard(json.dumps(doc["meshes"][0],sort_keys=True)==body_before,
          "BODY_MESH_CHANGED")
    guard(json.dumps(doc["meshes"][1],sort_keys=True)==hair_before,
          "HAIR_MESH_CHANGED")
    guard(json.dumps(doc["nodes"],sort_keys=True)==nodes_before,
          "APPROVED_BONE_PIVOTS_OR_PARENTS_CHANGED")
    guard(json.dumps(doc["skins"][0],sort_keys=True)==skin_joints_before,
          "ACCEPTED_BONE_SKIN_DATA_CHANGED")
    guard(json.dumps(doc["animations"][:2],sort_keys=True)==animations_before,
          "PREVIOUS_ANIMATION_CLIPS_CHANGED")
    guard(sha(bytes(added[:len(bin_bytes)]))==binary_hash,
          "V030_BUFFER_PREFIX_CHANGED")
    validation=validate_straighten(
        doc,bytes(added),base,positions,keys,name_map,original_j,original_w)
    doc["asset"].setdefault("extras",{})["replTailCampaignV040"]={
        "predecessor":"v0.3.0 complete",
        "owner_accepted_mane":"PRESERVED",
        "tail_pivot":"UNALTERED_V0.3",
        "gizmo":"optional off-by-default; export-only",
        "straightenClip":CLIP_NAME,
        "humanVerdict":"PENDING"
    }
    output=base.glb_encode(doc,bytes(added))
    guard("__EMBEDDED_GLB_BASE64__" in HTML_TEMPLATE
          and "__GIZMO_MODULE__" in HTML_TEMPLATE,
          "HTML_VIEWER_PLACEHOLDER_MISSING")
    html=HTML_TEMPLATE.replace(
        "__GIZMO_MODULE__",gizmo_js).replace(
        "__EMBEDDED_GLB_BASE64__",base64.b64encode(output).decode("ascii"))
    report={
        "campaign":CAMPAIGN,"version":VERSION,
        "source_sha256":SOURCE_SHA256,
        "predecessor_v030_sha256":sha(previous_glb),
        "material_and_mesh_identity":"unchanged from v0.3",
        "mane_weights_and_joints":"unchanged",
        "tail_weights_and_pivots":"unchanged",
        "review":motion,"validation":validation,
        "clips":["original neck/mane review","original tail sway",
                 "NEW slow 14-second straighten"],
        "gizmo":{
            "default":"OFF","interaction":"NON-MUTATING_MARKER_ONLY",
            "current_pivot":[0,1.05,-0.93],
            "arc_estimate_uncertain":[0.002,1.204,-0.889],
            "export":"operator-selected JSON, DOES NOT APPLY TO MODEL"
        },
        "renderer":"FULL ORIGINAL TEXTURED GLTF TRIANGLES, THREE.JS CDN",
        "source_model_overwritten":False,
        "no_hoof_or_body_animation":True,
        "human_owner_verdict":"PENDING"
    }
    return output,json.dumps(report,indent=2,sort_keys=True),html


def output_path(user):
    if user:return Path(user).expanduser().resolve()
    h=Path.home()
    downloads=h/"storage"/"downloads"
    return (downloads if downloads.is_dir() else h/"Downloads")/OUTPUT_FOLDER


def verify_existing(folder):
    p=folder/OUT_RECEIPT
    guard(p.is_file(),"VERSIONED_OUTPUT_PARTIAL_OR_COLLIDING")
    r=json.loads(p.read_text("utf8"))
    guard(r.get("version")==VERSION and
          r.get("source_sha256")==SOURCE_SHA256,
          "OUTPUT_RECEIPT_WRONG_IDENTITY")
    for name,expected in r.get("outputs",{}).items():
        actual=folder/name
        guard(actual.is_file() and file_sha(actual)==expected,
              "OUTPUT_HASH_MISMATCH:"+name)
    return r


def release(args,prev,old,base,gizmo_js):
    src=base.resolve_source(args.source)
    guard(file_sha(src)==SOURCE_SHA256,"SOURCE_SHA_NOT_APPROVED")
    folder=output_path(args.output)
    print("SOURCE_FILE="+str(src))
    print("SOURCE_SHA256="+SOURCE_SHA256)
    print("OUTPUT_FOLDER="+str(folder))
    if folder.exists():
        prior=verify_existing(folder)
        print("IDENTICAL_VERSION_ALREADY_VERIFIED=YES")
        print("GLB_SHA256="+prior["outputs"][OUT_GLB])
        print("HUMAN_VERDICT=PENDING")
        return
    guard(folder.parent.is_dir(),"PUBLIC_DOWNLOADS_UNAVAILABLE")
    tmp=Path(tempfile.mkdtemp(prefix=".repl_tail_v040_",dir=str(folder.parent)))
    try:
        glb,report,html=make_artifacts(src,prev,old,base,gizmo_js)
        files={OUT_GLB:glb,OUT_REPORT:report.encode("utf8"),
               OUT_HTML:html.encode("utf8")}
        for name,data in files.items():
            (tmp/name).write_bytes(data)
        hashes={name:file_sha(tmp/name) for name in files}
        receipt={
            "campaign":CAMPAIGN,"version":VERSION,
            "source_sha256":SOURCE_SHA256,
            "source_path":str(src),
            "github_commit":args.revision or "NOT_PINNED_BY_OPERATOR",
            "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "outputs":hashes,
            "status":"NUMERIC_PASS_WITH_TEXTURING / HUMAN_VISUAL_PENDING",
            "source_modified":False,
            "owner_mane_acceptance":"PRESERVED",
            "owner_tail_straighten_acceptance":"PENDING",
            "phone_browser_visible":"UNVERIFIED"
        }
        (tmp/OUT_RECEIPT).write_text(
            json.dumps(receipt,indent=2,sort_keys=True),encoding="utf8")
        guard(not folder.exists(),"OUTPUT_FOLDER_RACE")
        tmp.rename(folder)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    verify_existing(folder)
    print("DERIVED_GLB="+str(folder/OUT_GLB))
    print("TEXTURED_INTERACTIVE_PREVIEW="+str(folder/OUT_HTML))
    print("REPORT="+str(folder/OUT_REPORT))
    print("RECEIPT="+str(folder/OUT_RECEIPT))
    print("GLB_SHA256="+hashes[OUT_GLB])
    print("GIZMO_DEFAULT=OFF")
    print("HUMAN_VISUAL_VERDICT=PENDING")
    # Exact artifact publication; do not scan directories recursively.
    path=folder/OUT_HTML
    scanner="mediarefresh" if shutil.which("mediarefresh") else (
        "termux-media-scan" if shutil.which("termux-media-scan") else None)
    if scanner:
        try:
            result=subprocess.run([scanner,str(path)],timeout=12,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL,check=False)
            print("MEDIA_SCAN="+("REQUESTED" if result.returncode==0 else "FAILED"))
        except (OSError,subprocess.TimeoutExpired):
            print("MEDIA_SCAN=FAILED")
    else:print("MEDIA_SCAN=UNAVAILABLE")
    if shutil.which("termux-open"):
        try:
            result=subprocess.run(["termux-open",str(path)],timeout=10,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
            print("VIEWER_OPEN="+(
                "REQUESTED_NOT_CONFIRMED" if result.returncode==0
                else "FAILED"))
        except (OSError,subprocess.TimeoutExpired):
            print("VIEWER_OPEN=FAILED")
    else:print("VIEWER_OPEN=UNAVAILABLE")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation",nargs="?",default="run",
                        choices=("run","doctor","resume","status","rollback"))
    parser.add_argument("--source",help="Exact original Repl.glb path")
    parser.add_argument("--output",help="Versioned immutable output folder")
    parser.add_argument("--revision",help="Pinned Git commit SHA")
    args=parser.parse_args()
    print("CAMPAIGN="+CAMPAIGN)
    print("VERSION="+VERSION)
    print("RUNNER="+str(Path(__file__).resolve()))
    print("RUNNER_SHA256="+file_sha(Path(__file__).resolve()))
    print("SOURCE_SHA256_REQUIRED="+SOURCE_SHA256)
    if args.operation in ("status","rollback"):
        if args.operation=="rollback":
            print("ROLLBACK=UNNECESSARY_SOURCE_NEVER_MUTATED")
        folder=output_path(args.output)
        if folder.exists():
            r=verify_existing(folder);print("STATUS="+r["status"])
        else:print("STATUS=NOT_STARTED")
        return
    prev,old,base,gizmo_js=load_engines()
    src=base.resolve_source(args.source)
    base.glb_load(src)
    print("LOCKED_SOURCE_PREFLIGHT=PASS")
    print("LOCKED_ENGINE_AND_GIZMO_CHECKSUMS=PASS")
    if args.operation=="doctor":
        print("DOCTOR=PASS_NO_OUTPUT_MUTATION")
    else:release(args,prev,old,base,gizmo_js)


if __name__=="__main__":
    try:main()
    except (Blocked,ValueError,KeyError,IndexError,TypeError) as error:
        print("CAMPAIGN_STATUS=BLOCKED")
        print("CAUSE="+type(error).__name__+": "+str(error))
        print("SOURCE_MODIFIED=NO")
        print("HUMAN_VISUAL_VERDICT=PENDING")
        sys.exit(2)
    except Exception as error:
        traceback.print_exc()
        print("CAMPAIGN_STATUS=ERROR")
        print("CAUSE="+type(error).__name__+": "+str(error))
        print("SOURCE_MODIFIED=NO")
        sys.exit(3)
