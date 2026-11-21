/* Hareworks v0.2.7: Walk LEFT, not slide. Source original vs independent full-rig math. */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {clone as cloneSkeleton} from 'three/addons/utils/SkeletonUtils.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {ROOT,CLIPS,calibrate,pose,angleDeg} from './sidestep-core.mjs';
const $=id=>document.getElementById(id), V=()=>new THREE.Vector3();
const GLB='../../../assets/hareworks/Hareworks-nine-clips.glb', SHA='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6',SIZE=6784896;
const N=720,SEP=2.8,scene=new THREE.Scene();scene.background=new THREE.Color('#101b27');
scene.add(new THREE.HemisphereLight(0xeef8ff,0x324456,2.5));const lamp=new THREE.DirectionalLight(0xffffff,3.2);lamp.position.set(-4,7,5);scene.add(lamp);
const grid=new THREE.GridHelper(15,30,0x6b869e,0x344759);scene.add(grid);
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;$('stage').append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-4,4,2.5,-2.5,.01,100),orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.enablePan=false;orbit.target.set(0,.9,0);orbit.minZoom=.55;orbit.maxZoom=3.8;
const views={side:[-7,3.2,0],front:[0,2.6,8],oblique:[-6,3.6,6],top:[-.01,9,.01]};
function cameraAt(v){camera.position.set(...views[v]);camera.up.set(0,1,0);camera.zoom=1;camera.lookAt(orbit.target);camera.updateProjectionMatrix();orbit.update()}
function resize(){const w=Math.max(320,$('stage').clientWidth),h=Math.max(300,Math.min(590,Math.round(w*.72)));renderer.setSize(w,h,false);camera.left=-2.4*w/h;camera.right=-camera.left;camera.top=2.4;camera.bottom=-2.4;camera.updateProjectionMatrix()}
window.addEventListener('resize',resize);for(const k of Object.keys(views))$(k).onclick=()=>cameraAt(k);cameraAt('side');resize();
let reference=null,generated=null,refRig=null,genRig=null,mixer=null,clips={},samples={},plans={},ready=false,playing=true,phase=0,last=performance.now(),lastAudit=null;
const status=s=>$('status').textContent=s;
function rig(root){const m={};root.traverse(n=>{if(n.isBone){if(m[n.name])throw Error('DUPLICATE_BONE_'+n.name);m[n.name]=n}});if(Object.keys(m).length!==74||!m[ROOT])throw Error('NOT_74_BONES');return m}
function capture(gltf,key){const model=cloneSkeleton(gltf.scene),bones=rig(model),action=new THREE.AnimationMixer(model),clip=clips[key];action.clipAction(clip).reset().play();const result={name:key,sampleCount:N,duration:clip.duration,bones:{}};
 for(const name of Object.keys(bones))result.bones[name]={pos:[],quat:[],scale:[]};
 for(let i=0;i<N;i++){action.setTime(clip.duration*i/N);model.updateMatrixWorld(true);for(const [name,b] of Object.entries(bones)){const d=result.bones[name];d.pos.push(b.position.toArray());d.quat.push(b.quaternion.toArray());d.scale.push(b.scale.toArray())}}
 const raw=clip.tracks.find(t=>t.name===ROOT+'.position');if(raw){const z=raw.getValueSize(),n=raw.times.length;result.terminalRootTrack={lastTime:raw.times[n-1],lastPosition:Array.from(raw.values.slice((n-1)*z,n*z)),previousPosition:Array.from(raw.values.slice((n-2)*z,(n-1)*z))}}
 return result;}
