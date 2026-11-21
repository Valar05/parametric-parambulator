/* Hareworks Backward Woman Style Transfer v0.2.0.
 * Three source clips calibrate the generated result ONCE. The generated rig
 * has NO AnimationMixer and NO runtime source clip playback. Its backwards
 * base is reconstructed from source samples; woman-forward minus normal-
 * forward local bone deltas are contact-phase-warped onto it. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CLIPS,CONTACT,phaseTriplet,transferPose,sampleBone,quatAngle} from './transfer-kernel.mjs';
const $=id=>document.getElementById(id);
const MODEL_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const MODEL_URL='../../../assets/hareworks/Hareworks-nine-clips.glb';
const SAMPLES=240,SEP=2.5;
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const scene=new THREE.Scene();scene.background=new THREE.Color('#101a25');
scene.add(new THREE.HemisphereLight(0xf1f8ff,0x222f40,2.4));
const light=new THREE.DirectionalLight(0xffffff,3.2);light.position.set(-4,7,5);scene.add(light);
const floor=new THREE.GridHelper(14,28,0x5e7486,0x354753);scene.add(floor);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-3.4,3.4,2.2,-2.2,.01,100);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;
orbit.minZoom=.6;orbit.maxZoom=3.5;orbit.target.set(0,.98,0);
const cam={side:[-7,3.1,.05],front:[0,2.3,9],oblique:[-5.8,3.8,5],top:[-.02,9,.02]};
function cameraAt(name){camera.position.set(...cam[name]);camera.up.set(0,1,0);camera.zoom=1;orbit.target.set(0,.98,0);camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(290,Math.min(570,Math.round(w*.68)));renderer.setSize(w,h,false);
 camera.left=-2.2*w/h;camera.right=-camera.left;camera.top=2.2;camera.bottom=-2.2;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const c of Object.keys(cam))$(c).onclick=()=>cameraAt(c);
cameraAt('side');resize();
const scenes={},mixers={},rigs={},sourceClips={},samples={};let generated=null,generatedRig=null,ready=false,playing=true;
let phase=0,last=performance.now(),lastAudit=null,visualMode='back',sourceInfo=null;
function say(t){$('status').textContent=t}
function rigOf(root){const bones={};root.traverse(o=>{if(o.isBone){if(bones[o.name])throw Error('DUPLICATE_RIG_BONE '+o.name);bones[o.name]=o}});
 if(Object.keys(bones).length!==74)throw Error('RIG_NOT_74_BONES '+Object.keys(bones).length);
 for(const name of ['mixamorigHips','mixamorigSpine','mixamorigHead','mixamorigLeftFoot','mixamorigRightFoot','mixamorigLeftLeg','mixamorigRightLeg'])if(!bones[name])throw Error('ESSENTIAL_BONE_MISSING '+name);
 return bones}
function makeClipSample(name){const original=sourceClips[name],root=scenes[name],mixer=mixers[name],bones=rigs[name];
 const names=Object.keys(bones),out={sampleCount:SAMPLES,duration:original.duration,bones:{}};
 for(const bone of names)out.bones[bone]={quat:[],pos:[]};
 for(let i=0;i<SAMPLES;i++){
  mixer.setTime(original.duration*i/SAMPLES);root.updateMatrixWorld(true);
  for(const bone of names){const b=bones[bone];out.bones[bone].quat.push(b.quaternion.toArray());out.bones[bone].pos.push(b.position.toArray())}
 }
 mixer.setTime(0);root.updateMatrixWorld(true);return out;
}
function world(b){return b.getWorldPosition(V())}
function applyStyle(at=phase){
 if(!ready)return null;
 const gain=Number($('strength').value)/100;
 const m=transferPose(samples,at,gain);
 for(const [name,p] of Object.entries(m.bones)){
   const b=generatedRig[name];if(!b)throw Error('GENERATED_BONE_MISSING '+name);
   b.quaternion.fromArray(p.quat).normalize();b.position.fromArray(p.pos);
 }
 generated.updateMatrixWorld(true);
 const t=sourceClips.Walk_Backward.duration*m.phases.backward;
 mixers.Walk_Backward.setTime(t);scenes.Walk_Backward.updateMatrixWorld(true);
 mixers.Walking.setTime(sourceClips.Walking.duration*m.phases.normal);
 mixers.Walking_Woman.setTime(sourceClips.Walking_Woman.duration*m.phases.woman);
 scenes.Walking.updateMatrixWorld(true);scenes.Walking_Woman.updateMatrixWorld(true);
 $('phaseValue').textContent=`${Math.round(at*100)}% · back ${m.phases.backward.toFixed(3)} / normal ${m.phases.normal.toFixed(3)} / woman ${m.phases.woman.toFixed(3)}`;
 return m;
}
function setMode(mode){visualMode=mode;
 for(const [key,root] of Object.entries(scenes))root.visible=(mode==='back'?key==='Walk_Backward':key!=='Walk_Backward');
 if(generated)generated.visible=mode==='back';
 $('backMode').setAttribute('aria-pressed',String(mode==='back'));
 $('sourceMode').setAttribute('aria-pressed',String(mode==='sources'));
 $('leftCaption').textContent=mode==='back'?'SOURCE · normal backward':'SOURCE · normal forward';
 $('rightCaption').textContent=mode==='back'?'RESULT · woman-style backward':'SOURCE · woman forward';
 $('comparison').textContent=mode==='back'?'B + [W − N] with phase-mapped local quaternion differences':'Input difference: Walking → Walking_Woman';
}
function addMark(name,kind,error,rate,t,stats){
 if(!Number.isFinite(error))throw Error('AUDIT_NONFINITE '+name+' '+kind);
 const key=name+':'+kind,o=stats[key]??={bone:name,measurement:kind,count:0,sumSquares:0,max:0,worst:{t:0,rateHz:rate}};
 o.count++;o.sumSquares+=error*error;if(error>o.max){o.max=error;o.worst={t,rateHz:rate}}
}
function runAudit(exportNow=false){
 if(!ready)return;
 const wasPlaying=playing;playing=false;const previous=phase;
 const s={};const trials=[];let maxHipZ=0,sourceStyleCount=0,maxAngularStep=0,seamJump=0;
 try{
 for(const rate of [30,60,120]){
   let prior=null,maxStep=0,count=0;
   for(let i=0;i<Math.floor(sourceClips.Walk_Backward.duration*rate)*2;i++){
    const t=i/(2*rate),p=t/sourceClips.Walk_Backward.duration;if(p>=1)continue;
    const applied=applyStyle(p);const ref=rigs.Walk_Backward,gen=generatedRig;
    // Compare the styled root channel with the independently sampled
    // original backward clip, not with its own generated value.
    const originalInterpolated=sampleBone(samples.Walk_Backward,'mixamorigHips',p).pos[2];
    if(Math.abs(originalInterpolated-gen.mixamorigHips.position.z)>1e-8)throw Error('HIP_Z_LOCK_BROKEN');
    maxHipZ=Math.max(maxHipZ,Math.abs(gen.mixamorigHips.position.z-originalInterpolated));
    sourceStyleCount=Math.max(sourceStyleCount,applied.nonzeroBoneCount);
    const displayOffset=V(0,0,SEP);
    for(const [tag,bone] of [['left-ankle','mixamorigLeftFoot'],['right-ankle','mixamorigRightFoot'],['left-knee','mixamorigLeftLeg'],['right-knee','mixamorigRightLeg'],['hips','mixamorigHips'],['head','mixamorigHead']]){
     const source=world(ref[bone]).add(displayOffset),derived=world(gen[bone]);
     addMark(tag,'worldPosition',source.distanceTo(derived),rate,t,s);
    }
    const current=gen.mixamorigHips.quaternion.clone();
    if(prior)maxStep=Math.max(maxStep,THREE.MathUtils.radToDeg(prior.angleTo(current)));
    prior=current;count++;
   }
   maxAngularStep=Math.max(maxAngularStep,maxStep);trials.push({rateHz:rate,sampledPoses:count,pelvisMaxAngularStepDeg:maxStep});
 }
 const a=applyStyle(0),first=Object.fromEntries(Object.entries(a.bones).map(([k,v])=>[k,v.quat]));
 const b=applyStyle(1-1e-7);
 seamJump=Math.max(...Object.keys(first).map(k=>THREE.MathUtils.radToDeg(quatAngle(first[k],b.bones[k].quat))));
 const measured=Object.values(s).map(o=>({bone:o.bone,measurement:o.measurement,samples:o.count,rms:Math.sqrt(o.sumSquares/o.count),max:o.max,worst:o.worst}));
 measured.sort((a,b)=>b.rms-a.rms);
 const warnings=[];
 if(maxHipZ>1e-7)warnings.push('BACKWARD_PELVIS_Z_CHANGED');
 if(sourceStyleCount<10)warnings.push('STYLE_DELTA_MISSING');
 if(measured.filter(x=>x.bone.endsWith('ankle')).some(x=>x.rms>.11))warnings.push('POSSIBLE_FOOT_CONTACT_DRIFT');
 if(seamJump>8)warnings.push('CYCLE_SEAM_ANGLE_JUMP');
 const report={schema:'hareworks-three-clip-backward-style-v0.2.0',status:warnings.length?'MEASURED_WITH_WARNINGS_OWNER_REVIEW':'MEASURED_OWNER_REVIEW_REQUIRED',
  modelSha256:MODEL_SHA,threeSourceClips:CLIPS,sourceDurations:Object.fromEntries(CLIPS.map(k=>[k,sourceClips[k].duration])),
  comparison:'local delta = inverse(normal forward) * woman forward; generated = normal backward * delta',
  phaseMapping:'two-leg contact-event piecewise normalized phase warp; heuristic skinned witness anchors',anchors:CONTACT,
  styleGain:Number($('strength').value)/100,sourceBoneCount:74,calibrationSamplesPerClip:SAMPLES,
  generatedSourceAnimationTracks:0,rootBackwardDirectionPreserved:true,hipZDrift:maxHipZ,
  styleAffectedBones:sourceStyleCount,continuity:{rates:trials,maxHipAngularStepDeg:maxAngularStep,seamMaxBoneStepDeg:seamJump},
  measuredJointDifferences:measured,warnings,ownerAccepted:false};
 lastAudit=report;
 $('audit').textContent='AUDIT: '+report.status+' · 30/60/120Hz half-frame samples, '+sourceStyleCount+' nonzero style bones.\n'+
  measured.slice(0,7).map(r=>r.bone+' position RMS '+r.rms.toFixed(4)+' / max '+r.max.toFixed(4)).join('\n')+
  '\nCycle seam max joint change '+seamJump.toFixed(2)+'°; pelvis Z protection '+maxHipZ.toFixed(8)+' units.';
 say(warnings.length?'Backward style transfer measured with warnings; inspect derived gait and exported report.':'Three-way transfer measured; visual review required, not accepted automatically.');
 if(exportNow)download(report);
 }catch(e){say('BLOCKED_REAL_RIG_AUDIT '+e.message);console.error(e)}
 finally{phase=previous;try{applyStyle(phase)}catch(e){console.error(e)}playing=wasPlaying}
}
function download(obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='hareworks-backward-style-v0.2.0-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000)}
$('auditButton').onclick=()=>runAudit(true);
$('export').onclick=()=>lastAudit?download(lastAudit):say('Run real-rig audit before exporting evidence.');
$('strength').oninput=()=>{$('strengthValue').textContent=$('strength').value+'%';if(ready){applyStyle(phase);say('Style gain changed; repeat the audit for this version of the motion.')}};
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';phase=Number($('phase').value)/1000;applyStyle(phase)};
$('backMode').onclick=()=>setMode('back');$('sourceMode').onclick=()=>setMode('sources');
function draw(now){requestAnimationFrame(draw);const dt=Math.min(.075,Math.max(0,(now-last)/1000));last=now;
 if(ready){if(playing){phase=(phase+dt/sourceClips.Walk_Backward.duration)%1;try{applyStyle(phase)}catch(e){playing=false;say('POSE_ERROR '+e.message);console.error(e)}}
 $('phase').value=Math.round(phase*1000)}orbit.update();renderer.render(scene,camera)}
requestAnimationFrame(draw);
function showError(e){say('SOURCE_OR_RIG_ERROR '+(e?.message||String(e)));console.error(e)}
window.addEventListener('unhandledrejection',e=>showError(e.reason));
try{
 const r=await fetch(MODEL_URL,{cache:'no-store'});if(!r.ok)throw Error('GLB_HTTP_'+r.status);
 const buffer=await r.arrayBuffer();if(buffer.byteLength!==6784896)throw Error('GLB_BYTE_COUNT_'+buffer.byteLength);
 if(!crypto?.subtle)throw Error('BROWSER_CRYPTO_SHA256_UNAVAILABLE');
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==MODEL_SHA)throw Error('SOURCE_GLB_SHA_MISMATCH '+digest);
 const gltf=await new GLTFLoader().parseAsync(buffer,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('EXPECTED_NINE_SOURCE_CLIPS');
 for(const key of CLIPS){const clip=gltf.animations.find(x=>x.name===key);if(!clip)throw Error('SOURCE_CLIP_MISSING_'+key);sourceClips[key]=clip;scenes[key]=cloneSkeleton(gltf.scene);scene.add(scenes[key]);rigs[key]=rigOf(scenes[key]);
   mixers[key]=new THREE.AnimationMixer(scenes[key]);mixers[key].clipAction(clip).reset().play();mixers[key].setTime(0);
 }
 generated=cloneSkeleton(gltf.scene);generatedRig=rigOf(generated);scene.add(generated);
 for(const key of CLIPS){samples[key]=makeClipSample(key);if(Object.keys(samples[key].bones).join('|')!==Object.keys(samples.Walking?.bones||samples[key].bones).join('|'))throw Error('SOURCE_BONE_TOPOLOGY_MISMATCH')}
 // Return all models to pristine source time zero before generated runtime.
 for(const key of CLIPS)mixers[key].setTime(0);
 scenes.Walk_Backward.position.z=-SEP/2;scenes.Walking.position.z=-SEP/2;
 scenes.Walking_Woman.position.z=SEP/2;generated.position.z=SEP/2;
 const check=transferPose(samples,.33,1),baseline=transferPose(samples,.33,0);
 if(check.nonzeroBoneCount<10||quatAngle(check.bones.mixamorigSpine.quat,baseline.bones.mixamorigSpine.quat)<.002)throw Error('THREE_WAY_STYLE_DELTA_NOT_APPLIED');
 sourceInfo={styleBoneCount:check.nonzeroBoneCount,peakBone:check.peakBone,peakDeltaDeg:THREE.MathUtils.radToDeg(check.peakDeltaRad),modelSha256:MODEL_SHA};
 floor.position.y=new THREE.Box3().setFromObject(scenes.Walk_Backward).min.y;
 ready=true;setMode('back');applyStyle(0);
 $('identity').textContent=`v0.2.0 · source SHA ${MODEL_SHA.slice(0,12)} · three-clips sampled ${SAMPLES} phases · generated no clip mixer · repo ${new URLSearchParams(location.search).get('commit')?.slice(0,10)||'Termux readback pending'} · script ${new URLSearchParams(location.search).get('scriptSha')?.slice(0,12)||'unknown'}`;
 $('audit').textContent=`THREE-WAY SOURCE READY: ${check.nonzeroBoneCount} bones differ between normal and woman forward; strongest local delta ${check.peakBone} (${sourceInfo.peakDeltaDeg.toFixed(1)}°). Derived backward uses all these differences.`;
 say('SKINNED MODEL VERIFIED · Walking vs Walking_Woman style → Walk_Backward; actual derived gait playing, needs visual acceptance.');
 resize();cameraAt('side');runAudit(false);
}catch(e){showError(e)}
