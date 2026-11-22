#!/usr/bin/env python3
"""Patch EXACT published v0.1.14 with startup preview, verified original reference root and visible failure provenance."""
from pathlib import Path
import sys,json,hashlib
root=Path(sys.argv[1]).resolve()
target=root/'tools/hareworks-forward-woman/v0.1.15'
p=target/'viewer.mjs'
s=p.read_text()
def once(old,new):
 global s
 if s.count(old)!=1:raise RuntimeError('PATCH_ANCHOR_COUNT_'+str(s.count(old))+' '+old[:120])
 s=s.replace(old,new,1)
def region(first,end,replacement):
 global s
 if s.count(first)!=1 or s.count(end)!=1:raise RuntimeError('PATCH_REGION_NOT_UNIQUE '+first[:60]+' '+str(s.count(first)))
 a=s.index(first);b=s.index(end,a)
 if b<=a:raise RuntimeError('PATCH_REGION_ORDER')
 s=s[:a]+replacement+s[b:]
# New diagnostic mode does NOT play the source clip on the visible actor. It renders the
# accepted v0.1.9 analytic hip/ankle/knee-pole gait when physics calibration fails.
once("let sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;", """let sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;
let previewReady=false,previewLegs=null,previewFault='',previewStage='GLB_LOAD',previewFaults=0;
let motionMode='LOADING',frameTickCount=0,lastPreviewError='',previewCycle=0;
const REFERENCE_ROOT_UNITS_PER_CYCLE=1.224546;
const ownerAcceptance=false; // No synthetic or diagnostic result can grant visual acceptance.
function previewStatus(stage,why){
 if(motionMode==='PHYSICAL_GROUND_PINNING')previewCycle=totalPhase;
 previewStage=stage;previewFault=String(why);motionMode='PROCEDURAL_PREVIEW_UNPINNED';ready=false;playing=true;
 for(const p of Object.values(drawPins))p.visible=false;
 $('play').textContent='Pause';
 status('PHYSICAL_IK_BLOCKED '+stage+' '+previewFault+' · V0.1.9 PROCEDURAL WALK PREVIEW MOVING · NOT GROUND PINNED');
 $('metrics').textContent='PROCEDURAL PREVIEW ONLY, NOT CONTACT VALIDATION\\n'+previewFault;
 if(actor)pinCamera();
 if(previewReady) Promise.resolve().then(()=>fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({schema:'hareworks-v0.1.15-startup-diagnostic',stage,error:previewFault,sourceSha256:SOURCE_SHA,
  mode:motionMode,ownerVisualAcceptance:false,previewReady,physicalContactVerified:false})}).catch(()=>{}));
}
function initPreviewLegs(){
 if(!actor||!rig||!rest||!footProfile||!pelvisProfile||!fit)throw Error('PREVIEW_BASELINE_NOT_READY');
 previewLegs={};for(const [side,arr] of Object.entries(names)){
  const chain=arr.map(n=>rig[n]);if(chain.some(x=>!x))throw Error('PREVIEW_LEG_MISSING_'+side);
  const [up,knee,bridge,foot]=chain;
  previewLegs[side]={chain,up,knee,foot,upperLength:wpos(up).distanceTo(wpos(knee)),
   lowerLength:wpos(knee).distanceTo(wpos(foot))};
 }
 previewReady=true;motionMode='PROCEDURAL_PREVIEW_UNPINNED';
}
function diagnosticPoseStep(dt){
 // The original accepted phase equations, not the source AnimationMixer.
 previewCycle+=Math.max(0,speed)*dt/REFERENCE_ROOT_UNITS_PER_CYCLE;
 phase=mod1(previewCycle);worldZ=REFERENCE_ROOT_UNITS_PER_CYCLE*previewCycle;
 frameBody(phase);
 const q=phase*clipDuration,yaw=independentPose(pelvisProfile,q).pelvisYaw;
 for(const [side,c] of Object.entries(previewLegs||{})){
  try{
   for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
   const H=wpos(c.up),K0=wpos(c.knee),v=legAt(footProfile,side,q);
   const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));
   const dist=target.distanceTo(H),limit=c.upperLength+c.lowerLength-.001;
   if(dist>limit||dist<Math.abs(c.upperLength-c.lowerLength)+.001){
    target.sub(H).setLength(clamp(dist,Math.abs(c.upperLength-c.lowerLength)+.001,limit)).add(H);
    previewFaults++;lastPreviewError='ANATOMICAL_PREVIEW_REACH_CLAMP_'+side+'_'+dist.toFixed(5);
   }
   const K=V(...kneeFromTarget(H.toArray(),target.toArray(),c.upperLength,c.lowerLength,rotateY(v.poleLocal,yaw)));
   turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
   turnToward(c.knee,wpos(c.foot),target);actor.updateMatrixWorld(true);
   if(sourceSamples&&sourceSamples[side]&&sourceSamples[side].length>=60){
    const f=sourceAt(sourceSamples[side],phase);setWorldQ(c.foot,measuredFootQ(f));actor.updateMatrixWorld(true);
   }
  }catch(err){
   previewFaults++;lastPreviewError=String(err.message||err);
  }
 }
 frameTickCount++;
 if(frameTickCount%40===0){
  $('metrics').textContent='V0.1.9 PROCEDURAL MOTION PREVIEW · NOT GROUND PINNED\\n'+
   'phase '+phase.toFixed(3)+' root Z '+worldZ.toFixed(3)+' model '+SOURCE_SHA.slice(0,12)+'\\n'+
   'PHYSICAL_CONTACT_GATE=BLOCKED '+previewStage+' '+previewFault+'\\n'+
   'diagnostic solver warnings '+previewFaults+(lastPreviewError?' '+lastPreviewError:'');
 }
}
""")
# Real contact physics is unchanged, but entering it requires an observable 32-step smoke test.
once("$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';status(playing?'RUNNING · world travel and anchored soles':'PAUSED · world contact anchors retained')};", """$('play').onclick=()=>{
 if(!ready&&!previewReady){status('BLOCKED_NO_RUNNING_CONTROLLER · model is visible only');return;}
 playing=!playing;$('play').textContent=playing?'Pause':'Play';
 if(motionMode!=='PHYSICAL_GROUND_PINNING'){
  status((playing?'PREVIEW_RUNNING':'PREVIEW_PAUSED')+' · ORIGINAL V0.1.9 PROCEDURAL GAIT · UNPINNED · '+previewFault);
 }else status(playing?'PHYSICAL_WORLD_IK_RUNNING':'PHYSICAL_WORLD_IK_PAUSED');
};""")
once("$('reset').onclick=()=>{initRun();status('WORLD RUN RESET · actor, anchors and camera synchronized')};", """$('reset').onclick=()=>{
 if(motionMode!=='PHYSICAL_GROUND_PINNING'){
  if(!previewReady){status('RESET_UNAVAILABLE_NO_CONTROLLER');return;}
  previewCycle=0;worldZ=0;frameBody(0);for(const p of Object.values(drawPins))p.visible=false;
  status('V0.1.9 PROCEDURAL PREVIEW RESET · UNPINNED · '+previewFault);pinCamera();return;
 }
 try{initRun();status('PHYSICAL WORLD RUN RESET · actor, anchors and orbit synchronized');}
 catch(e){previewStatus('PHYSICAL_RESET',e.message||String(e));}
};""")
once("function updateMotionStatus(){\n $('motionStatus').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;\n}", """function updateMotionStatus(){
 if(motionMode==='PROCEDURAL_PREVIEW_UNPINNED'){
  $('motionStatus').textContent='UNPINNED SOURCE PROCEDURAL PREVIEW · '+REFERENCE_ROOT_UNITS_PER_CYCLE.toFixed(4)+' u/full cycle · contact audit NOT available';
 }else $('motionStatus').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;
}""")
once("$('showContacts').onchange=()=>{for(const side of ['left','right'])drawPins[side].visible=$('showContacts').checked};", """$('showContacts').onchange=()=>{
 for(const side of ['left','right'])drawPins[side].visible=ready&&motionMode==='PHYSICAL_GROUND_PINNING'&&$('showContacts').checked;
};""")
once("finally{const summary=$('metrics').textContent;speed=oldSpeed;initRun();$('metrics').textContent=summary;playing=was;$('play').textContent=playing?'Pause':'Play';}", """finally{const summary=$('metrics').textContent;speed=oldSpeed;
  if(motionMode==='PHYSICAL_GROUND_PINNING'){
   try{initRun();$('metrics').textContent=summary;}
   catch(e){previewStatus('PHYSICAL_AUDIT_RESTART',e.message||String(e));}
  }
  playing=was;$('play').textContent=playing?'Pause':'Play';}
""")
once("$('audit').onclick=async()=>{if(!ready)return;", """$('audit').onclick=async()=>{if(!ready){status('PHYSICAL_AUDIT_UNAVAILABLE · V0.1.9 PREVIEW DOES NOT PROVE GROUND PINNING · '+previewFault);return;}""")
region('function frame(now){requestAnimationFrame(frame);','requestAnimationFrame(frame);\ntry{\n const response=', """function frame(now){requestAnimationFrame(frame);
 const delta=Math.min(.055,Math.max(0,(now-frameTimer)/1000));frameTimer=now;
 if(playing&&motionMode==='PHYSICAL_GROUND_PINNING'&&ready){
  accumulator=Math.min(.06,accumulator+delta);
  try{let count=0;while(accumulator>=1/120&&count<9){physicsStep(1/120);accumulator-=1/120;count++}
   pinCamera();if(runFrames%30===0)renderMetrics();
  }catch(e){failedFrames++;previewStatus('PHYSICAL_RUNTIME_STEP',e.message||String(e));}
 }else if(playing&&previewReady&&motionMode==='PROCEDURAL_PREVIEW_UNPINNED'){
  try{diagnosticPoseStep(delta);pinCamera();}catch(e){lastPreviewError=String(e.message||e);status('PREVIEW_STEP_ERROR '+lastPreviewError);}
 }
 orbit.update();renderer.render(scene,camera);
}
""")
# Model + original fit becomes enough to start an honest procedural reference preview.
once("fit=sampleFitted(source,mixer,srcRig);mixer.setTime(0);source.updateMatrixWorld(true);", """try{fit=sampleFitted(source,mixer,srcRig);}catch(fitError){
  fit={};previewFault='UPPER_BODY_FIT_FAILED '+String(fitError.message||fitError);
  console.warn('UPPER_BODY_FIT_RECOVERY_TO_REST_UPPER',fitError);
 }
 mixer.setTime(0);source.updateMatrixWorld(true);
 initPreviewLegs();previewStage='PROCEDURAL_REFERENCE_LIVENESS';
 diagnosticPoseStep(0);
 const relativeFoot=(side)=>wpos(previewLegs[side].foot).sub(wpos(previewLegs[side].up));
 const atStart={left:relativeFoot('left'),right:relativeFoot('right')};
 diagnosticPoseStep(.35*REFERENCE_ROOT_UNITS_PER_CYCLE/Math.max(speed,.1));
 const previewLegAmplitude=Math.max(...['left','right'].map(side=>relativeFoot(side).distanceTo(atStart[side])));
 if(!Number.isFinite(previewLegAmplitude)||previewLegAmplitude<.045){
  previewReady=false;throw Error('V019_PROCEDURAL_PREVIEW_LEG_MOTION_NOT_OBSERVABLE '+previewLegAmplitude);
 }
 previewCycle=0;worldZ=0;frameBody(0);
 console.info('V019_REFERENCE_LEG_MOTION_LIVENESS_PASS',previewLegAmplitude);
 previewStage='SHOE_WITNESS_CALIBRATION';
 if(previewFault)throw Error(previewFault);
 status('V0.1.9 PROCEDURAL REFERENCE GAIT MOVEMENT VERIFIED · calibrating physical contacts…');""")
