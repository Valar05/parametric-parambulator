#!/usr/bin/env python3
import pathlib,sys,re,json
root=pathlib.Path(sys.argv[1]);view=(root/'viewer.mjs').read_text();html=(root/'index.html').read_text()
need=['new OrbitControls(camera,renderer.domElement)','orbit.target.add(delta)','new SourceFootContact','rootAt(rootCurve,totalPhase)',
'acceptedAnkle=sourceHip.clone()','initPreviewLegs();previewStage=', 'function diagnosticPoseStep(dt){',
'PREVIEW_RUNNING','PROCEDURAL_PREVIEW_UNPINNED','PHYSICAL_GROUND_PINNING',
'PHYSICAL_AUDIT_UNAVAILABLE','REAL_GLB_32_STEP_STARTUP_SMOKE','ARCHIVED_V019_ROOT_CONTACTS',
'32;i++)physicsStep(1/120)', 'ownerVisualAcceptance:false', 'calibrationErrorBehavior']
for n in need[:-1]:
 if n not in view:raise SystemExit('REGRESSION_MISSING:'+n)
assert 'calibrationErrorBehavior' in (root/'contract.json').read_text()
assert 'touch-action:none' in html and 'resetCamera' in html
assert 'new THREE.AnimationMixer(actor)' not in view
if 'playing=false;ready=false;if(actor&&!actor.parent)' in view:raise SystemExit('STATIC_GAIT_FAILURE_REINTRODUCED')
assert view.count("function frame(now)")==1
assert view.count("requestAnimationFrame(frame);")==2
for p in root.glob('*.mjs'):
 if 'v0.1.14' in p.name:raise SystemExit('OLD_NAMED_SOURCE_COLLISION')
print('STARTUP_PREVIEW_AND_PHYSICS_BOUNDARY_REGRESSIONS_PASS')
