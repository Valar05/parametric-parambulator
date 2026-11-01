/* Repl Pose Lab phone bone inspector v0.6.6.
   Forks the concrete pointer/twist interaction idea from Pose Lab without
   importing Pose Lab or moving Repl into its repository.
   Edits are browser-memory only. Canonical GLB and animation never mutated. */
const REPL_POSE_VERSION = '0.6.6';
const REPL_TIP_BONES = new Set(['Bone_012','Bone_018','Bone_023','Bone_028']);
const REPL_TAP_DISTANCE_PX = 13;
const REPL_PICK_RADIUS_PX = 27;
const REPL_DOUBLE_TAP_MS = 370;
const REPL_DOUBLE_TAP_PX = 32;
function replWrappedAngle(v) {return Math.atan2(Math.sin(v),Math.cos(v));}
function replDistancePointSegment(p,a,b) {
 const dx=b.x-a.x,dy=b.y-a.y,den=dx*dx+dy*dy;
 if (den<1e-6) return Math.hypot(p.x-a.x,p.y-a.y);
 const t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/den));
 return Math.hypot(p.x-(a.x+dx*t),p.y-(a.y+dy*t));
}
function installReplPoseLab({root,scene,camera,canvas,orbit,THREE,mixer,
                            getStatus,animation,getAction,getPaused,setPaused,
                            restRotations,sourceSha}) {
 const ui=id=>document.getElementById(id);
 const controls=['clip','play','replay','timeline','save-sheet','gizmo-enable'];
 const bones=[];const byName=new Map();
 root.traverse(o=>{if(o.isBone){bones.push(o);byName.set(o.name,o);}});
 if(bones.length!==50)throw Error('POSE_LAB_WRONG_RIG_JOINT_COUNT:'+bones.length);
 for(const tip of REPL_TIP_BONES)if(!byName.has(tip))throw Error('POSE_LAB_TIP_BONE_MISSING:'+tip);
 const state={editing:false,cameraMode:false,selected:new Set(),
  locks:{X:false,Y:true,Z:true},axis:'X',protectedTips:true,
  pointers:new Map(),gesture:null,down:new Map(),lastEmpty:null,
  history:[],redo:[],baseline:new Map(),clipName:'',clipTime:0,
  dirty:false,lastExported:false};
 const baseColors={selected:0x41ffee,default:0xd7a15c,protected:0xf6778b};
 const material=new THREE.LineBasicMaterial({color:0xd6a66f,transparent:true,opacity:.9,depthTest:false});
 const overlay=new THREE.Group();overlay.name='ReplPoseLabNonExportedOverlay';scene.add(overlay);
 const markers=[];
 const markerGeom=new THREE.SphereGeometry(.014,10,7);
 for(const bone of bones){
  const point=new THREE.Mesh(markerGeom,new THREE.MeshBasicMaterial({color:0xd7a15c,
    depthTest:false,depthWrite:false}));point.renderOrder=999;
  overlay.add(point);
  let line=null;
  if(bone.parent?.isBone){
   const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(6),3));
   line=new THREE.Line(geo,material);line.frustumCulled=false;line.renderOrder=998;overlay.add(line);
  }
  markers.push({bone,point,line});
 }
 const select=ui('pl-bone-select');select.replaceChildren();
 let blank=document.createElement('option');blank.value='';blank.textContent='Choose bone by name…';select.append(blank);
 for(const bone of bones){const o=document.createElement('option');o.value=bone.name;
  o.textContent=bone.name+(REPL_TIP_BONES.has(bone.name)?' · suspected tip':'');select.append(o);}
 const vec=new THREE.Vector3(),parentPos=new THREE.Vector3(),local=new THREE.Vector3();
 const qaxis=new THREE.Quaternion();
 function status(msg){ui('pl-status').textContent=msg;}
 function selectedLabel(){
  const names=[...state.selected];
  ui('pl-selected').textContent=names.length?'Selected ('+names.length+'): '+names.join(', '):'No bones selected';
  const protectedNames=names.filter(n=>state.protectedTips&&REPL_TIP_BONES.has(n));
  ui('pl-protected').textContent=protectedNames.length?
   'Protected tip(s): '+protectedNames.join(', ')+' (rotation disabled)':'Protected tips: '+(state.protectedTips?'ON':'OFF');
  select.value=names.length===1?names[0]:'';
 }
 function updateMarkers(){
  overlay.visible=ui('pl-skeleton').checked;
  if(!overlay.visible)return;
  root.updateMatrixWorld(true);
  for(const {bone,point,line} of markers){
   bone.getWorldPosition(vec);point.position.copy(vec);
   const color=state.selected.has(bone.name)?baseColors.selected:
      REPL_TIP_BONES.has(bone.name)?baseColors.protected:baseColors.default;
   point.material.color.setHex(color);
   point.scale.setScalar(state.selected.has(bone.name)?1.8:1.15);
   if(line){
    bone.parent.getWorldPosition(parentPos);
    const v=line.geometry.attributes.position;
    v.setXYZ(0,parentPos.x,parentPos.y,parentPos.z);
    v.setXYZ(1,vec.x,vec.y,vec.z);v.needsUpdate=true;
   }
  }
 }
 function screenPoint(p){
  const r=canvas.getBoundingClientRect();local.copy(p).project(camera);
  if(local.z>1||local.z< -1)return null;
  return {x:r.left+(local.x+1)*r.width/2,y:r.top+(1-local.y)*r.height/2};
 }
 function pickBone(x,y){
  if(!ui('pl-skeleton').checked)return '';
  root.updateMatrixWorld(true);
  const target={x,y};let chosen='',distance=REPL_PICK_RADIUS_PX;
  for(const {bone} of markers){
   bone.getWorldPosition(vec);const b=screenPoint(vec);if(!b)continue;
   let d=Math.hypot(x-b.x,y-b.y);
   if(bone.parent?.isBone){
    bone.parent.getWorldPosition(parentPos);const a=screenPoint(parentPos);
    if(a)d=Math.min(d,replDistancePointSegment(target,a,b));
   }
   if(d<distance){distance=d;chosen=bone.name;}
  }
  return chosen;
 }
 function selectBone(name){
  if(!byName.has(name))return;
  if(!ui('pl-additive').checked)state.selected.clear();
  if(state.selected.has(name))state.selected.delete(name);
  else state.selected.add(name);
  selectedLabel();updateMarkers();status(name+' selection changed. Two-finger twist rotates selected bones.');
 }
 function clearSelection(){state.selected.clear();selectedLabel();updateMarkers();status('Deselected. Tap any bone to select.');}
 function snapshot(){return Object.fromEntries(bones.map(b=>[b.name,b.quaternion.toArray()]));}
 function restore(s){for(const b of bones)if(s[b.name])b.quaternion.fromArray(s[b.name]);
  root.updateMatrixWorld(true);updateMarkers();}
 function remember(){state.history.push(snapshot());if(state.history.length>40)state.history.shift();
  state.redo=[];}
 function changed(){state.dirty=true;state.lastExported=false;status('Pose edited locally. Save Pose JSON to preserve your reference.');}
 function lockStatus(){
  const a=state.axis;return state.locks[a]?'Axis '+a+' is locked. Unlock it in the panel.':'';
 }
 function editableNames(){return [...state.selected].filter(n=>!(state.protectedTips&&REPL_TIP_BONES.has(n)));}
 function applyAxisDelta(deg,starting){
  const axis=state.axis,choice=editableNames();
  if(!choice.length){status('Nothing editable selected. Suspected toe tips are protected.');return false;}
  if(state.locks[axis]){status(lockStatus());return false;}
  const rad=THREE.MathUtils.degToRad(Math.max(-85,Math.min(85,deg)));
  const direction=axis==='X'?new THREE.Vector3(1,0,0):axis==='Y'?
                 new THREE.Vector3(0,1,0):new THREE.Vector3(0,0,1);
  qaxis.setFromAxisAngle(direction,rad);
  for(const name of choice){byName.get(name).quaternion.fromArray(starting[name]).multiply(qaxis).normalize();}
  root.updateMatrixWorld(true);updateMarkers();ui('pl-delta').textContent=deg.toFixed(1)+'° '+axis;
  return true;
 }
 function rotateBy(deg){
  if(!state.editing||state.cameraMode)return;
  if(!editableNames().length){status('No editable bones selected.');return;}
  if(state.locks[state.axis]){status(lockStatus());return;}
  const from=snapshot();remember();
  if(applyAxisDelta(deg,from))changed();
 }
 function enter(){
  if(!mixer||!getAction()){status('Wait for Repl GLB to finish loading.');return false;}
  if(ui('gizmo-enable').checked){status('Disable the tail pivot gizmo before editing bones.');return false;}
  state.editing=true;state.cameraMode=false;setPaused(true);
  state.clipName=getAction().getClip().name;state.clipTime=getAction().time;
  // Restore ONLY known problematic distal-tip control nodes to their GLB rest
  // rotations for the pose-workbench baseline. THIS DOES NOT ALTER THE GLB.
  if(state.protectedTips)for(const n of REPL_TIP_BONES){
   const b=byName.get(n),r=restRotations.get(b);
   if(r)b.quaternion.copy(r);
  }
  state.baseline=new Map(bones.map(b=>[b.name,b.quaternion.clone()]));
  state.history=[];state.redo=[];state.dirty=false;state.lastExported=false;
  for(const id of controls)ui(id).disabled=true;
  ui('pl-camera').disabled=false;orbit.enabled=false;updateMarkers();
  status('Pose paused at '+state.clipTime.toFixed(2)+'s. Tip controls frozen to rest. Tap bones, then twist with two fingers.');
  return true;
 }
 function leave(){
  if(state.dirty&&!state.lastExported&&!window.confirm('Discard unsaved bone pose? Export Pose JSON first if you want to keep it.')){
   ui('pl-edit').checked=true;return false;
  }
  state.editing=false;state.cameraMode=false;state.pointers.clear();state.gesture=null;
  for(const id of controls)ui(id).disabled=false;
  orbit.enabled=true;
  // Source animation remains untouched; re-evaluate it to restore the exact frame.
  mixer.setTime(state.clipTime);
  status('Pose mode off. Original v0.6.5 gait restored without modifying Repl.glb.');
  return true;
 }
 function currentAngle(){
  const pts=[...state.pointers.values()].slice(0,2);
  if(pts.length<2)return null;
  return Math.atan2(pts[1].y-pts[0].y,pts[1].x-pts[0].x);
 }
 function pointerDown(e){
  if(!state.editing||state.cameraMode)return;
  e.preventDefault();e.stopImmediatePropagation();
  if(state.pointers.size>=2)return;
  const point={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};
  state.pointers.set(e.pointerId,point);
  canvas.setPointerCapture?.(e.pointerId);
  if(state.pointers.size===2&&state.selected.size){
   state.gesture={startAngle:currentAngle(),start:snapshot(),changed:false};
   ui('pl-delta').textContent='0.0° '+state.axis;
  }
 }
 function pointerMove(e){
  if(!state.editing||state.cameraMode||!state.pointers.has(e.pointerId))return;
  e.preventDefault();e.stopImmediatePropagation();
  const p=state.pointers.get(e.pointerId);p.x=e.clientX;p.y=e.clientY;
  if(state.gesture&&state.pointers.size===2){
   const now=currentAngle();const diff=replWrappedAngle(now-state.gesture.startAngle);
   const deg=THREE.MathUtils.radToDeg(diff)*Number(ui('pl-sensitivity').value);
   if(Math.abs(deg)>=.15&&applyAxisDelta(deg,state.gesture.start))state.gesture.changed=true;
  }
 }
 function finishPointer(e,cancelled=false){
  if(!state.editing||state.cameraMode||!state.pointers.has(e.pointerId))return;
  e.preventDefault();e.stopImmediatePropagation();
  const p=state.pointers.get(e.pointerId);state.pointers.delete(e.pointerId);
  try{canvas.releasePointerCapture?.(e.pointerId);}catch(_){}
  if(state.gesture){
   const gesture=state.gesture;
   if(cancelled){restore(gesture.start);state.gesture=null;status('Gesture cancelled, pose restored.');return;}
   if(state.pointers.size<2){
    state.gesture=null;
    if(gesture.changed){state.history.push(gesture.start);if(state.history.length>40)state.history.shift();state.redo=[];changed();}
   }
   return;
  }
  if(state.pointers.size)return;
  if(cancelled||Math.hypot(e.clientX-p.startX,e.clientY-p.startY)>REPL_TAP_DISTANCE_PX)return;
  const name=pickBone(e.clientX,e.clientY);
  if(name){state.lastEmpty=null;selectBone(name);return;}
  const prev=state.lastEmpty,now=Date.now();
  if(prev&&now-prev.time<REPL_DOUBLE_TAP_MS&&Math.hypot(e.clientX-prev.x,e.clientY-prev.y)<REPL_DOUBLE_TAP_PX){
   state.lastEmpty=null;clearSelection();return;
  }
  state.lastEmpty={x:e.clientX,y:e.clientY,time:now};
 }
 canvas.addEventListener('pointerdown',pointerDown,true);
 canvas.addEventListener('pointermove',pointerMove,true);
 canvas.addEventListener('pointerup',e=>finishPointer(e),true);
 canvas.addEventListener('pointercancel',e=>finishPointer(e,true),true);
 ui('pl-edit').addEventListener('change',e=>{if(e.target.checked){if(!enter())e.target.checked=false;}
  else leave();});
 ui('pl-skeleton').addEventListener('change',updateMarkers);
 ui('pl-additive').addEventListener('change',()=>status('Additive selection '+(ui('pl-additive').checked?'ON':'OFF')));
 ui('pl-axis').addEventListener('change',e=>{state.axis=e.target.value;ui('pl-delta').textContent='0° '+state.axis;
  status('Local rotation axis: '+state.axis+'. '+lockStatus());});
 for(const axis of 'XYZ')ui('pl-lock'+axis).addEventListener('change',e=>{
  state.locks[axis]=e.target.checked;status('Axis '+axis+' '+(e.target.checked?'locked':'unlocked'));});
 ui('pl-tips').addEventListener('change',e=>{state.protectedTips=e.target.checked;
  selectedLabel();status('Tip protection '+(state.protectedTips?'enabled':'disabled')+' for manual pose only.');});
 ui('pl-camera').addEventListener('click',()=>{
  if(!state.editing){status('Activate Pose Mode first.');return;}
  state.cameraMode=!state.cameraMode;orbit.enabled=state.cameraMode;
  ui('pl-camera').textContent=state.cameraMode?'Exit Camera Mode':'Camera / Orbit';
  status(state.cameraMode?'Camera mode: use one finger to orbit and two to zoom.':'Bone mode: tap to select; two-finger twist rotates.');
 });
 select.addEventListener('change',e=>{if(state.editing&&e.target.value)selectBone(e.target.value);});
 ui('pl-clear').addEventListener('click',clearSelection);
 ui('pl-minus').addEventListener('click',()=>rotateBy(-Number(ui('pl-step').value)));
 ui('pl-plus').addEventListener('click',()=>rotateBy(Number(ui('pl-step').value)));
 ui('pl-undo').addEventListener('click',()=>{if(!state.editing||!state.history.length)return;
  state.redo.push(snapshot());restore(state.history.pop());changed();});
 ui('pl-redo').addEventListener('click',()=>{if(!state.editing||!state.redo.length)return;
  state.history.push(snapshot());restore(state.redo.pop());changed();});
 ui('pl-reset-selected').addEventListener('click',()=>{
  if(!state.editing||!state.selected.size)return;remember();
  for(const n of state.selected){const q=state.baseline.get(n);if(q)byName.get(n).quaternion.copy(q);}
  updateMarkers();changed();});
 ui('pl-reset-all').addEventListener('click',()=>{
  if(!state.editing)return;remember();
  for(const b of bones)b.quaternion.copy(state.baseline.get(b.name));
  updateMarkers();changed();});
 function exportPose(){
  if(!state.editing){status('Activate Pose Mode to export a meaningful frame.');return;}
  root.updateMatrixWorld(true);
  const altered=[];
  for(const b of bones){const q0=state.baseline.get(b.name);
   const delta=q0.clone().invert().multiply(b.quaternion).normalize();
   const degrees=THREE.MathUtils.radToDeg(2*Math.acos(Math.min(1,Math.abs(delta.w))));
   if(degrees<=.01)continue;
   b.getWorldPosition(vec);
   altered.push({name:b.name,parent:b.parent?.name||'',baselineLocalQuaternion:q0.toArray(),
    editedLocalQuaternion:b.quaternion.toArray(),deltaLocalQuaternion:delta.toArray(),
    angularDistanceDegrees:Math.round(degrees*1000)/1000,worldJointPosition:vec.toArray()});
  }
  const payload={schema:'repl.pose-lab-bone-controls.v1',version:REPL_POSE_VERSION,
   sourceRepository:'Valar05/parametric-parambulator',sourceCanonicalPath:'assets/repl/Repl.glb',
   sourceCanonicalSha256:sourceSha,clip:state.clipName,clipTimeSeconds:state.clipTime,
   axis:state.axis,axisLocks:state.locks,protectedTipNames:[...REPL_TIP_BONES],
   tipRestFrozenForPreview:state.protectedTips,selected:[...state.selected],
   cameraPosition:camera.position.toArray(),cameraTarget:orbit.target.toArray(),
   alteredBones:altered,notes:'Browser-only pose reference. NOT baked into GLB. Excludes viewer helper geometry.'};
  const json=JSON.stringify(payload,null,2)+'\n';
  const blob=new Blob([json],{type:'application/json'}),url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download='REPL_POSE_REF_v0.6.6_'+Math.round(state.clipTime*1000)+'ms.json';
  document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  state.lastExported=true;status('Pose JSON exported: '+altered.length+' changed bones. Share the JSON and a frame screenshot.');
 }
 ui('pl-export').addEventListener('click',exportPose);
 ui('pl-edit').disabled=false;
 select.value='';selectedLabel();
 status('Skeleton ready. Enable Pose Mode to select and rotate without modifying the GLB.');
 return {update:updateMarkers,getState:()=>({editing:state.editing,selected:[...state.selected],
   axis:state.axis,locks:{...state.locks},dirty:state.dirty}),exportPose};
}
