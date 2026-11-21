/* Hareworks v0.2.2 full 74-bone Walk_Backward to independent in-place pose.
 * Exactly ONE source clip is used for calibration. The generated skeleton has
 * no AnimationMixer, no source clip track playback, and no feminine delta.
 * The original clip is played ONLY on the independent left reference model.
 */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CLIP,ROOT,deriveInPlace,poseInPlace,angleDeg} from './inplace-kernel.mjs';
const MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const MODEL_URL='../../../assets/hareworks/Hareworks-nine-clips.glb';
const SAMPLES=720,SEP=2.7,$=id=>document.getElementById(id),V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const scene=new THREE.Scene();scene.background=new THREE.Color('#101a25');
scene.add(new THREE.HemisphereLight(0xe7f5ff,0x293d4e,2.5));const sun=new THREE.DirectionalLight(0xffffff,3.2);sun.position.set(-4,7,4);scene.add(sun);
const grid=new THREE.GridHelper(14,28,0x5e7486,0x344756);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3.4,3.4,2.2,-2.2,.01,100);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.98,0);
const views={side:[-7,3.2,0],front:[0,2.5,9],oblique:[-5.8,3.8,5],top:[-.01,9,.01]};
function cameraAt(k){camera.position.set(...views[k]);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(290,Math.min(570,Math.round(w*.68)));renderer.setSize(w,h,false);camera.left=-2.2*w/h;camera.right=-camera.left;camera.top=2.2;camera.bottom=-2.2;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const k of Object.keys(views))$(k).onclick=()=>cameraAt(k);cameraAt('side');resize();
let ref=null,gen=null,refRig=null,genRig=null,mixer=null,clip=null,source=null,plan=null,ready=false,sourceReady=false,playing=true,phase=0,last=performance.now(),lastAudit=null,lastSourceZero=null;
const say=s=>$('status').textContent=s;
function bonesOf(root){const d={};root.traverse(o=>{if(o.isBone){if(d[o.name])throw Error('DUPLICATE_BONE_'+o.name);d[o.name]=o}});
 if(Object.keys(d).length!==74||!d[ROOT])throw Error('SOURCE_NOT_74_BONES');return d}
