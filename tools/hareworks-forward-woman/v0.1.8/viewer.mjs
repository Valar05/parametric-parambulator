/* v0.1.6: preserve v0.1.3 leg/foot/pelvis posing byte-for-byte at the
 * procedural stage. Replace only generated character's clip-driven upper
 * body with a smooth, periodic, phase-fitted rotation-vector controller.
 * Reference remains original Walking_Woman. No root travel, lateral gait,
 * physical sole contact or independently travelling procedural walk claimed. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {independentPose,validateProfile,angleDiff} from '../v0.1.2/pose-kernel.mjs';
import {legAt,rotateY,kneeFromTarget,validateFootProfile} from '../v0.1.3/foot-kernel.mjs';
import {quatMultiply,quatConjugate,quatLog,quatExp,fitVectorSeries,evalVectorSeries,quatAngle} from '../v0.1.5/upper-kernel.mjs';
import {createAudit, observe, finalizeAudit, rankOffenders} from './parity-math.mjs';
import {checkedPreset,presetSeparation,compareBonePose} from './parity-presets.mjs';
import {fitSourceAnchoredTrack,evalSourceAnchoredTrack} from './upper-anchor.mjs';

const $=id=>document.getElementById(id);
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const Q=()=>new THREE.Quaternion();
const YA=V(0,1,0);
const SEP=2.75, FPS=30, SOURCE='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const provenance=new URLSearchParams(location.search);
const receiptModelSha=provenance.get('modelSha');
if(receiptModelSha&&receiptModelSha!==SOURCE)throw Error('VIEWER_MODEL_RECEIPT_IDENTITY_MISMATCH');
$('buildIdentity').textContent='Build '+(provenance.get('build')||'not in URL')+' | Script SHA256 '+(provenance.get('scriptSha')||'not in URL')+' | GLB SHA256 '+SOURCE+' | Walking_Woman | generated source-anchored upper body';
const names={
 left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],
 right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']
};
const world=o=>o.getWorldPosition(V());
const wq=o=>o.getWorldQuaternion(Q());
const forwardYaw=q=>{const f=V(0,0,1).applyQuaternion(q);return Math.atan2(f.x,f.z)};
const rad=x=>THREE.MathUtils.radToDeg(x);
function rigOf(scene){
 const bones=new Map();scene.traverse(o=>{if(o.isBone){if(bones.has(o.name))throw Error('DUPLICATE_BONE_'+o.name);bones.set(o.name,o)}});
 if(bones.size!==74)throw Error('RIG_JOINT_COUNT_'+bones.size);
 const hips=bones.get('mixamorigHips'),spine=bones.get('mixamorigSpine');if(!hips||!spine)throw Error('HIPS_OR_SPINE_MISSING');
 const legs={};for(const [side,cn] of Object.entries(names)){
  const chain=cn.map(name=>{const b=bones.get(name);if(!b)throw Error('MISSING_BONE_'+name);return b});
  if(chain[0].parent!==hips||chain.some((b,i)=>i&&b.parent!==chain[i-1]))throw Error('LEG_HIERARCHY_'+side);
  legs[side]={chain,up:chain[0],knee:chain[1],ankle:chain[3],toe:chain[4]};
 }
 return {hips,spine,legs,bones};
}
function pose(b){return {position:b.position.clone(),quaternion:b.quaternion.clone(),scale:b.scale.clone()}}
function restore(b,p){b.position.copy(p.position);b.quaternion.copy(p.quaternion);b.scale.copy(p.scale)}
function setWorldBoneRotation(b,desired){const parent=wq(b.parent).invert();b.quaternion.copy(parent.multiply(desired)).normalize()}
function turnBoneToward(b,from,to){
 const a=from.clone().sub(world(b)),z=to.clone().sub(world(b));
 if(a.lengthSq()<1e-10||z.lengthSq()<1e-10)throw Error('ZERO_LENGTH_BONE_SOLVE');
 const delta=Q().setFromUnitVectors(a.normalize(),z.normalize());
 setWorldBoneRotation(b,delta.multiply(wq(b)));
}
// Atomic deterministic posing: a failed frame must never leave half a leg updated.
function takePose() {
 const state=[];
 generated.traverse(o=>{if(o.isBone)state.push([o,pose(o)])});
 return state;
}
function restorePose(state){for(const [bone,p] of state)restore(bone,p);generated.updateMatrixWorld(true)}
function snapshotRecord(state){return state.map(([bone,p])=>({name:bone.name,position:p.position.toArray(),quaternion:p.quaternion.toArray(),scale:p.scale.toArray()}));}
function currentRecord(state){return state.map(([bone])=>({name:bone.name,position:bone.position.toArray(),quaternion:bone.quaternion.toArray(),scale:bone.scale.toArray()}));}
function rollbackDiagnosis(state){return compareBonePose(snapshotRecord(state),currentRecord(state));}
function poseMatches(state){return rollbackDiagnosis(state).pass;}
// Stable analytical foot orientation, no frame-history-dependent Newton solver.
// Align the toe vector then resolve the projected heading as a single twist.
function setFootProcedural(leg, desiredToeVector, desiredYaw) {
 const from=world(leg.toe).sub(world(leg.ankle));
 const to=V(...desiredToeVector);
 if(from.lengthSq()<1e-9||to.lengthSq()<1e-9)throw Error('ZERO_FOOT_VECTOR');
 const axis=to.normalize();
 const base=Q().setFromUnitVectors(from.normalize(),axis).multiply(wq(leg.ankle));
 const forward=V(0,0,1).applyQuaternion(base);
 const desired=V(Math.sin(desiredYaw),0,Math.cos(desiredYaw));
 const fp=forward.addScaledVector(axis,-forward.dot(axis));
 const dp=desired.addScaledVector(axis,-desired.dot(axis));
 if(fp.lengthSq()<1e-7||dp.lengthSq()<1e-7)throw Error('FOOT_HEADING_SINGULAR');
 fp.normalize();dp.normalize();
 const twist=Math.atan2(axis.dot(fp.clone().cross(dp)),fp.dot(dp));
 const solved=Q().setFromAxisAngle(axis,twist).multiply(base).normalize();
 setWorldBoneRotation(leg.ankle,solved);
}

const scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
scene.add(new THREE.HemisphereLight(0xe2eeff,0x323d45,2.6));
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(-4,7,3);scene.add(light);
const floor=new THREE.GridHelper(10,20,0x728390,0x3e4f5e);scene.add(floor);
const camera=new THREE.OrthographicCamera(-4,4,2,-2,.05,100);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
$('stage').append(renderer.domElement);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.dampingFactor=.1;orbit.enablePan=false;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.9,0);
const presets={side:[-7,3.4,0],front:[0,2.3,9],top:[-.01,9,.01],oblique:[-6,4.5,5]};
function cameraPreset(k){camera.position.set(...presets[k]);orbit.target.set(0,.9,0);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=$('stage').clientWidth,h=Math.max(300,Math.min(590,Math.round(w*.69)));renderer.setSize(w,h,false);camera.left=-2.25*w/h;camera.right=-camera.left;camera.top=2.25;camera.bottom=-2.25;camera.updateProjectionMatrix();orbit.update()}
window.addEventListener('resize',resize);
for(const k of ['side','front','top','oblique'])$(k).onclick=()=>cameraPreset(k);
$('resetCamera').onclick=()=>cameraPreset('side');
cameraPreset('side');resize();
let reference,generated,refRig,genRig,refMixer,clip,profile,footProfile,seed,upperProfile,upperAudit;
let running=false,playing=false,frame=0,last=performance.now(),elapsed=0,cycleT=0,markersVisible=false,markers=[],lastReport=null;
let nFrames=29,lastParityReport=null;
function addMarkers(rig,cols){for(const side of ['left','right']){
 for(const part of ['ankle','knee']){
 const mat=new THREE.MeshBasicMaterial({color:cols[side],depthTest:false});
 const ball=new THREE.Mesh(new THREE.SphereGeometry(part==='ankle'?.03:.023,10,8),mat);ball.renderOrder=40;scene.add(ball);markers.push({ball,node:rig.legs[side][part]});
 }}}
function showMarkers(){for(const m of markers){m.ball.position.copy(world(m.node));m.ball.visible=markersVisible}}
function excludedTrackNames(root){
 const forbidden=new Set();for(const leg of Object.values(genRig.legs))for(const b of leg.chain)forbidden.add(b.name);
 let parent=genRig.hips;while(parent){if(parent.name)forbidden.add(parent.name);parent=parent.parent}
 const allowed=new Set();genRig.spine.traverse(o=>{if(o.isBone)allowed.add(o.name)});
 return {forbidden,allowed};
}
// Source upper-body tracks are sampled ONCE as fitting evidence. Their
// keyframes never run on the generated character during playback. They are
// reconstructed by short periodic local rotation-vector functions.
// Sample the source once for fitting; the generated upper body never plays
// source tracks. Crucially, capture q(0) from the SOURCE, not a stopped mixer.
function buildUpperProfile(boneNames,sampleCount=120,maxHarmonics=12){
 refMixer.setTime(0);reference.updateMatrixWorld(true);
 const bones=boneNames.map(name=>{
  const r=refRig.bones.get(name),g=genRig.bones.get(name);
  if(!r||!g||!g.isBone||!r.isBone)throw Error('UPPER_BONE_MISSING_'+name);
  return {name,reference:r,generated:g,scaleSeed:r.scale.clone(),samples:[]};
 });
 for(let i=0;i<sampleCount;i++){
  refMixer.setTime(clip.duration*i/sampleCount);reference.updateMatrixWorld(true);
  for(const b of bones)b.samples.push({quaternion:b.reference.quaternion.toArray(),position:b.reference.position.toArray()});
 }
 refMixer.setTime(0);reference.updateMatrixWorld(true);
 return bones.map(b=>({name:b.name,bone:b.generated,scaleSeed:b.scaleSeed,
   fit:fitSourceAnchoredTrack(b.samples,maxHarmonics)}));
}
function applyUpperBody(t,explicitPreset=null){
 const chosen=checkedPreset(explicitPreset ?? {strength:Number($('upperStrength').value),harmonics:Number($('upperHarmonics').value)});
 const q=t/clip.duration;
 for(const item of upperProfile){
  const solved=evalSourceAnchoredTrack(item.fit,q,chosen.harmonics,chosen.strength);
  item.bone.quaternion.fromArray(solved.quaternion).normalize();
  item.bone.position.fromArray(solved.position);
  item.bone.scale.copy(item.scaleSeed);
 }
}
// Check the ACTUAL reference and generated local rotations at source time zero.
// This is a non-negotiable gate even if other parity metrics are poor.
function sourceZeroAudit(){
 const m=evaluateTime(0,null,{strength:1,harmonics:12});
 if(!m)throw Error('SOURCE_ZERO_NOT_POSED');
 let maxLocalDegrees=0,maxLocalTranslation=0,maxWorldJointDistance=0,offender=null;
 for(const item of upperProfile){
  const r=refRig.bones.get(item.name),g=item.bone;
  const degrees=rad(r.quaternion.angleTo(g.quaternion));
  const local=r.position.distanceTo(g.position);
  const worldDist=world(r).add(V(0,0,SEP)).distanceTo(world(g));
  if(degrees>maxLocalDegrees){maxLocalDegrees=degrees;offender=item.name;}
  maxLocalTranslation=Math.max(maxLocalTranslation,local);maxWorldJointDistance=Math.max(maxWorldJointDistance,worldDist);
 }
 const pass=maxLocalDegrees<.001&&maxLocalTranslation<1e-6&&maxWorldJointDistance<.0001;
 const result={pass,jointCount:upperProfile.length,maxLocalDegrees,maxLocalTranslation,maxWorldJointDistance,offender};
 if(!pass)throw Error('SOURCE_T0_ANCHOR_FAILURE '+JSON.stringify(result));
 return result;
}
function upperFrameSnapshot(){
 const out={};for(const item of upperProfile)out[item.name]=item.bone.quaternion.toArray();
 return out;
}
function upperStepAudit(rate){
 const n=Math.floor((clip.duration-1e-4)*rate)+1;
 let before=null,maxStep=0,offender=null;const perBone={};
 for(let i=0;i<=n;i++){
  const t=i===n?0:i/rate;
  applyUpperBody(t);const sample=upperFrameSnapshot();
  if(before)for(const name of Object.keys(sample)){
   const deg=THREE.MathUtils.radToDeg(quatAngle(before[name],sample[name]));
   perBone[name]=Math.max(perBone[name]||0,deg);
   if(deg>maxStep){maxStep=deg;offender=name}
  }
  before=sample;
 }
 const offenders=Object.entries(perBone).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([name,maxStepDeg])=>({name,maxStepDeg}));
 return {rateHz:rate,samples:n,maxStepDeg:maxStep,worstBone:offender,topTen:offenders};
}
function applyGeneratedPose(t,fault=null,explicitPreset=null){
 const sourceTime=Math.min(t,clip.duration-1e-6);
 const prediction=independentPose(profile,sourceTime);
 applyUpperBody(sourceTime,explicitPreset);
 for(const [b,p] of seed.legPose)restore(b,p);
 restore(genRig.hips,seed.hip);
 // The pelvis offset is in measured world units, transformed into the local
 // space of the hips parent. No source clip hip tracks run on generated.
 const delta=V(...prediction.pelvis).sub(V(...profile.zeroPelvis));
 const parent=genRig.hips.parent;generated.updateMatrixWorld(true);
 const localDelta=delta.applyQuaternion(wq(parent).invert());
 const parentScale=parent.getWorldScale(V());localDelta.set(localDelta.x/parentScale.x,localDelta.y/parentScale.y,localDelta.z/parentScale.z);
 genRig.hips.position.copy(seed.hip.position).add(localDelta);
 const dyaw=angleDiff(prediction.pelvisYaw,profile.zeroPelvisYaw);
 const parentQ=wq(parent),localYaw=parentQ.clone().invert().multiply(Q().setFromAxisAngle(YA,dyaw)).multiply(parentQ);
 genRig.hips.quaternion.copy(localYaw.multiply(seed.hip.quaternion)).normalize();
 generated.updateMatrixWorld(true);
 const pelvisYaw=forwardYaw(wq(genRig.hips));
 const rows=[];
 for(const side of ['left','right']){
  const leg=genRig.legs[side],f=legAt(footProfile,side,sourceTime),cfg=footProfile[side];
  const H=world(leg.up),vec=V(...rotateY(f.ankleLocal,pelvisYaw));
  const A=H.clone().add(vec);
  if(fault==='unreachable'&&side==='right')A.y+=2.0;
  const l1=world(leg.up).distanceTo(world(leg.knee));
  const l2=world(leg.knee).distanceTo(world(leg.ankle));
  if(Math.abs(l1-cfg.upperLength)>.009||Math.abs(l2-cfg.lowerLength)>.009)throw Error('LINK_LENGTH_MISMATCH_'+side);
  const K=V(...kneeFromTarget(H.toArray(),A.toArray(),l1,l2,rotateY(f.poleLocal,pelvisYaw)));
  turnBoneToward(leg.up,world(leg.knee),K);generated.updateMatrixWorld(true);
  turnBoneToward(leg.knee,world(leg.ankle),A);generated.updateMatrixWorld(true);
  const target=prediction.feet[side];
  setFootProcedural(leg,target.toeVector,target.ankleYaw);generated.updateMatrixWorld(true);
  const actualAnkle=world(leg.ankle),actualKnee=world(leg.knee),actualToe=world(leg.toe);
  const toeVector=actualToe.clone().sub(actualAnkle);
  const r={side,relativeForward:f.ankleLocal[2],reachMargin:(l1+l2)-H.distanceTo(A),hip:world(leg.up).toArray(),knee:actualKnee.toArray(),ankle:actualAnkle.toArray(),toe:actualToe.toArray(),
   ikResidual:actualAnkle.distanceTo(A),toeVectorDifferenceToCurve:toeVector.distanceTo(V(...target.toeVector)),
   ankleYawDifferenceToCurveDeg:rad(angleDiff(forwardYaw(wq(leg.ankle)),target.ankleYaw))};
  if(![r.ikResidual,r.toeVectorDifferenceToCurve,r.ankleYawDifferenceToCurveDeg,...r.hip,...r.knee,...r.ankle,...r.toe].every(Number.isFinite))throw Error('NONFINITE_GENERATED_POSE');
  if(r.ikResidual>.008)throw Error('IK_TARGET_RESIDUAL '+side+' '+r.ikResidual.toFixed(6));
  rows.push(r);
 }
 return {t:sourceTime,profilePhase:prediction.q,pelvis:world(genRig.hips).toArray(),pelvisYaw:pelvisYaw,legs:rows};
}
function evaluateTime(t, fault=null,explicitPreset=null){
 if(!running)return null;
 t=Math.max(0,Math.min(t,clip.duration-1e-6));
 const before=takePose();
 try {
 refMixer.setTime(t);reference.updateMatrixWorld(true);
 const generatedPose=applyGeneratedPose(t,fault,explicitPreset);
 const refPelvis=world(refRig.hips).add(V(0,0,SEP));
 const metrics={frame:Math.min(nFrames-1,Math.round(t*FPS)),t,hipDiff:world(genRig.hips).distanceTo(refPelvis),pelvisYawDiffDeg:rad(angleDiff(generatedPose.pelvisYaw,forwardYaw(wq(refRig.hips)))),legs:{}};
 for(const s of ['left','right']){
  const gen=genRig.legs[s],ref=refRig.legs[s],r=generatedPose.legs.find(x=>x.side===s);
  const refKnee=world(ref.knee).add(V(0,0,SEP)),refAnkle=world(ref.ankle).add(V(0,0,SEP)),refToe=world(ref.toe).add(V(0,0,SEP));
  metrics.legs[s]={forward:r.relativeForward,reachMargin:r.reachMargin,kneeDiff:world(gen.knee).distanceTo(refKnee),ankleDiff:world(gen.ankle).distanceTo(refAnkle),toeDiff:world(gen.toe).distanceTo(refToe),ikResidual:r.ikResidual,
   ankleYawDifferenceToReferenceDeg:rad(angleDiff(forwardYaw(wq(gen.ankle)),forwardYaw(wq(ref.ankle)))),
   toeVectorCurveResidual:r.toeVectorDifferenceToCurve,ankleYawCurveResidualDeg:r.ankleYawDifferenceToCurveDeg,
   upperQuat:gen.up.quaternion.toArray(),lowerQuat:gen.knee.quaternion.toArray(),footQuat:gen.ankle.quaternion.toArray()};
 }
 showMarkers();return metrics;
 }catch(e){restorePose(before);const restored=rollbackDiagnosis(before);if(!restored.pass)throw Error('ATOMIC_ROLLBACK_FAILED '+JSON.stringify(restored)+' ORIGINAL '+e.message);throw e;}
}
function evaluate(f){return evaluateTime(f/FPS)}
function display(m){if(!m)return;
 $('frame').value=m.frame;$('frameNumber').textContent=`${m.frame}/${nFrames-1} (${m.t.toFixed(3)}s)`;
 $('metrics').textContent=`v0.1.8 source-anchored upper: periodic ${$('upperHarmonics').value}-harmonic fit / ${$('upperStrength').value} amplitude, NO upper clip playback\nFrame ${m.frame}/${nFrames-1}, time ${m.t.toFixed(3)}s\nGenerated hips Δ ${m.hipDiff.toFixed(4)} units / yaw Δ ${m.pelvisYawDiffDeg.toFixed(2)}°\nLEFT   forward ${m.legs.left.forward.toFixed(3)}   ankle Δ ${m.legs.left.ankleDiff.toFixed(3)}  knee Δ ${m.legs.left.kneeDiff.toFixed(3)}  toe Δ ${m.legs.left.toeDiff.toFixed(3)}\nRIGHT  forward ${m.legs.right.forward.toFixed(3)}   ankle Δ ${m.legs.right.ankleDiff.toFixed(3)}  knee Δ ${m.legs.right.kneeDiff.toFixed(3)}  toe Δ ${m.legs.right.toeDiff.toFixed(3)}\nFoot yaw reference Δ ${m.legs.left.ankleYawDifferenceToReferenceDeg.toFixed(1)}° / ${m.legs.right.ankleYawDifferenceToReferenceDeg.toFixed(1)}°\nAnkle IK residual ${m.legs.left.ikResidual.toFixed(5)} / ${m.legs.right.ikResidual.toFixed(5)}`;
}
function sampleTime(t){try{const m=evaluateTime(t);frame=Math.floor(t*FPS)%nFrames;display(m)}catch(e){playing=false;$('status').textContent='BLOCKED_REAL_RIG '+e.message;console.error(e)}}
function sampleFrame(f){frame=(f+nFrames)%nFrames;cycleT=frame/FPS;sampleTime(cycleT)}
function render(now){requestAnimationFrame(render);const dt=Math.min(.065,(now-last)/1000);last=now;
 if(playing&&running){
  elapsed+=dt;
  const rate=Number($('playRate').value);
  let advances=0;
  while(elapsed>=1/rate&&advances<5){elapsed-=1/rate;cycleT+=1/rate;advances++;
   if(cycleT>=clip.duration){if(!$('loop').checked){cycleT=clip.duration-1/120;playing=false;$('play').textContent='Replay cycle';break}else cycleT=0}
  }
  if(advances>0)sampleTime(cycleT);
 }
 orbit.update();renderer.render(scene,camera);
}
requestAnimationFrame(render);
$('play').onclick=()=>{if(!running)return;if(!playing&&cycleT>clip.duration-.04)sampleFrame(0);playing=!playing;$('play').textContent=playing?'Pause':'Play cycle'};
$('previous').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame-1)};
$('next').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame+1)};
$('frame').oninput=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(Number($('frame').value))};
$('markers').onclick=()=>{markersVisible=!markersVisible;showMarkers()};
for(const id of ['upperStrength','upperHarmonics'])$(id).addEventListener('change',()=>{if(running){sampleTime(cycleT);$('status').textContent='UPPER RECONSTRUCTION SETTINGS CHANGED · run real-rig checks again to measure continuity';}});
const jsonDownload=(filename,obj)=>{const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),4000)};
$('export').onclick=()=>{if(lastParityReport){jsonDownload('hareworks-forward-woman-parity-v0.1.8.json',lastParityReport);return;}if(lastReport)jsonDownload('hareworks-upper-continuity-v0.1.8.json',lastReport);else $('status').textContent='No measurements yet.';};
function runRealRigGate(auto=false){
 if(!running)return;
 playing=false;
 const max={pelvis:0,ankle:0,knee:0,toe:0,footYaw:0,IK:0,quatStep30:0,quatStep60:0,quatStep120:0},maxFront={left:-Infinity,right:-Infinity},minReach={left:Infinity,right:Infinity};
 const errors=[],rows=[],rateReports=[];const bones=['upperQuat','lowerQuat','footQuat'];
 for(const rate of [30,60,120]){
   const per=[];let lastRow=null,stepMax=0;
   const expected=Math.floor((clip.duration-1e-4)*rate)+1;
   for(let i=0;i<expected;i++){
    try{
     const r=evaluateTime(i/rate);per.push(r);
     if(rate===30)rows.push(r);
     max.pelvis=Math.max(max.pelvis,r.hipDiff);
     for(const side of ['left','right']){
       const v=r.legs[side];
       max.ankle=Math.max(max.ankle,v.ankleDiff);max.knee=Math.max(max.knee,v.kneeDiff);max.toe=Math.max(max.toe,v.toeDiff);
       max.footYaw=Math.max(max.footYaw,Math.abs(v.ankleYawDifferenceToReferenceDeg));max.IK=Math.max(max.IK,v.ikResidual);
       maxFront[side]=Math.max(maxFront[side],v.forward);minReach[side]=Math.min(minReach[side],v.reachMargin);
       if(lastRow){for(const bone of bones){const p=new THREE.Quaternion().fromArray(lastRow.legs[side][bone]);const q=new THREE.Quaternion().fromArray(v[bone]);stepMax=Math.max(stepMax,rad(p.angleTo(q)))}}
     }
     lastRow=r;
    }catch(e){errors.push({rate,frame:i,t:i/rate,message:e.message});break}
   }
   if(per.length>1){for(const side of ['left','right'])for(const bone of bones){const p=new THREE.Quaternion().fromArray(per.at(-1).legs[side][bone]),q=new THREE.Quaternion().fromArray(per[0].legs[side][bone]);stepMax=Math.max(stepMax,rad(p.angleTo(q)))}}
   max['quatStep'+rate]=stepMax;
   rateReports.push({fps:rate,expected,completed:per.length,maximumJointStepDeg:stepMax});
 }
 for(const side of ['left','right'])if(maxFront[side]<.30)errors.push({message:'NO_AHEAD_OF_HIP_SWING',side,value:maxFront[side]});
 if(max.IK>.008)errors.push({message:'IK_TARGET_RESIDUAL',value:max.IK});
 if(max.ankle>.040||max.knee>.050)errors.push({message:'REFERENCE_LEG_MISMATCH',ankle:max.ankle,knee:max.knee});
 if(max.pelvis>.030)errors.push({message:'PELVIS_REGRESSION',value:max.pelvis});
 if(minReach.left<0||minReach.right<0)errors.push({message:'UNREACHABLE_GEOMETRY',minReach});
 for(const [r,cap] of [[30,30],[60,18],[120,11]])if(max['quatStep'+r]>cap)errors.push({message:'JOINT_SNAP',fps:r,max:max['quatStep'+r],limit:cap});
 // Deliberately force an unreachable request to verify atomic rollback on the real rig.
 let injection='NOT_CHECKED',rollbackEvidence=null;
 try{
   const before=takePose();
   try{evaluateTime(rows[Math.min(rows.length-1,4)]?.t ?? (4/30),'unreachable');injection='FAULT_WAS_NOT_REJECTED'}
   catch(e){
     rollbackEvidence=rollbackDiagnosis(before);
     injection=/UNREACHABLE_KNEE/.test(e.message)&&rollbackEvidence.pass?'ROLLBACK_PASS':'ROLLBACK_FAIL '+e.message;
   }
 }catch(e){injection='ROLLBACK_EXCEPTION '+e.message}
 if(injection!=='ROLLBACK_PASS')errors.push({message:'ATOMIC_INJECTED_FAILURE',detail:injection});
 const upperRates=[30,60,120].map(upperStepAudit);
 for(const [rate,limit] of [[30,18],[60,11],[120,7]]){const measured=upperRates.find(r=>r.rateHz===rate);if(!Number.isFinite(measured.maxStepDeg)||measured.maxStepDeg>limit)errors.push({message:'UPPER_JOINT_SNAP',rate,maxStepDeg:measured.maxStepDeg,limit,worstBone:measured.worstBone});}
 const report={schema:'hareworks-forward-woman-v0.1.8-real-rig',sourceSha256:SOURCE,sourceClip:'Walking_Woman',pelvisImplementation:'v0.1.2 unchanged',legAnimationTracks:0,ankleTargets:'six-harmonic phase equation',anatomicalKneePoles:'six-harmonic phase equation',footOrientation:'analytical toe align and yaw twist',worldRootMotion:false,
  fpsRates:[30,60,120],rateReports,maxFront,minReach,maximumErrors:max,upperBody:{mode:'periodic phase fit from source joints, generated source track count 0',strength:Number($('upperStrength').value),harmonics:Number($('upperHarmonics').value),jointCount:upperProfile.length,rateAudits:upperRates},atomicInjection:injection,rollbackEvidence,errors,rows,ownerAccepted:false,
  result:errors.length?'BLOCKED_REAL_RIG_PHYSICAL_GATE':'MEASURED_REQUIRES_OWNER_VISUAL_REVIEW'};
 lastReport=report;sampleFrame(0);
 $('status').textContent=report.result+' · '+rateReports.map(r=>r.completed+'/'+r.expected+' @'+r.fps).join(', ')+' · upper 30Hz max '+report.upperBody.rateAudits[0].maxStepDeg.toFixed(1)+'° ('+report.upperBody.rateAudits[0].worstBone+') · '+(errors[0]?.message||'review upper motion from side and oblique');
 console.info('HAREWORKS_v018_REAL_RIG_GATE',report);
 if(!auto)jsonDownload('hareworks-upper-continuity-v0.1.8.json',report);
}
$('test').onclick=()=>runRealRigGate(false);

// Source-vs-generated parity is a separate acceptance gate from smoothness.
// Sample ACTUAL posed bones in both skinned models; never compare two fits.
function compareCurrentToReference(audit,rate,t,m) {
  const refShift=V(0,0,SEP);
  for (const b of upperProfile) {
    const r=refRig.bones.get(b.name),g=b.bone;
    if (!r || !g) throw Error('PARITY_JOINT_MISSING_'+b.name);
    observe(audit,b.name,'localRotationDeg',rad(r.quaternion.angleTo(g.quaternion)),rate,t);
    observe(audit,b.name,'worldRotationDeg',rad(wq(r).angleTo(wq(g))),rate,t);
    observe(audit,b.name,'localPosition',r.position.distanceTo(g.position),rate,t);
    observe(audit,b.name,'worldPosition',world(r).add(refShift).distanceTo(world(g)),rate,t);
  }
  for (const side of ['left','right']) {
    const lm=m.legs[side];
    observe(audit,side+'-ankle','worldPosition',lm.ankleDiff,rate,t);
    observe(audit,side+'-knee','worldPosition',lm.kneeDiff,rate,t);
  }
}
function measurePreset(strength,harmonics) {
  const preset=checkedPreset({strength,harmonics});
  const audit=createAudit();const errors=[];const counts=[];
  for(const rate of [30,60,120]) {
    let n=0;
    // Include exact frame samples and midframes; do not sample the reset endpoint.
    for(let i=0;i<Math.floor(clip.duration*rate)*2;i++) {
      const t=i/(2*rate);
      if(t>=clip.duration-1e-8)break;
      try { const metrics=evaluateTime(t,null,preset);compareCurrentToReference(audit,rate,t,metrics);n++; }
      catch(e) {errors.push({rateHz:rate,t,kind:'REAL_SKINNED_EVALUATION',message:e.message});}
    }
    // Near seam at each rate and at t=0 (separate from the source's anomalous endpoint).
    for(const t of [0,clip.duration-1e-6]){
      try{const metrics=evaluateTime(t,null,preset);compareCurrentToReference(audit,rate,t,metrics);n++;}
      catch(e){errors.push({rateHz:rate,t,kind:'SEAM_EVALUATION',message:e.message});}
    }
    counts.push({rateHz:rate,sampledPoses:n});
  }
  const summary=finalizeAudit(audit);
  const failures=[];
  // These are provisional reproduction tolerances. No hidden widening on failure.
  for(const [bone,kinds] of Object.entries(summary)) {
    const upper=upperProfile.some(b=>b.name===bone);
    if(upper) {
      const rot=kinds.localRotationDeg, pos=kinds.worldPosition;
      if(!rot||rot.rms>2||rot.max>5)failures.push({bone,measurement:'localRotationDeg',rms:rot?.rms,max:rot?.max,limitRms:2,limitMax:5});
      if(!pos||pos.rms>.01)failures.push({bone,measurement:'worldPosition',rms:pos?.rms,limitRms:.01});
    } else if(!kinds.worldPosition||kinds.worldPosition.rms>.01) {
      failures.push({bone,measurement:'lowerBodyWorldPosition',rms:kinds.worldPosition?.rms,limitRms:.01});
    }
  }
  if(!Object.keys(summary).length)failures.push({kind:'NO_VALID_SAMPLES'});
  if(errors.length)failures.push({kind:'RIG_EVALUATION_ERRORS',count:errors.length});
  const offenders=rankOffenders(summary,'localRotationDeg',12);
  const positionOffenders=rankOffenders(summary,'worldPosition',12);
  return {preset:{strength,harmonics},fps:[30,60,120],counts,poseErrors:errors.slice(0,60),poseErrorCount:errors.length,
    thresholds:{upperRotationRmsDeg:2,upperRotationMaxDeg:5,worldJointPositionRms:.01,lowerJointPositionRms:.01},
    jointCount:Object.keys(summary).length,allMeasurements:summary,offenders,positionOffenders,
    failures:failures.slice(0,100),failureCount:failures.length,
    verdict:failures.length?'REJECTED_PARITY_OUTSIDE_TOLERANCE':'MEASURED_WITHIN_PROVISIONAL_TOLERANCE_OWNER_REVIEW_REQUIRED'};
}
function verifyRealRigPresetSeparation() {
 const a=checkedPreset({strength:.7,harmonics:3});
 const b=checkedPreset({strength:1,harmonics:4});
 const samplesA=[],samplesB=[],sampleTimes=[.08,.19,.31,.47,.62,.81];
 for(const t of sampleTimes){
   evaluateTime(t,null,a);samplesA.push(upperFrameSnapshot());
   evaluateTime(t,null,b);samplesB.push(upperFrameSnapshot());
 }
 const evidence=presetSeparation(samplesA,samplesB,0.0001);
 if(!evidence.pass)throw Error('VERIFIER_PRESETS_IDENTICAL '+JSON.stringify(evidence));
 return {...evidence,sampleTimes,firstPreset:a,secondPreset:b};
}
function runParityAudit(exportNow=false){
  if(!running)return;
  const saved={strength:$('upperStrength').value,harmonics:$('upperHarmonics').value,time:cycleT,playing};
  playing=false;
  let report;
  try {
    const sourceZero=sourceZeroAudit();
    const presetSensitivity=verifyRealRigPresetSeparation();
    const trials=[];
    trials.push(measurePreset(.7,3)); // prior restrained benchmark with corrected anchor
    trials.push(measurePreset(1,4)); // prior full benchmark with corrected anchor
    trials.push(measurePreset(1,12)); // higher-resolution phase fit, same anchored architecture
    if(JSON.stringify(trials[0].allMeasurements)===JSON.stringify(trials[1].allMeasurements))
      throw Error('VERIFIER_IDENTICAL_METRICS_FOR_DIFFERENT_POSES');
    report={schema:'hareworks-reference-parity-v0.1.8',modelSha256:SOURCE,sourceClip:'Walking_Woman',sourceZero,presetSensitivity,
      auditedPublishedImplementation:'v0.1.5 pose equations unchanged',
      evidence:'exact GLB / reference animation vs generated skinned bone transforms at matched timestamps',
      referenceModelOffsetRemoved:true,referenceNotUsedAsGeneratedRuntimeTracks:true,
      sampledRatesHz:[30,60,120],halfFrames:true,sourceEndpointExcluded:true,
      variants:trials,ownerVisualAcceptance:false,requestedOutcome:'small_error_reference_replication',
      note:'This measures accuracy, not independently moving world-space locomotion.'};
    lastParityReport=report;
    if(lastReport)lastReport.referenceParity=report;
    const best=trials.reduce((a,b)=>a.failureCount<=b.failureCount?a:b);
    const worst=best.offenders[0];const pos=best.positionOffenders[0];
    $('parityReport').textContent=`REFERENCE PARITY v0.1.8 | exact source vs skinned generated\n`+
      trials.map(x=>`Amplitude ${x.preset.strength}, harmonics ${x.preset.harmonics}: ${x.verdict}, ${x.failureCount} violations, ${x.poseErrorCount} pose errors`).join('\n')+
      `\nBest-by-failures worst local bone rotation: ${worst?.bone||'none'} RMS ${worst?.rms?.toFixed(2)||'?'}° max ${worst?.max?.toFixed(2)||'?'}° at ${worst?.worst?.t?.toFixed(3)||'?'}s`+
      `\nWorst world joint displacement: ${pos?.bone||'none'} RMS ${pos?.rms?.toFixed(4)||'?'} max ${pos?.max?.toFixed(4)||'?'}`+
      `\nSensitivity ${presetSensitivity.maxQuaternionDistance.toFixed(5)} quaternion units at ${presetSensitivity.offender?.bone}.\n30/60/120Hz plus half-frames; all joint results in Export evidence. No automatic tolerance relaxation.`;
    $('status').textContent=trials.every(x=>!x.failureCount)?'REFERENCE_PARITY_MEASURED_WITHIN_TOLERANCE · owner review pending':'REJECTED_REFERENCE_PARITY · select Export evidence for failing joints/timestamps';
    if(exportNow)jsonDownload('hareworks-forward-woman-parity-v0.1.8.json',report);
  }catch(e){lastParityReport={schema:'hareworks-reference-parity-v0.1.8',verdict:'VERIFIER_INSTRUMENT_BLOCKED',message:e.message,ownerAccepted:false};$('parityReport').textContent='VERIFIER_INSTRUMENT_BLOCKED '+e.message;console.error(e)}
  finally{
    $('upperStrength').value=saved.strength;$('upperHarmonics').value=saved.harmonics;
    try{sampleTime(saved.time)}catch(e){console.error(e)}
    playing=saved.playing;
  }
  return report;
}
$('parity').onclick=()=>runParityAudit(true);


try{
 const paths=['../v0.1.2/motion-profile.json','../v0.1.3/foot-profile.json'];
 const loaded=await Promise.all([...paths.map(p=>fetch(p).then(r=>{if(!r.ok)throw Error('FETCH_'+p+'_'+r.status);return r.json()})),new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb')]);
 [profile,footProfile]=loaded;const gltf=loaded[2];validateProfile(profile);validateFootProfile(footProfile);
 if(footProfile.sourceSha256!==SOURCE||profile.sourceSha256!==SOURCE)throw Error('MODEL_PARAMETER_SHA_MISMATCH');
 reference=gltf.scene;generated=cloneSkeleton(gltf.scene);reference.position.z=-SEP/2;generated.position.z=SEP/2;
 scene.add(reference,generated);reference.updateMatrixWorld(true);generated.updateMatrixWorld(true);
 const clips=gltf.animations;clip=clips.find(c=>c.name==='Walking_Woman');
 if(clips.length!==9||!clip||Math.abs(clip.duration-profile.duration)>.001)throw Error('SOURCE_CLIP_CONTRACT');
 refRig=rigOf(reference);genRig=rigOf(generated);
 refMixer=new THREE.AnimationMixer(reference);refMixer.clipAction(clip).reset().play();refMixer.setTime(0);
 const seedMixer=new THREE.AnimationMixer(generated);seedMixer.clipAction(clip).reset().play();seedMixer.setTime(0);
 const legPose=new Map();for(const leg of Object.values(genRig.legs))for(const b of leg.chain)legPose.set(b,pose(b));
 seed={hip:pose(genRig.hips),legPose};
 seedMixer.stopAllAction();seedMixer.uncacheRoot(generated);
 // Only bones in the Spine subtree are eligible for a source upper-body track.
 // Hip/root and both leg chains are explicitly excluded from the generated mixer.
 const {forbidden,allowed}=excludedTrackNames(generated);
 const allowedTracks=clip.tracks.filter(tr=>{const boneName=tr.name.replace(/\..*$/,'').replace(/\[.*$/,'');return allowed.has(boneName)&&!forbidden.has(boneName)});
 const excludedLeg=clip.tracks.filter(tr=>Object.values(names).flat().some(n=>tr.name.startsWith(n+'.')||tr.name.startsWith(n+'[')));
 const excludedHip=clip.tracks.filter(tr=>tr.name.startsWith(genRig.hips.name+'.')||tr.name.startsWith(genRig.hips.name+'['));
 if(excludedLeg.length<4||excludedHip.length<1||allowedTracks.length<1)throw Error('SOURCE_TRACK_FILTER_MISSING '+excludedLeg.length+' '+excludedHip.length+' '+allowedTracks.length);
 if(allowedTracks.some(tr=>!allowed.has(tr.name.split('.')[0])))throw Error('UNAUTHORIZED_GENERATED_TRACK');
 const upperNames=[...new Set(allowedTracks.map(tr=>tr.name.split('.')[0]))];
 upperProfile=buildUpperProfile(upperNames);
 upperAudit={upperSourceTracks:allowedTracks.length,generatedClipUpperTracks:0,fitSamples:120,maxHarmonics:12,upperBoneCount:upperProfile.length,sourceClip:clip.name};
 profile.zeroPelvis=[profile.pelvis.x.start,profile.pelvis.y.start,profile.pelvis.z.start];profile.zeroPelvisYaw=profile.pelvis.yaw.start;
 addMarkers(refRig,{left:0x1ecbff,right:0xffb767});addMarkers(genRig,{left:0x1ecbff,right:0xffb767});
 floor.position.y=new THREE.Box3().setFromObject(reference).min.y;
 nFrames=Math.floor(clip.duration*FPS)+1;while((nFrames-1)/FPS>=clip.duration-1e-6)nFrames--;
 $('frame').max=nFrames-1;
 running=true;display(evaluate(0));resize();cameraPreset('side');
 $('status').textContent=`REAL SKINNED GLB READY v0.1.8 · unchanged v0.1.3 legs + v0.1.2 hips; ${allowedTracks.length} source upper tracks calibrated, ZERO played on generated upper. Orbit to review shoulder, arm and head continuity.`;
 runRealRigGate(true);
 runParityAudit(false);
 console.info('HAREWORKS_v018_TRACK_AUDIT',{excludedLeg:excludedLeg.length,excludedHip:excludedHip.length,upperBodyFitted:allowedTracks.length,upperProfile:upperAudit,sourceSha:SOURCE});
}catch(e){running=false;$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
