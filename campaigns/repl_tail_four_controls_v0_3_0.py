#!/usr/bin/env python3
"""Repl v0.3.0: refine ONLY the tail to a four-control tapered chain.

Authoritative predecessor: v0.2.0 with three accepted mane controls and
two previously authored tail controls. The former is never modified in place.
Two new tail descendants are appended, leaving old joint IDs and all mane
weights unmodified. A separate gentle tail-only review clip is added.
Every body vertex, source asset, texture, material and original animation
remains unmodified. No hoof keys, cloth or wind shader.
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

VERSION = "0.3.0"
CAMPAIGN = "REPL_TAIL_TAPERED_FOUR_CONTROLS"
PREDECESSOR = "repl_hair_five_controls_v0_2_0.py"
PREDECESSOR_BLOB_SHA = "287567d6baf8e8fa415580dc57ee86600772f797"
SOURCE_SHA256 = "d28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f"
OUTPUT_DIR = "Repl_TailFourControls_v0.3.0"
GLB_NAME = "Repl_TailFourControls_v0.3.0.glb"
HTML_NAME = "Repl_TailFourControls_v0.3.0_TEXTURERENDER.html"
REPORT_NAME = "Repl_TailFourControls_v0.3.0_report.json"
RECEIPT_NAME = "RECEIPT_v0.3.0.json"
TAIL_NAMES = ("REPL_TAIL_BASE", "REPL_TAIL_TIP",
              "REPL_TAIL_NEAR_TIP", "REPL_TAIL_TERMINAL")
MANE_NAMES = ("REPL_MANE_REAR", "REPL_MANE_MIDDLE", "REPL_MANE_FRONT")
# Existing two bones and their rest transforms remain unchanged.
# Two new descendants form a progressively shrinking chain.
TAIL_PIVOTS = (
    (0.0, 1.05, -0.93),
    (0.0, 0.80, -1.27),
    (0.0, 0.62, -1.43),
    (0.0, 0.51, -1.54),
)
APPENDED_CONTROLS = (
    ("REPL_TAIL_NEAR_TIP", "REPL_TAIL_TIP", TAIL_PIVOTS[2]),
    ("REPL_TAIL_TERMINAL", "REPL_TAIL_NEAR_TIP", TAIL_PIVOTS[3]),
)
EXPECTED_NODES = 53
EXPECTED_JOINTS = 50
TAIL_REVIEW_TIMES = tuple(i * 0.125 for i in range(33))
TAIL_AMPLITUDES = (2.0, 3.5, 4.5, 5.5)
TAIL_AXIAL_KNOTS = (0.0, 0.51, 0.80, 1.0)


class Blocked(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise Blocked(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(content):
    return hashlib.sha1(
        b"blob " + str(len(content)).encode() + b"\0" + content
    ).hexdigest()


def load_predecessor():
    path = Path(__file__).with_name(PREDECESSOR)
    require(path.is_file(), "LOCKED_V0_2_0_ENGINE_MISSING")
    require(git_blob_sha(path.read_bytes()) == PREDECESSOR_BLOB_SHA,
            "PREDECESSOR_BLOB_SHA_MISMATCH")
    spec = importlib.util.spec_from_file_location("repl_hair_v020", path)
    prev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prev)
    require(prev.VERSION == "0.2.0" and prev.SOURCE_SHA256 == SOURCE_SHA256,
            "PREDECESSOR_IDENTITY_CHANGED")
    base = prev.load_predecessor()
    return prev, base


def check_progressive_lengths():
    lengths = [
        math.dist(TAIL_PIVOTS[i], TAIL_PIVOTS[i+1])
        for i in range(len(TAIL_PIVOTS)-1)
    ]
    require(all(a > b > 0 for a, b in zip(lengths, lengths[1:])),
            "TAIL_BONE_LENGTHS_NOT_PROGRESSIVELY_SHORTER")
    return lengths


def add_descendants(doc, bin_data, prev, base):
    joints = doc["skins"][0]["joints"]
    nodes = doc["nodes"]
    require(len(joints) == 48 and len(nodes) == 51,
            "V020_RIG_STRUCTURE_CHANGED")
    skin = doc["skins"][0]
    inverse_raw = base.accessor(doc, bin_data, skin["inverseBindMatrices"])
    require(len(inverse_raw) == 48, "V020_INVERSE_BINDS_WRONG_COUNT")
    ibms = [prev.matrix_from_glb_mat4(x) for x in inverse_raw]
    by_name = {
        nodes[node]["name"]: (i, node)
        for i, node in enumerate(joints)
    }
    require(all(name in by_name for name in MANE_NAMES + TAIL_NAMES[:2]),
            "LOCKED_MANE_OR_TAIL_CONTROLS_MISSING")
    preexisting_node_ids = tuple(by_name[n][1] for n in MANE_NAMES)
    preexisting_ibms = tuple(
        tuple(ibms[by_name[n][0]]) for n in MANE_NAMES + TAIL_NAMES[:2]
    )
    original_old_bone_transforms = {
        name: dict(nodes[by_name[name][1]])
        for name in MANE_NAMES + TAIL_NAMES[:2]
    }
    appended = []
    for name, parent, point in APPENDED_CONTROLS:
        require(name not in by_name and parent in by_name,
                "NEW_TAIL_PARENT_OR_DUPLICATE_ERROR")
        parent_joint, parent_node = by_name[parent]
        local = base.apply_matrix(ibms[parent_joint], point)
        inverse = prev.translation_matrix(tuple(-v for v in local))
        new_ibm = base.matrix_mult(inverse, ibms[parent_joint])
        node_id = len(nodes)
        nodes.append({
            "name": name,
            "translation": [float(v) for v in local],
            "rotation": [0, 0, 0, 1],
            "scale": [1, 1, 1],
            "extras": {
                "role": "TAIL_HAIR_ONLY",
                "version": VERSION,
                "owner_rest_parent": parent,
                "motion": "REST_EXCEPT_SEPARATE_TAIL_REVIEW_CLIP"
            }
        })
        nodes[parent_node].setdefault("children", []).append(node_id)
        joint_index = len(joints)
        joints.append(node_id)
        ibms.append(new_ibm)
        by_name[name] = (joint_index, node_id)
        appended.append({
            "name": name, "parent": parent,
            "node": node_id, "joint": joint_index,
            "world_pivot": list(point), "local_offset": list(local)
        })
    require(len(nodes) == EXPECTED_NODES
            and len(joints) == EXPECTED_JOINTS,
            "NEW_JOINT_COUNT_ERROR")
    for name in MANE_NAMES:
        node_before = original_old_bone_transforms[name]
        require(nodes[by_name[name][1]] == node_before,
                "LOCKED_MANE_NODE_MODIFIED")
    # The existing TAIL_TIP gains only a child reference.
    for name in TAIL_NAMES[:2]:
        before = dict(original_old_bone_transforms[name])
        after = dict(nodes[by_name[name][1]])
        before.pop("children", None)
        after.pop("children", None)
        require(after == before, "EXISTING_TAIL_CONTROL_TRANSFORM_MODIFIED")
    require(tuple(by_name[n][1] for n in MANE_NAMES) == preexisting_node_ids,
            "MANE_BONE_IDS_CHANGED")
    require(tuple(tuple(ibms[by_name[n][0]])
                  for n in MANE_NAMES + TAIL_NAMES[:2]) == preexisting_ibms,
            "PREEXISTING_BIND_MATRICES_CHANGED")
    return ibms, by_name, appended


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def axial_weights(u):
    """Smooth neighboring weights with 0 side influences from remote regions."""
    u = min(1.0, max(0.0, u))
    if u >= 1.0:
        return (0.0, 0.0, 0.0, 1.0)
    for i in range(3):
        lo, hi = TAIL_AXIAL_KNOTS[i:i+2]
        if lo <= u < hi:
            blend = smoothstep((u - lo) / (hi - lo))
            values = [0.0] * 4
            values[i] = 1.0 - blend
            values[i+1] = blend
            return tuple(values)
    raise Blocked("TAIL_WEIGHT_INTERPOLATOR_OUT_OF_RANGE")


def remap_tail_only(doc, bin_data, base, by_name):
    hair = doc["meshes"][1]["primitives"][0]
    positions = base.accessor(doc, bin_data, hair["attributes"]["POSITION"])
    oldj = base.accessor(doc, bin_data, hair["attributes"]["JOINTS_0"])
    oldw = base.accessor(doc, bin_data, hair["attributes"]["WEIGHTS_0"])
    require(len(positions) == len(oldj) == len(oldw) == 1819,
            "LOCKED_HAIR_MESH_VERTEX_COUNT_CHANGED")
    newj, neww = [], []
    report = {"mane_vertices_preserved": 0, "tail_vertices_reweighted": 0,
              "tail_influence_sums": {n: 0.0 for n in TAIL_NAMES},
              "weight_sums_max_error": 0.0, "seam_conflicts": 0}
    seen = {}
    mane_src_hash = hashlib.sha256()
    mane_dst_hash = hashlib.sha256()
    for p, js, ws in zip(positions, oldj, oldw):
        if p[2] >= -0.65:
            jj, ww = tuple(int(x) for x in js), tuple(float(x) for x in ws)
            report["mane_vertices_preserved"] += 1
            for j, w in zip(jj, ww):
                mane_src_hash.update(int(j).to_bytes(2, "little"))
                mane_src_hash.update(float(w).hex().encode("ascii"))
            for j, w in zip(jj, ww):
                mane_dst_hash.update(int(j).to_bytes(2, "little"))
                mane_dst_hash.update(float(w).hex().encode("ascii"))
        else:
            u = (-0.86 - p[2]) / (1.594 - 0.86)
            vals = axial_weights(u)
            pairs = [
                (by_name[name][0], value)
                for name, value in zip(TAIL_NAMES, vals)
                if value > 1e-10
            ]
            jj = tuple([p[0] for p in pairs] +
                       [0] * (4-len(pairs)))
            ww = tuple([p[1] for p in pairs] +
                       [0.0] * (4-len(pairs)))
            report["tail_vertices_reweighted"] += 1
            for name, value in zip(TAIL_NAMES, vals):
                report["tail_influence_sums"][name] += value
        require(all(0 <= k < EXPECTED_JOINTS for k in jj),
                "HAIR_JOINT_OUT_OF_RANGE")
        error = abs(sum(ww) - 1.0)
        report["weight_sums_max_error"] = max(
            report["weight_sums_max_error"], error)
        require(error < 1e-5, "HAIR_WEIGHTS_NOT_NORMALIZED")
        key = tuple(round(float(x), 5) for x in p)
        signature = (jj, tuple(round(x, 5) for x in ww))
        require(key not in seen or signature == seen[key],
                "HAIR_UV_SEAM_WEIGHT_CONFLICT")
        seen[key] = signature
        newj.append(jj)
        neww.append(ww)
    require(mane_src_hash.digest() == mane_dst_hash.digest(),
            "MANE_WEIGHT_BYTES_CHANGED")
    require(report["mane_vertices_preserved"] > 600 and
            report["tail_vertices_reweighted"] > 900,
            "MANE_OR_TAIL_CLASSIFICATION_CHANGED")
    require(all(value > 5 for value in report["tail_influence_sums"].values()),
            "TAIL_BONE_WITHOUT_MEANINGFUL_SKIN_COVERAGE")
    report["mane_influence_signature_sha256"] = mane_src_hash.hexdigest()
    return newj, neww, positions, report, oldj, oldw


def loop_wave(t, lag):
    # 4-second loop, all joints neutral at start/end; phase offset creates
    # progressive movement without uncontrolled pendulum/cloth behavior.
    angle = math.pi * 2 * t / 4.0
    return (math.sin(angle) * math.cos(lag)
            + 0.30 * math.sin(2 * angle) * math.sin(lag))


def add_tail_clip(doc, bin_data, base, by_name):
    require(len(doc.get("animations", [])) == 1,
            "V020_NECK_CLIP_MISSING_OR_CHANGED")
    previous = json.dumps(doc["animations"][0], sort_keys=True)
    times_id = base.emit_accessor(
        doc, bin_data, [(t,) for t in TAIL_REVIEW_TIMES],
        5126, "SCALAR")
    samplers, channels, sampled = [], [], {}
    for i, name in enumerate(TAIL_NAMES):
        nodeid = by_name[name][1]
        rot0 = base.node_rotation(doc["nodes"][nodeid])
        values = []
        for t in TAIL_REVIEW_TIMES:
            yaw = TAIL_AMPLITUDES[i] * loop_wave(t, i * 0.20)
            pitch = 0.3 * TAIL_AMPLITUDES[i] * loop_wave(t, i * 0.27)
            q = base.qmul(rot0, base.qmul(
                base.axisq((0, 1, 0), yaw),
                base.axisq((1, 0, 0), pitch)
            ))
            norm = math.sqrt(sum(v*v for v in q))
            values.append(tuple(float(v/norm) for v in q))
        require(max(abs(x-y) for x, y in zip(values[0], values[-1])) < 1e-6,
                "TAIL_CLIP_DOES_NOT_LOOP")
        id_out = base.emit_accessor(doc, bin_data, values, 5126, "VEC4")
        samplers.append({
            "input": times_id, "output": id_out,
            "interpolation": "LINEAR"
        })
        channels.append({
            "sampler": i,
            "target": {"node": nodeid, "path": "rotation"}
        })
        sampled[nodeid] = values
    doc["animations"].append({
        "name": "REPL_TAIL_FOUR_BONE_EXPRESSIVE_SWAY_NO_HOOF_MOTION",
        "channels": channels, "samplers": samplers,
        "extras": {
            "owner": "tail_only",
            "duration_seconds": 4.0,
            "acceptance": "PENDING",
            "mane_and_body_motion": "NONE",
            "wind_or_cloth": False
        }
    })
    require(json.dumps(doc["animations"][0], sort_keys=True) == previous,
            "LOCKED_NECK_CLIP_MODIFIED")
    return sampled


def pose_at_frame(sampled, ix):
    return {nodeid: quaternions[ix] for nodeid, quaternions in sampled.items()}


def validate_real_skin(doc, binary, base, by_name,
                       newj, neww, positions, oldj, oldw, sampled):
    body = doc["meshes"][0]["primitives"][0]
    bodypos = base.accessor(doc, binary, body["attributes"]["POSITION"])
    bodyj = base.accessor(doc, binary, body["attributes"]["JOINTS_0"])
    bodyw = base.accessor(doc, binary, body["attributes"]["WEIGHTS_0"])
    require(len(bodypos) == 6082, "BODY_VERTEX_COUNT_CHANGED")
    old_expected = base.EXPECTED_JOINTS
    try:
        base.EXPECTED_JOINTS = EXPECTED_JOINTS
        rest = base.skin_matrices(doc, binary, base.world_matrices(doc, {}))
        original_mane = [
            base.deform_vertex(p, j, w, rest)
            for p, j, w in zip(positions, oldj, oldw)
            if p[2] >= -0.65
        ]
        new_mane = [
            base.deform_vertex(p, j, w, rest)
            for p, j, w in zip(positions, newj, neww)
            if p[2] >= -0.65
        ]
        root_mane_delta = max(
            math.dist(x, y) for x, y in zip(original_mane, new_mane)
        )
        require(root_mane_delta < 1e-8, "MANE_ACCEPTED_REST_DEFORM_CHANGED")
        tail_indices = [
            i for i, p in enumerate(positions) if p[2] < -0.65
        ]
        mane_indices = [
            i for i, p in enumerate(positions) if p[2] >= -0.65
        ]
        rest_tail = [
            base.deform_vertex(positions[i], newj[i], neww[i], rest)
            for i in tail_indices
        ]
        rest_error = max(
            math.dist(positions[i], p)
            for i, p in zip(tail_indices, rest_tail)
        )
        require(rest_error < 0.0003, "TAIL_REST_SILHOUETTE_CHANGED")
        hoof_indices = [i for i, p in enumerate(bodypos) if p[1] < 0.12]
        require(len(hoof_indices) >= 50, "HOOF_WITNESSES_MISSING")
        rest_hooves = [
            base.deform_vertex(bodypos[i], bodyj[i], bodyw[i], rest)
            for i in hoof_indices
        ]
        max_hoof = 0.0
        max_body = 0.0
        max_mane = 0.0
        max_tail = 0.0
        sample_counts = 0
        for frame_index in range(len(TAIL_REVIEW_TIMES)):
            pose = pose_at_frame(sampled, frame_index)
            matrices = base.skin_matrices(
                doc, binary, base.world_matrices(doc, pose))
            for i, p0 in zip(hoof_indices, rest_hooves):
                p1 = base.deform_vertex(bodypos[i], bodyj[i], bodyw[i], matrices)
                max_hoof = max(max_hoof, math.dist(p0, p1))
            for i in range(0, len(bodypos), 16):
                p0 = base.deform_vertex(
                    bodypos[i], bodyj[i], bodyw[i], rest)
                p1 = base.deform_vertex(
                    bodypos[i], bodyj[i], bodyw[i], matrices)
                max_body = max(max_body, math.dist(p0, p1))
            for i in mane_indices:
                p0 = base.deform_vertex(
                    positions[i], newj[i], neww[i], rest)
                p1 = base.deform_vertex(
                    positions[i], newj[i], neww[i], matrices)
                max_mane = max(max_mane, math.dist(p0, p1))
            for i in tail_indices:
                p = base.deform_vertex(
                    positions[i], newj[i], neww[i], matrices)
                require(all(math.isfinite(v) for v in p),
                        "NONFINITE_TAIL_GEOMETRY")
                max_tail = max(max_tail, math.dist(rest_tail[
                    tail_indices.index(i)], p))
            sample_counts += 1
        require(max_body < 1e-6 and max_hoof < 1e-6,
                "TAIL_CLIP_MOVED_BODY_OR_HOOF")
        require(max_mane < 1e-6,
                "TAIL_CLIP_MOVED_ACCEPTED_MANE")
        require(0.01 < max_tail < 0.35,
                "TAIL_MOTION_INVISIBLE_OR_EXPLOSIVE")
        # Preserve predecessor neck review: no new keys affect its original
        # clip, and the mane's joint indices and weights have not changed.
        return {
            "sampled_frames": sample_counts,
            "original_mane_rest_delta": root_mane_delta,
            "tail_rest_delta": rest_error,
            "body_drift": max_body,
            "hoof_drift": max_hoof,
            "mane_drift_in_tail_clip": max_mane,
            "tail_max_motion": max_tail,
            "tail_joint_channels": len(sampled),
            "animation_clips": len(doc["animations"]),
            "human_acceptance": "PENDING"
        }
    finally:
        base.EXPECTED_JOINTS = old_expected


HTML_TEMPLATE = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Repl four-tail-control textured 3D review</title>
<style>
body{margin:0;background:#141720;color:#eee;font:15px/1.5 system-ui}
main{max-width:1200px;margin:auto;padding:12px}
#stage{width:100%;height:75vh;min-height:400px;border:1px solid #4c5063;
border-radius:10px;display:block;background:#deddd8;touch-action:none}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
button,select{padding:10px;font:inherit;border-radius:7px}
#status{font-weight:600;color:#a9e1c5}
small{color:#ccc}
</style></head><body><main>
<h2>Repl v0.3.0: full textured tail review</h2>
<p id="status" role="status" aria-live="polite">Loading the real GLB and original materials…</p>
<div class="controls">
<label>Clip <select id="clip"><option value="tail">Tail motion (four bones)</option>
<option value="neck">Original neck/mane review</option></select></label>
<label>View <select id="view"><option value="three">Three-quarter</option>
<option value="side">Side</option><option value="front">Front</option>
<option value="rear">Rear</option></select></label>
<button id="pause">Pause</button><button id="capture">Save full-resolution PNG frame</button>
</div>
<canvas id="stage" aria-label="Textured 3D model of Repl in tail review"></canvas>
<p>All original body vertices, skin, textures, and three mane controls are preserved.
There are <strong>four progressively shorter tail controls</strong>. During the
tail-only clip, the body, hooves, mane and horn remain stationary. No wind or cloth.
Rotate the camera with touch or drag, pinch to zoom. The clip is an engineering
candidate and still needs a human visual verdict.</p>
<small>This browser-based GLB preview uses the Three.js libraries from the pinned
public CDN and therefore needs internet connectivity once to load those
libraries. The accompanying GLB itself contains the original materials and
does not depend on the CDN.</small>
<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const canvas=document.querySelector('#stage');
const status=document.querySelector('#status');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.25;
const scene=new THREE.Scene();scene.background=new THREE.Color('#dad8d4');
const camera=new THREE.PerspectiveCamera(40,1,.01,100);
scene.add(new THREE.HemisphereLight(0xffffff,0x686365,2.5));
const sun=new THREE.DirectionalLight(0xffffff,3.0);sun.position.set(5,9,7);scene.add(sun);
const fill=new THREE.DirectionalLight(0xffbbc4,1.1);fill.position.set(-5,4,-5);scene.add(fill);
const controls=new OrbitControls(camera,canvas);
controls.enableDamping=true; controls.enablePan=true;
const grid=new THREE.GridHelper(4,20,0x999999,0xb8b8b8);
grid.position.y=-.012;scene.add(grid);
const mixerClock=new THREE.Clock();
let mixer=null,root=null,gltf=null,currentAction=null,paused=false;
function resize(){
  const w=canvas.clientWidth||800,h=canvas.clientHeight||600;
  renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(canvas);resize();
function selectClip(){
  if(!mixer||!gltf)return;
  mixer.stopAllAction();
  const tail=gltf.animations.find(c=>c.name.includes('TAIL_FOUR_BONE'));
  const neck=gltf.animations.find(c=>c.name.includes('NECK_REVIEW'));
  currentAction=mixer.clipAction(document.querySelector('#clip').value==='tail'?
      (tail||gltf.animations[gltf.animations.length-1]):
      (neck||gltf.animations[0]));
  currentAction.reset().play();
  mixer.update(0);
}
function cameraPreset(){
  if(!root)return;
  const b=new THREE.Box3().setFromObject(root),c=b.getCenter(new THREE.Vector3());
  const s=b.getSize(new THREE.Vector3()),r=Math.max(s.length()*.75,1.4);
  controls.target.copy(c);
  const value=document.querySelector('#view').value;
  const offsets={three:[1,.5,1],side:[1,.18,0],front:[0,.12,1],rear:[0,.12,-1]};
  const o=offsets[value];
  camera.position.set(c.x+o[0]*r*1.7,c.y+o[1]*r*1.7,c.z+o[2]*r*1.7);
  controls.update();
}
document.querySelector('#view').addEventListener('change',cameraPreset);
document.querySelector('#clip').addEventListener('change',selectClip);
document.querySelector('#pause').addEventListener('click',e=>{
  paused=!paused;e.target.textContent=paused?'Resume':'Pause';
});
document.querySelector('#capture').addEventListener('click',()=>{
  canvas.toBlob(blob=>{if(!blob)return;
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);
    a.download='Repl_TailFourControls_v0.3.0_frame.png';
    a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  },'image/png');
});
function render(){
  requestAnimationFrame(render);
  const dt=Math.min(mixerClock.getDelta(),.07);
  if(mixer&&!paused)mixer.update(dt);
  controls.update();renderer.render(scene,camera);
}
render();
try{
  const encoded='__GLB_BASE64__';
  const bytes=Uint8Array.from(atob(encoded),v=>v.charCodeAt(0));
  new GLTFLoader().parse(bytes.buffer,'',model=>{
    gltf=model;root=model.scene;scene.add(root);
    root.traverse(o=>{if(o.isMesh){o.frustumCulled=false;}});
    mixer=new THREE.AnimationMixer(root);
    cameraPreset();selectClip();
    status.textContent='Real textured GLB loaded: '+gltf.animations.length+
      ' clips. Tail motion is separate from the locked mane review.';
  },error=>{status.textContent='GLB parse error: '+String(error);});
}catch(error){status.textContent='Viewer error: '+String(error);}
</script></main></body></html>"""