# Archived source witnesses are canonical, reproducible, and independent of how a later shoe mesh splits.
region(" sourceGaits={left:inferVelocityContact(sourceSamples.left),right:inferVelocityContact(sourceSamples.right)};",
       " updateMotionStatus();", """ previewStage='ARCHIVED_V019_ROOT_CONTACTS';
 const archivedResponse=await fetch('../v0.1.3/reference-leg-witnesses.json',{cache:'no-store'});
 if(!archivedResponse.ok)throw Error('ARCHIVED_SOURCE_WITNESSES_HTTP_'+archivedResponse.status);
 const archived=await archivedResponse.json();
 if(archived.sourceSha256!==SOURCE_SHA||archived.sourceClip!=='Walking_Woman'||archived.samples?.length!==60)
  throw Error('ARCHIVED_V019_WITNESS_IDENTITY_INVALID');
 const baseline={left:[],right:[]};let largestFitDifference=0;
 for(let i=0;i<60;i++)for(const side of ['left','right']){
  const archivedLeg=archived.samples[i].legs[side],measured=sourceSamples[side][i*6];
  largestFitDifference=Math.max(largestFitDifference,V(...archivedLeg.ankle).distanceTo(V(...measured.ankle)));
  baseline[side].push({...measured,ankle:archivedLeg.ankle});
 }
 if(largestFitDifference>.045)throw Error('PROCEDURAL_V019_REFERENCE_POSE_DRIFT '+largestFitDifference.toFixed(6));
 sourceGaits={left:inferVelocityContact(baseline.left),right:inferVelocityContact(baseline.right)};
 const phaseSeparation=mod1(sourceGaits.left.start-sourceGaits.right.start);
 if(phaseSeparation<.30||phaseSeparation>.70)throw Error('LEFT_RIGHT_CONTACT_TIMING_AMBIGUOUS '+phaseSeparation);
 rootCurve=buildRootCurve(baseline,sourceGaits);stride=rootCurve.stride;
 previewStage='PHYSICAL_IK_WARM_START';
""")
# Remove duplicate old phase/window+root build now contained in replacement, preserving main rest.
# Source previously has a phase-separation block just before rootCurve; the replacement extends to updateMotionStatus.
# The replacement above retains the preceding original phase-separation block? guard no duplicate in resulting code.
# New real physical startup must run enough steps to reject a static or throwing controller.
once("ready=true;initRun();pinCamera();status('ACCEPTED V0.1.9 WALK + INVERTED WORLD SUPPORT · orbit restored · owner review pending');", """previewStage='REAL_GLB_32_STEP_STARTUP_SMOKE';
 ready=true;initRun();
 const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);
 const travelled=worldZ-startZ;
 if(!Number.isFinite(travelled)||travelled<.04)throw Error('NO_OBSERVABLE_WORLD_TRAVEL_AT_STARTUP '+travelled);
 if(!Number.isFinite(wpos(rig.mixamorigHips).x))throw Error('NONFINITE_ACTUAL_SKINNED_BODY');
 initRun();motionMode='PHYSICAL_GROUND_PINNING';playing=true;pinCamera();
 status('PHYSICAL IK CONTROLLER STARTED · 32 REAL SKINNED STEPS EXECUTED · owner gait approval pending');""")
