/* Hareworks v0.1.1: forward-only skinned-leg comparison, NOT generalized locomotion. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {trajectory,worldOffset} from './gait-kernel.mjs';
const $=id=>document.getElementById(id);
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const Q=()=>new THREE.Quaternion();
const SOURCE='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const EPS=1e-8, PARENT_OFFSET=2.75;
const boneNames={
 left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],
 right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']
};
const toDegrees=x=>x*180/Math.PI;
function world(b){return b.getWorldPosition(V())}
function wq(b){return b.getWorldQuaternion(Q())}
function pelvisYaw(b){const f=V(0,0,1).applyQuaternion(wq(b));return Math.atan2(f.x,f.z)}
function getRig(model){
 const bones=new Map();model.traverse(o=>{if(o.isBone){if(bones.has(o.name))throw Error('DUPLICATE_BONE '+o.name);bones.set(o.name,o)}});
 if(bones.size!==74)throw Error('EXPECTED_74_BONES got '+bones.size);
 const hips=bones.get('mixamorigHips');if(!hips)throw Error('HIPS_MISSING');
 const legs={};
 for(const [side,names] of Object.entries(boneNames)){
  const c=names.map(n=>{const b=bones.get(n);if(!b)throw Error('BONE_MISSING '+n);return b});
  if(c[0].parent!==hips||c.some((b,i)=>i&&b.parent!==c[i-1]))throw Error('BONE_CHAIN_MISMATCH '+side);
  legs[side]={up:c[0],knee:c[1],mid:c[2],ankle:c[3],toe:c[4],chain:c};
 }
 return {hips,legs};
}
function fromToBone(bone,point,desired){
 const pivot=world(bone),actual=point.clone().sub(pivot),want=desired.clone().sub(pivot);
 if(actual.lengthSq()<EPS||want.lengthSq()<EPS)throw Error('ZERO_LENGTH_SOLVER');
 const delta=Q().setFromUnitVectors(actual.normalize(),want.normalize());
 const parentInv=wq(bone.parent).invert();
 bone.quaternion.copy(parentInv.multiply(delta).multiply(wq(bone))).normalize();
}
function analyticKnee(H,A,L1,L2,poleLocal,yaw){
 const axis=A.clone().sub(H),d=axis.length();
 if(d>L1+L2-.003||d<Math.abs(L1-L2)+.003)throw Error('UNREACHABLE_TARGET '+d.toFixed(5)+' lengths '+(L1+L2).toFixed(5));
 axis.divideScalar(d);
 const a=(L1*L1-L2*L2+d*d)/(2*d),rad=Math.sqrt(Math.max(0,L1*L1-a*a));
 const pw=V(...poleLocal).applyAxisAngle(V(0,1,0),yaw);
 const perp=pw.addScaledVector(axis,-pw.dot(axis));
 if(perp.lengthSq()<EPS)throw Error('POLE_SINGULARITY');perp.normalize();
 return H.clone().addScaledVector(axis,a).addScaledVector(perp,rad);
}

const scene=new THREE.Scene();scene.background=new THREE.Color('#101821');
scene.add(new THREE.HemisphereLight(0xd9e4ff,0x30303c,2.5));const sunlight=new THREE.DirectionalLight(0xffffff,3.2);sunlight.position.set(-4,7,3);scene.add(sunlight);
const grid=new THREE.GridHelper(9,18,0x59727e,0x344553);scene.add(grid);
const camera=new THREE.OrthographicCamera(-3.6,3.6,1.9,-1.9,.05,120);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
$('stage').append(renderer.domElement);
function resize(){const w=$('stage').clientWidth,h=Math.max(260,Math.min(570,w*.68));renderer.setSize(w,h,false);camera.left=-3.4*w/h/2;camera.right=-camera.left;camera.top=1.9;camera.bottom=-1.9;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);
camera.position.set(-7,3.3,0);camera.lookAt(0,1,0);
let reference,generated,refRig,genRig,refMixer,genMixer,sourceClip,profile;
let active=false,playing=true,frame=0,last=performance.now(),accumulator=0,metrics=[],debug=true;
let markers=[];
function buildMarkers(rig,color){for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.025,10,8),new THREE.MeshBasicMaterial({color:color[side],depthTest:false}));m.renderOrder=50;scene.add(m);markers.push({rig,side,m})}}
function validateProfile(){if(profile.modelSha256!==SOURCE||profile.clip!=='Walking_Woman')throw Error('PROFILE_SOURCE_MISMATCH');}
function sample(t){
 refMixer.setTime(t);genMixer.setTime(t);
 reference.updateMatrixWorld(true);generated.updateMatrixWorld(true);
 const output=[];
 for(const side of ['left','right']){
  const ref=refRig.legs[side],leg=genRig.legs[side],p=profile[side],yaw=pelvisYaw(genRig.hips);
  const H=world(leg.up),f=trajectory(t,profile,side);
  // Standard Three.js R_y: local forward +Z maps to (+sin(yaw), 0, +cos(yaw)).
  const offset=V(...worldOffset(f,yaw,H.y));
  const A=H.clone().add(offset),L1=world(leg.up).distanceTo(world(leg.knee)),L2=world(leg.knee).distanceTo(world(leg.ankle));
  if(Math.abs(L1-p.upperLength)>.009||Math.abs(L2-p.lowerLength)>.009)throw Error('SOURCE_RIG_LINK_LENGTH_MISMATCH '+side+' '+L1+' '+L2);
  const K=analyticKnee(H,A,L1,L2,p.pole,yaw);
  // Direct two-link solve, not iterative CCD, and no previous-frame solver state.
  // Intermediate and toe bone local bind transforms are preserved.
  const actualK=world(leg.knee);fromToBone(leg.up,actualK,K);generated.updateMatrixWorld(true);
  fromToBone(leg.knee,world(leg.ankle),A);generated.updateMatrixWorld(true);
  // Foot orientation intentionally BORROWED from source during this isolated leg geometry proof.
  leg.ankle.quaternion.copy(wq(leg.ankle.parent).invert().multiply(wq(ref.ankle)));
  generated.updateMatrixWorld(true);
  const reached=world(leg.ankle),knee=world(leg.knee),sourceK=world(ref.knee).add(V(0,0,PARENT_OFFSET)),sourceA=world(ref.ankle).add(V(0,0,PARENT_OFFSET));
  const residual=reached.distanceTo(A),kneeError=knee.distanceTo(sourceK),ankleError=reached.distanceTo(sourceA);
  const kneeh=world(leg.up).distanceTo(knee),kneel=knee.distanceTo(reached);
  if(![residual,kneeError,ankleError,kneeh,kneel].every(Number.isFinite))throw Error('NONFINITE_SOLUTION');
  if(residual>.012)throw Error('IK_TARGET_RESIDUAL_'+side+'='+residual.toFixed(5));
  if(Math.abs(kneeh-L1)>.001||Math.abs(kneel-L2)>.001)throw Error('BONE_LENGTH_CHANGED');
  output.push({side,t,relativeForward:f.z,ankleResidual:residual,ankleDifferenceToReference:ankleError,kneeDifferenceToReference:kneeError,
   hipWorld:H.toArray(),kneeWorld:knee.toArray(),ankleWorld:reached.toArray(),footOrientationSource:'reference clip quaternion (isolated leg proof)'});
 }
 for(const {rig,side,m} of markers){m.position.copy(world(rig.legs[side].ankle));m.visible=debug}
 return output;
}
function resetLegs(){
 for(const side of ['left','right'])for(const b of genRig.legs[side].chain)b.quaternion.copy(b.userData.seedQuat);
 generated.updateMatrixWorld(true);
}
function tick(){
 if(!active)return;
 const t=(frame/30)%sourceClip.duration;
 resetLegs();
 try{
  const o=sample(t);
  $('measure').textContent=`frame ${frame} · ${t.toFixed(3)}s  |  Left +Z ${o[0].relativeForward.toFixed(3)} / IK ${o[0].ankleResidual.toFixed(4)}  |  Right +Z ${o[1].relativeForward.toFixed(3)} / IK ${o[1].ankleResidual.toFixed(4)}`;
  if(metrics.length<600)metrics.push(o);
 }catch(e){playing=false;$('play').textContent='Play';$('status').textContent='BLOCKED_REAL_RIG '+e.message;console.error(e)}
 renderer.render(scene,camera);
}
function animate(now){requestAnimationFrame(animate);const dt=Math.min(.08,(now-last)/1000);last=now;if(playing&&active){accumulator+=dt;if(accumulator>=1/30){const steps=Math.min(2,Math.floor(accumulator*30));accumulator-=steps/30;frame+=steps;if(frame>=Math.round(sourceClip.duration*30)-1){frame=Math.round(sourceClip.duration*30)-1;playing=false;$('play').textContent='Replay cycle'}tick()}}}
requestAnimationFrame(animate);
$('play').onclick=()=>{if(!playing&&frame>=Math.round(sourceClip.duration*30)-1){frame=0;accumulator=0}playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('next').onclick=()=>{playing=false;$('play').textContent='Play';frame=(frame+1)%Math.round(sourceClip.duration*30);tick()};
$('prev').onclick=()=>{playing=false;$('play').textContent='Play';frame=(frame-1+Math.round(sourceClip.duration*30))%Math.round(sourceClip.duration*30);tick()};
$('markers').onclick=()=>{debug=!debug;tick()};
$('export').onclick=()=>{
 const report={schema:'hareworks-forward-woman-v0.1.1-browser-geometry-check',sourceSha256:SOURCE,model:'actual GLB',input:'Walking_Woman upper/root tracks, original foot orientations borrowed',phase:sourceClip.duration,frames:metrics,ownerAcceptance:false};
 const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-woman-forward-v0.1.1-real-rig.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
};
$('review').onclick=()=>{
 if(!active)return;playing=false;$('play').textContent='Play';metrics=[];
 const report={frames:0,maxResidual:0,maxKneeDiff:0,maxAnkleDiff:0,frontLeft:-Infinity,frontRight:-Infinity,errors:[]};
 for(let i=0;i<Math.round(sourceClip.duration*30);i++){
  frame=i;resetLegs();try{const o=sample(i/30);metrics.push(o);report.frames++;for(const p of o){report.maxResidual=Math.max(report.maxResidual,p.ankleResidual);report.maxKneeDiff=Math.max(report.maxKneeDiff,p.kneeDifferenceToReference);report.maxAnkleDiff=Math.max(report.maxAnkleDiff,p.ankleDifferenceToReference);if(p.side==='left')report.frontLeft=Math.max(report.frontLeft,p.relativeForward);else report.frontRight=Math.max(report.frontRight,p.relativeForward)}}catch(e){report.errors.push({frame:i,message:e.message});break}
 }
 $('status').textContent='30 FPS REAL RIG: '+(report.errors.length?'BLOCKED '+JSON.stringify(report.errors[0]):`MEASURED ${report.frames} frames; max IK residual ${report.maxResidual.toFixed(4)}, knee difference ${report.maxKneeDiff.toFixed(4)}. Visual review REQUIRED.`);
 console.info('HAREWORKS_FORWARD_PROOF',report);frame=0;resetLegs();tick();
};
try{
 $('status').textContent='Loading exact nine-clip Hareworks model and forward gait parameters...';
 [profile]=await Promise.all([fetch('./profile.json').then(r=>{if(!r.ok)throw Error('PROFILE_FETCH_'+r.status);return r.json()})]);
 validateProfile();
 const loaded=await new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb');
 reference=loaded.scene;generated=cloneSkeleton(loaded.scene);
 reference.position.z=-PARENT_OFFSET/2;generated.position.z=PARENT_OFFSET/2;
 scene.add(reference,generated);reference.updateMatrixWorld(true);generated.updateMatrixWorld(true);
 const names=loaded.animations.map(x=>x.name);sourceClip=loaded.animations.find(x=>x.name===profile.clip);
 if(names.length!==9||!sourceClip)throw Error('NINE_CLIP_SOURCE_NOT_FOUND');
 if(Math.abs(sourceClip.duration-profile.clipDuration)>.001)throw Error('CLIP_DURATION_MISMATCH');
 refRig=getRig(reference);genRig=getRig(generated);
 refMixer=new THREE.AnimationMixer(reference);refMixer.clipAction(sourceClip).reset().play();refMixer.setTime(0);
 const allExcluded=Object.values(boneNames).flat();
 const removedTracks=sourceClip.tracks.filter(tr=>allExcluded.some(b=>tr.name.startsWith(b+'.')||tr.name.startsWith(b+'[')));
 if(removedTracks.length<4)throw Error('LEG_TRACK_FILTER_FAILED count='+removedTracks.length);
 const torsoClip=new THREE.AnimationClip('Walking_Woman_torso_only',sourceClip.duration,sourceClip.tracks.filter(tr=>!removedTracks.includes(tr)));
 // Exactly one seed frame, to anchor explicit leg rotational baselines.
 const seedMixer=new THREE.AnimationMixer(generated);seedMixer.clipAction(sourceClip).reset().play();seedMixer.setTime(0);
 for(const side of ['left','right'])for(const b of genRig.legs[side].chain)b.userData.seedQuat=b.quaternion.clone();
 seedMixer.stopAllAction();seedMixer.uncacheRoot(generated);
 genMixer=new THREE.AnimationMixer(generated);genMixer.clipAction(torsoClip).reset().play();genMixer.setTime(0);
 resetLegs();
 buildMarkers(refRig,{left:0x46c5fa,right:0xffc67b});buildMarkers(genRig,{left:0x46c5fa,right:0xffc67b});
 const bounds=new THREE.Box3().setFromObject(reference),bounds2=new THREE.Box3().setFromObject(generated);bounds.union(bounds2);grid.position.y=bounds.min.y;
 resize();active=true;playing=false;$('play').textContent='Play';tick();
 $('status').textContent='REAL SKINNED GLB LOADED · one reference woman clip vs generated leg IK. Run 30 fps check; visual review pending. No walking controller claim.';
}catch(e){$('status').textContent='BLOCKED_SOURCE_OR_RIG '+e.message;console.error(e)}