def make_artifacts(source, prev, base):
    v020_glb, v020_report, _unused_preview = prev.create_artifacts(source, base)
    doc, original_bin = prev.read_glb_bytes(v020_glb)
    require(len(doc.get("animations", [])) == 1, "V020_ANIMATIONS_CHANGED")
    original_body_json = json.dumps(doc["meshes"][0], sort_keys=True)
    original_mane_node_json = {
        n["name"]: json.dumps(n, sort_keys=True)
        for n in doc["nodes"] if n.get("name") in MANE_NAMES
    }
    original_hair_prim = doc["meshes"][1]["primitives"][0]
    static_attrs = {
        k: original_hair_prim["attributes"][k]
        for k in ("POSITION", "NORMAL", "TEXCOORD_0")
    }
    source_material = original_hair_prim.get("material")
    lengths = check_progressive_lengths()
    ibms, by_name, newmanifest = add_descendants(doc, original_bin, prev, base)
    newj, neww, positions, coverage, oldj, oldw = remap_tail_only(
        doc, original_bin, base, by_name)
    extra = bytearray(original_bin)
    matrix_acc = base.emit_accessor(
        doc, extra, [prev.matrix_to_glb_mat4(m) for m in ibms],
        5126, "MAT4")
    doc["skins"][0]["inverseBindMatrices"] = matrix_acc
    hair = doc["meshes"][1]["primitives"][0]
    hair["attributes"]["JOINTS_0"] = base.emit_accessor(
        doc, extra, newj, 5123, "VEC4", 34962)
    hair["attributes"]["WEIGHTS_0"] = base.emit_accessor(
        doc, extra, neww, 5126, "VEC4", 34962)
    require(hair.get("material") == source_material and all(
        hair["attributes"][k] == v for k,v in static_attrs.items()),
        "ACCEPTED_HAIR_GEOMETRY_OR_MATERIAL_CHANGED")
    require(json.dumps(doc["meshes"][0], sort_keys=True) == original_body_json,
            "ACCEPTED_BODY_MESH_DEFINITION_CHANGED")
    require(all(json.dumps(n, sort_keys=True) == original_mane_node_json[n["name"]]
                for n in doc["nodes"] if n.get("name") in MANE_NAMES),
            "ACCEPTED_MANE_NODE_CHANGED")
    require(bytes(extra[:len(original_bin)]) == original_bin,
            "ACCEPTED_BINARY_BUFFER_REWRITTEN")
    clip = add_tail_clip(doc, extra, base, by_name)
    verdict = validate_real_skin(
        doc, bytes(extra), base, by_name, newj, neww, positions,
        oldj, oldw, clip)
    doc["asset"].setdefault("extras", {})["replHairCampaign"] = {
        "version": VERSION,
        "predecessor": "v0.2.0: three accepted mane controls preserved",
        "four_tail_controls": list(TAIL_NAMES),
        "tail_length_decreasing": lengths,
        "wind_simulation": False,
        "human_acceptance": "PENDING_TAIL_ONLY"
    }
    final_glb = base.glb_encode(doc, bytes(extra))
    # Genuine textured triangles, original materials and both animation clips.
    html = HTML_TEMPLATE.replace(
        "__GLB_BASE64__", base64.b64encode(final_glb).decode("ascii"))
    report = {
        "campaign": CAMPAIGN, "version": VERSION,
        "source_sha256": SOURCE_SHA256,
        "predecessor": "0.2.0",
        "locked_original_predecessor_blob": PREDECESSOR_BLOB_SHA,
        "mane": "UNMODIFIED: same three nodes, same index and weight tuples",
        "tail": {
            "four_controls": list(TAIL_NAMES),
            "world_pivots": [list(x) for x in TAIL_PIVOTS],
            "shrinking_link_lengths": lengths,
            "added": newmanifest
        },
        "coverage": coverage,
        "validation": verdict,
        "materials": "ORIGINAL GLB ASSET MATERIALS, NO CHANGES",
        "review": {
            "primary": "FULL_TEXTURED_3D_BROWSER_GLTF",
            "renderer": "Three.js v0.170 CDN; requires network for renderer modules",
            "fallback": "original-material derived GLB for compatible 3D viewer",
            "predecessor_dot_cloud": "NOT USED"
        },
        "human_tail_visual_verdict": "PENDING",
        "untouched": [
            "Repl.blend", "source Repl.glb", "body mesh/weights",
            "original 43 joints", "existing 3 mane controls",
            "existing 2 tail-control positions/parents",
            "original neck review clip", "all glTF textures/materials"
        ],
        "excluded": [
            "hoof locomotion", "cloth", "wind shader", "extra mane bones",
            "manual weight painting", "source overwrite"
        ]
    }
    return final_glb, json.dumps(report, indent=2, sort_keys=True), html