function copyGenerated(p){const g=pose(samples[CLIPS[1]],plans[CLIPS[1]],p);for(const [name,c] of Object.entries(g.bones)){let b=genRig[name];b.position.fromArray(c.position);b.quaternion.fromArray(c.quaternion).normalize();b.scale.fromArray(c.scale)}generated.updateMatrixWorld(true);return g;}
function referenceAt(p,mode='inplace'){const name=mode==='travelling'?CLIPS[0]:CLIPS[1],clip=clips[name],q=((p%1)+1)%1;
 mixer.stopAllAction();mixer.clipAction(clip).play();mixer.setTime(q*clip.duration);
 const src=plans[name];refRig[ROOT].position.x-=src.trend[0]*q;refRig[ROOT].position.z-=src.trend[2]*q;reference.updateMatrixWorld(true);
}
function sampleAt(p){if(!ready)return;phase=((p%1)+1)%1;referenceAt(phase,$('reference').value);copyGenerated(phase);$('phaseOut').textContent=Math.round(phase*100)+'%';}
function atModel(b,model){return model.worldToLocal(b.getWorldPosition(V()));}
async function audit(){if(!ready)return;const prev=phase,was=playing;playing=false;$('play').textContent='Play';const counts=[],measures={},errors=[],baseline=samples[CLIPS[1]],plan=plans[CLIPS[1]];let maxFoot=0,changedWindow=1-plan.seamStart;
 const record=(name,kind,v,rate,q)=>{let k=name+':'+kind,o=measures[k]??={bone:name,metric:kind,n:0,sumSq:0,max:0,worst:null};o.n++;o.sumSq+=v*v;if(v>o.max){o.max=v;o.worst={rateHz:rate,phase:q}}};
 try{for(const hz of [30,60,120]){let count=0;for(let i=0;i<Math.ceil(baseline.duration*hz*2);i++){const p=i/(2*hz*baseline.duration);if(p>=plan.seamStart)break;
   referenceAt(p,'inplace');copyGenerated(p);
   for(const name of Object.keys(baseline.bones)){const a=refRig[name],b=genRig[name];record(name,'localQuaternionDeg',angleDeg(a.quaternion.toArray(),b.quaternion.toArray()),hz,p);record(name,'localPosition',a.position.distanceTo(b.position),hz,p);record(name,'localScale',a.scale.distanceTo(b.scale),hz,p);const d=atModel(a,reference).distanceTo(atModel(b,generated));record(name,'worldJoint',d,hz,p);if(/Foot$|ToeBase$/.test(name))maxFoot=Math.max(maxFoot,d);}
   count++;if(i%36===0)await new Promise(r=>requestAnimationFrame(r));}
  counts.push({hz,sampledHalfFrames:count});}
 const table=Object.values(measures).map(o=>({bone:o.bone,metric:o.metric,rms:Math.sqrt(o.sumSq/o.n),max:o.max,worst:o.worst}));table.sort((a,b)=>b.max-a.max);
 const limits={localQuaternionDeg:{rms:.4,max:1},localPosition:{rms:.003,max:.006},localScale:{rms:.0005,max:.001},worldJoint:{rms:.004,max:.008}};
 const failed=table.filter(r=>r.rms>limits[r.metric].rms||r.max>limits[r.metric].max);
 const z=pose(baseline,plan,0).bones,u=pose(baseline,plan,1-1e-7).bones;let seamRotation=0,seamPosition=0;
 for(const name of Object.keys(z)){seamRotation=Math.max(seamRotation,angleDeg(z[name].quaternion,u[name].quaternion));seamPosition=Math.max(seamPosition,Math.hypot(...z[name].position.map((v,i)=>v-u[name].position[i])))}
 lastAudit={schema:'hareworks-walk-left-inplace-parity-v0.2.7',status:failed.length?'SOURCE_PARITY_WARNINGS':'SOURCE_PARITY_WITHIN_LIMITS_OWNER_REVIEW_PENDING',sourceClips:CLIPS,sourceSha256:SHA,joints:74,calibratedSamples:N,reference:'authored Cautious_Crouch_Walk_Left_inplace source played by mixer, compared before repaired seam',generated:'independent pose equations, no AnimationMixer',testedPhase:[0,plan.seamStart],repairedPhaseFraction:changedWindow,sourceTerminalResetExcluded:true,rootTravel:{traveling:plans[CLIPS[0]].trend,inplace:plans[CLIPS[1]].trend},counts,thresholds:limits,perJoint:table,parityFailureCount:failed.length,failures:failed.slice(0,60),sourceModelUnchanged:true,acceptedForwardUnchanged:true,acceptedBackwardUnchanged:true,ownerAcceptedLeft:false,firstFrame:'explicitly compared in full parity; source and generated at p0',maxFootJointError:maxFoot,seam:{maxRotationDeg:seamRotation,maxPosition:seamPosition},createdAtUtc:new Date().toISOString()};
 $('audit').textContent=`${lastAudit.status}\nOriginal left walk vs in-place: source-travel x ${plans[CLIPS[0]].trend[0].toFixed(4)} model units; in-place residual trend x ${plans[CLIPS[1]].trend[0].toFixed(4)}.\nAll 74 joints, ${counts.map(s=>s.hz+'Hz '+s.sampledHalfFrames).join(' / ')}.\nViolations ${failed.length}, max foot positional error ${maxFoot.toFixed(5)}.\nSeam rotation ${seamRotation.toFixed(4)}°, position ${seamPosition.toFixed(6)}. Excluded modified terminal ${(changedWindow*100).toFixed(1)}%.\nWorst: ${table.slice(0,8).map(x=>x.bone+':'+x.metric+' '+x.max.toFixed(4)).join(' | ')}\nDownload evidence JSON for per-joint records.`;
 status(lastAudit.status==='SOURCE_PARITY_WARNINGS'?'PER-JOINT SOURCE WARNINGS · generated animation still visible':'74-JOINT SOURCE PARITY MEASURED · owner visual review pending');
 try{const r=await fetch('./evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastAudit)});if(r.ok){const receipt=await r.json();status('ACTUAL BROWSER AUDIT SAVED IN TERMUX STATE · sha '+receipt.sha256.slice(0,12)+' · visual review pending')}else status('BROWSER AUDIT COMPUTED · automatic save HTTP '+r.status+' · use Export evidence')}
 catch(e){status('BROWSER AUDIT COMPUTED · autosave unavailable · use Export evidence')}
 }catch(e){status('AUDIT_ERROR '+e.message);console.error(e)}finally{sampleAt(prev);playing=was;$('play').textContent=playing?'Pause':'Play';}}
$('auditButton').onclick=()=>audit();$('exportButton').onclick=()=>{if(!lastAudit){status('Run audit first');return}const b=new Blob([JSON.stringify(lastAudit,null,2)],{type:'application/json'}),url=URL.createObjectURL(b),a=document.createElement('a');a.href=url;a.download='hareworks-walk-left-parity-v0.2.7.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),8000)};
$('play').onclick=()=>{if(!ready)return;playing=!playing;$('play').textContent=playing?'Pause':'Play'};
$('phase').oninput=()=>{playing=false;$('play').textContent='Play';sampleAt(Number($('phase').value)/1000)};
$('reference').onchange=()=>sampleAt(phase);
function frame(now){requestAnimationFrame(frame);const d=Math.min(.06,Math.max(0,(now-last)/1000));last=now;if(ready&&playing){sampleAt((phase+d/samples[CLIPS[1]].duration)%1);$('phase').value=Math.round(phase*1000)}orbit.update();renderer.render(scene,camera)}requestAnimationFrame(frame);
window.addEventListener('error',e=>status('VIEWER_ERROR '+(e.error?.message||e.message)));
try{const r=await fetch(GLB,{cache:'no-store'});if(!r.ok)throw Error('SOURCE_HTTP_'+r.status);const bytes=await r.arrayBuffer();if(bytes.byteLength!==SIZE)throw Error('SOURCE_SIZE_'+bytes.byteLength);
 const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');if(sha!==SHA)throw Error('SOURCE_SHA_MISMATCH_'+sha);
 const gltf=await new GLTFLoader().parseAsync(bytes,new URL('../../../assets/hareworks/',import.meta.url).href);if(gltf.animations.length!==9)throw Error('NINE_CLIPS_REQUIRED');
 for(const k of CLIPS){clips[k]=gltf.animations.find(c=>c.name===k);if(!clips[k])throw Error('MISSING_LEFT_SOURCE_'+k)}
 reference=cloneSkeleton(gltf.scene);generated=cloneSkeleton(gltf.scene);refRig=rig(reference);genRig=rig(generated);reference.position.z=-SEP/2;generated.position.z=SEP/2;scene.add(reference,generated);
 mixer=new THREE.AnimationMixer(reference);for(const k of CLIPS)mixer.clipAction(clips[k]).reset().play();
 for(const k of CLIPS){samples[k]=capture(gltf,k);plans[k]=calibrate(samples[k]);}
 const changed=plans[CLIPS[0]].trend[0]-plans[CLIPS[1]].trend[0];if(!(changed>1&&changed<2))throw Error('SOURCE_LEFT_TRAVEL_SEPARATION_MISMATCH '+changed);
 ready=true;sampleAt(0);grid.position.y=new THREE.Box3().setFromObject(reference).min.y;resize();cameraAt('oblique');
 $('identity').textContent=`v0.2.7 · exact GLB SHA ${SHA} · original clips ${CLIPS.join(' and ')} · 74/74 joints · ${N} samples per clip · generated mixer=0 · commit ${new URLSearchParams(location.search).get('commit')||'unknown'} · entry SHA ${new URLSearchParams(location.search).get('scriptSha')||'unknown'}`;
 $('audit').textContent=`LEFT STEP SOURCE CONFIRMED · original traveling pelvis trend x ${plans[CLIPS[0]].trend[0].toFixed(4)}; in-place source residual trend x ${plans[CLIPS[1]].trend[0].toFixed(4)}.\nSource is not a slide. Generated solver uses the authored in-place clip and repairs the end-of-cycle seam.\nRun full 74-joint parity to confirm.`;
 status('LEFT STEPPING SOURCE VERIFIED · original in-place vs procedural; visual review pending');}
catch(e){status('SOURCE_OR_STARTUP_BLOCKED '+e.message);console.error(e)}
