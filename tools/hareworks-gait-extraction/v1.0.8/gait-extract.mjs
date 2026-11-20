import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const SOURCE_SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6';
const expected=['Idle_Turn_Left','Idle_Turn_Right'];
const $=id=>document.getElementById(id);
const scene=new THREE.Scene();scene.background=new THREE.Color(0x151b25);
const camera=new THREE.PerspectiveCamera(38,1,.01,1000);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));$('stage').append(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x38445a,2.0));const key=new THREE.DirectionalLight(0xffffff,2.5);key.position.set(4,8,6);scene.add(key);
const grid=new THREE.GridHelper(20,20,0x778899,0x334455);scene.add(grid);
const V=()=>new THREE.Vector3();
const vec=a=>new THREE.Vector3(...a);
const rnd=x=>Number.isFinite(x)?+x.toFixed(6):null;
const xyz=v=>v.toArray().map(rnd);
const qyaw=q=>{const f=new THREE.Vector3(0,0,1).applyQuaternion(q);return Math.atan2(f.x,f.z)};
const degrees=r=>rnd(THREE.MathUtils.radToDeg(r));
const delta=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
const quantile=(a,p)=>{if(!a.length)return null;const s=[...a].sort((x,y)=>x-y);return s[Math.floor((s.length-1)*p)]};
const distXZ=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]);
let root,clips,mixer,report=null,current=0,play=true,last=performance.now(),floorY=0,actions=[];
function findBone(name){const arr=[];root.traverse(o=>{if(o.isBone&&o.name===name)arr.push(o)});if(arr.length!==1)throw Error('UNIQUE_BONE_REQUIRED '+name+' count '+arr.length);return arr[0]}
function buildRig(){
 const hips=findBone('mixamorigHips');
 const legs={};for(const [side,mid] of [['left','Bone_017'],['right','Bone_013']]){
  const S=side==='left'?'Left':'Right';const names=[`mixamorig${S}UpLeg`,`mixamorig${S}Leg`,mid,`mixamorig${S}Foot`,`mixamorig${S}ToeBase`];
  const chain=names.map(findBone);if(chain[0].parent!==hips||chain.some((b,i)=>i&&b.parent!==chain[i-1]))throw Error('RIG_HIERARCHY_'+side);legs[side]={chain,ankle:chain[3],toe:chain[4]};
 }
 const upper=['mixamorigSpine','mixamorigSpine1','mixamorigSpine2','mixamorigNeck','mixamorigHead'].map(n=>{const arr=[];root.traverse(o=>{if(o.isBone&&o.name===n)arr.push(o)});return arr.length===1?arr[0]:null});
 return {hips,legs,upper,upperNames:upper.map((b,i)=>b?.name||null)};
}
function world(o){return xyz(o.getWorldPosition(V()))}
function quaternion(o){return o.getWorldQuaternion(new THREE.Quaternion())}
function skinnedWitnesses(rig){
 // Collect bounded skinned toe/sole witnesses by dominant skin influence.
 // If mesh influences cannot resolve unambiguously, mark sole evidence unavailable.
 const info={left:[],right:[]};const meshes=[];root.traverse(o=>{if(o.isSkinnedMesh&&o.geometry?.attributes?.skinIndex&&o.geometry?.attributes?.position)meshes.push(o)});
 for(const mesh of meshes){const skin=mesh.geometry.attributes.skinIndex, weight=mesh.geometry.attributes.skinWeight, pos=mesh.geometry.attributes.position;
  const inverse=new Map(mesh.skeleton.bones.map((b,i)=>[b,i]));
  for(const side of ['left','right']){
   const {ankle,toe}=rig.legs[side];const target=new Set([inverse.get(ankle),inverse.get(toe)]);
   if(target.has(undefined))continue;
   const candidates=[];
   for(let i=0;i<pos.count;i++){
    let bestW=0,bestI=-1;
    for(let k=0;k<4;k++){const w=weight.getComponent(i,k);if(w>bestW){bestW=w;bestI=skin.getComponent(i,k)}}
    if(target.has(bestI)&&bestW>=.5)candidates.push(i);
   }
   // Deterministic subsampling, preserves spatial coverage without large per-frame work.
   const limit=64,step=Math.max(1,Math.ceil(candidates.length/limit));for(let i=0;i<candidates.length;i+=step)info[side].push({mesh,index:candidates[i]});
  }
 }
 return {info,counts:Object.fromEntries(Object.entries(info).map(([s,a])=>[s,a.length])),meshCount:meshes.length};
}
function solePoints(witnesses){const out={};for(const side of ['left','right']){
 const pts=[];for(const {mesh,index} of witnesses.info[side]){
  const p=mesh.applyBoneTransform(index,V());mesh.localToWorld(p);pts.push(p);
 }
 if(!pts.length){out[side]=null;continue}
 pts.sort((a,b)=>a.y-b.y);const band=pts.slice(0,Math.max(3,Math.ceil(pts.length*.20)));
 const center=band.reduce((v,p)=>v.add(p),V()).multiplyScalar(1/band.length);
 out[side]={center:xyz(center),bottomY:rnd(pts[0].y),spreadY:rnd(pts.at(-1).y-pts[0].y)};
 }return out;
}
function sampleClip(clip,rig,witnesses){
 // Isolate each animation action so the previous clip cannot contaminate samples.
 mixer.stopAllAction();mixer.setTime(0);const action=mixer.clipAction(clip);action.reset().setLoop(THREE.LoopOnce,1).play();
 const count=Math.max(60,Math.ceil(clip.duration*60));const samples=[];
 for(let i=0;i<=count;i++){
  const t=clip.duration*i/count;mixer.setTime(t);root.updateMatrixWorld(true);
  const hips=world(rig.hips),hipQ=quaternion(rig.hips),hipYaw=qyaw(hipQ), sole=solePoints(witnesses);
  const upper=rig.upper.map(b=>b?{position:world(b),yaw:qyaw(quaternion(b))}:null);
  const feet={};for(const side of ['left','right']){
   const chain=rig.legs[side].chain.map(world);
   feet[side]={hip:chain[0],knee:chain[1],intermediate:chain[2],ankle:chain[3],toe:chain[4],ankleYaw:qyaw(quaternion(rig.legs[side].ankle)),sole:sole[side]};
  }
  samples.push({t:rnd(t),pelvis:hips,pelvisYaw:hipYaw,upper,feet});
 }
 action.stop();
 // Stable unwrap across -pi/+pi, maintaining signed accumulated rotation.
 const unwrapped=[];for(let i=0;i<samples.length;i++)unwrapped.push(i?unwrapped[i-1]+delta(samples[i].pelvisYaw,samples[i-1].pelvisYaw):0);
 const rotation=degrees(unwrapped.at(-1));const translation=xyz(vec(samples.at(-1).pelvis).sub(vec(samples[0].pelvis)));
 const upperTurns={};rig.upper.forEach((b,j)=>{if(!b)return;let v=0;const s=samples.map(x=>x.upper[j].yaw);for(let i=1;i<s.length;i++)v+=delta(s[i],s[i-1]);upperTurns[b.name]={worldYawDeltaDeg:degrees(v),relativeToPelvisDeg:degrees(v-unwrapped.at(-1))}});
 const feet={};for(const side of ['left','right']){
  const rows=samples.map(s=>s.feet[side]);const bottoms=rows.map(r=>r.sole?.bottomY).filter(x=>x!==undefined&&x!==null);const haveSole=bottoms.length===rows.length;
  const baseline=haveSole?quantile(bottoms,.08):null;
  const verticalRange=haveSole?quantile(bottoms,.95)-quantile(bottoms,.05):null;
  const tol=haveSole?Math.max(.005,verticalRange*.13):null;
  // Distinguish planted translating feet from turning pivots; label both heuristically.
  const velocities=[],rotRates=[];for(let i=1;i<rows.length;i++){
   const dt=samples[i].t-samples[i-1].t;
   const a=rows[i].sole?.center||rows[i].toe,b=rows[i-1].sole?.center||rows[i-1].toe;
   velocities.push(distXZ(a,b)/dt);rotRates.push(Math.abs(delta(rows[i].ankleYaw,rows[i-1].ankleYaw))/dt);
  }
  const speedThreshold=haveSole?Math.max(.015,(quantile(velocities,.25)||0)*1.35):null;
  const contact=[];let slides=0,angular=0,contactCount=0;const intervals=[];let start=null;
  for(let i=0;i<rows.length;i++){
   const near=haveSole&&rows[i].sole.bottomY-baseline<=tol;
   // Ground-near is evidence for potential support; speed is scored separately.
   const supported=Boolean(near);contact.push(supported);
   if(supported){contactCount++;if(start===null)start=i;if(i>0){slides+=distXZ(rows[i].sole.center,rows[i-1].sole.center);angular+=Math.abs(delta(rows[i].ankleYaw,rows[i-1].ankleYaw));}}
   else if(start!==null){intervals.push([samples[start].t,samples[i-1].t]);start=null}
  }
  if(start!==null)intervals.push([samples[start].t,samples.at(-1).t]);
  feet[side]={soleWitnessCount:witnesses.counts[side],evidence:haveSole?'SKINNED_VERTEX_WITNESSES_HEURISTIC':'UNAVAILABLE_NO_SKINNED_SOLE_WITNESSES',baselineSoleY:baseline,heightThreshold:tol,contactCandidateFraction:haveSole?rnd(contactCount/rows.length):null,groundNearIntervals:intervals,groundNearAccumulatedTravel:rnd(slides),groundNearAccumulatedFootYawDeg:degrees(angular),contactSpeedReference:speedThreshold,peakCenterHorizontalSpeed:rnd(Math.max(...velocities)),ankleYawDeltaDeg:degrees(rows.reduce((a,r,i)=>i?a+delta(r.ankleYaw,rows[i-1].ankleYaw):0,0)),note:'Support intervals are preliminary. Sole witnesses are sampled from skinned vertices, not verified contact patches; no measured world floor or force data.'};
  rows.forEach((r,i)=>{r.contactCandidate=contact[i];r.horizontalSpeed=i?rnd(velocities[i-1]):null});
 }
 return {name:clip.name,duration:rnd(clip.duration),samples:samples.length,pelvisTranslation:translation,pelvisYawDeltaDeg:rotation,pelvisYawPathDeg:degrees(unwrapped.reduce((sum,v,i)=>i?sum+Math.abs(v-unwrapped[i-1]):0,0)),upperTurns,feet,classification:/Idle_Turn/i.test(clip.name)?'IDLE_TURN_REFERENCE':'LOCOMOTION_REFERENCE',sourceFrame:'world +Y up, +Z reference forward; yaw around world Y, positive toward +X',cautions:['Pelvis is a joint, not proven independent root-motion transform','Ground/support identification is heuristic; check actual mesh contact and floor','Turn clip is reference motion, not an implemented aim controller'],tracks:samples};
}
function summary(r){return {clip:r.name,duration:r.duration,pelvisYawDeg:r.pelvisYawDeltaDeg,pelvisTravelXZ:rnd(Math.hypot(r.pelvisTranslation[0],r.pelvisTranslation[2])),chestYawRelDeg:r.upperTurns.mixamorigSpine2?.relativeToPelvisDeg??null,leftGroundNear:r.feet.left.contactCandidateFraction,rightGroundNear:r.feet.right.contactCandidateFraction,leftFootTravel:r.feet.left.groundNearAccumulatedTravel,rightFootTravel:r.feet.right.groundNearAccumulatedTravel}}
function renderTable(){const body=$('table');body.textContent='';for(const x of report.summary){const tr=document.createElement('tr');for(const k of ['clip','duration','pelvisYawDeg','pelvisTravelXZ','chestYawRelDeg','leftGroundNear','rightGroundNear']){const td=document.createElement('td');td.textContent=x[k]??'unknown';tr.append(td)}body.append(tr)}}
function save(name,obj){const url=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),3000)}
function draw(){const now=performance.now();if(mixer&&play)mixer.update(Math.min((now-last)/1000,.05));last=now;renderer.render(scene,camera);requestAnimationFrame(draw)}requestAnimationFrame(draw);
function size(){const width=Math.max(300,$('stage').clientWidth),height=Math.round(width*.65);renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix()}addEventListener('resize',size);
function select(i){current=i;mixer.stopAllAction();mixer.setTime(0);mixer.clipAction(clips[i]).reset().play();$('clip').value=String(i);$('detail').textContent=JSON.stringify(summary(report.clips[i]),null,2)}
$('play').onclick=()=>{play=!play;$('play').textContent=play?'Pause':'Play'};
$('clip').onchange=e=>select(+e.target.value);
$('export').onclick=()=>report&&save('hareworks-nine-clip-gait-and-idle-turn-v1.0.8.json',report);
$('turnleft').onclick=()=>select(clips.findIndex(c=>c.name==='Idle_Turn_Left'));
$('turnright').onclick=()=>select(clips.findIndex(c=>c.name==='Idle_Turn_Right'));
try{
 $('status').textContent='Loading nine-clip rig and skinned surfaces…';const gltf=await new GLTFLoader().loadAsync('../../../assets/hareworks/Hareworks-nine-clips.glb');root=gltf.scene;scene.add(root);clips=gltf.animations;
 if(clips.length!==9||expected.some(n=>!clips.find(c=>c.name===n)))throw Error('NINE_CLIP_SET_MISMATCH');
 mixer=new THREE.AnimationMixer(root);const rig=buildRig();const witnesses=skinnedWitnesses(rig);
 if(!witnesses.counts.left||!witnesses.counts.right)throw Error('MISSING_SKINNED_FOOT_WITNESSES');
 const bbox=new THREE.Box3().setFromObject(root);const center=bbox.getCenter(V()),sz=bbox.getSize(V());floorY=bbox.min.y;grid.position.y=floorY;
 camera.position.set(center.x+sz.x*2+1,center.y+sz.y*1.4+1,center.z+sz.z*2+2);camera.lookAt(center);
 report={schema:'hareworks-gait-and-idle-turn-v1.0.8',sourceSha256:SOURCE_SHA,computedInBrowserAt:new Date().toISOString(),rig:{jointCount:74,upperBones:rig.upperNames,legChains:Object.fromEntries(Object.entries(rig.legs).map(([s,v])=>[s,v.chain.map(b=>b.name)])),skinnedWitnesses:witnesses.counts},coordinates:'GLTF world space, +Y up, +Z heading convention; root translation cannot be inferred from pelvis alone',idleAimDesign:{status:'PROPOSED_NOT_IMPLEMENTED',inputs:['movement vector','world aim angle','last planted stance','turn rate','torso twist limit'],plan:['When moving, let gait heading and aim heading be measured independently','When stopped, maintain planted support until upper-body twist budget is reached','Use measured left/right idle turn clips to estimate step direction, pivot foot, pelvis yaw and stance transfer','Trigger a deliberate foot reposition when the torso/hip twist budget is exceeded','Blend upper-body aiming independently from footstep progression; never rotate planted feet through the ground'],calibration:'Derive thresholds from user-approved visual review after measurements. No arbitrary accepted degrees.'},notes:['Measured source clips, NOT procedural IK or implemented aim input','Uniform ~60 Hz clip sampling; endpoint may reflect loop discontinuity','Sole witnesses approximate weighted foot vertices, not full outsole/contact mechanics','World yaw path unwrapped to avoid modulo 360 aliasing'],clips:[]};
 for(const clip of clips){$('status').textContent='Extracting '+clip.name;report.clips.push(sampleClip(clip,rig,witnesses));const opt=document.createElement('option');opt.value=String($('clip').length);opt.textContent=clip.name;$('clip').append(opt)}
 report.summary=report.clips.map(summary);renderTable();select(0);size();$('status').textContent='All nine clips analyzed. Idle left/right turn deltas, upper twist, sole witnesses and tentative support exported. Visual approval pending.';
}catch(e){$('status').textContent='BLOCKED '+e.message;console.error(e)}
