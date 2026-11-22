/* v0.1.20. ONE moving Walking_Woman. REAL world-fixed skinned-sole contacts.
   Generated actor has NO AnimationMixer, NO per-frame original clip sampling,
   NO source leg joint tracks. Pelvis+upper motions are fitted once at startup.
   Leg joint rotations are freshly computed from anchored world foot targets. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {selectShoeWitnesses} from './shoe-witness.mjs';
import {fitSourceAnchoredTrack,evalSourceAnchoredTrack} from '../v0.1.9/upper-anchor.mjs';
import {independentPose,validateProfile} from '../v0.1.2/pose-kernel.mjs';
import {legAt,rotateY,validateFootProfile} from '../v0.1.3/foot-kernel.mjs';
import {kneeFromTarget} from './ik-core.mjs';
import {chooseSourceKnee,stableForwardPole} from './source-knee-governor.mjs';
import {mod1,clamp,followCamera,cadenceFor} from './contact-core.mjs';
import {sourceAt,SourceFootContact} from './foot-gait.mjs';
import {speedGait,blendMotion,transformSourceFoot,adjustAnkleForSpeed,rootStepDistance} from './speed-gait.mjs';
import {distalHeading} from './foot-heading.mjs';
import {inferVelocityContact,buildRootCurve,rootAt,kneeFlexion} from './root-motion.mjs';
const $=id=>document.getElementById(id),V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z),Q=()=>new THREE.Quaternion();
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const MODEL='../../../assets/hareworks/Hareworks-nine-clips.glb',BONES=74,CLIP='Walking_Woman';
const names={left:['mixamorigLeftUpLeg','mixamorigLeftLeg','Bone_017','mixamorigLeftFoot','mixamorigLeftToeBase'],right:['mixamorigRightUpLeg','mixamorigRightLeg','Bone_013','mixamorigRightFoot','mixamorigRightToeBase']};
const scene=new THREE.Scene();scene.background=new THREE.Color('#102030');scene.add(new THREE.HemisphereLight(0xf3f9ff,0x34485d,2.5));
const sun=new THREE.DirectionalLight(0xffffff,3.1);sun.position.set(-4,8,4);scene.add(sun);
const ground=new THREE.GridHelper(180,180,0x6b8696,0x354858);scene.add(ground);
for(let i=0;i<24;i++){const marker=new THREE.Mesh(new THREE.BoxGeometry(.075,.025,.075),new THREE.MeshBasicMaterial({color:i%2?0x42768b:0x6ea9a9}));marker.position.set(-1.3,.015,i*1.5);scene.add(marker)}
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3,3,2,-2,.01,300);const cameraOffsets={oblique:[-4.8,3.15,5.7],side:[-6.4,2.75,0],front:[0,2.9,7.0],top:[-.01,8,.01]};let view='oblique';
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.dampingFactor=.10;orbit.enablePan=false;orbit.enableRotate=true;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.90,0);camera.position.fromArray(cameraOffsets[view]);orbit.update();
function resize(){const w=Math.max(300,$('stage').clientWidth),h=Math.max(310,Math.min(690,Math.round(w*.76)));renderer.setSize(w,h,false);camera.top=2.2;camera.bottom=-2.2;camera.left=-2.2*w/h;camera.right=-camera.left;camera.updateProjectionMatrix()}
addEventListener('resize',resize);resize();const status=x=>$('status').textContent=x;
let actor=null,rig=null,legs=null,fit=null,pelvisProfile=null,footProfile=null,clipDuration=0,rest=null,patches=null,worldContacts=null,footOrient=null;
let ready=false,playing=true,speed=.52,stride=.66,phase=0,totalPhase=0,rootCurve=null,worldZ=0,frameTimer=performance.now(),accumulator=0,groundOffset=0,runFrames=0,report=null,lastStats=null;
let maxDrift=0,maxIK=0,maxPenetration=0,unreachable=0,contactCount=0,swingCount=0,transitions=0,failedFrames=0,maxTrailingExtensionDeficit=0,maxAnchorHeight=0;
let sourceSamples=null,sourceGaits=null,sourceGround=0,witnessCache=null,sourceSeamRepair={},shapeSum=0,shapeCount=0;
let previewReady=false,previewLegs=null,previewFault='',previewStage='GLB_LOAD',previewFaults=0;
let motionMode='LOADING',frameTickCount=0,lastPreviewError='',previewCycle=0;
let dynamicMotion=null; // v0.1.20 anatomical pre-IK targets never depend on foot yaw
let maxDistalKneeDelta=0,maxKneeFlexDelta=0,unstyledWitnessCache=null;
// Source knee alignment is separate from foot styling and world ankle pinning.
let priorWorldKnee={left:null,right:null},minSignedKneeCenterline=Infinity,
    maxKneeSourcePositionDelta=0,maxKneeWorldStep=0,kneeCenterlineCorrections=0;
let maxAnkleContactConflict=0,sourceKneeBaselineMismatches=0;
const REFERENCE_ROOT_UNITS_PER_CYCLE=1.224546;
const ownerAcceptance=false; // No synthetic or diagnostic result can grant visual acceptance.
function previewStatus(stage,why){
 if(motionMode==='PHYSICAL_GROUND_PINNING')previewCycle=totalPhase;
 previewStage=stage;previewFault=String(why);motionMode='PROCEDURAL_PREVIEW_UNPINNED';ready=false;playing=true;
 for(const p of Object.values(drawPins))p.visible=false;
 $('play').textContent='Pause';
 status('PHYSICAL_IK_BLOCKED '+stage+' '+previewFault+' · V0.1.9 PROCEDURAL WALK PREVIEW MOVING · NOT GROUND PINNED');
 $('metrics').textContent='PROCEDURAL PREVIEW ONLY, NOT CONTACT VALIDATION\n'+previewFault;
 if(actor)pinCamera();
 if(previewReady) Promise.resolve().then(()=>fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({schema:'hareworks-v0.1.20-startup-diagnostic',stage,error:previewFault,sourceSha256:SOURCE_SHA,
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
 dynamicMotion=blendMotion(dynamicMotion,speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE),dt);
 const nextCycle=previewCycle+(dynamicMotion.cadence*dt);
 worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;
 previewCycle=nextCycle;phase=mod1(previewCycle);
 frameBody(phase);
 const q=phase*clipDuration,yaw=independentPose(pelvisProfile,q).pelvisYaw;
 for(const [side,c] of Object.entries(previewLegs||{})){
  try{
   for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
   const H=wpos(c.up),K0=wpos(c.knee),v=legAt(footProfile,side,q);
   const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));
    target.fromArray(adjustAnkleForSpeed(H.toArray(),target.toArray(),side,dynamicMotion));
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
    const footFit=independentPose(pelvisProfile,q).feet[side];
    const original=wq(c.foot).clone(),fitted=runwayFootQ(c,footFit.toeVector,distalHeading(side,footFit,pelvisProfile));
    setWorldQ(c.foot,original.slerp(fitted,.52));actor.updateMatrixWorld(true);
   }
  }catch(err){
   previewFaults++;lastPreviewError=String(err.message||err);
  }
 }
 frameTickCount++;
 if(frameTickCount%40===0){
  $('metrics').textContent='V0.1.9 PROCEDURAL MOTION PREVIEW · NOT GROUND PINNED\n'+
   'phase '+phase.toFixed(3)+' root Z '+worldZ.toFixed(3)+' model '+SOURCE_SHA.slice(0,12)+'\n'+
   'PHYSICAL_CONTACT_GATE=BLOCKED '+previewStage+' '+previewFault+'\n'+
   'diagnostic solver warnings '+previewFaults+(lastPreviewError?' '+lastPreviewError:'');
 }
}

const drawPins={};for(const side of ['left','right']){const m=new THREE.Mesh(new THREE.SphereGeometry(.045,12,10),new THREE.MeshBasicMaterial({color:side==='left'?0x6bf5bf:0xb8fa83,depthTest:false}));m.renderOrder=15;scene.add(m);drawPins[side]=m;}
const wpos=b=>b.getWorldPosition(V());const wq=b=>b.getWorldQuaternion(Q());
function bonesOf(o){let found={};o.traverse(b=>{if(b.isBone){if(found[b.name])throw Error('DUPLICATE_BONE_'+b.name);found[b.name]=b}});if(Object.keys(found).length!==BONES)throw Error('EXPECTED_74_JOINTS_GOT_'+Object.keys(found).length);return found}
const skinned=o=>{let a=[];o.traverse(x=>{if(x.isSkinnedMesh){x.frustumCulled=false;a.push(x)}});return a};
function pickSolePatch(meshes,foot){const anchor=wpos(foot),near=[];
 for(let mi=0;mi<meshes.length;mi++){const m=meshes[mi],attribute=m.geometry.getAttribute('position');if(!attribute)continue;
  const step=Math.max(1,Math.floor(attribute.count/16000));for(let j=0;j<attribute.count;j+=step){const p=m.getVertexPosition(j,V());m.localToWorld(p);const d=p.distanceToSquared(anchor);if(d<.32*.32)near.push({mi,j,point:p.toArray(),d})}}
 if(near.length<15)throw Error('SKINNED_SOLE_VERTICES_NOT_FOUND_'+foot.name+'_'+near.length);
 near.sort((a,b)=>a.d-b.d);const candidates=near.slice(0,180),low=Math.min(...candidates.map(a=>a.point[1]));
 const chosen=candidates.filter(p=>p.point[1]<=low+.02).slice(0,20);if(chosen.length<4)throw Error('SOLE_PATCH_TOO_SMALL_'+foot.name);
 return {indexes:chosen.map(p=>({mi:p.mi,j:p.j})),low,count:chosen.length};
}
function soleWorld(meshes,patch){const out=V();for(const {mi,j} of patch.indexes){const m=meshes[mi];if(!m)throw Error('SOLE_SKINNED_MESH_MISMATCH');const p=m.getVertexPosition(j,V());m.localToWorld(p);out.add(p)}return out.multiplyScalar(1/patch.indexes.length)}
function witnessWorld(c,kind){
 if(kind==='ankle')return wpos(c.foot);
 const patch=kind==='heel'?c.heelPatch:kind==='toe'?c.toePatch:c.patch;
 return soleWorld(c.meshes,patch);
}
function splitFootPatches(meshes,foot,toe,all){
 // The v0.1.13 bug partitioned only 20 points from the ALREADY-selected sole.
 // Select the actual whole shoe through the skinned vertex weights and spatial bounds.
 const ankle=wpos(foot),toePos=wpos(toe),boneNames=new Set([foot.name,toe.name]);
 const profiles=[];
 for(let mi=0;mi<meshes.length;mi++){
  const m=meshes[mi],position=m.geometry.getAttribute('position'),skinIdx=m.geometry.getAttribute('skinIndex'),skinW=m.geometry.getAttribute('skinWeight');
  if(!position)continue;
  const bones=m.skeleton?.bones||[],footBones=new Set(bones.map((b,i)=>boneNames.has(b.name)?i:-1).filter(i=>i>=0));
  const step=Math.max(1,Math.floor(position.count/40000));
  for(let j=0;j<position.count;j+=step){
   const p=m.getVertexPosition(j,V());m.localToWorld(p);
   const r=Math.min(p.distanceTo(ankle),p.distanceTo(toePos));
   if(r>.42||p.y>ankle.y+.14||Math.abs(p.x-ankle.x)>.24)continue;
   let influence=0;
   if(skinIdx&&skinW&&footBones.size){
    for(let k=0;k<4;k++)if(footBones.has(skinIdx.getComponent(j,k)))influence+=skinW.getComponent(j,k);
   }
   profiles.push({mi,j,xyz:p.toArray(),influence,radialDistance:r});
  }
 }
 let last='',chosen=null;
 // Prefer genuine foot/toe SKIN influence; adapt the selection without inventing geometry.
 for(const gate of [.20,.10,.04,0]){
  const a=profiles.filter(p=>p.influence>=gate&&(gate>0||p.radialDistance<.33));
  if(a.length<24){last='INSUFFICIENT_FOOT_INFLUENCE gate='+gate+' count='+a.length;continue;}
  try{chosen=selectShoeWitnesses(a,toePos.clone().sub(ankle).toArray());
   chosen.evidence.weightThreshold=gate;
   chosen.evidence.sampledCandidateVertices=profiles.length;
   break;
  }catch(e){last=e.message;}
 }
 if(!chosen)throw Error('REAL_SHOE_GEOMETRY_CANNOT_SPLIT_'+foot.name+' '+last);
 console.info('REAL_SHOE_WITNESSES '+foot.name,chosen.evidence);
 return chosen;
}
// Accepted v0.1.9 toe-vector + ankle-yaw analytical orientation.
function runwayFootQ(c,toeVector,ankleYaw){
 const from=wpos(c.toe).sub(wpos(c.foot)),to=V(...toeVector);
 if(from.lengthSq()<1e-9||to.lengthSq()<1e-9)throw Error('RUNWAY_FOOT_VECTOR_DEGENERATE');
 const axis=to.normalize(),base=Q().setFromUnitVectors(from.normalize(),axis).multiply(wq(c.foot));
 const forward=V(0,0,1).applyQuaternion(base),desired=V(Math.sin(ankleYaw),0,Math.cos(ankleYaw));
 const fp=forward.addScaledVector(axis,-forward.dot(axis)),dp=desired.addScaledVector(axis,-desired.dot(axis));
 if(fp.lengthSq()<1e-7||dp.lengthSq()<1e-7)throw Error('RUNWAY_FOOT_HEADING_SINGULAR');
 fp.normalize();dp.normalize();
 const twist=Math.atan2(axis.dot(fp.clone().cross(dp)),fp.dot(dp));
 return Q().setFromAxisAngle(axis,twist).multiply(base).normalize();
}
function measuredFootQ(s){return Q().fromArray(s.q0).slerp(Q().fromArray(s.q1),s.qt).normalize()}
function setWorldQ(b,desired){b.quaternion.copy(wq(b.parent).invert().multiply(desired)).normalize()}
function turnToward(b,from,to){const origin=wpos(b),a=from.clone().sub(origin),c=to.clone().sub(origin);
 if(a.lengthSq()<1e-10||c.lengthSq()<1e-10)throw Error('IK_ZERO_BONE_VECTOR_'+b.name);
 const delta=Q().setFromUnitVectors(a.normalize(),c.normalize());setWorldQ(b,delta.multiply(wq(b)))}
const copyLocal=(b,p)=>{b.position.fromArray(p.p);b.quaternion.fromArray(p.q);b.scale.fromArray(p.s)};
function captureSeed(){const out={};for(const [name,b] of Object.entries(rig))out[name]={p:b.position.toArray(),q:b.quaternion.toArray(),s:b.scale.toArray()};return out}
function sampleFitted(source,mixer,sourceRig,count=120){const tracked=[sourceRig.mixamorigHips];sourceRig.mixamorigSpine.traverse(b=>{if(b.isBone)tracked.push(b)});
 const data=new Map(tracked.map(b=>[b.name,[]]));for(let i=0;i<count;i++){mixer.setTime(i*clipDuration/count);source.updateMatrixWorld(true);for(const b of tracked)data.get(b.name).push({quaternion:b.quaternion.toArray(),position:b.position.toArray()})}
 mixer.setTime(0);source.updateMatrixWorld(true);return Object.fromEntries([...data.entries()].map(([name,samples])=>[name,fitSourceAnchoredTrack(samples,12)]))}
function frameBody(p){const fitPhase=mod1(p),pelvis=independentPose(pelvisProfile,fitPhase*clipDuration),zero=independentPose(pelvisProfile,0);
 for(const [name,r] of Object.entries(rest))if(name in rig&&!(name in fit)&&name!=='mixamorigHips')copyLocal(rig[name],r);
 for(const [name,track] of Object.entries(fit)){const b=rig[name],s=evalSourceAnchoredTrack(track,fitPhase,12,1);b.quaternion.fromArray(s.quaternion).normalize();b.position.fromArray(s.position)}
 const hip=rig.mixamorigHips,p0=rest.mixamorigHips.p;hip.position.set(p0[0]+pelvis.pelvis[0]-zero.pelvis[0],p0[1]+pelvis.pelvis[1]-zero.pelvis[1],p0[2]+pelvis.pelvis[2]-zero.pelvis[2]);
 actor.position.z=worldZ;actor.position.y=-groundOffset;actor.updateMatrixWorld(true);}
function measuredWitnesses(){const out={};for(const side of ['left','right']){
 const c=legs[side];out[side]=Object.fromEntries(['ankle','heel','sole','toe'].map(k=>[k,witnessWorld(c,k).toArray()]));
 }return out;}
function contactTargets(){const out={};for(const side of ['left','right']){
 out[side]=worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion});
 }return out;}
function adjustReach(targets){
 // The source-v0.1.9 hip curve is a protected style constraint. Do NOT push pelvis
 // down by an arbitrary 0.14 units. The real IK gate records any genuine overreach.
 for(const side of ['left','right']){
  const c=legs[side],reach=wpos(c.up).distanceTo(V(...targets[side].ankleTarget))-(c.upperLength+c.lowerLength);
  if(reach>.003)unreachable++;
 }
}
function solveLeg(side,t){
 const c=legs[side],desiredQ=measuredFootQ(t.source),requested=V(...t.ankleTarget);
 // Start every step from the original v0.1.9 source phase, not the previous
 // frame's knee quaternion, contact error, or a history-dependent pole.
 for(const b of c.chain)copyLocal(b,rest[b.name]);actor.updateMatrixWorld(true);
 const H=wpos(c.up),K0=wpos(c.knee);
 const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;
 // Stable source-calibrated pole, fixed relative to model heading. No X sway.
 const pole=stableForwardPole(side,yaw);
 const hipCenterX=(wpos(legs.left.up).x+wpos(legs.right.up).x)*.5;
 const chosen=chooseSourceKnee({hip:H.toArray(),sourceHip:t.source.hip,
   sourceKnee:t.source.knee,sourceAnkle:t.source.ankle,
   contactAnkle:requested.toArray(),pole,upperLength:c.upperLength,
   lowerLength:c.lowerLength,side,centerX:hipCenterX,
   maxKneeDeviation:.025,minSideClearance:.012});
 // Keep the same ORIGINAL v0.1.9 two-link solve. Shoe style remains distal.
 const A=V(...chosen.ankle),K=V(...chosen.knee);
 turnToward(c.up,K0,K);actor.updateMatrixWorld(true);
 turnToward(c.knee,wpos(c.foot),A);actor.updateMatrixWorld(true);
 setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
 const kneeBefore=wpos(c.knee),hipBefore=wpos(c.up),ankleBefore=wpos(c.foot);
 const upperQ=c.up.quaternion.clone(),shinQ=c.knee.quaternion.clone();
 // Keep witness caching unstyled; foot-yaw and knee pose are independent.
 if(!unstyledWitnessCache)unstyledWitnessCache={};
 unstyledWitnessCache[side]=Object.fromEntries(['ankle','heel','sole','toe'].map(k=>[k,witnessWorld(c,k).toArray()]));
 // Exact approved v0.1.18 foot heading logic, unchanged.
 const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];
 const kneeToFoot=clamp(kneeBefore.x-ankleBefore.x,-.16,.16);
 const stylizedToe=[footFit.toeVector[0]+.20*kneeToFoot,footFit.toeVector[1],footFit.toeVector[2]];
 try{
  const original=wq(c.foot),fitted=runwayFootQ(c,stylizedToe,distalHeading(side,footFit,pelvisProfile));
  const styleBlend=t.planted?(chosen.unfulfilledContactDelta<.008?.35:.08):.52;
  setWorldQ(c.foot,original.slerp(fitted,styleBlend));actor.updateMatrixWorld(true);
 }catch(footError){
  setWorldQ(c.foot,desiredQ);previewFaults++;lastPreviewError=String(footError.message||footError);
 }
 const kneeChanged=kneeBefore.distanceTo(wpos(c.knee));
 const hipChanged=hipBefore.distanceTo(wpos(c.up));
 const ankleChanged=ankleBefore.distanceTo(wpos(c.foot));
 const kneeQuatChanged=Math.max(upperQ.angleTo(c.up.quaternion),shinQ.angleTo(c.knee.quaternion));
 if(Math.max(kneeChanged,hipChanged,ankleChanged,kneeQuatChanged)>1e-6)
  throw Error('DISTAL_FOOT_STYLE_MUTATED_KNEE_IK_'+side+'_'+kneeChanged.toExponential(2));
 maxDistalKneeDelta=Math.max(maxDistalKneeDelta,kneeChanged);
 const currentKnee=wpos(c.knee);
 const signedKnee=(side==='left'?1:-1)*(currentKnee.x-hipCenterX);
 minSignedKneeCenterline=Math.min(minSignedKneeCenterline,signedKnee);
 maxKneeSourcePositionDelta=Math.max(maxKneeSourcePositionDelta,chosen.kneeSourceError);
 maxAnkleContactConflict=Math.max(maxAnkleContactConflict,chosen.unfulfilledContactDelta);
 if(chosen.baselineMismatch)sourceKneeBaselineMismatches++;
 if(priorWorldKnee[side])maxKneeWorldStep=Math.max(maxKneeWorldStep,currentKnee.distanceTo(V(...priorWorldKnee[side])));
 priorWorldKnee[side]=currentKnee.toArray(); // evidence only, never used by solver
 const actual=witnessWorld(c,t.planted?t.pivot:'ankle'),drift=actual.distanceTo(V(...t.witnessTarget));
 const ankle=wpos(c.foot),reference=V(...t.source.ankle).add(actor.position);
 if(t.planted){const g=sourceGaits[side],u=mod1(phase-g.start)/g.duty;
  if(u>.70){const actualRelative=ankle.z-wpos(c.up).z,sourceRelative=t.source.ankle[2]-t.source.hip[2];
   maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,actualRelative-sourceRelative));}
  maxAnchorHeight=Math.max(maxAnchorHeight,t.badAnchorHeight||0);
 }
 const flex=kneeFlexion(c.upperLength,c.lowerLength,wpos(c.up).toArray(),ankle.toArray());
 const referenceFlex=kneeFlexion(c.upperLength,c.lowerLength,t.source.hip,t.source.ankle);
 if(Number.isFinite(flex)&&Number.isFinite(referenceFlex))
  maxKneeFlexDelta=Math.max(maxKneeFlexDelta,Math.abs(flex-referenceFlex));
 const shapeError=ankle.distanceTo(reference);shapeSum+=shapeError*shapeError;shapeCount++;
 if(t.planted){maxDrift=Math.max(maxDrift,drift);contactCount++}else swingCount++;
 const h=['heel','sole','toe'].map(k=>witnessWorld(c,k).y);
 maxPenetration=Math.max(maxPenetration,Math.max(0,...h.map(y=>-y)));
 maxIK=Math.max(maxIK,drift);
 drawPins[side].position.copy(V(...t.witnessTarget));drawPins[side].visible=$('showContacts').checked;
 drawPins[side].material.color.setHex(t.planted?0x65f2b7:0xffb65f);
 return {planted:t.planted,pivot:t.pivot,drift,sole:witnessWorld(c,'sole').toArray(),
  ankle:ankle.toArray(),target:t.ankleTarget,anchor:t.anchor,shapeError,reach:c.upperLength+c.lowerLength,
  kneeFlexionDeg:flex,sourceKneeFlexionDeg:referenceFlex,distalKneePositionChange:kneeChanged,
  sourceKneeError:chosen.kneeSourceError,contactConflict:chosen.unfulfilledContactDelta,
  kneeSideClearance:signedKnee,sourceReferenceFallback:chosen.baselineMismatch};
}
function physicsStep(dt){
 // Capture last physically solved geometry BEFORE frameBody restores the source-calibration skeleton.
 witnessCache=unstyledWitnessCache?{...unstyledWitnessCache}:measuredWitnesses();
 dynamicMotion=blendMotion(dynamicMotion,speedGait(speed,rootCurve.stride),dt);
 const cadence=cadenceFor(speed,dynamicMotion.stride),newPhase=totalPhase+cadence*dt;
 worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);
 totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);
 const targets=contactTargets();adjustReach(targets);const feet={};
 for(const side of ['left','right']){
  const c=worldContacts[side],t=targets[side];
  if(t.planted&&c.transitions!==lastContactTransition[side]&&t.anchor){
   lastContactTransition[side]=c.transitions;
   const touchdown={side,z:t.anchor[2],phase:totalPhase};
   const prev=footfallHistory.at(-1);
   if(prev&&prev.side!==side)latestStepSpacing=Math.abs(touchdown.z-prev.z);
   footfallHistory.push(touchdown);if(footfallHistory.length>16)footfallHistory.shift();
  }
 }
 for(const side of ['left','right'])feet[side]=solveLeg(side,targets[side]);
 transitions=worldContacts.left.transitions+worldContacts.right.transitions;runFrames++;
 lastStats={phase,worldTravelZ:worldZ,speed,cadence,worldRootZ:actor.position.z,feet,transitions,
 maxSkinnedStanceDrift:maxDrift,maxSkinnedTargetError:maxIK,maxNewFloorPenetration:maxPenetration,
 sourceAnkleRms:Math.sqrt(shapeSum/Math.max(1,shapeCount)),reachAdjustments:unreachable,
 contactFrames:contactCount,swingFrames:swingCount,solvedIKPerFrame:true,generatedAnimationMixerCount:0};
 return lastStats;
}
let footfallHistory=[],lastContactTransition={left:-1,right:-1},latestStepSpacing=null;
const trackedFollow=V(0,.90,0);
function pinCamera(){
 if(!actor)return;
 const desired=actor.position.clone().add(V(0,.90,0)),delta=desired.sub(trackedFollow);
 orbit.target.add(delta);camera.position.add(delta);trackedFollow.add(delta);orbit.update();
}
function setCameraPreset(k){
 view=k;const world=actor?actor.position:V();trackedFollow.copy(world).add(V(0,.90,0));
 orbit.target.copy(trackedFollow);camera.position.fromArray(cameraOffsets[k]).add(world);
 camera.up.set(0,1,0);orbit.update();camera.updateProjectionMatrix();
}
function renderMetrics(prefix='LIVE'){if(!lastStats)return;const feet=lastStats.feet;
 $('metrics').textContent=`${prefix} · DYNAMIC SOURCE-ANCHORED WALKING_WOMAN · WORLD IK\nTravel Z ${worldZ.toFixed(3)} u, phase ${(phase*100).toFixed(1)}%, cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s, planned step ${(dynamicMotion?.stepDistance||stride/2).toFixed(3)} u, measured step ${latestStepSpacing===null?"pending":latestStepSpacing.toFixed(3)} u, full cycle ${(dynamicMotion?.stride||stride).toFixed(3)}\nLEFT ${feet.left.pivot} ${feet.left.planted?'PLANTED':'SWING'}, drift ${feet.left.drift.toFixed(4)} u\nRIGHT ${feet.right.pivot} ${feet.right.planted?'PLANTED':'SWING'}, drift ${feet.right.drift.toFixed(4)} u\nSkinned support error ${maxDrift.toFixed(5)} u, floor penetration ${maxPenetration.toFixed(5)} u\nSource ankle RMS ${lastStats.sourceAnkleRms.toFixed(5)} u; knee reach warnings ${unreachable}\nContact transitions ${transitions}; source stance L ${(sourceGaits.left.duty*100).toFixed(1)}%, R ${(sourceGaits.right.duty*100).toFixed(1)}%\nSOURCE_KNEE_RESTORED clearance ${Number.isFinite(minSignedKneeCenterline)?minSignedKneeCenterline.toFixed(4):"pending"} u · source knee Δ ${maxKneeSourcePositionDelta.toFixed(4)} u · maximum contact conflict ${maxAnkleContactConflict.toFixed(4)} u · max step ${maxKneeWorldStep.toFixed(4)} u\nFOOT_YAW_TO_KNEE_IK_COUPLING ${maxDistalKneeDelta.toFixed(8)} u · max knee vs source flexion ${maxKneeFlexDelta.toFixed(2)}°\nANIMATION MIXER ON VISIBLE ACTOR: ZERO · source joints NOT replayed`;
}
function clearStats(){priorWorldKnee={left:null,right:null};minSignedKneeCenterline=Infinity;
 maxKneeSourcePositionDelta=0;maxKneeWorldStep=0;kneeCenterlineCorrections=0;maxAnkleContactConflict=0;sourceKneeBaselineMismatches=0;
 maxDistalKneeDelta=0;maxKneeFlexDelta=0;footfallHistory=[];lastContactTransition={left:-1,right:-1};latestStepSpacing=null;maxDrift=0;maxIK=0;maxPenetration=0;unreachable=0;contactCount=0;swingCount=0;transitions=0;runFrames=0;lastStats=null;shapeSum=0;shapeCount=0;maxTrailingExtensionDeficit=0;maxAnchorHeight=0;}
function initRun(){if(!ready)return;
 phase=0;totalPhase=0;worldZ=0;dynamicMotion=speedGait(speed,rootCurve.stride);
 clearStats();frameBody(0);unstyledWitnessCache=null;witnessCache=measuredWitnesses();const next={};
 for(const side of ['left','right'])next[side]=new SourceFootContact({samples:sourceSamples[side],gait:sourceGaits[side],
  sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q),
  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});
 worldContacts=next;physicsStep(0);pinCamera();renderMetrics('RESET');
}
$('play').onclick=()=>{
 if(!ready&&!previewReady){status('BLOCKED_NO_RUNNING_CONTROLLER · model is visible only');return;}
 playing=!playing;$('play').textContent=playing?'Pause':'Play';
 if(motionMode!=='PHYSICAL_GROUND_PINNING'){
  status((playing?'PREVIEW_RUNNING':'PREVIEW_PAUSED')+' · ORIGINAL V0.1.9 PROCEDURAL GAIT · UNPINNED · '+previewFault);
 }else status(playing?'PHYSICAL_WORLD_IK_RUNNING':'PHYSICAL_WORLD_IK_PAUSED');
};
$('reset').onclick=()=>{
 if(motionMode!=='PHYSICAL_GROUND_PINNING'){
  if(!previewReady){status('RESET_UNAVAILABLE_NO_CONTROLLER');return;}
  previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);for(const p of Object.values(drawPins))p.visible=false;
  status('V0.1.9 PROCEDURAL PREVIEW RESET · UNPINNED · '+previewFault);pinCamera();return;
 }
 try{initRun();status('PHYSICAL WORLD RUN RESET · actor, anchors and orbit synchronized');}
 catch(e){previewStatus('PHYSICAL_RESET',e.message||String(e));}
};
$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};
function updateMotionStatus(){
 if(motionMode==='PROCEDURAL_PREVIEW_UNPINNED'){
  $('motionStatus').textContent='UNPINNED DYNAMIC GEOMETRY PREVIEW · target stride '+(dynamicMotion?.stride||0).toFixed(3)+' u/full cycle · no contact proof';
 }else $('motionStatus').textContent=`DYNAMIC SOURCE-ANCHORED FOOT PATH · full-cycle root stride ${(dynamicMotion?.stride||stride).toFixed(3)} u, planned half-cycle step ${(dynamicMotion?.stepDistance||stride/2).toFixed(3)} u · cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s · crossover ${(dynamicMotion?.crossover||0).toFixed(3)} u`;

}
updateMotionStatus();
$('showContacts').onchange=()=>{
 for(const side of ['left','right'])drawPins[side].visible=ready&&motionMode==='PHYSICAL_GROUND_PINNING'&&$('showContacts').checked;
};
for(const k of Object.keys(cameraOffsets))$(k).onclick=()=>setCameraPreset(k);
$('resetCamera').onclick=()=>setCameraPreset('oblique');
$('export').onclick=()=>{if(!report){status('Run real skinned foot-pin audit first.');return}const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='hareworks-woman-accepted-v019-world-pin-v0.1.20.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),6000)};
$('audit').onclick=async()=>{if(!ready){status('PHYSICAL_AUDIT_UNAVAILABLE · V0.1.9 PREVIEW DOES NOT PROVE GROUND PINNING · '+previewFault);return;}const was=playing;playing=false;
 status('Auditing measured contacts across 3 cycles, 120 Hz; source resemblance is a separate gate…');const oldSpeed=speed;speed=.52;
 try{initRun();const cameraOffsetBefore=camera.position.clone().sub(actor.position);const n=Math.ceil((3/cadenceFor(speed,speedGait(speed,stride).stride))*120);
  const worst={left:0,right:0},previous={left:null,right:null},pivotCounts={},samples=[];
  let anchorMaxStep=0;
  for(let i=0;i<n;i++){
   const m=physicsStep(1/120);
   for(const side of ['left','right']){
    const f=m.feet[side];pivotCounts[side+':'+f.pivot]=(pivotCounts[side+':'+f.pivot]||0)+1;
    if(f.planted){worst[side]=Math.max(worst[side],f.drift);
      if(previous[side]&&previous[side].pivot===f.pivot)
       anchorMaxStep=Math.max(anchorMaxStep,Math.hypot(...f.anchor.map((x,j)=>x-previous[side].anchor[j])));
      previous[side]={pivot:f.pivot,anchor:f.anchor?.slice()};}
    else previous[side]=null;
   }
   if(i%15===0)samples.push({time:i/120,phase:m.phase,worldZ:m.worldTravelZ,
    left:m.feet.left,right:m.feet.right,cameraTrackingOffset:cameraOffsets[view]});
   if(i%35===0)await new Promise(requestAnimationFrame);
  }
  pinCamera();const cameraError=camera.position.clone().sub(actor.position).distanceTo(cameraOffsetBefore);
  const physicalPass=worst.left<=.025&&worst.right<=.025&&maxPenetration<=.020&&anchorMaxStep<=1e-8&&worldZ>speedGait(speed,stride).stride*2.70&&cameraError<1e-6&&unreachable===0&&maxTrailingExtensionDeficit<.055&&maxAnchorHeight<.026&&maxDistalKneeDelta<=1e-6&&maxKneeFlexDelta<6&&minSignedKneeCenterline>=.012&&maxKneeSourcePositionDelta<=.025&&maxAnkleContactConflict<=.025&&sourceKneeBaselineMismatches===0;
  report={schema:'hareworks-woman-accepted-v019-world-pin-v0.1.20',sourceSha256:SOURCE_SHA,
    sourceClip:CLIP,rigBones:74,sourceContactMethod:sourceGaits,sourceSeamRepair,
    strideCycle:stride,actualCyclesTested:n/120*cadenceFor(speed,dynamicMotion.stride),
    nominalForwardAdvance:worldZ,generatedAnimationMixerCount:0,calibrationOnlySourceMixer:true,
    oneVisibleCharacter:true,rootMovementIsWorldTravel:true,cameraFixedFollow:true,
    stanceAnchorCoordinateSystem:'WORLD',contactPatch:'skinned heel/sole/toe witnesses',physicsRateHz:120,
    sampledFrames:n,worldTravelZ:worldZ,referenceRigWasNotDisplayed:true,
    solver:'accepted v0.1.9 ankle/pelvis curves + inverse phase-dependent support-root + world-space contact IK',
    maxSkinnedSoleDriftPerSide:worst,maximumContactAnchorTranslation:anchorMaxStep,
    maxFootPenetration:maxPenetration,maxIKResidual:maxIK,reachAdjustments:unreachable,
    cameraWorldFollowError:cameraError,touchdownTransitions:transitions,contactPivotCounts:pivotCounts,
    sourceAnkleRms:Math.sqrt(shapeSum/Math.max(shapeCount,1)),sourcePoseSamples:360,
    rootMethod:rootCurve.method,rootStridePerFullCycle:rootCurve.stride,
    speedResponsiveGait:dynamicMotion,referenceV019FootOrientationBlend:.52,
    cameraOrbitEnabled:orbit.enableRotate&&orbit.enableZoom,
    maxTrailingExtensionDeficit,maxAnchorHeight,
    contactGate:physicalPass?'PASS':'WARN',resemblanceGate:'OWNER_VISUAL_REVIEW_PENDING',
    status:physicalPass?'PHYSICAL_CONTACT_PASS_STYLE_OWNER_PENDING':'PHYSICAL_CONTACT_WARN_OWNER_REVIEW_REQUIRED',
    ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,
    kneeIKDecoupledFromFootYaw:true,maxDistalKneeDelta,maxKneeFlexDelta,
    minSignedKneeCenterline,maxKneeSourcePositionDelta,maxKneeWorldStep,
    kneeCenterlineCorrections:0,kneeSourceAuthority:'stationary character-local anterior knee poles; stateless 60-frame source shape envelope',maxAnkleContactConflict,sourceKneeBaselineMismatches,observations:samples};
  // Real GLB physical checks at three distinct speeds. Changing speed is not a
  // pass unless contact drift, reach and actual root advance are acceptable.
  const speedMatrix=[];
  for(const requested of [.30,.52,.80]){
   speed=requested;initRun();
   const expected=speedGait(requested,stride),steps=Math.ceil((1.20/expected.cadence)*120);
   for(let j=0;j<steps;j++){
    physicsStep(1/120);
    if(j%40===0)await new Promise(requestAnimationFrame);
   }
   const realTime=steps/120;
   speedMatrix.push({requested,realTime,travel:worldZ,measuredLastFootfall:latestStepSpacing,
    stride:dynamicMotion.stride,cadence:dynamicMotion.cadence,
    maxDrift,maxPenetration,unreachable,
    rootMeanSpeed:worldZ/realTime,
    status:'REAL_SKINNED_GLTF_SOLVER',
    pass:maxDrift<=.025&&maxPenetration<=.020&&unreachable===0&&
      Math.abs(worldZ/realTime-requested)<.17});
  }
  report.speedMatrix=speedMatrix;
  report.dynamicSpeedGate=speedMatrix.every(x=>x.pass)?'PASS':'WARN';
  if(report.dynamicSpeedGate!=='PASS'){
   report.contactGate='WARN';report.status='DYNAMIC_SPEED_PHYSICAL_GATES_WARN_OWNER_REVIEW_REQUIRED';
  }
  speed=oldSpeed;initRun();
  $('metrics').textContent=`${report.status}\nCONTACT: heel/sole/toe anchors L ${worst.left.toFixed(5)}, R ${worst.right.toFixed(5)} u (limit .025)\nSource ankle RMS ${report.sourceAnkleRms.toFixed(5)} u (advisory, NOT gait approval)\nFloor intrusion ${maxPenetration.toFixed(5)} u; IK warnings ${unreachable}\n3 measured cycles, 120 Hz, traveling root ${worldZ.toFixed(3)} u\nSTYLE GATE: must resemble v0.1.9 Walking_Woman in owner's inspection`;
  try{const response=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
   if(!response.ok)throw Error('HTTP_'+response.status);const receipt=await response.json();status(report.status+' · evidence saved '+receipt.sha256.slice(0,12));}
  catch(e){status(report.status+' · autosave unavailable '+e.message+' · Export still works')}
 }catch(e){status('SOURCE_GAIT_AUDIT_ERROR '+e.message);console.error(e)}
 finally{const summary=$('metrics').textContent;speed=oldSpeed;
  if(motionMode==='PHYSICAL_GROUND_PINNING'){
   try{initRun();$('metrics').textContent=summary;}
   catch(e){previewStatus('PHYSICAL_AUDIT_RESTART',e.message||String(e));}
  }
  playing=was;$('play').textContent=playing?'Pause':'Play';}

};
function frame(now){requestAnimationFrame(frame);
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
requestAnimationFrame(frame);
try{
 const response=await fetch(MODEL,{cache:'no-store'});if(!response.ok)throw Error('SOURCE_HTTP_'+response.status);const bytes=await response.arrayBuffer();if(bytes.byteLength!==6784896)throw Error('SOURCE_SIZE_'+bytes.byteLength);
 const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(sha!==SOURCE_SHA)throw Error('SOURCE_SHA_MISMATCH '+sha);
 const [p,f]=await Promise.all([fetch('../v0.1.2/motion-profile.json',{cache:'no-store'}).then(x=>x.json()),fetch('../v0.1.3/foot-profile.json',{cache:'no-store'}).then(x=>x.json())]);validateProfile(p);validateFootProfile(f);pelvisProfile=p;footProfile=f;
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);const sourceClip=gltf.animations.find(a=>a.name===CLIP);if(!sourceClip||gltf.animations.length!==9)throw Error('SOURCE_WALKING_WOMAN_REQUIRED');clipDuration=sourceClip.duration;
 const source=cloneSkeleton(gltf.scene);actor=cloneSkeleton(gltf.scene);const srcRig=bonesOf(source);rig=bonesOf(actor);const mixer=new THREE.AnimationMixer(source);mixer.clipAction(sourceClip).reset().play();mixer.setTime(0);source.updateMatrixWorld(true);
 for(const [name,b] of Object.entries(rig)){const a=srcRig[name];b.position.copy(a.position);b.quaternion.copy(a.quaternion);b.scale.copy(a.scale)}actor.updateMatrixWorld(true);rest=captureSeed();
 scene.add(actor);actor.updateMatrixWorld(true); // verified 3D model remains visible even if calibration later fails
 $('identity').textContent='v0.1.14 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · SOURCE MATH AND CONTACT AUDIT PENDING';
 try{fit=sampleFitted(source,mixer,srcRig);}catch(fitError){
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
 previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);
 console.info('V019_REFERENCE_LEG_MOTION_LIVENESS_PASS',previewLegAmplitude);
 previewStage='SHOE_WITNESS_CALIBRATION';
 if(previewFault)throw Error(previewFault);
 status('V0.1.9 PROCEDURAL REFERENCE GAIT MOVEMENT VERIFIED · calibrating physical contacts…');
 const actorMeshes=skinned(actor),refMeshes=skinned(source);if(actorMeshes.length!==refMeshes.length||actorMeshes.length<1)throw Error('SKINNED_MESH_1_TO_1_REQUIRED');
 legs={};patches={};for(const [side,arr] of Object.entries(names)){const b=arr.map(n=>rig[n]);if(b.some(x=>!x))throw Error('LEG_JOINTS_MISSING_'+side);const [up,knee,bridge,foot,toe]=b;
  if(up.parent!==rig.mixamorigHips||knee.parent!==up||bridge.parent!==knee||foot.parent!==bridge||toe.parent!==foot)throw Error('LEG_CHAIN_TOPOLOGY_'+side);
  const patch=pickSolePatch(actorMeshes,foot),sole=soleWorld(actorMeshes,patch),soleLocal=foot.worldToLocal(sole.clone());
  const upperLength=wpos(up).distanceTo(wpos(knee)),lowerLength=wpos(knee).distanceTo(wpos(foot));if(upperLength<.20||lowerLength<.20)throw Error('ANATOMICAL_LINKS_INVALID_'+side);
  if(Math.abs(upperLength-footProfile[side].upperLength)>.009||Math.abs(lowerLength-footProfile[side].lowerLength)>.009)throw Error('SOURCE_FOOT_PROFILE_LENGTH_MISMATCH_'+side);
  const split=splitFootPatches(actorMeshes,foot,toe,patch),heelPatch=split.heel,toePatch=split.toe,solePatch=split.sole;
  legs[side]={side,chain:b,up,knee,bridge,foot,toe,patch:solePatch,heelPatch,toePatch,meshes:actorMeshes,soleLocal,upperLength,lowerLength};patches[side]=solePatch;}
 // Measure actual heel/toe/sole/ankle positions and orientation from the immutable source clip.
 const N=360;sourceSamples={left:[],right:[]};let absoluteGround=Infinity;
 for(let i=0;i<N;i++){
  mixer.setTime(clipDuration*i/N);source.updateMatrixWorld(true);
  for(const side of ['left','right']){
   const c=legs[side],foot=srcRig[c.foot.name],q=wq(foot).toArray();
   const sourceHip=wpos(srcRig[c.up.name]),accepted=legAt(footProfile,side,clipDuration*i/N),
     acceptedYaw=independentPose(pelvisProfile,clipDuration*i/N).pelvisYaw;
   const acceptedAnkle=sourceHip.clone().add(V(...rotateY(accepted.ankleLocal,acceptedYaw)));
   const obs={phase:i/N,ankle:acceptedAnkle.toArray(),hip:sourceHip.toArray(),knee:wpos(srcRig[c.knee.name]).toArray(),
    heel:soleWorld(refMeshes,c.heelPatch).toArray(),
    sole:soleWorld(refMeshes,c.patch).toArray(),toe:soleWorld(refMeshes,c.toePatch).toArray(),q};
   sourceSamples[side].push(obs);absoluteGround=Math.min(absoluteGround,obs.heel[1],obs.toe[1]);
  }
 }
 // Preserve original sub-duration source samples unchanged; do not invent a seam morph.
 sourceSeamRepair={left:{repaired:false},right:{repaired:false}};
 sourceGround=absoluteGround;
 previewStage='ARCHIVED_V019_ROOT_CONTACTS';
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
 updateMotionStatus();
 groundOffset=absoluteGround;mixer.stopAllAction();mixer.uncacheRoot(source); // calibration only, NEVER drives actor
 actor.position.y=-groundOffset;scene.add(actor);actor.updateMatrixWorld(true);
 const footPhases=Object.fromEntries(Object.entries(sourceGaits).map(([side,g])=>
  [side,{contactStart:g.start,sourceStanceDuty:g.duty,threshold:g.threshold,seam:sourceSeamRepair[side]}]));
 previewStage='REAL_GLB_32_STEP_STARTUP_SMOKE';
 ready=true;initRun();
 const startZ=worldZ;for(let i=0;i<32;i++)physicsStep(1/120);
 const travelled=worldZ-startZ;
 if(!Number.isFinite(travelled)||travelled<.04)throw Error('NO_OBSERVABLE_WORLD_TRAVEL_AT_STARTUP '+travelled);
 if(!Number.isFinite(wpos(rig.mixamorigHips).x))throw Error('NONFINITE_ACTUAL_SKINNED_BODY');
 initRun();motionMode='PHYSICAL_GROUND_PINNING';playing=true;pinCamera();
 status('PHYSICAL IK CONTROLLER STARTED · 32 REAL SKINNED STEPS EXECUTED · owner gait approval pending');
 $('identity').textContent=`v0.1.20 ACCEPTED V019 SOURCE ROOT + HONEST RUNNING PREVIEW · SHA ${SOURCE_SHA} · exact Walking_Woman · 74 bones · two-bone world IK · one actor · root WORLD travel · source mixer CALIBRATION ONLY · inferred heel/toe contact ${JSON.stringify(footPhases)} · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
}catch(e){if(actor&&!actor.parent){scene.add(actor);actor.updateMatrixWorld(true);}
 console.error('REAL_MODEL_CALIBRATION_BLOCKED stage='+previewStage,e);
 previewStatus(previewStage,e.message||String(e));
 if(!previewReady){playing=false;status('CALIBRATION_AND_PREVIEW_UNAVAILABLE '+previewStage+' '+String(e.message||e));}
}