once("}catch(e){playing=false;ready=false;if(actor&&!actor.parent){scene.add(actor);actor.updateMatrixWorld(true);}\n status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message+' · ORIGINAL RIG VISIBLE (STATIC DIAGNOSTIC; NOT A WALK)');console.error(e)}", """}catch(e){if(actor&&!actor.parent){scene.add(actor);actor.updateMatrixWorld(true);}
 console.error('REAL_MODEL_CALIBRATION_BLOCKED stage='+previewStage,e);
 previewStatus(previewStage,e.message||String(e));
 if(!previewReady){playing=false;status('CALIBRATION_AND_PREVIEW_UNAVAILABLE '+previewStage+' '+String(e.message||e));}
}""")
once("/* v0.1.14. ONE moving Walking_Woman.", "/* v0.1.15. ONE moving Walking_Woman.")
once('v0.1.14 ACCEPTED V019 INVERSE SUPPORT ROOT + REAL SHOE WITNESSES', 'v0.1.15 ACCEPTED V019 SOURCE ROOT + HONEST RUNNING PREVIEW')
once("a.download='hareworks-woman-accepted-v019-world-pin-v0.1.14.json'", "a.download='hareworks-woman-accepted-v019-world-pin-v0.1.15.json'")
once("schema:'hareworks-woman-accepted-v019-world-pin-v0.1.14'", "schema:'hareworks-woman-accepted-v019-world-pin-v0.1.15'")
p.write_text(s)
# Preserve reset/play/camera controls from v0.1.14; lock new launch identity.
html=target/'index.html';h=html.read_text().replace('v0.1.14','v0.1.15')
h=h.replace('src="./viewer.mjs?build=v0.1.15-geometry-fix"','src="./viewer.mjs?build=v0.1.15-startup-and-preview"')
h=h.replace('src="./viewer.mjs?build=v0.1.15"','src="./viewer.mjs?build=v0.1.15-startup-and-preview"')
html.write_text(h)
rp=target/'review-server.py';r=rp.read_text().replace('v0.1.14','v0.1.15')
a="if not 450<=size<=4000000:raise ValueError('invalid evidence size')"
b="if not 100<=size<=4000000:raise ValueError('invalid evidence size')"
if r.count(a)!=1:raise RuntimeError('EVIDENCE_SIZE_GATE_ANCHOR')
r=r.replace(a,b)
a="if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('wrong artifact or source')"
b="""if d.get('schema')=='hareworks-v0.1.15-startup-diagnostic':
                if d.get('sourceSha256')!=SOURCE or d.get('ownerVisualAcceptance') is not False or d.get('physicalContactVerified') is not False:
                    raise ValueError('diagnostic cannot claim physical contact')
                if d.get('mode')!='PROCEDURAL_PREVIEW_UNPINNED':raise ValueError('wrong diagnostic mode')
                if not isinstance(d.get('error'),str) or len(d['error'])>1000:raise ValueError('invalid diagnostic error')
                out=pathlib.Path(state);out.mkdir(parents=True,exist_ok=True)
                path=out/'startup-diagnostic-v0.1.15.json';path.write_bytes(raw)
                receipt={'state':'UNPINNED_PROCEDURAL_PREVIEW_DIAGNOSTIC_SAVED','sha256':hashlib.sha256(raw).hexdigest(),
                         'path':str(path),'modelSha256':SOURCE,'ownerVisualAcceptance':False,'physicalContactVerified':False}
                b=json.dumps(receipt).encode();self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
            if size<450:raise ValueError('physical audit payload too small')
            if d.get('schema')!=SCHEMA or d.get('sourceSha256')!=SOURCE:raise ValueError('wrong artifact or source')"""
