/* Hareworks v0.2.6. Four independent source-measured dynamic style overlays.
 * Two independently evaluated procedural backward rigs: accepted v0.2.2
 * baseline and gated candidate. NO source AnimationMixer on either.
 * Walking and Walking_Woman mixers exist solely on hidden calibration clones.
 */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CLIP,ROOT,deriveInPlace,poseInPlace,angleDeg} from './inplace-kernel.mjs';
import {LAYERS,PHASE_OFFSET,stylePose,zeroGains,groupOf} from './style-layers.mjs';
import {comparisonPoint,collectComparisonPositions} from './comparison-space.mjs';
const SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const PRIORS_SHA='f631eaf0bb48bb81afa9b451cf2191aa4c98b07bd768f2574caaaa28938ffebe';
const GLB='../../../assets/hareworks/Hareworks-nine-clips.glb';
const $=id=>document.getElementById(id),V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const SEP=2.8,BACK_SAMPLES=720,STYLE_SAMPLES=360;
const scene=new THREE.Scene();scene.background=new THREE.Color('#111b26');
scene.add(new THREE.HemisphereLight(0xf1f8ff,0x2a3f50,2.6));
const lamp=new THREE.DirectionalLight(0xffffff,3.3);lamp.position.set(-4,7,4);scene.add(lamp);
const floor=new THREE.GridHelper(14,28,0x5b7183,0x344658);scene.add(floor);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-4,4,2.2,-2.2,.05,100);
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.minZoom=.55;orbit.maxZoom=3.5;orbit.target.set(0,.9,0);
const views={side:[-7,3.2,0],front:[0,2.5,9],oblique:[-6,4.2,5],top:[-.01,9,.01]};
function cameraAt(key){camera.position.set(...views[key]);camera.up.set(0,1,0);camera.zoom=1;orbit.target.set(0,.9,0);camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(300,Math.min(610,Math.round(w*.70)));renderer.setSize(w,h,false);camera.left=-2.4*w/h;camera.right=-camera.left;camera.top=2.4;camera.bottom=-2.4;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const k of Object.keys(views))$(k).onclick=()=>cameraAt(k);cameraAt('side');resize();
let baseline=null,candidate=null,baseRig=null,candidateRig=null;
let originalClips={},sourceClones={},sourceMixers={},backwardSource=null,backwardPlan=null,styleNormal=null,styleWoman=null;
let sourceReady=false,ready=false,playing=true,busy=false,phase=0,last=performance.now(),gateRevision=0;
let allowed=zeroGains(),lastAudit=null,researchPriors=null,controlSampleAudit=null;
const status=s=>$('status').textContent=s;
function rigOf(root){const o={};root.traverse(b=>{if(b.isBone){if(o[b.name])throw Error('DUPLICATE_BONE '+b.name);o[b.name]=b}});if(Object.keys(o).length!==74||!o[ROOT])throw Error('RIG_NOT_74_BONES');return o}
const wpos=b=>b.getWorldPosition(V());
function copyPose(rig,root,pose){for(const [name,channels] of Object.entries(pose.bones)){const b=rig[name];if(!b)throw Error('MISSING_GENERATED_BONE_'+name);b.quaternion.fromArray(channels.quaternion).normalize();b.position.fromArray(channels.position);b.scale.fromArray(channels.scale)}root.updateMatrixWorld(true)}
function captureClip(clipName,n){const root=sourceClones[clipName],mixer=sourceMixers[clipName],duration=originalClips[clipName].duration,rig=rigOf(root),bones={};
 for(const name of Object.keys(rig))bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<n;i++){mixer.setTime(duration*i/n);root.updateMatrixWorld(true);for(const [name,b] of Object.entries(rig)){const s=bones[name];s.pos.push(b.position.toArray());s.quat.push(b.quaternion.toArray());s.scale.push(b.scale.toArray())}}
 mixer.setTime(0);root.updateMatrixWorld(true);return {sampleCount:n,duration,bones};}
