// REPL_TAIL_GIZMO v0.4.0
// Optional, non-mutating, real-model pivot measurement tool.
// Rendered on demand only. Never changes the GLB rig, joints or skins.
// This file is embedded verbatim by the Git-authored v0.4 campaign runner.
function installTailPivotGizmo({scene,camera,canvas,orbit,renderer,root,THREE,TransformControls,status}) {
  const get = id => document.getElementById(id);
  const chosen = new THREE.Vector3(0,1.05,-0.93); // preserved v0.3 root pivot
  const arcEstimate = new THREE.Vector3(0.002,1.204,-0.889); // not owner-approved
  const originalSourceSha = 'd28a8b4537ea6396839dc8e3b1f94127d97f93b3308f0d75d8c371d1c139bd9f';
  const marker = new THREE.Group();
  marker.name='REPL_OPTIONAL_PIVOT_MARKER_V040';
  marker.position.copy(chosen);
  const orb = new THREE.Mesh(
    new THREE.SphereGeometry(.012,14,12),
    new THREE.MeshBasicMaterial({color:0x00fff1,depthTest:false}));
  orb.renderOrder=999;
  marker.add(orb);
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(.027,.0015,6,64),
    new THREE.MeshBasicMaterial({color:0x26d9ff,depthTest:false}));
  marker.add(ring);ring.renderOrder=999;
  const arrow = new THREE.ArrowHelper(new THREE.Vector3(0,.7,-.7).normalize(),
    new THREE.Vector3(),.14,0x00d6c9,.02,.01);
  marker.add(arrow);
  scene.add(marker);
  const existing = new THREE.Mesh(
    new THREE.SphereGeometry(.012,12,10),
    new THREE.MeshBasicMaterial({color:0xffb04a,depthTest:false}));
  existing.position.copy(chosen);existing.renderOrder=998;scene.add(existing);
  const transform = new TransformControls(camera,canvas);
  transform.attach(marker);
  transform.setMode('translate');
  transform.setSpace('world');
  transform.setSize(.72);
  scene.add(transform.getHelper());
  transform.addEventListener('dragging-changed', e => {
    orbit.enabled = !e.value;
  });
  transform.addEventListener('objectChange',updateFields);
  let enabled=false, ghost=false, wire=false;
  const bodies=[];
  root.traverse(o=>{if(o.isSkinnedMesh){bodies.push({
    mesh:o, material:o.material
  });}});
  function updateBody() {
    for (const {mesh,material} of bodies) {
      if (mesh.material !== material) {
        (Array.isArray(mesh.material)?mesh.material:[mesh.material])
          .forEach(m=>{if(m&&!(Array.isArray(material)?material:[material]).includes(m))
            m.dispose();});
      }
      if (enabled && (ghost||wire)) {
        const clone = m => {
          const c=m.clone();c.transparent=true;c.opacity=ghost?.21:1;
          c.depthWrite=!ghost;c.side=THREE.DoubleSide;c.wireframe=wire;
          return c;
        };
        mesh.material=Array.isArray(material)?material.map(clone):clone(material);
      } else mesh.material=material;
    }
  }
  function fmt(n){return Number(n).toFixed(5);}
  function updateFields(){
    const p=marker.position;
    for(const [id,v] of [['pivotX',p.x],['pivotY',p.y],['pivotZ',p.z]]) {
      get(id).value=fmt(v);
    }
    get('gizmo-coordinates').value='X='+fmt(p.x)+', Y='+fmt(p.y)+', Z='+fmt(p.z);
    get('gizmo-status').textContent='Pivot ['+[p.x,p.y,p.z].map(fmt).join(', ')+'] (guide only)';
  }
  function fromInputs(){
    const values=['pivotX','pivotY','pivotZ'].map(id=>Number(get(id).value));
    if(values.every(Number.isFinite)){marker.position.set(...values);updateFields();}
  }
  for(const id of ['pivotX','pivotY','pivotZ'])
    get(id).addEventListener('change',fromInputs);
  get('gizmo-original').addEventListener('click',()=>{
    marker.position.copy(chosen);updateFields();
  });
  get('gizmo-arc-estimate').addEventListener('click',()=>{
    marker.position.copy(arcEstimate);updateFields();
    status.textContent='Intersection ARC estimate loaded for comparison; it is not a certified joint center.';
  });
  function refreshRing(){
    ring.geometry.dispose();
    ring.geometry=new THREE.TorusGeometry(
      Number(get('gizmo-radius').value),.0015,6,64);
    const angle=Number(get('gizmo-tilt').value)*Math.PI/180;
    const direction=new THREE.Vector3(0,Math.cos(angle),Math.sin(angle)).normalize();
    ring.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),direction);
    arrow.setDirection(direction);
    ring.visible=enabled&&get('gizmo-ring').checked;
    get('gizmo-radius-value').textContent=Number(get('gizmo-radius').value).toFixed(3);
    get('gizmo-tilt-value').textContent=get('gizmo-tilt').value;
  }
  get('gizmo-radius').addEventListener('input',refreshRing);
  get('gizmo-tilt').addEventListener('input',refreshRing);
  get('gizmo-ring').addEventListener('change',refreshRing);
  get('gizmo-xray').addEventListener('change',()=>{
    ghost=get('gizmo-xray').checked;updateBody();
  });
  get('gizmo-wire').addEventListener('change',()=>{
    wire=get('gizmo-wire').checked;updateBody();
  });
  function enable(yes){
    enabled=!!yes;
    get('gizmo-panel').hidden=!enabled;
    marker.visible=enabled;
    transform.visible=enabled;transform.enabled=enabled;
    existing.visible=enabled&&get('gizmo-show-original').checked;
    ghost=enabled&&get('gizmo-xray').checked;
    wire=enabled&&get('gizmo-wire').checked;
    updateBody();refreshRing();updateFields();
  }
  get('gizmo-enable').addEventListener('change',e=>{
    enable(e.target.checked);
    status.textContent=enabled
      ? 'Optional pivot gizmo enabled. It edits an overlay only; animation and rig are unchanged.'
      : 'Pivot gizmo hidden. Original textured materials restored.';
  });
  get('gizmo-show-original').addEventListener('change',()=>{
    existing.visible=enabled&&get('gizmo-show-original').checked;
  });
  async function copy(){
    const value=get('gizmo-coordinates').value;
    try {
      if(!navigator.clipboard?.writeText)throw new Error('clipboard unavailable');
      await navigator.clipboard.writeText(value);
      status.textContent='Selected pivot coordinates copied.';
    } catch(e) {
      get('gizmo-coordinates').focus();
      get('gizmo-coordinates').select();
      const ok=document.execCommand('copy');
      status.textContent=ok?'Coordinates copied.':'Coordinates selected; copy them manually.';
    }
  }
  get('gizmo-copy').addEventListener('click',copy);
  get('gizmo-export').addEventListener('click',()=>{
    const p=marker.position;
    const record={
      subject:'Repl tail root pivot placement',
      tool:'Repl Integrated Tail Gizmo v0.4.0',
      inputGLBSha256:originalSourceSha,
      coordinateSpace:'Original Repl.glb glTF world; +Y up, +Z forward',
      x:p.x,y:p.y,z:p.z,
      priorV030Root:[chosen.x,chosen.y,chosen.z],
      openArcEstimate:[arcEstimate.x,arcEstimate.y,arcEstimate.z],
      ringRadius:Number(get('gizmo-radius').value),
      ringTiltDegrees:Number(get('gizmo-tilt').value),
      method:'Manual placement, original textured rig view',
      sourceIsOpenArcNotExactRing:true,
      appliedToRig:false,
      ownerVerdict:'OWNER_SELECTED_NOT_YET_COMMITTED'
    };
    const url=URL.createObjectURL(new Blob(
      [JSON.stringify(record,null,2)],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;
    link.download='Repl_TailPivot_Selected_v0.4.0.json';
    link.click();
    setTimeout(()=>URL.revokeObjectURL(url),3000);
    status.textContent='Pivot JSON download requested, rig remains unchanged.';
  });
  get('gizmo-focus').addEventListener('click',()=>{
    const p=marker.position;
    orbit.target.copy(p);
    camera.position.set(p.x+1.05,p.y+.40,p.z-1.15);
    camera.lookAt(orbit.target);orbit.update();
  });
  get('gizmo-reset-camera').addEventListener('click',()=>{
    document.getElementById('view').dispatchEvent(new Event('change'));
  });
  enable(false); // Explicit opt-in. No body material changes by default.
  return {
    get enabled(){return enabled;},
    pivot:marker.position,
    disable:()=>{get('gizmo-enable').checked=false;enable(false);}
  };
}
