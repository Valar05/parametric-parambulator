import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const loader=new GLTFLoader();
const output=document.querySelector('#status'), selector=document.querySelector('#clip'), table=document.querySelector('#table');
const stage=document.querySelector('#stage');
const scene=new THREE.Scene();scene.background=new THREE.Color('#20242d');
const camera=new THREE.PerspectiveCamera(38,1,.01,1000);camera.position.set(4,3.8,5.2);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));stage.append(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x404050,2));const sun=new THREE.DirectionalLight(0xffffff,2.5);sun.position.set(4,7,5);scene.add(sun);
const floor=new THREE.GridHelper(20,20,0x667788,0x444455);scene.add(floor);
let model,mixer,clips=[],last=performance.now(),playing=true,active=0,report=null;
const bones={left:['mixamorig:LeftUpLeg','mixamorig:LeftLeg','mixamorig:LeftFoot','mixamorig:LeftToeBase'],right:['mixamorig:RightUpLeg','mixamorig:RightLeg','mixamorig:RightFoot','mixamorig:RightToeBase']};
const expectedIntermediates={left:'Bone_017',right:'Bone_013'};
function skeletonNames(root){const names=[];root.traverse(o=>{if(o.isBone)names.push(o.name)});return names}
function exactBone(root,name){let found=null;root.traverse(o=>{if(o.isBone&&o.name===name){if(found)throw new Error('Duplicate bone '+name);found=o}});return found}
function ancestorOf(parent,child){for(let p=child?.parent;p;p=p.parent)if(p===parent)return true;return false}
function findPelvis(root){return exactBone(root,'mixamorig:Hips')}
function resolveLegs(root){const found={};for(const [side,names] of Object.entries(bones)){
 found[side]=names.map(n=>exactBone(root,n));if(found[side].some(n=>!n))throw new Error('SOURCE_RIG_MISMATCH '+side+': '+names.filter((n,i)=>!found[side][i]).join(',')+'; actual skeleton: '+skeletonNames(root).join(', '));
 const [hip,knee,ankle,toe]=found[side], intermediate=exactBone(root,expectedIntermediates[side]);
 if(!intermediate||hip.parent?.name!=='mixamorig:Hips'||knee.parent!==hip||intermediate.parent!==knee||ankle.parent!==intermediate||toe.parent!==ankle)
 throw new Error('SOURCE_HIERARCHY_MISMATCH '+side+' (expected hip > knee > '+expectedIntermediates[side]+' > ankle > toe)');
}return found}
function pos(b){return b.getWorldPosition(new THREE.Vector3()).toArray().map(x=>+x.toFixed(6))}
function angle(a,b,c){const u=new THREE.Vector3().fromArray(a).sub(new THREE.Vector3().fromArray(b)).normalize();const v=new THREE.Vector3().fromArray(c).sub(new THREE.Vector3().fromArray(b)).normalize();return +THREE.MathUtils.radToDeg(Math.acos(THREE.MathUtils.clamp(u.dot(v),-1,1))).toFixed(3)}
function quantile(a,p){if(!a.length)return null;const s=[...a].sort((x,y)=>x-y);return s[Math.floor((s.length-1)*p)]}
function analyze(clip){const nodes=resolveLegs(model);
const pelvis=findPelvis(model);if(!pelvis)throw new Error('Pelvis unresolved; actual skeleton: '+skeletonNames(model).join(', '));
const duration=clip.duration, count=Math.max(60,Math.ceil(duration*60));const tracks=[];
const prior=mixer.timeScale;mixer.timeScale=1;mixer.stopAllAction();const action=mixer.clipAction(clip);action.reset().play();
for(let i=0;i<=count;i++){const t=duration*i/count;mixer.setTime(t);model.updateMatrixWorld(true);let row={t:+t.toFixed(6),pelvis:pos(pelvis),feet:{}};for(const side of ['left','right']){const [hip,knee,ankle,toeNode]=nodes[side];const hp=pos(hip),kp=pos(knee),ap=pos(ankle),tp=pos(toeNode||ankle);row.feet[side]={hip:hp,knee:kp,ankle:ap,toe:tp,toeProxy:!toeNode,kneeAngle:angle(hp,kp,ap)}}tracks.push(row)}
action.stop();mixer.timeScale=prior;
const profiles={};for(const side of ['left','right']){const ys=tracks.map(r=>r.feet[side].toe[1]);const baseline=quantile(ys,.08);const speeds=[];for(let i=1;i<tracks.length;i++){const a=tracks[i-1].feet[side].toe,b=tracks[i].feet[side].toe;const dt=tracks[i].t-tracks[i-1].t;speeds.push(Math.hypot(b[0]-a[0],b[2]-a[2])/dt)}const threshold=Math.max(.015,(quantile(speeds,.25)||0)*1.35);const tolerance=Math.max(.012,(quantile(ys,.75)-baseline)*.17);let contacts=0,segments=[],open=null;for(let i=0;i<tracks.length;i++){const grounded=(ys[i]-baseline)<tolerance && (i===0||speeds[i-1]<threshold);tracks[i].feet[side].contactCandidate=grounded;if(grounded){contacts++;if(open===null)open=i}else if(open!==null){segments.push([tracks[open].t,tracks[i-1].t]);open=null}}if(open!==null)segments.push([tracks[open].t,tracks.at(-1).t]);profiles[side]={baselineToeY:baseline,contactHeightTolerance:tolerance,contactSpeedThreshold:threshold,contactFraction:contacts/tracks.length,contactIntervals:segments,verticalToeRange:[Math.min(...ys),Math.max(...ys)],kneeAngleRange:[Math.min(...tracks.map(r=>r.feet[side].kneeAngle)),Math.max(...tracks.map(r=>r.feet[side].kneeAngle))]}}
const p0=tracks[0].pelvis,p1=tracks.at(-1).pelvis;return {clip:clip.name,duration,samples:tracks.length,rootPelvisDisplacement:p1.map((x,i)=>+(x-p0[i]).toFixed(6)),contactInference:'HEURISTIC: toe height + horizontal velocity, not verified skinned-sole contact',profiles,tracks}}
function renderReport(){table.textContent='';for(const r of report.clips){const tr=document.createElement('tr');for(const x of [r.clip,r.duration.toFixed(2),r.samples,r.profiles.left.contactFraction.toFixed(2),r.profiles.right.contactFraction.toFixed(2)]){const td=document.createElement('td');td.textContent=x;tr.append(td)}table.append(tr)}}
function download(name,content){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type:'application/json'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),3000)}
document.querySelector('#export').onclick=()=>{if(report)download('hareworks-gait-seven-clips-v1.0.2.json',JSON.stringify(report,null,2))};
document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Play'};
selector.onchange=()=>{active=+selector.value;mixer.stopAllAction();mixer.clipAction(clips[active]).reset().play()};
function size(){const w=stage.clientWidth,h=Math.max(320,Math.round(w*.63));renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}window.addEventListener('resize',size);
function tick(now){requestAnimationFrame(tick);if(mixer&&playing)mixer.update(Math.min((now-last)/1000,.05));last=now;renderer.render(scene,camera)}requestAnimationFrame(tick);
try{output.textContent='Loading source GLB…';const gltf=await loader.loadAsync('../../../assets/hareworks/Hareworks.glb');model=gltf.scene;scene.add(model);model.updateMatrixWorld(true);const bbox=new THREE.Box3().setFromObject(model);const center=bbox.getCenter(new THREE.Vector3()),size3=bbox.getSize(new THREE.Vector3());floor.position.y=bbox.min.y;camera.position.set(size3.x*2+1,size3.y*1.2+1,size3.z*2+3);camera.lookAt(center);clips=gltf.animations;mixer=new THREE.AnimationMixer(model);report={schema:'hareworks-gait-extraction-v1.0.2',sourceSha256:'4ee555a0e416e3b2d03290fea85fa5306f894b9b4a5e8feb3f41078d5eb7d828',units:'source model units',frame:'model scene/world coordinates; root motion NOT subtracted',resolvedSkeleton:{names:skeletonNames(model),legs:Object.fromEntries(Object.entries(resolveLegs(model)).map(([side,chain])=>[side,chain.map(n=>n?.name||null)])),pelvis:findPelvis(model)?.name},notes:['Exact source joint names and intermediate leg joints verified against original GLB','Heuristic contact candidates, not validated skinned sole','Root motion vs in-place classification requires further analysis','No procedural IK implemented in this campaign'],clips:[]};for(const clip of clips){output.textContent='Analyzing '+clip.name;report.clips.push(analyze(clip));const o=document.createElement('option');o.value=String(selector.length);o.textContent=clip.name;selector.append(o)}renderReport();mixer.stopAllAction();mixer.clipAction(clips[0]).reset().play();size();output.textContent='Seven-clip analysis complete. Rig verified from actual GLB. Export JSON for the full trajectories.'}catch(e){output.textContent='BLOCKED: '+e.message;console.error(e)}
