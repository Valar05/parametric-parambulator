/* v0.1.2: ONE forward cycle, original reference against generated pelvis, IK
 * and foot motion. Reference tracks are never used as inputs to generated
 * pelvis, leg or ankle orientation. Upper body tracks remain reference-derived.
 * This does NOT claim root travel, planted sole contact or full procedural walk. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {trajectory,worldOffset} from '../v0.1.1/gait-kernel.mjs';
import {independentPose,validateProfile,angleDiff,clamp} from './pose-kernel.mjs';

const $=id=>document.getElementById(id);
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const Q=()=>new THREE.Quaternion();
const YA=V(0,1,0);
const SEP=2.75, FPS=30, SOURCE='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
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
function kneePoint(hip,ankle,l1,l2,pole,yaw){
 const axis=ankle.clone().sub(hip),d=axis.length();
 if(!(d<l1+l2-.003&&d>Math.abs(l1-l2)+.003))throw Error('UNREACHABLE_KNEE '+d.toFixed(5));
 axis.divideScalar(d);
 const a=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-a*a));
 const tangent=V(...pole).applyAxisAngle(YA,yaw).addScaledVector(axis,-V(...pole).applyAxisAngle(YA,yaw).dot(axis));
 if(tangent.lengthSq()<1e-9)throw Error('ANATOMICAL_POLE_SINGULAR');
 return hip.clone().addScaledVector(axis,a).addScaledVector(tangent.normalize(),h);
}
function setFootProcedural(leg,desiredToeVector,desiredYaw){
 const actualVector=world(leg.toe).sub(world(leg.ankle));
 const wanted=V(...desiredToeVector);
 if(actualVector.lengthSq()<1e-8||wanted.lengthSq()<1e-8)throw Error('ZERO_FOOT_VECTOR');
 const dir=wanted.clone().normalize();
 let footQ=Q().setFromUnitVectors(actualVector.normalize(),dir).multiply(wq(leg.ankle));
 // Twist around the toe direction, preserving its orientation, to match a
 // separate fitted world-yaw curve. No source/ref ankle quaternion is read.
 for(let i=0;i<5;i++){
  const err=angleDiff(desiredYaw,forwardYaw(footQ));
  if(Math.abs(err)<.0005)break;
  const step=.012;
  const plus=Q().setFromAxisAngle(dir,step).multiply(footQ);
  const minus=Q().setFromAxisAngle(dir,-step).multiply(footQ);
  const derivative=angleDiff(forwardYaw(plus),forwardYaw(minus))/(2*step);
  if(!Number.isFinite(derivative)||Math.abs(derivative)<.15)break;
  footQ.premultiply(Q().setFromAxisAngle(dir,clamp(err/derivative,-.35,.35))).normalize();
 }
 setWorldBoneRotation(leg.ankle,footQ);
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
let reference,generated,refRig,genRig,refMixer,genMixer,clip,profile,legProfile,seed,refBase,genBase;
let running=false,playing=false,frame=0,last=performance.now(),elapsed=0,markersVisible=false,markers=[],lastReport=null;
let nFrames=29;
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
function applyGeneratedPose(t){
 const sourceTime=Math.min(t,clip.duration-1e-6);
 const prediction=independentPose(profile,sourceTime);
 genMixer.setTime(sourceTime);
 for(const [b,p] of seed.legPose)restore(b,p);
 restore(genRig.hips,seed.hip);
 // The pelvis offset is in measured world units, transformed into the local
 // space of the hips parent. No source clip hip tracks are in genMixer.
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
  const leg=genRig.legs[side],f=trajectory(sourceTime,legProfile,side),cfg=legProfile[side];
  const H=world(leg.up),vec=V(...worldOffset(f,pelvisYaw,H.y));
  const A=H.clone().add(vec);
  const l1=world(leg.up).distanceTo(world(leg.knee));
  const l2=world(leg.knee).distanceTo(world(leg.ankle));
  if(Math.abs(l1-cfg.upperLength)>.009||Math.abs(l2-cfg.lowerLength)>.009)throw Error('LINK_LENGTH_MISMATCH_'+side);
  const K=kneePoint(H,A,l1,l2,cfg.pole,pelvisYaw);
  turnBoneToward(leg.up,world(leg.knee),K);generated.updateMatrixWorld(true);
  turnBoneToward(leg.knee,world(leg.ankle),A);generated.updateMatrixWorld(true);
  const target=prediction.feet[side];
  setFootProcedural(leg,target.toeVector,target.ankleYaw);generated.updateMatrixWorld(true);
  const actualAnkle=world(leg.ankle),actualKnee=world(leg.knee),actualToe=world(leg.toe);
  const toeVector=actualToe.clone().sub(actualAnkle);
  const r={side,relativeForward:f.z,hip:world(leg.up).toArray(),knee:actualKnee.toArray(),ankle:actualAnkle.toArray(),toe:actualToe.toArray(),
   ikResidual:actualAnkle.distanceTo(A),toeVectorDifferenceToCurve:toeVector.distanceTo(V(...target.toeVector)),
   ankleYawDifferenceToCurveDeg:rad(angleDiff(forwardYaw(wq(leg.ankle)),target.ankleYaw))};
  if(![r.ikResidual,r.toeVectorDifferenceToCurve,r.ankleYawDifferenceToCurveDeg,...r.hip,...r.knee,...r.ankle,...r.toe].every(Number.isFinite))throw Error('NONFINITE_GENERATED_POSE');
  if(r.ikResidual>.012)throw Error('IK_TARGET_RESIDUAL '+side+' '+r.ikResidual.toFixed(5));
  rows.push(r);
 }
 return {t:sourceTime,profilePhase:prediction.q,pelvis:world(genRig.hips).toArray(),pelvisYaw:pelvisYaw,legs:rows};
}
function evaluate(f){
 if(!running)return null;
 const t=f/FPS;refMixer.setTime(t);reference.updateMatrixWorld(true);
 const generatedPose=applyGeneratedPose(t);
 const refPelvis=world(refRig.hips).add(V(0,0,SEP));
 const metrics={frame:f,t,hipDiff:world(genRig.hips).distanceTo(refPelvis),pelvisYawDiffDeg:rad(angleDiff(generatedPose.pelvisYaw,forwardYaw(wq(refRig.hips)))),legs:{}};
 for(const s of ['left','right']){
  const gen=genRig.legs[s],ref=refRig.legs[s],r=generatedPose.legs.find(x=>x.side===s);
  const refKnee=world(ref.knee).add(V(0,0,SEP)),refAnkle=world(ref.ankle).add(V(0,0,SEP)),refToe=world(ref.toe).add(V(0,0,SEP));
  metrics.legs[s]={forward:r.relativeForward,kneeDiff:world(gen.knee).distanceTo(refKnee),ankleDiff:world(gen.ankle).distanceTo(refAnkle),toeDiff:world(gen.toe).distanceTo(refToe),ikResidual:r.ikResidual,
   ankleYawDifferenceToReferenceDeg:rad(angleDiff(forwardYaw(wq(gen.ankle)),forwardYaw(wq(ref.ankle)))),
   toeVectorCurveResidual:r.toeVectorDifferenceToCurve,ankleYawCurveResidualDeg:r.ankleYawDifferenceToCurveDeg,
   upperQuat:gen.up.quaternion.toArray(),lowerQuat:gen.knee.quaternion.toArray(),footQuat:gen.ankle.quaternion.toArray()};
 }
 showMarkers();return metrics;
}
function display(m){if(!m)return;
 $('frame').value=m.frame;$('frameNumber').textContent=`${m.frame}/${nFrames-1}`;
 $('metrics').textContent=`Frame ${m.frame}/${nFrames-1}, time ${m.t.toFixed(3)}s\nGenerated hips Δ ${m.hipDiff.toFixed(4)} units / yaw Δ ${m.pelvisYawDiffDeg.toFixed(2)}°\nLEFT   forward ${m.legs.left.forward.toFixed(3)}   ankle Δ ${m.legs.left.ankleDiff.toFixed(3)}  knee Δ ${m.legs.left.kneeDiff.toFixed(3)}  toe Δ ${m.legs.left.toeDiff.toFixed(3)}\nRIGHT  forward ${m.legs.right.forward.toFixed(3)}   ankle Δ ${m.legs.right.ankleDiff.toFixed(3)}  knee Δ ${m.legs.right.kneeDiff.toFixed(3)}  toe Δ ${m.legs.right.toeDiff.toFixed(3)}\nFoot yaw reference Δ ${m.legs.left.ankleYawDifferenceToReferenceDeg.toFixed(1)}° / ${m.legs.right.ankleYawDifferenceToReferenceDeg.toFixed(1)}°\nAnkle IK residual ${m.legs.left.ikResidual.toFixed(5)} / ${m.legs.right.ikResidual.toFixed(5)}`;
}
function sampleFrame(f){frame=(f+nFrames)%nFrames;try{display(evaluate(frame))}catch(e){playing=false;$('status').textContent='BLOCKED_REAL_RIG '+e.message;console.error(e)}}
function render(now){requestAnimationFrame(render);let dt=Math.min(.1,(now-last)/1000);last=now;
 if(playing&&running){elapsed+=dt;if(elapsed>=1/FPS){const steps=Math.max(1,Math.min(2,Math.floor(elapsed*FPS)));elapsed-=steps/FPS;frame=Math.min(frame+steps,nFrames-1);sampleFrame(frame);if(frame===nFrames-1){playing=false;$('play').textContent='Replay cycle'}}}
 orbit.update();renderer.render(scene,camera);
}
requestAnimationFrame(render);
$('play').onclick=()=>{if(!running)return;if(!playing&&frame===nFrames-1)sampleFrame(0);playing=!playing;$('play').textContent=playing?'Pause':'Play cycle'};
$('previous').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame-1)};
$('next').onclick=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(frame+1)};
$('frame').oninput=()=>{playing=false;$('play').textContent='Play cycle';sampleFrame(Number($('frame').value))};
$('markers').onclick=()=>{markersVisible=!markersVisible;showMarkers()};
const jsonDownload=(filename,obj)=>{const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),4000)};
$('export').onclick=()=>{if(!lastReport){$('status').textContent='Run the 30 fps real-rig comparison first to create exportable evidence.';return}jsonDownload('hareworks-independent-woman-v0.1.2.json',lastReport)};
$('test').onclick=()=>{
 if(!running)return;playing=false;let rows=[],errors=[];
 const max={pelvis:0,ankle:0,knee:0,toe:0,footYaw:0,IK:0,quatStep:0},maxFront={left:-Infinity,right:-Infinity};
 try{for(let i=0;i<nFrames;i++){
  const r=evaluate(i);rows.push(r);max.pelvis=Math.max(max.pelvis,r.hipDiff);
  for(const s of ['left','right']){const v=r.legs[s];max.ankle=Math.max(max.ankle,v.ankleDiff);max.knee=Math.max(max.knee,v.kneeDiff);max.toe=Math.max(max.toe,v.toeDiff);max.footYaw=Math.max(max.footYaw,Math.abs(v.ankleYawDifferenceToReferenceDeg));max.IK=Math.max(max.IK,v.ikResidual);maxFront[s]=Math.max(maxFront[s],v.forward);
   if(i>0){for(const key of ['upperQuat','lowerQuat','footQuat']){const previous=new THREE.Quaternion().fromArray(rows[i-1].legs[s][key]),current=new THREE.Quaternion().fromArray(v[key]);max.quatStep=Math.max(max.quatStep,rad(previous.angleTo(current)))}}
  }
 }}catch(e){errors.push({frame:rows.length,message:e.message})}
 if(maxFront.left<.30||maxFront.right<.30)errors.push({message:'FEET_DO_NOT_REACH_AHEAD_OF_HIPS',maxFront});
 if(max.quatStep>60)errors.push({message:'JOINT_ROTATION_SNAP_OVER_60_DEG_PER_30FPS_FRAME',value:max.quatStep});
 if(max.IK>.012)errors.push({message:'ANATOMICAL_IK_SOLVER_RESIDUAL',value:max.IK});
 const report={schema:'hareworks-forward-woman-v0.1.2-real-rig',sourceSha256:SOURCE,referenceClip:'Walking_Woman',generatedLegTracks:0,generatedHipTracks:0,
  generatedPelvis:'phase-parametric fitted movement (independent)',generatedAnkleYaw:'phase-parametric toe-vector/yaw solved rotation (independent)',
  upperBodyTracks:'source upper-body clips remain',fps:FPS,frameCount:rows.length,expectedFrames:nFrames,
  maximumErrors:max,frontReach:maxFront,errors,rows,ownerAccepted:false,worldFootPlantImplemented:false,
  result:errors.length?'BLOCKED_GEOMETRIC_GATE':'MEASURED_REQUIRES_OWNER_VISUAL_REVIEW'};
 lastReport=report;sampleFrame(0);
 $('status').textContent=report.result+' · '+rows.length+'/'+nFrames+' frames · '+(errors.length?JSON.stringify(errors[0]):'both feet advance ahead of hips; orbit to inspect knees and toes');
 console.info('HAREWORKS_PROCEDURAL_POSE_GATE',report);
 jsonDownload('hareworks-independent-woman-v0.1.2.json',report);
};

try{
 const paths=['./motion-profile.json','../v0.1.1/profile.json'];
 const loaded=await Promise.all([...paths.map(p=>fetch(p).then(r=>{if(!r.ok)throw Error('FETCH_'+p+'_'+r.status);return r.json()})),new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb')]);
 [profile,legProfile]=loaded;const gltf=loaded[2];validateProfile(profile);
 if(legProfile.modelSha256!==SOURCE||profile.sourceSha256!==SOURCE)throw Error('MODEL_PARAMETER_SHA_MISMATCH');
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
 genMixer=new THREE.AnimationMixer(generated);genMixer.clipAction(new THREE.AnimationClip('upper_body_only',clip.duration,allowedTracks)).reset().play();
 profile.zeroPelvis=[profile.pelvis.x.start,profile.pelvis.y.start,profile.pelvis.z.start];profile.zeroPelvisYaw=profile.pelvis.yaw.start;
 addMarkers(refRig,{left:0x1ecbff,right:0xffb767});addMarkers(genRig,{left:0x1ecbff,right:0xffb767});
 floor.position.y=new THREE.Box3().setFromObject(reference).min.y;
 nFrames=Math.floor(clip.duration*FPS)+1;while((nFrames-1)/FPS>=clip.duration-1e-6)nFrames--;
 $('frame').max=nFrames-1;
 running=true;display(evaluate(0));resize();cameraPreset('side');
 $('status').textContent=`REAL SKINNED GLB READY · ${excludedLeg.length} leg tracks and ${excludedHip.length} hip tracks excluded from generated animation; ${allowedTracks.length} upper-body tracks retained. Orbit viewer to judge results. Visual acceptance pending.`;
 console.info('HAREWORKS_v012_TRACK_AUDIT',{excludedLeg:excludedLeg.length,excludedHip:excludedHip.length,upperBody:allowedTracks.length,sourceSha:SOURCE});
}catch(e){running=false;$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
