/* Hareworks v0.2.3 source-only forward gait style research. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {alignPhase,compareClips,poseAt,mod1,angleDeg,conjugate,multiply,rms,range} from './analysis-core.mjs';
const $=id=>document.getElementById(id),V=()=>new THREE.Vector3(),Q=()=>new THREE.Quaternion();
const SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6', URL_GLB='../../../assets/hareworks/Hareworks-nine-clips.glb';
const CLIPS=['Walking','Walking_Woman'],N=360,SEP=2.9;
const scene=new THREE.Scene();scene.background=new THREE.Color('#111c28');scene.add(new THREE.HemisphereLight(0xeaf3ff,0x344459,2.6));
const light=new THREE.DirectionalLight(0xffffff,3.3);light.position.set(-4,7,6);scene.add(light);
const grid=new THREE.GridHelper(13,26,0x6d8699,0x364d60);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-4,4,2.5,-2.5,.01,100),orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.target.set(0,.95,0);orbit.minZoom=.55;orbit.maxZoom=3.5;
const cameraPos={side:[-7,3.4,0],front:[0,2.5,9],oblique:[-5.5,3.5,5.5],top:[-.01,9,.01]};
function cameraAt(key){camera.position.set(...cameraPos[key]);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(290,Math.min(570,Math.round(w*.67)));renderer.setSize(w,h,false);camera.left=-2.3*w/h;camera.right=-camera.left;camera.top=2.3;camera.bottom=-2.3;camera.updateProjectionMatrix();orbit.update()}
window.addEventListener('resize',resize);for(const key of Object.keys(cameraPos))$(key).onclick=()=>cameraAt(key);cameraAt('side');resize();
const models={},rigs={},mixers={},clips={},samples={},rootTrend={};let ready=false,playing=false,phase=0,last=performance.now(),report=null,alignment=null;
const status=s=>$('status').textContent=s;
function rigOf(root){const bones={};root.traverse(x=>{if(x.isBone){if(bones[x.name])throw Error('DUPLICATE_BONE_'+x.name);bones[x.name]=x}});if(Object.keys(bones).length!==74)throw Error('EXPECTED_74_BONES_'+Object.keys(bones).length);for(const name of ['mixamorigHips','mixamorigHead','mixamorigLeftFoot','mixamorigRightFoot','mixamorigLeftArm','mixamorigRightArm','mixamorigLeftForeArm','mixamorigRightForeArm','mixamorigLeftHand','mixamorigRightHand'])if(!bones[name])throw Error('REQUIRED_JOINT_MISSING_'+name);return bones}
function capture(key){const root=models[key],rig=rigs[key],mixer=mixers[key],clip=clips[key],boneNames=Object.keys(rig);
 const data={count:N,boneNames,duration:clip.duration,bones:{},rootPositions:[],rootOrientations:[]};for(const name of boneNames)data.bones[name]=[];
 for(let i=0;i<N;i++){
  const p=i/N;mixer.setTime(p*clip.duration);root.updateMatrixWorld(true);
  const hips=rig.mixamorigHips,hipPos=hips.getWorldPosition(V()),hipQuat=hips.getWorldQuaternion(Q()),inverse=hipQuat.clone().invert();
  data.rootPositions.push(hips.position.toArray());data.rootOrientations.push(hipQuat.toArray());
  for(const name of boneNames){const b=rig[name],wp=b.getWorldPosition(V()),hp=wp.clone().sub(hipPos).applyQuaternion(inverse);
   data.bones[name].push({lq:b.quaternion.toArray(),lp:b.position.toArray(),wp:wp.toArray(),hq:b.getWorldQuaternion(Q()).toArray(),hp:hp.toArray()});
  }
 }
 mixer.setTime(0);root.updateMatrixWorld(true);
 // Measure root trend before the baked terminal reset, as a DISPLAY correction only.
 const p0=data.rootPositions[0],p1=data.rootPositions[Math.floor(N*.89)],f=.89;
 rootTrend[key]=[(p1[0]-p0[0])/f,0,(p1[2]-p0[2])/f];
 return data;
}
function referenceAt(p){for(const key of CLIPS){const q=key==='Walking_Woman'&&$('aligned').checked&&alignment?mod1(p+alignment.womanPhaseOffset):p;
  mixers[key].setTime(q*clips[key].duration);
  if($('inPlace').checked){const hips=rigs[key].mixamorigHips,vec=rootTrend[key];hips.position.x-=vec[0]*q;hips.position.z-=vec[2]*q;}
  models[key].updateMatrixWorld(true);
 }
 $('phaseLabel').textContent=`${Math.round(p*100)}% / aligned woman ${Math.round((alignment?mod1(p+alignment.womanPhaseOffset):p)*100)}%`;
}
function download(data,name,type){const blob=new Blob([data],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.download=name;a.href=url;a.click();setTimeout(()=>URL.revokeObjectURL(url),5500)}
function csvEvidence(r){const cols=['bone','group','sampledAlignedPhases','staticPoseOffsetDeg','meanRawPoseDifferenceDeg','motionDeltaRmsDeg','motionDeltaMaxDeg','phaseOfMaxDynamicDifference','normalMotionFromAnchorRmsDeg','womanMotionFromAnchorRmsDeg','motionFromAnchorRmsRatio','hipRelativePositionDifferenceRmsUnits','localTranslationMotionDeltaRmsUnits'];const rows=[cols.join(',')];for(const b of r.perBone){rows.push(cols.map(k=>String(b[k]??'').replaceAll('"','""')).map(v=>`"${v}"`).join(','))}return rows.join('\n')+'\n'}
function sourceGaitTraits(clip,key){
 const usable=Math.floor(N*.93),hip=clip.rootPositions.slice(0,usable),ori=clip.rootOrientations.slice(0,usable);
 const eulers=ori.map(q=>new THREE.Euler().setFromQuaternion(new THREE.Quaternion().fromArray(q),'YXZ'));
 const unwrap=v=>{const out=[];let previous=null;for(let x of v){if(previous!==null){while(x-previous>Math.PI)x-=2*Math.PI;while(x-previous<-Math.PI)x+=2*Math.PI}out.push(x);previous=x}return out};
 const tr=key=>range(unwrap(eulers.map(x=>x[key])))*180/Math.PI;
 const relative=(name,axis)=>clip.bones[name].slice(0,usable).map(s=>s.hp[axis]);
 const head=clip.bones.mixamorigHead,chest=clip.bones.mixamorigSpine2??clip.bones.mixamorigSpine1??clip.bones.mixamorigSpine;
 const angularHead=[];if(head&&chest){const q0=multiply(conjugate(chest[0].hq),head[0].hq);
  for(let i=0;i<usable;i++){const q=multiply(conjugate(chest[i].hq),head[i].hq);angularHead.push(angleDeg(q0,q))}}
 const footEvents={};for(const side of ['Left','Right']){const name='mixamorig'+side+'Foot';const ys=clip.bones[name].slice(0,usable).map(s=>s.wp[1]);let min=0;for(let i=1;i<ys.length;i++)if(ys[i]<ys[min])min=i;footEvents[side.toLowerCase()]={lowestFootPhase:min/N,sourceFootHeight:ys[min],interpretation:'lowest-foot candidate, not proven foot contact'}}
 return {durationSeconds:clip.duration,
  pelvisYawRangeDeg:tr('y'),pelvisPitchRangeDeg:tr('x'),pelvisRollRangeDeg:tr('z'),
  pelvisVerticalBounceUnits:range(hip.map(v=>v[1])),
  pelvisLateralSwayDetrendedUnits:range(hip.map((v,i)=>v[0]-(rootTrend[key][0]*i/N))),
  headSideToSideRelativeToHipsUnits:range(relative('mixamorigHead',0)),
  headOrientationRelativeToChestRmsChangeDeg:rms(angularHead),
  leftFootForeAftHipFrameUnits:range(relative('mixamorigLeftFoot',2)),
  rightFootForeAftHipFrameUnits:range(relative('mixamorigRightFoot',2)),
  leftFootLateralHipFrameUnits:range(relative('mixamorigLeftFoot',0)),
  rightFootLateralHipFrameUnits:range(relative('mixamorigRightFoot',0)),
  footLowPointCandidates:footEvents};
}
function traitSection(r){const a=r.gaitTraits.Walking,b=r.gaitTraits.Walking_Woman;
 const fields=[['Pelvis yaw range','pelvisYawRangeDeg','°'],['Pelvis pitch range','pelvisPitchRangeDeg','°'],['Pelvis roll range','pelvisRollRangeDeg','°'],['Vertical pelvis bounce','pelvisVerticalBounceUnits',' units'],['Detrended sideways pelvis travel','pelvisLateralSwayDetrendedUnits',' units'],['Head lateral excursion vs pelvis','headSideToSideRelativeToHipsUnits',' units'],['Head/chest orientation RMS','headOrientationRelativeToChestRmsChangeDeg','°'],['Left foot fore-aft travel','leftFootForeAftHipFrameUnits',' units'],['Right foot fore-aft travel','rightFootForeAftHipFrameUnits',' units'],['Left foot lateral travel','leftFootLateralHipFrameUnits',' units'],['Right foot lateral travel','rightFootLateralHipFrameUnits',' units']];
 return ['SOURCE GAIT TRAITS: normal vs woman (authored clip measurements):',...fields.map(([label,key,unit])=>` ${label.padEnd(35)} ${a[key]?.toFixed(3)??'n/a'} → ${b[key]?.toFixed(3)??'n/a'}${unit}  (${a[key]>1e-8?((b[key]/a[key]-1)*100).toFixed(0)+'%':'ratio n/a'})`)];
}
function publish(r){const sort=$('sort').value, ranked=[...r.perBone].sort((a,b)=>(b[sort]??-Infinity)-(a[sort]??-Infinity));
 $('rows').replaceChildren();for(const b of ranked){const tr=document.createElement('tr');const vals=[b.bone.replace('mixamorig',''),b.group,b.motionDeltaRmsDeg.toFixed(2)+'°',b.staticPoseOffsetDeg.toFixed(2)+'°',b.motionFromAnchorRmsRatio===null?'n/a':b.motionFromAnchorRmsRatio.toFixed(2)+'×',b.hipRelativePositionDifferenceRmsUnits.toFixed(4)];for(const s of vals){const td=document.createElement('td');td.textContent=s;tr.append(td)}$('rows').append(tr)}
 const arms=r.perBone.filter(b=>/shoulders|upper-arms|forearms|hands/.test(b.group));const groups=Object.entries(r.groups).sort((a,b)=>b[1].meanBoneMotionDeltaRmsDeg-a[1].meanBoneMotionDeltaRmsDeg);
 const landmark=['mixamorigHips','mixamorigSpine','mixamorigNeck','mixamorigHead','mixamorigLeftShoulder','mixamorigRightShoulder','mixamorigLeftArm','mixamorigRightArm','mixamorigLeftForeArm','mixamorigRightForeArm','mixamorigLeftHand','mixamorigRightHand','mixamorigLeftFoot','mixamorigRightFoot'];
 const lines=[`ACTUAL SOURCE CLIPS: Walking ${r.clips.Walking.durationSeconds.toFixed(6)}s vs Walking_Woman ${r.clips.Walking_Woman.durationSeconds.toFixed(6)}s`,`CYCLE DURATION: Woman is ${((1-r.clips.Walking_Woman.durationSeconds/r.clips.Walking.durationSeconds)*100).toFixed(1)}% shorter`,`FIT FOOT-TRAJECTORY OFFSET: ${(r.alignment.womanPhaseOffset*100).toFixed(2)}% of female cycle (cost ${r.alignment.cost.toFixed(4)})`,`ALIGNED SOURCE PHASE PAIRS: ${r.sampledMatchedPhases} | 74/74 joints | last 7% excluded`,`NOTE: Static pose difference != dynamic motion difference. Ranked by dynamic difference, not initial pose.`,``,...traitSection(r),``,`BODY REGION (mean local rotation dynamic delta RMS):`,...groups.map(([k,v])=>` ${k.padEnd(16)} ${v.meanBoneMotionDeltaRmsDeg.toFixed(2).padStart(7)}° across ${v.boneCount} bones`),``,`CORE BODY + ARMS:`,...landmark.map(name=>{const b=r.perBone.find(x=>x.bone===name);return b?` ${name.replace('mixamorig','').padEnd(19)} motion Δ ${b.motionDeltaRmsDeg.toFixed(2)}° | initial offset ${b.staticPoseOffsetDeg.toFixed(2)}° | travel W/N ${(b.hipFramePositionRange.z.woman/(b.hipFramePositionRange.z.normal||1)).toFixed(2)}×`:` ${name}: unavailable`}),``,`MOST DIFFERENT ARM JOINTS (dynamic, not static):`,...arms.sort((a,b)=>b.motionDeltaRmsDeg-a.motionDeltaRmsDeg).slice(0,8).map(b=>` ${b.bone.replace('mixamorig','')} ${b.motionDeltaRmsDeg.toFixed(2)}° RMS; peak at ${Math.round(b.phaseOfMaxDynamicDifference*100)}%`),``,`METHOD: original GLB, local relative-to-first-aligned-pose SO(3) motion + hip-frame world landmarks. No generated clip. No style-transfer claim.`];
 $('summary').textContent=lines.join('\n');status(`RESEARCH COMPLETE · ${r.perBone.length} original joints measured · local report stored on phone: ${r.persistence||'saving'}`);
}
async function persist(r){try{const response=await fetch('./research-report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});if(!response.ok)throw Error('HTTP_'+response.status);const x=await response.json();if(!x.saved)throw Error('NOT_SAVED');r.persistence=`SAVED ${x.path} (${x.sha256?.slice(0,12)})`;return true}catch(e){r.persistence=`browser export available; phone auto-save unavailable: ${e.message}`;return false}}
async function analyse(){if(!ready)return;status('Measuring source motion, including shoulders, elbows, wrists, hands, torso and head…');
 try{await new Promise(r=>setTimeout(r,0));alignment=alignPhase(samples.Walking,samples.Walking_Woman);
  const result=compareClips(samples.Walking,samples.Walking_Woman,alignment);
  const traits={Walking:sourceGaitTraits(samples.Walking,'Walking'),Walking_Woman:sourceGaitTraits(samples.Walking_Woman,'Walking_Woman')};
  const reportData={schema:'hareworks-forward-style-research-v0.2.3',sourceClipNames:CLIPS,sourceModelSHA256:SHA,modelJoints:74,analysisOnly:true,createdNewAnimation:false,sourceClipsUnchanged:true,ownerApprovedForwardUntouched:true,ownerApprovedBackwardUntouched:true,samplingPhaseCount:N,
   clips:Object.fromEntries(CLIPS.map(k=>[k,{durationSeconds:clips[k].duration,sceneRootDetrendingDisplayOnly:rootTrend[k],originalClipTracks:clips[k].tracks.length}])),gaitTraits:traits,alignment,sourceMeasuredPhaseWindow:'0 <= phase < 0.93 for BOTH clips, aligned by pair of pelvis-relative ankle trajectories; excludes terminal reset',
   caveats:['This compares these two authored animations, not sexes in general','All 74 joints share exactly the same skeleton','A source static offset is not evidence of dynamic movement style','Measured foot phase fit is descriptive, not force-contact evidence','No backward gait is modified by this research','No candidate style transfer is applied'],...result};
  report=reportData;publish(report);await persist(report);publish(report);referenceAt(phase);
 }catch(e){status('SOURCE_ANALYSIS_ERROR '+e.message);console.error(e)}
}
$('analyze').onclick=analyse;$('sort').onchange=()=>{if(report)publish(report)};
$('jsonExport').onclick=()=>report?download(JSON.stringify(report,null,2),'hareworks-walking-vs-walking-woman-74joint-v0.2.3.json','application/json'):status('Research report not ready');
$('csvExport').onclick=()=>report?download(csvEvidence(report),'hareworks-walking-vs-walking-woman-74joint-v0.2.3.csv','text/csv'):status('Research report not ready');
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';phase=Number($('phase').value)/1000;if(ready)referenceAt(phase)};
$('aligned').onchange=$('inPlace').onchange=()=>{if(ready)referenceAt(phase)};
function render(now){requestAnimationFrame(render);const delta=Math.min(.06,Math.max(0,(now-last)/1000));last=now;if(ready&&playing){phase=mod1(phase+delta/clips.Walking.duration);referenceAt(phase);$('phase').value=Math.round(phase*1000)}orbit.update();renderer.render(scene,camera)}
requestAnimationFrame(render);
try{
 const response=await fetch(URL_GLB,{cache:'no-store'});if(!response.ok)throw Error('SOURCE_GLB_HTTP_'+response.status);
 const raw=await response.arrayBuffer();if(raw.byteLength!==6784896)throw Error('SOURCE_BYTES_'+raw.byteLength);
 if(!crypto?.subtle)throw Error('LOCALHOST_CRYPTO_UNAVAILABLE');const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw))).map(x=>x.toString(16).padStart(2,'0')).join('');if(digest!==SHA)throw Error('SOURCE_SHA256_MISMATCH_'+digest);
 const gltf=await new GLTFLoader().parseAsync(raw,new URL('../../../assets/hareworks/',import.meta.url).href);if(gltf.animations.length!==9)throw Error('SOURCE_NINE_CLIPS_REQUIRED');
 for(const key of CLIPS){const clip=gltf.animations.find(x=>x.name===key);if(!clip)throw Error('SOURCE_CLIP_NOT_FOUND_'+key);clips[key]=clip;models[key]=cloneSkeleton(gltf.scene);scene.add(models[key]);models[key].position.z=key==='Walking'?-SEP/2:SEP/2;rigs[key]=rigOf(models[key]);mixers[key]=new THREE.AnimationMixer(models[key]);mixers[key].clipAction(clip).reset().play();mixers[key].setTime(0);}
 for(const key of CLIPS)samples[key]=capture(key);
 ready=true;playing=true;grid.position.y=Math.min(...CLIPS.map(key=>new THREE.Box3().setFromObject(models[key]).min.y));
 $('identity').textContent=`v0.2.3 · SOURCE ${SHA} · original Walking + Walking_Woman clips · 74/74 bones · ${N} original poses/clip · commit ${new URLSearchParams(location.search).get('commit')||'unavailable'} · launcher SHA ${new URLSearchParams(location.search).get('scriptSha')||'unavailable'}`;
 referenceAt(0);cameraAt('side');resize();status('ORIGINAL SOURCE ANIMATIONS VERIFIED · research in progress');await analyse();
}catch(e){status('SOURCE_OR_RIG_ERROR '+e.message);console.error(e)}
