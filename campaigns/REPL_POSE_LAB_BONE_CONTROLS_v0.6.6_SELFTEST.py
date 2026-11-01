#!/usr/bin/env python3
"""Functional source and gesture math gate, no network or repo mutation."""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path

def check(ok,reason):
 if not ok:raise RuntimeError('SELFTEST_FAIL:'+reason)
def main():
 a=argparse.ArgumentParser();a.add_argument('--packet',required=True);args=a.parse_args()
 p=Path(args.packet);m=json.loads((p/'manifest.json').read_text())
 check(m['version']=='0.6.6','version')
 for name,meta in m['files'].items():
  b=(p/name).read_bytes();check(len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256'],'hash:'+name)
 js=(p/'campaign/pose_lab_bones.js').read_text()
 patch=(p/'campaign/patch_viewer.py').read_text()
 for fragment in ('pointerdown','pointermove','pointerup','pointercancel','pl-additive','replWrappedAngle',
  'REPL_TIP_BONES','pl-lock','state.locks[axis]','pl-export','replDistancePointSegment'):
  check(fragment in js,'missing_js:'+fragment)
 check('tipRestFrozenForPreview' in js,'toe_rest_export')
 check('sourceCanonicalSha256' in js,'provenance')
 check('updateMarkers' in js and 'overlay.visible' in js,'skeleton_renderer')
 import importlib.util
 spec=importlib.util.spec_from_file_location('pl_patch',p/'campaign/patch_viewer.py')
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 tpl=('''<html><style></style><title>Repl · visible four-leg swing shape v0.6.5</title>'''
      '''<h1>Repl · visible four-leg bend correction (forward travel)</h1>'''
      '''<div id="footfall"></div><script type="module">'''
      '''let neckRoot=null,neckWorld0=null,lastTravel=0;'''
      '''function animate(){syncCamera();reportFootfalls();updateHinges();orbit.update();renderer.render(scene,camera);}'''
      '''  selectClip();\n },error=>'''+'''__GIZMO_JS__ __EMBEDDED_GLB_BASE64__''')
 out=v.patch(tpl,js,'a'*64)
 check(out.count('installReplPoseLab')==2 and out.count('id="pl-edit"')==1,'injection')
 check(len(re.findall('id="pl-lock[XYZ]"',out))==3,'axis_locks')
 check(out.count('let poseLab=null')==1,'state')
 node=shutil.which('node')
 if node:
  # Syntax check the actual injected editor (no remote browser or THREE needed).
  q=subprocess.run([node,'--check','--input-type=module'],input=js,encoding='utf8',capture_output=True)
  check(q.returncode==0,'node_js_parse:'+q.stderr[-200:])
  math='''const assert=require('node:assert/strict');'''+js+'''
  assert.ok(Math.abs(replWrappedAngle(4*Math.PI))<1e-12);
  assert.ok(Math.abs(replWrappedAngle(3*Math.PI/2)+Math.PI/2)<1e-9);
  assert.equal(replDistancePointSegment({x:5,y:5},{x:0,y:0},{x:10,y:0}),5);
  assert.equal(replDistancePointSegment({x:12,y:0},{x:0,y:0},{x:10,y:0}),2);
  console.log('GESTURE_MATH=PASS');'''
  r=subprocess.run([node],input=math,encoding='utf8',capture_output=True)
  check(r.returncode==0,'gesture_math:'+r.stderr[-250:])
  print('JS_SYNTAX=PASS\nGESTURE_MATH=PASS',flush=True)
 else:print('NODE=NOT_INSTALLED__HOST_SOURCE_SYNTAX_PRETESTED',flush=True)
 print('PACKET_SELFTEST=PASS',flush=True)
if __name__=='__main__':main()