function world(b){return b.getWorldPosition(V())}
function adaptiveSeam(candidateSource){
 const candidates=[];let selected=null;
 // Try the shortest repair first. Extend it only when the full skeleton
 // fails the real 30/60/120 Hz continuity thresholds.
 for(const start of [.93,.92,.905,.89,.875,.86]){
  let candidate;
  try{candidate=deriveInPlace(candidateSource,start)}catch(e){candidates.push({start,blocked:e.message});continue}
  const rates=[];
  for(const rate of [30,60,120]){
   let lastPose=poseInPlace(candidateSource,candidate,0).bones,max=0,worst='';
   for(let i=1;i<=Math.ceil(clip.duration*rate);i++){
    const q=Math.min(1-1e-8,i/(clip.duration*rate)),current=poseInPlace(candidateSource,candidate,q).bones;
    for(const bone of Object.keys(current)){
     const step=angleDeg(lastPose[bone].quaternion,current[bone].quaternion);
     if(step>max){max=step;worst=bone}
    }
    lastPose=current;
   }
   rates.push({rateHz:rate,maxStepDeg:max,limitDeg:rate===30?20:rate===60?12:7,worstBone:worst});
  }
  const pass=rates.every(x=>x.maxStepDeg<=x.limitDeg);
  const c={start,rates,pass,score:rates.reduce((x,y)=>x+y.maxStepDeg/y.limitDeg,0)};
  candidates.push(c);
  if(pass){selected=candidate;break}
 }
 if(!selected){
  const ranked=candidates.filter(x=>x.rates).sort((a,b)=>a.score-b.score);
  if(!ranked.length)throw Error('NO_ADAPTIVE_SEAM_SOURCE_OPTION '+JSON.stringify(candidates));
  selected=deriveInPlace(candidateSource,ranked[0].start);
 }
 selected.selectionCandidates=candidates;
 selected.selectionPass=candidates.some(x=>x.pass);
 return selected;
}
function generatedAt(p){const m=poseInPlace(source,plan,p);
 for(const [name,s] of Object.entries(m.bones)){
  const b=genRig[name];if(!b)throw Error('GENERATED_BONE_MISSING_'+name);
  b.quaternion.fromArray(s.quaternion).normalize();b.position.fromArray(s.position);b.scale.fromArray(s.scale);
 }
 gen.updateMatrixWorld(true);return m;
}
// Every bone must agree at phase zero. A stopped-calibration rest pose is
// NEVER allowed to masquerade as the first procedural animation frame.
function checkSourceTimeZero(){
  referenceAt(0);generatedAt(0);
  let worstRotation={bone:null,error:0},worstLocalPosition={bone:null,error:0},
      worstScale={bone:null,error:0},worstWorldPosition={bone:null,error:0};
  for(const name of Object.keys(refRig)){
    const a=refRig[name],b=genRig[name];
    const rot=angleDeg(a.quaternion.toArray(),b.quaternion.toArray());
    const pos=a.position.distanceTo(b.position),scale=a.scale.distanceTo(b.scale);
    const w=world(a).add(V(0,0,SEP)).distanceTo(world(b));
    for(const [field,value] of [['worstRotation',rot],['worstLocalPosition',pos],['worstScale',scale],['worstWorldPosition',w]]){
      const entry=({worstRotation,worstLocalPosition,worstScale,worstWorldPosition})[field];
      if(value>entry.error){entry.error=value;entry.bone=name}
    }
  }
  const pass=worstRotation.error<.001&&worstLocalPosition.error<1e-6&&worstScale.error<1e-6&&worstWorldPosition.error<1e-4;
  const result={pass,jointCount:Object.keys(refRig).length,worstRotation,worstLocalPosition,worstScale,worstWorldPosition};
  if(!pass)throw Error('SOURCE_T0_POSE_MISMATCH '+JSON.stringify(result));
  return result;
}
function referenceAt(p){const q=((p%1)+1)%1;mixer.setTime(q*clip.duration);ref.updateMatrixWorld(true);
 const b=refRig[ROOT];b.position.x-=plan.cycleTravel[0]*q;b.position.z-=plan.cycleTravel[2]*q;ref.updateMatrixWorld(true);
}
function sourceTerminalRootTrack(){
 const track=clip.tracks.find(t=>t.name===ROOT+'.position');
 if(!track||track.times.length<2)return null;
 const size=track.getValueSize(),k=track.times.length;
 if(size!==3)return null;
 return {lastTime:Number(track.times[k-1]),previousTime:Number(track.times[k-2]),
   lastPosition:Array.from(track.values.slice((k-1)*size,k*size)),
   previousPosition:Array.from(track.values.slice((k-2)*size,(k-1)*size))};
}
function sampleAt(p){if(!ready)return;
 try { referenceAt(p);generatedAt(p);phase=((p%1)+1)%1;$('phaseValue').textContent=Math.round(phase*100)+'% · terminal seam starts '+Math.round(plan.seamStart*100)+'%'; }
 catch(e){playing=false;say('SOURCE_OR_GENERATED_POSE_ERROR '+e.message);console.error(e)}
}
function collect(stats,bone,kind,x,rate,t){if(!Number.isFinite(x))throw Error('NONFINITE_METRIC '+bone+' '+kind);const key=bone+':'+kind;
 const a=stats[key]??={bone,measurement:kind,count:0,sum:0,max:0,worst:{timeSeconds:0,rateHz:rate}};
 a.count++;a.sum+=x*x;if(x>a.max){a.max=x;a.worst={timeSeconds:t,rateHz:rate}};
}
function audit(exportIt=false){if(!ready)return;const playingWas=playing,phaseWas=phase;playing=false;const stats={},countByRate=[],errors=[];let maxRootX=0,maxRootZ=0;
 try{
  for(const rate of [30,60,120]){
   let count=0;
   for(let i=0;i<Math.ceil(clip.duration*rate*2);i++){
    const t=i/(rate*2),q=t/clip.duration;
    if(q>=plan.seamStart||q>=1)break;
    try {
     referenceAt(q);const m=generatedAt(q);
     for(const name of Object.keys(source.bones)){
      const a=refRig[name],b=genRig[name];
      collect(stats,name,'localRotationDegrees',angleDeg(a.quaternion.toArray(),b.quaternion.toArray()),rate,t);
      collect(stats,name,'localPositionUnits',a.position.distanceTo(b.position),rate,t);
      collect(stats,name,'localScaleUnits',a.scale.distanceTo(b.scale),rate,t);
      const aw=world(a).add(V(0,0,SEP)),bw=world(b);collect(stats,name,'worldPositionUnits',aw.distanceTo(bw),rate,t);
     }
     maxRootX=Math.max(maxRootX,Math.abs(m.bones[ROOT].position[0]-source.bones[ROOT].pos[0][0]));
     maxRootZ=Math.max(maxRootZ,Math.abs(m.bones[ROOT].position[2]-source.bones[ROOT].pos[0][2]));
     count++;
    }catch(e){errors.push({rate,t,message:e.message})}
   }
   countByRate.push({rateHz:rate,completedFramesAndHalfFrames:count});
  }
  const table=Object.values(stats).map(s=>({bone:s.bone,measurement:s.measurement,samples:s.count,rms:Math.sqrt(s.sum/s.count),max:s.max,worst:s.worst}));
  table.sort((a,b)=>b.rms-a.rms);
  const limits={localRotationDegrees:{rms:1,max:2},localPositionUnits:{rms:.006,max:.012},localScaleUnits:{rms:.0005,max:.001},worldPositionUnits:{rms:.008,max:.018}};
  const violations=table.filter(x=>x.rms>limits[x.measurement].rms||x.max>limits[x.measurement].max);
  // The last part of this source clip contains a baked teleport. Parity
  // there is meaningless; instead test C0/C1 periodic seam and joint steps.
  const before=poseInPlace(source,plan,1-1e-7).bones,after=poseInPlace(source,plan,0).bones;
  let seamMaxDegrees=0,seamMaxPosition=0,seamWorst='',maxStep30=0,maxStep60=0,maxStep120=0;
  for(const bone of Object.keys(before)){
   const d=angleDeg(before[bone].quaternion,after[bone].quaternion);
   const dp=Math.hypot(...before[bone].position.map((v,j)=>v-after[bone].position[j]));
   if(d>seamMaxDegrees){seamMaxDegrees=d;seamWorst=bone}seamMaxPosition=Math.max(seamMaxPosition,dp);
  }
  const steps=[];
  for(const rate of [30,60,120]){
   let max=0,worst='';let prior=poseInPlace(source,plan,0).bones;
   for(let i=1;i<=Math.ceil(clip.duration*rate);i++){
    const p=Math.min(1-1e-8,i/(rate*clip.duration)),current=poseInPlace(source,plan,p).bones;
    for(const bone of Object.keys(current)){const a=angleDeg(prior[bone].quaternion,current[bone].quaternion);
     if(a>max){max=a;worst=bone}}
    prior=current;
   }
   steps.push({rateHz:rate,maxLocalJointStepDeg:max,worstBone:worst,limitDeg:rate===30?20:rate===60?12:7});
  }
  const seamPass=seamMaxDegrees<.015&&seamMaxPosition<.0001&&plan.selectionPass;
  const stepsPass=steps.every(s=>s.maxLocalJointStepDeg<=s.limitDeg);
  const sufficient=countByRate.every(c=>c.completedFramesAndHalfFrames>=Math.floor(clip.duration*c.rateHz*2*plan.seamStart)-2);
  const unmappedTracks=clip.tracks.filter(tr=>!refRig[tr.name.split('.')[0]]).map(tr=>tr.name);
  const parityPass=violations.length===0&&errors.length===0&&table.length===296&&sufficient&&unmappedTracks.length===0;
  const report={schema:'hareworks-full-rig-backward-inplace-v0.2.2',adaptiveSeamSelection:{pass:plan.selectionPass,trials:plan.selectionCandidates},sourceClip:CLIP,modelSha256:MODEL_SHA,sourceDuration:clip.duration,samplesPerCycle:SAMPLES,
   sourceJointCount:74,sourceZeroPose:lastSourceZero,generatedAnimationMixerCount:0,styleTransferBoneCount:0,referenceMode:'raw source played on reference only, horizontal root cycle detrended',
   generatedMode:'per-joint independent source-calibrated continuous quaternion, translation and scale equations',
   inPlace:{cycleHorizontalTravelRemoved:plan.cycleTravel,rootDisplacementMagnitude:plan.cycleTravelMagnitude,rawResetOnsetPhase:plan.cleanPhase,rawResetSample:plan.resetIndex,rawResetJump:plan.resetRootStep,resetEvidence:plan.resetEvidence,terminalRootTrack:plan.terminalRootTrack,terminalSeamStart:plan.seamStart,changedSourceWindowFraction:1-plan.seamStart,maxRemainingRootX:maxRootX,maxRemainingRootZ:maxRootZ},
   sourceCoverage:{clipTracks:clip.tracks.length,calibratedBones:Object.keys(source.bones).length,unmappedTracks},
   comparisonPhaseRange:[0,plan.seamStart],rates:countByRate,thresholds:limits,perJointMetrics:table,parityViolations:violations.slice(0,100),parityViolationCount:violations.length,poseErrors:errors.slice(0,40),poseErrorCount:errors.length,
   seam:{maxRotationDegrees:seamMaxDegrees,worstBone:seamWorst,maxPositionUnits:seamMaxPosition,pass:seamPass},jointContinuity:steps,sourceEndpointResetExcludedFromParity:true,
   verdict:parityPass&&seamPass&&stepsPass?'MEASURED_SOURCE_PARITY_WITHIN_TOLERANCE_OWNER_REVIEW_PENDING':'REJECTED_FULL_RIG_PARITY_OR_SEAM',ownerAccepted:false};
  lastAudit=report;
  $('audit').textContent=`${report.verdict}\nSource: ${clip.name} · ${clip.duration.toFixed(6)}s · ALL 74 bones · ${SAMPLES} calibration poses\nOriginal Z travel ${plan.cycleTravel[2].toFixed(4)} units removed; reset at ${(plan.cleanPhase*100).toFixed(2)}% · seam repair ${(100*plan.seamStart).toFixed(1)}–100%\nFull-rig source parity: ${countByRate.map(x=>x.rateHz+'Hz '+x.completedFramesAndHalfFrames+' poses').join(' / ')}\nViolations ${violations.length}, pose errors ${errors.length}; ${violations.slice(0,5).map(x=>x.bone+' '+x.measurement+' RMS '+x.rms.toFixed(4)).join(' | ')||'none'}\nCycle seam ${seamMaxDegrees.toFixed(4)}° at ${seamWorst}; max joint steps ${steps.map(x=>x.rateHz+'Hz '+x.maxLocalJointStepDeg.toFixed(2)+'° '+x.worstBone).join(' / ')}\nTerminal-key reset is excluded from generated gait; endpoint-only reset permitted. Export for every joint and timestamp.`;
  say(report.verdict==='MEASURED_SOURCE_PARITY_WITHIN_TOLERANCE_OWNER_REVIEW_PENDING'?'FULL-RIG SOURCE MATCH MEASURED · OWNER VISUAL APPROVAL PENDING':'REFERENCE PARITY WARNINGS · inspect exported offending joints; viewer remains available');
  if(exportIt)download(report);
 }catch(e){say('AUDIT_EXCEPTION '+e.message);console.error(e)}finally{sampleAt(phaseWas);playing=playingWas}
}
function download(obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-backward-inplace-v0.2.2-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),4500)}
$('auditButton').onclick=()=>audit(true);$('export').onclick=()=>lastAudit?download(lastAudit):say('Run the source-parity audit first');
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';if(ready)sampleAt(Number($('phase').value)/1000);else if(sourceReady){phase=Number($('phase').value)/1000;mixer.setTime(phase*clip.duration);ref.updateMatrixWorld(true)}};
function render(now){requestAnimationFrame(render);const delta=Math.min(.070,Math.max(0,(now-last)/1000));last=now;
 if(sourceReady&&playing){if(ready)sampleAt((phase+delta/clip.duration)%1);else{phase=(phase+delta/clip.duration)%1;mixer.setTime(phase*clip.duration);ref.updateMatrixWorld(true);$('phaseValue').textContent=Math.round(phase*100)+'% · reference only (procedural calibration blocked)'}$('phase').value=Math.round(phase*1000)}
 orbit.update();renderer.render(scene,camera)}requestAnimationFrame(render);