function rawRootEndpoint(){const t=originalClips[CLIP].tracks.find(x=>x.name===ROOT+'.position');if(!t)return null;const n=t.times.length,k=t.getValueSize();return {lastTime:t.times[n-1],last:Array.from(t.values.slice((n-1)*k,n*k)),prior:Array.from(t.values.slice((n-2)*k,(n-1)*k))}}
function calibrateBackward(){const raw=backwardSource;const attempts=[],starts=[.93,.92,.905,.89,.875,.86];let best=null;
 for(const seam of starts){try{const plan=deriveInPlace(raw,seam);let cost=0;
 for(const hz of [30,60,120]){const limit=hz===30?20:hz===60?12:7;let prior=poseInPlace(raw,plan,0).bones,max=0;
  for(let i=1;i<=Math.ceil(raw.duration*hz);i++){const pose=poseInPlace(raw,plan,Math.min(1-1e-7,i/(raw.duration*hz))).bones;for(const name of Object.keys(pose))max=Math.max(max,angleDeg(prior[name].quaternion,pose[name].quaternion));prior=pose}
  cost+=max/limit;}
 attempts.push({seam,cost});if(best===null||cost<best.cost)best={cost,plan};if(cost<=3)break;
 }catch(e){attempts.push({seam,error:e.message})}}
 if(!best)throw Error('BACKWARD_CALIBRATION_NO_VALID_SEAM '+JSON.stringify(attempts));
 best.plan.candidateSeams=attempts;return best.plan;
}
function baselinePose(p){return poseInPlace(backwardSource,backwardPlan,p)}
function experimentalPose(p,gains=allowed){return stylePose(baselinePose(p),styleNormal,styleWoman,p,gains)}
function displayAt(p){if(!ready)return;phase=((p%1)+1)%1;copyPose(baseRig,baseline,baselinePose(phase));copyPose(candidateRig,candidate,experimentalPose(phase));$('phaseValue').textContent=Math.round(100*phase)+'%';}
function zeroAudit(){displayAt(0);const errors=[];for(const name of Object.keys(baseRig)){const a=baseRig[name],b=candidateRig[name];const q=angleDeg(a.quaternion.toArray(),b.quaternion.toArray()),loc=a.position.distanceTo(b.position),s=a.scale.distanceTo(b.scale),world=comparisonPoint(baseline,a,V).distanceTo(comparisonPoint(candidate,b,V));if(q>.001||loc>1e-6||s>1e-6||world>1e-4)errors.push({bone:name,rotation:q,position:loc,scale:s,world})}if(errors.length)throw Error('PHASE_ZERO_STYLE_MUST_MATCH_ACCEPTED '+JSON.stringify(errors.slice(0,4)));return {pass:true,joints:74}}
const markers=['mixamorigLeftFoot','mixamorigRightFoot','mixamorigLeftToeBase','mixamorigRightToeBase','mixamorigLeftLeg','mixamorigRightLeg','mixamorigHead'];
const feet=['mixamorigLeftFoot','mixamorigRightFoot'];
function collectPositions(rig,root){return collectComparisonPositions(rig,root,markers,V)}
function readRequest(){const r=zeroGains();for(const key of LAYERS){r[key]=$('on'+key[0].toUpperCase()+key.slice(1)).checked?Number($(key).value)/100:0;}return r}
function updateControls(){for(const key of LAYERS){const C=key[0].toUpperCase()+key.slice(1);$('val'+C).textContent=$(key).value+'%';$('actual'+C).textContent=allowed[key]?'APPLIED '+(allowed[key]*100).toFixed(1)+'% after safeguards':'OFF / rejected / not requested';}}
for(const key of LAYERS){const C=key[0].toUpperCase()+key.slice(1);$(key).oninput=()=>{$('val'+C).textContent=$(key).value+'%';};$('on'+C).onchange=()=>{status('Style request changed. Run Test and apply; accepted backward remains locked.')}}
function getFootProfiles(){const observations=[];for(let i=0;i<90;i++){const p=i/90;copyPose(baseRig,baseline,baselinePose(p));const o=collectPositions(baseRig,baseline);observations.push({phase:p,y:feet.map(f=>o[f].y)})}const min=feet.map((_,j)=>Math.min(...observations.map(o=>o.y[j])));return {min,notes:'low-foot witnesses only; not force contact'}}
// Use a separate, measured candidate rig. No source animation action ever
// drives it. Reference remains accepted procedural v0.2.2 equations.
async function measure(gains,rates=[30,60],yieldFrames=false){const footProfiles=window.__footProfile;const met={maxContactAnkle:0,maxContactToe:0,maxSwingAnkle:0,maxRootZ:0,maxRootX:0,maxHead:0,maxFloorPenetration:0,maxStepAdded:0,lowestContactCount:0,sampleCount:0,perRate:[],worst:[],maxWorldDifference:0};
 const fail=(kind,err,at,bone,rate)=>{if(err>(met['max'+kind]??0))met['max'+kind]=err;met.worst.push({kind,error:err,phase:at,bone,rateHz:rate})};
 for(const hz of rates){const n=Math.ceil(backwardSource.duration*hz)*2;let priorB=null,priorC=null,maxBaseStep=0,maxStyleStep=0;
  for(let i=0;i<n;i++){const p=i/(2*hz*backwardSource.duration);if(p>=1)break;
   const b=baselinePose(p),c=stylePose(b,styleNormal,styleWoman,p,gains);copyPose(baseRig,baseline,b);copyPose(candidateRig,candidate,c);
   const bp=collectPositions(baseRig,baseline),cp=collectPositions(candidateRig,candidate);
   for(let j=0;j<2;j++){const side=j?'Right':'Left',f='mixamorig'+side+'Foot',toe='mixamorig'+side+'ToeBase';const dist=bp[f].distanceTo(cp[f]),dtoe=bp[toe].distanceTo(cp[toe]);
    const planted=bp[f].y<=footProfiles.min[j]+.028;
    if(planted){met.lowestContactCount++;fail('ContactAnkle',dist,p,f,hz);fail('ContactToe',dtoe,p,toe,hz)}else fail('SwingAnkle',dist,p,f,hz);
    // A new foot penetrating materially below its approved trajectory is prohibited.
    fail('FloorPenetration',Math.max(0,bp[f].y-cp[f].y-.025),p,f,hz);
   }
   fail('RootZ',Math.abs(b.bones[ROOT].position[2]-c.bones[ROOT].position[2]),p,ROOT,hz);
   fail('RootX',Math.abs(b.bones[ROOT].position[0]-c.bones[ROOT].position[0]),p,ROOT,hz);
   fail('Head',bp.mixamorigHead.distanceTo(cp.mixamorigHead),p,'mixamorigHead',hz);
   if(priorB){for(const bone of Object.keys(b.bones)){const ba=angleDeg(priorB[bone].quaternion,b.bones[bone].quaternion),ca=angleDeg(priorC[bone].quaternion,c.bones[bone].quaternion);maxBaseStep=Math.max(maxBaseStep,ba);maxStyleStep=Math.max(maxStyleStep,ca)}}
   priorB=b.bones;priorC=c.bones;met.sampleCount++;
   if(yieldFrames&&i%16===0)await new Promise(resolve=>requestAnimationFrame(resolve));
  }
  met.perRate.push({rateHz:hz,maxBaselineJointStepDeg:maxBaseStep,maxCandidateJointStepDeg:maxStyleStep});
  fail('StepAdded',Math.max(0,maxStyleStep-maxBaseStep),1,'full-rig',hz);
 }
 const b0=baselinePose(0),b1=baselinePose(1-1e-7),c0=stylePose(b0,styleNormal,styleWoman,0,gains),c1=stylePose(b1,styleNormal,styleWoman,1-1e-7,gains);
 met.seamBase=0;met.seamCandidate=0;met.seamPosition=0;
 for(const name of Object.keys(c0.bones)){met.seamBase=Math.max(met.seamBase,angleDeg(b0.bones[name].quaternion,b1.bones[name].quaternion));met.seamCandidate=Math.max(met.seamCandidate,angleDeg(c0.bones[name].quaternion,c1.bones[name].quaternion));met.seamPosition=Math.max(met.seamPosition,Math.hypot(...c0.bones[name].position.map((v,j)=>v-c1.bones[name].position[j])))}
 met.comparisonSpace='each character model-local, visually separated scene origins removed';met.viewerSeparationExcluded=SEP;
 const limits={maxContactAnkle:.050,maxContactToe:.070,maxSwingAnkle:.150,maxRootZ:1e-8,maxRootX:.045,maxHead:.200,maxFloorPenetration:.020,maxStepAdded:8.0,seamRotationAddedDeg:1.0,seamPosition:.002};
 const checks=[['stance ankle',met.maxContactAnkle,limits.maxContactAnkle],['stance toe',met.maxContactToe,limits.maxContactToe],['swing ankle',met.maxSwingAnkle,limits.maxSwingAnkle],['backward root Z',met.maxRootZ,limits.maxRootZ],['lateral root sway',met.maxRootX,limits.maxRootX],['head model-space shift',met.maxHead,limits.maxHead],['new downward foot penetration',met.maxFloorPenetration,limits.maxFloorPenetration],['extra joint step',met.maxStepAdded,limits.maxStepAdded],['extra seam rotation',Math.max(0,met.seamCandidate-met.seamBase),limits.seamRotationAddedDeg],['seam position',met.seamPosition,limits.seamPosition]];
 met.rejections=checks.filter(([name,actual,max])=>actual>max+1e-10).map(([name,actual,max])=>({name,actual,max}));
 met.worst=met.worst.sort((a,b)=>b.error-a.error).slice(0,22);met.limits=limits;met.pass=met.rejections.length===0&&met.lowestContactCount>0;
 return met;
}
async function applyRequested(){if(!ready||busy)return;busy=true;playing=false;$('play').textContent='Play';$('apply').disabled=true;
 const requested=readRequest(),accepted=zeroGains(),trials=[];
 try{
  for(const key of LAYERS){if(requested[key]===0)continue;
   let passGain=0,best=null;const tested=[];
   // Bounded adaptive search. Each candidate is judged against ALL enabled
   // earlier layers. Never silently apply a rejected combination.
   for(const fraction of [1,.8,.6,.4,.25,.125,.0625]){
    const g={...accepted,[key]:requested[key]*fraction};const m=await measure(g,[30,60],false);
    tested.push({requested:g[key],pass:m.pass,reasons:m.rejections.slice(0,3)});
    if(m.pass&&g[key]>passGain){passGain=g[key];best=m;break}
   }
   if(passGain>0.02){accepted[key]=passGain;trials.push({layer:key,requested:requested[key],applied:passGain,status:'GATED_PASS',tested})}
   else trials.push({layer:key,requested:requested[key],applied:0,status:'REJECTED_SAFETY_GATE',tested});
   $('audit').textContent='Testing '+key+'…\n'+trials.map(x=>x.layer+': '+x.status+' '+Math.round(x.applied*100)+'%').join('\n');
   await new Promise(resolve=>requestAnimationFrame(resolve));
  }
  // The final composition must independently pass ALL three rates.
  let final=await measure(accepted,[30,60,120],true);
  if(!final.pass){const before={...accepted};for(const key of LAYERS.slice().reverse()){
   if(!accepted[key])continue;const requestedGain=accepted[key];
   for(const fraction of [.75,.5,.25,0]){accepted[key]=requestedGain*fraction;final=await measure(accepted,[30,60,120],true);if(final.pass)break}
   if(final.pass)break;
  }
   if(!final.pass){accepted.pelvis=0;accepted.legs=0;accepted.torso=0;accepted.arms=0;final=await measure(accepted,[30,60,120],true)}
   trials.push({status:'FINAL_COMBINATION_REQUIRES_ATTENUATION',previous:before,actual:{...accepted}});
  }
  if(!final.pass)throw Error('SAFE_COMBINATION_NOT_FOUND '+JSON.stringify(final.rejections));
  allowed={...accepted};const actualLocalStart=zeroAudit();displayAt(phase);
  lastAudit={comparisonSpace:'model-local via root.worldToLocal',zeroStrengthControl:controlSampleAudit,schema:'hareworks-gated-backward-style-lab-v0.2.6',sourceSha256:SHA,sourceClips:['Walk_Backward','Walking','Walking_Woman'],ownerAcceptedBackward:'v0.2.2 immutable',ownerAcceptedForward:'v0.1.9 immutable',referenceStudy:'v0.2.3 74-bone research; static offsets excluded',stylePhaseOffset:PHASE_OFFSET,uploadedResearchReportSHA256:PRIORS_SHA,analysisSource:'owner-exported v0.2.3 JSON embedded byte-for-byte',
   approvedBackwardMotionPlaybackTracks:0,generatedSourceAnimationTracks:0,sourceCalibrationOnly:true,sourceBones:74,sourceSamples:{backward:BACK_SAMPLES,normal:STYLE_SAMPLES,woman:STYLE_SAMPLES},requested,applied:{...allowed},trials,fullRateAudit:final,zeroFrame:actualLocalStart,
   styleAcceptedByOwner:false,sourceModelUnchanged:true,originalGaitsUnchanged:true,manualVisualApprovalRequired:true};
  updateControls();$('audit').textContent='LAB SAFETY GATE PASS · Owner review pending\n'+trials.map(x=>x.layer?`${x.layer}: requested ${Math.round(x.requested*100)}%, applied ${Math.round(x.applied*100)}% (${x.status})`:x.status).join('\n')+
   `\nMeasured ${final.sampleCount} frame/half-frame poses at 30/60/120 Hz. Low-foot witnesses ${final.lowestContactCount}.\nStance ankle max ${final.maxContactAnkle.toFixed(4)}, stance toe ${final.maxContactToe.toFixed(4)}, swing ankle ${final.maxSwingAnkle.toFixed(4)}, head Δ ${final.maxHead.toFixed(4)}.\nWorst joint-step addition ${final.maxStepAdded.toFixed(3)}°. Phase-zero 74/74 exact. Accepted base not modified.`;
  status('REAL-RIG STYLE TRIAL APPLIED WITH GUARDS · owner visual review required');
  try{const r=await fetch('./style-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastAudit)});if(!r.ok)throw Error('evidence receiver HTTP '+r.status);const receipt=await r.json();status('REAL-RIG STYLE TRIAL GATED · JSON saved in phone state ('+receipt.sha256.slice(0,12)+') · owner review required')}
  catch(e){status('STYLE TRIAL GATED · phone evidence autosave unavailable: '+e.message+' · use Export JSON');}
 }catch(e){allowed=zeroGains();displayAt(phase);status('STYLE_GUARD_REJECTED '+e.message);$('audit').textContent='No unsafe candidate applied.\n'+e.message;console.error(e)}
 finally{busy=false;$('apply').disabled=false;updateControls()}
}
$('apply').onclick=()=>applyRequested();
$('reset').onclick=()=>{if(busy)return;allowed=zeroGains();for(const key of LAYERS)$('on'+key[0].toUpperCase()+key.slice(1)).checked=false;updateControls();displayAt(phase);status('APPROVED v0.2.2 BASELINE RESTORED · no style applied');};
const download=data=>{const b=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(b),a=document.createElement('a');a.href=url;a.download='hareworks-backward-style-lab-v0.2.6-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),6000)};
$('export').onclick=()=>lastAudit?download(lastAudit):status('No tested real-rig style candidate yet. Test layers first.');
$('play').onclick=()=>{if(!ready||busy)return;playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{if(!ready||busy)return;playing=false;$('play').textContent='Play';displayAt(Number($('phase').value)/1000)};
function render(now){requestAnimationFrame(render);const dt=Math.min(.07,Math.max(0,(now-last)/1000));last=now;
 if(ready&&!busy&&playing){try{displayAt((phase+dt/backwardSource.duration)%1);$('phase').value=Math.round(phase*1000)}catch(e){playing=false;status('POSE_FAILURE '+e.message);console.error(e)}}orbit.update();renderer.render(scene,camera)}requestAnimationFrame(render);
window.addEventListener('unhandledrejection',e=>{status('BROWSER_ERROR '+(e.reason?.message||String(e.reason)));console.error(e.reason)});
try{
 const response=await fetch(GLB,{cache:'no-store'});if(!response.ok)throw Error('MODEL_HTTP_'+response.status);const bytes=await response.arrayBuffer();if(bytes.byteLength!==6784896)throw Error('SOURCE_SIZE_'+bytes.byteLength);
 const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(actual!==SHA)throw Error('SOURCE_SHA_MISMATCH '+actual);
 const priorsResponse=await fetch('./research-priors.json',{cache:'no-store'});if(!priorsResponse.ok)throw Error('OWNER_RESEARCH_PRIORS_HTTP_'+priorsResponse.status);
 const priorsBytes=await priorsResponse.arrayBuffer(),priorsHex=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',priorsBytes))).map(x=>x.toString(16).padStart(2,'0')).join('');
 if(priorsHex!==PRIORS_SHA)throw Error('OWNER_RESEARCH_PRIORS_SHA_MISMATCH');
 researchPriors=JSON.parse(new TextDecoder().decode(priorsBytes));
 if(researchPriors.schema!=='hareworks-forward-style-research-v0.2.3'||researchPriors.sourceModelSHA256!==SHA||researchPriors.perBone.length!==74||Math.abs(researchPriors.alignment.womanPhaseOffset-PHASE_OFFSET)>1e-9)throw Error('OWNER_RESEARCH_PRIORS_CONTRACT_MISMATCH');
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);
 if(gltf.animations.length!==9)throw Error('SOURCE_NINE_CLIPS_REQUIRED');
 for(const key of [CLIP,'Walking','Walking_Woman']){const clip=gltf.animations.find(c=>c.name===key);if(!clip)throw Error('MISSING_SOURCE_CLIP '+key);originalClips[key]=clip;sourceClones[key]=cloneSkeleton(gltf.scene);sourceMixers[key]=new THREE.AnimationMixer(sourceClones[key]);sourceMixers[key].clipAction(clip).reset().play();}
 backwardSource=captureClip(CLIP,BACK_SAMPLES);styleNormal=captureClip('Walking',STYLE_SAMPLES);styleWoman=captureClip('Walking_Woman',STYLE_SAMPLES);
 backwardPlan=calibrateBackward();sourceReady=true;
 baseline=cloneSkeleton(gltf.scene);candidate=cloneSkeleton(gltf.scene);baseRig=rigOf(baseline);candidateRig=rigOf(candidate);baseline.position.z=-SEP/2;candidate.position.z=SEP/2;scene.add(baseline,candidate);
 floor.position.y=new THREE.Box3().setFromObject(baseline).min.y;
 ready=true;displayAt(0);const zero=zeroAudit();window.__footProfile=getFootProfiles();displayAt(0);
 // Independent negative control: ZERO style must have no displacement at all
 // despite the 2.8-unit visual separation of the rendered models.
 controlSampleAudit=await measure(zeroGains(),[30,60,120],false);
 if(!controlSampleAudit.pass || controlSampleAudit.maxContactAnkle>1e-5 || controlSampleAudit.maxContactToe>1e-5 || controlSampleAudit.maxSwingAnkle>1e-5 || controlSampleAudit.maxHead>1e-5 || controlSampleAudit.maxRootX>1e-8 || controlSampleAudit.maxRootZ>1e-8){
  throw Error('ZERO_GAIN_COMPARISON_SPACE_REGRESSION '+JSON.stringify(controlSampleAudit.rejections));
 }
 displayAt(0);
 $('identity').textContent=`v0.2.6 · source ${SHA} · research SHA ${PRIORS_SHA} · clips Walking/Walking_Woman/Walk_Backward · 74 bones · no generated clip mixer · locked base v0.2.2 · pinned commit ${new URLSearchParams(location.search).get('commit')||'UNKNOWN'} · entry SHA ${new URLSearchParams(location.search).get('scriptSha')||'UNKNOWN'}`;
 $('audit').textContent=`EXACT BACKWARD BASELINE LOADED · 74/74 joint t0 equality\nVERIFIED OWNER v0.2.3 REPORT SHA ${PRIORS_SHA.slice(0,12)} · research phase alignment: ${PHASE_OFFSET.toFixed(6)} · backward seam starts ${backwardPlan.seamStart.toFixed(3)} · root Δ ${(backwardPlan.cycleTravel[2]).toFixed(4)} removed.\nZERO-STYLE SAFETY CONTROL VERIFIED (separation excluded, 30/60/120 Hz) · All four style layers OFF until separately tested. Sampling from exact GLB: backward ${BACK_SAMPLES}, normal/woman ${STYLE_SAMPLES} each.\nSource raw terminal key: ${JSON.stringify(rawRootEndpoint())}`;
 updateControls();status('ZERO-STYLE SPACE GATE PASS · accepted backward baseline playing · enable and test style layers');cameraAt('side');resize();
}catch(e){status('MODEL_OR_RIG_BLOCKED '+e.message);console.error(e)}