if r.count(a)!=1:raise RuntimeError('EVIDENCE_SCHEMA_GATE_ANCHOR')
r=r.replace(a,b);rp.write_text(r)
contract=target/'contract.json';j=json.loads(contract.read_text());j['schema']='hareworks-woman-accepted-v019-startup-recovery-v0.1.15';j['parent']='7a3690fa99c52f70636fa49be851e521a793838c';j['mutablePaths']=['tools/hareworks-forward-woman/v0.1.15/'];j['ownerVisualAcceptance']=False
j['calibrationErrorBehavior']='accepted v0.1.9 procedural reference preview continues moving but is clearly labeled UNPINNED; exact failure preserved'
j['realSourceMotion']='single generated actor; 32 step real world IK startup smoke or explicit unpinned preview';j['physicalGate']='real 74-joint skinned footwear audit 120Hz x 3 cycles; preview cannot substitute';contract.write_text(json.dumps(j,indent=2)+'\n')
(target/'README.md').write_text("""# Hareworks v0.1.15: startup motion recovery

This is a recovery from v0.1.14, where a calibrated model could be visible but a gait-calibration or first IK-step exception froze it with no movement. The status line was insufficient and the Play button could claim RUNNING despite no controller. The exact error is not known from the owner's report, so this version diagnoses actual runtime failures without asserting a guess.

- Keep the source SHA-256 `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`, original model, original v0.1.9 six-harmonic ankle and knee-pole equations, four-harmonic pelvis, all art, and OrbitControls.
- Build the full-cycle root and contacts from the archived 60 original v0.1.9 source witness frames, not the unstable 360-frame seam. Verify the 60-frame measured fit against the current real GLB before use. This corrects calibration fragility without changing the accepted math.
- Do 32 actual 120-Hz world-IK physics steps BEFORE declaring the physics controller started. Real skinning and real foot anchors must run; any exception records its stage and switches to a separately labeled procedural-motion preview, never a false PHYSICAL PASS.
- The preview contains the accepted source-fitted procedural hip, ankle and knee-pole gait solved through IK, traveling root, one visible actor and orbitable camera. It is **NOT ground pinned** and is not a substitute for the requested physical gait. Source clip mixer runs ONLY on the invisible calibration reference.
- The viewer's explicit status, Play control and saved diagnostic evidence distinguish a moving unpinned preview from a running physical controller. If the underlying reference fit itself fails, report that actual blocker rather than silently claim motion.

Read `AGENTS.md` and Campaign Etiquette first. Termux Git only. Persistent Android Documents checkout, new version path only, no GLB writes, no previous version writes, no force push. Real-device browser/motion success is not claimed by author-side tests. Human visual approval is independent.
""")
print('PATCH_V015_PROCEDURAL_STARTUP_RECOVERY_DONE')