function showError(e){say('SOURCE_OR_RIG_ERROR '+(e?.message||String(e)));console.error(e)}
window.addEventListener('error',e=>showError(e.error||e.message));window.addEventListener('unhandledrejection',e=>showError(e.reason));
try{
 const response=await fetch(MODEL_URL,{cache:'no-store'});if(!response.ok)throw Error('SOURCE_GLTF_HTTP_'+response.status);
 const buffer=await response.arrayBuffer();if(buffer.byteLength!==6784896)throw Error('SOURCE_GLB_BYTES_'+buffer.byteLength);
 if(!crypto?.subtle)throw Error('SHA256_BROWSER_WEBCRYPTO_UNAVAILABLE');
 const hex=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(hex!==MODEL_SHA)throw Error('SOURCE_GLB_SHA256_MISMATCH '+hex);
 const gltf=await new GLTFLoader().parseAsync(buffer,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('SOURCE_NINE_CLIPS_EXPECTED');
 clip=gltf.animations.find(a=>a.name===CLIP);if(!clip||clip.duration<.8||clip.duration>.96)throw Error('EXPECTED_WALK_BACKWARD_SOURCE_CLIP');
 ref=cloneSkeleton(gltf.scene);gen=cloneSkeleton(gltf.scene);refRig=bonesOf(ref);genRig=bonesOf(gen);
 scene.add(ref,gen);ref.position.z=-SEP/2;gen.position.z=SEP/2;
 mixer=new THREE.AnimationMixer(ref);mixer.clipAction(clip).reset().play();mixer.setTime(0);ref.updateMatrixWorld(true);
 sourceReady=true;gen.visible=false; // Do not display the uninitialized bind pose as a gait.
 $('identity').textContent=`v0.2.2 · model ${MODEL_SHA} · clip ${CLIP} · source loaded · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · script SHA ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 source={sampleCount:SAMPLES,duration:clip.duration,bones:{}};
 for(const name of Object.keys(refRig))source.bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<SAMPLES;i++){
  mixer.setTime(clip.duration*i/SAMPLES);ref.updateMatrixWorld(true);
  for(const [name,b] of Object.entries(refRig)){
   const s=source.bones[name];s.pos.push(b.position.toArray());s.quat.push(b.quaternion.toArray());s.scale.push(b.scale.toArray());
  }
 }
 mixer.setTime(0);ref.updateMatrixWorld(true);
 source.terminalRootTrack=sourceTerminalRootTrack();
 plan=adaptiveSeam(source);
 const unmapped=clip.tracks.filter(tr=>!refRig[tr.name.split('.')[0]]);
 if(unmapped.length)console.warn('SOURCE_NON_BONE_TRACKS_UNREPRESENTED',unmapped.map(x=>x.name));
 grid.position.y=new THREE.Box3().setFromObject(ref).min.y;
 lastSourceZero=checkSourceTimeZero();
 gen.visible=true;ready=true;sampleAt(0);resize();cameraAt('side');
 $('identity').textContent=`v0.2.2 · exact GLB ${MODEL_SHA} · source ${CLIP} · 74/74 procedural joint curves · 720 calibrations · no style transfer · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · script SHA ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 $('audit').textContent=`Real backwards source loaded. Hip travel ${(plan.cycleTravel[2]).toFixed(4)} units; reset evidence ${plan.resetEvidence}, clean phase ${(plan.cleanPhase*100).toFixed(2)}%; source-t0 ${lastSourceZero.jointCount}/74 exact joints. Measuring all 74 joints…`;
 say('SOURCE T0=GENERATED T0 VERIFIED (74 JOINTS) · procedural in-place gait playing · measuring parity');
 audit(false);
}catch(e){if(sourceReady&&!ready){if(gen)gen.visible=false; $('audit').textContent='BLOCKED_GENERATED_CALIBRATION · original backward reference remains playable; '+(e.message||String(e)); showError(new Error('PROCEDURAL_STARTUP_BLOCKED · original reference remains playable. See audit.'));}else showError(e)}