def output_folder(value):
    if value:
        return Path(value).expanduser().resolve()
    h = Path.home()
    base = h/"storage"/"downloads"
    return (base if base.is_dir() else h/"Downloads")/OUTPUT_DIR


def validate_receipt(folder):
    receiptfile = folder/RECEIPT_NAME
    require(receiptfile.is_file(), "INCOMPLETE_OR_COLLIDING_RELEASE")
    r = json.loads(receiptfile.read_text(encoding="utf8"))
    require(r.get("version") == VERSION and
            r.get("source_sha256") == SOURCE_SHA256,
            "EXISTING_OUTPUT_WRONG_VERSION_OR_SOURCE")
    for name, digest in r.get("outputs", {}).items():
        path = folder/name
        require(path.is_file() and file_sha(path) == digest,
                "RELEASE_READBACK_HASH_MISMATCH:" + name)
    return r


def release(args, prev, base):
    source = base.resolve_source(args.source)
    print("ORIGINAL_INPUT="+str(source))
    print("ORIGINAL_SHA256="+file_sha(source))
    folder = output_folder(args.output)
    print("VERSIONED_DESTINATION="+str(folder))
    if folder.exists():
        receipt = validate_receipt(folder)
        print("RELEASE_ALREADY_VERIFIED=YES")
        print("GLB_SHA256="+receipt["outputs"][GLB_NAME])
        print("HUMAN_VERDICT=PENDING_TAIL_ONLY")
        return
    require(folder.parent.is_dir(), "SHARED_DOWNLOADS_PARENT_UNAVAILABLE")
    tmp = Path(tempfile.mkdtemp(prefix=".repl_tail_v030_",
                                dir=str(folder.parent)))
    try:
        glb, report, html = make_artifacts(source, prev, base)
        outputs = {
            GLB_NAME: glb,
            HTML_NAME: html.encode("utf8"),
            REPORT_NAME: report.encode("utf8")
        }
        for name, content in outputs.items():
            (tmp/name).write_bytes(content)
        hashes = {n: file_sha(tmp/n) for n in outputs}
        receipt = {
            "campaign": CAMPAIGN, "version": VERSION,
            "source_sha256": SOURCE_SHA256,
            "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_path": str(source),
            "github_commit_pin": args.revision or "UNSPECIFIED",
            "outputs": hashes,
            "status": "NUMERIC_VALIDATED / HUMAN_TAIL_VISUAL_PENDING",
            "original_source_modified": False,
            "mane_acceptance": "PRESERVED_FROM_V0.2.0_OWNER_VERDICT",
            "tail_acceptance": "PENDING",
            "physical_android_browser_visual": "UNVERIFIED"
        }
        (tmp/RECEIPT_NAME).write_text(
            json.dumps(receipt, indent=2, sort_keys=True), encoding="utf8")
        require(not folder.exists(), "VERSIONED_OUTPUT_RACE")
        tmp.rename(folder)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    validate_receipt(folder)
    print("DERIVED_GLB="+str(folder/GLB_NAME))
    print("TEXTURED_PREVIEW="+str(folder/HTML_NAME))
    print("DERIVED_GLB_SHA256="+hashes[GLB_NAME])
    print("FULL_TEXTURED_RENDER=HTML_BROWSER_AVAILABLE_NEEDS_VISUAL_REVIEW")
    print("HUMAN_TAIL_VERDICT=PENDING")
    # One exact-file media registration, not a recursive folder scan.
    target = folder/HTML_NAME
    cmd = "mediarefresh" if shutil.which("mediarefresh") else (
        "termux-media-scan" if shutil.which("termux-media-scan") else None)
    if cmd:
        try:
            p = subprocess.run([cmd, str(target)], timeout=15,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               check=False)
            print("MEDIA_SCAN="+(
                "REQUESTED" if p.returncode == 0 else "FAILED"))
        except (OSError, subprocess.TimeoutExpired):
            print("MEDIA_SCAN=FAILED")
    else:
        print("MEDIA_SCAN=UNAVAILABLE")
    if shutil.which("termux-open"):
        try:
            p = subprocess.run(["termux-open",str(target)],timeout=14,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,check=False)
            print("VIEWER_OPEN="+(
                "REQUESTED_NOT_CONFIRMED" if p.returncode == 0
                else "FAILED"))
        except (OSError, subprocess.TimeoutExpired):
            print("VIEWER_OPEN=FAILED")
    else:
        print("VIEWER_OPEN=UNAVAILABLE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", nargs="?", default="run",
                        choices=("run","resume","doctor","status","rollback"))
    parser.add_argument("--source", help="Exact existing Repl.glb path")
    parser.add_argument("--output", help="Immutable versioned output folder")
    parser.add_argument("--revision", help="Pinned Git SHA from launcher")
    args = parser.parse_args()
    print("CAMPAIGN="+CAMPAIGN)
    print("VERSION="+VERSION)
    print("RUNNER="+str(Path(__file__).resolve()))
    print("RUNNER_SHA256="+file_sha(Path(__file__).resolve()))
    print("EXPECTED_SOURCE_SHA256="+SOURCE_SHA256)
    if args.operation in ("status","rollback"):
        if args.operation == "rollback":
            print("ROLLBACK=NOT_REQUIRED_ORIGINAL_NEVER_OVERWRITTEN")
        folder = output_folder(args.output)
        if folder.exists():
            r = validate_receipt(folder)
            print("DELIVERY="+r["status"])
        else:
            print("DELIVERY=NOT_STARTED")
        return
    prev, base = load_predecessor()
    source = base.resolve_source(args.source)
    base.glb_load(source)
    print("SOURCE_PREFLIGHT=PASS")
    print("PREDECESSOR_ENGINE_IDENTITY=VERIFIED")
    if args.operation == "doctor":
        print("DOCTOR=PASS_NO_MUTATION")
    else:
        release(args, prev, base)


if __name__ == "__main__":
    try:
        main()
    except (Blocked, ValueError, KeyError, IndexError, TypeError) as e:
        print("CAMPAIGN_STATUS=BLOCKED")
        print("CAUSE="+type(e).__name__+": "+str(e))
        print("SOURCE_MODIFIED=NO")
        print("HUMAN_VERDICT=PENDING")
        sys.exit(2)
    except Exception as e:
        traceback.print_exc()
        print("CAMPAIGN_STATUS=FAILED")
        print("CAUSE="+type(e).__name__+": "+str(e))
        print("SOURCE_MODIFIED=NO")
        sys.exit(3)
