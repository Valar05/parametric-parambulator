import assert from 'node:assert/strict';
import {TERRAIN_MODES,terrainHeight,terrainNormal,terrainGrid,terrainBodyLift} from './terrain-core.mjs';
import {SourceFootContact} from './foot-gait.mjs';
const H=terrainHeight;
assert.equal(TERRAIN_MODES.length,5);
for(const x of [-2.1,0,1.4])for(const z of [-7,0,2,15])assert.equal(H(x,z,'flat',.65),0);
assert(Math.abs(H(0,0,'rough',.65))<1e-12);
assert(H(0,10,'uphill',1)>H(0,2,'uphill',1));
assert(H(0,10,'downhill',1)<H(0,2,'downhill',1));
assert(H(1,0,'cross-slope',1)>H(-1,0,'cross-slope',1));
for(const mode of TERRAIN_MODES){
 const mesh=terrainGrid(mode,.7,10,15,35),count=(15+1)*(35+1);
 assert.equal(mesh.positions.length,count*3);
 assert.equal(mesh.colors.length,count*3);
 assert.equal(mesh.indices.length,15*35*6);
 for(let i=0;i<count;i++){
  const [x,y,z]=mesh.positions.slice(i*3,i*3+3);
  assert(Math.abs(y-H(x,z,mode,.7))<1e-12,'visible mesh must be collision surface');
 }
 for(const i of mesh.indices)assert(i>=0&&i<count);
 for(const z of [0,.5,3,12]){
  const n=terrainNormal(.09,z,mode,.7);
  assert(n.every(Number.isFinite)&&Math.abs(Math.hypot(...n)-1)<1e-10);
  assert(n[1]>.95,'terrain too steep for this conservative IK test');
 }
}
assert.throws(()=>H(0,0,'random',1));
assert.throws(()=>H(NaN,0,'rough',1));
assert.throws(()=>terrainGrid('rough',1,0,0,10));
const samples=Array.from({length:60},(_,i)=>{
 const q=i/60,z=.18*Math.sin(2*Math.PI*q),x=.09;
 return {ankle:[x,.18,z],hip:[x,.9,0],knee:[x,.53,.1],heel:[x,.03,z-.07],sole:[x,0,z],toe:[x,.03,z+.08]};
});
let seen=0,stance=0,swing=0,anchorAtStance=null,held=0;
const witness=(kind)=>kind==='ankle'?[.09,.18,seen*.003]:[.09,0,seen*.003];
const contact=new SourceFootContact({samples,gait:{start:.10,duty:.58},sourceGround:0,
 readWitness:witness,rootAt:q=>q,terrainAt:(x,z)=>H(x,z,'rough',.7)});
for(let i=0;i<380;i++){
 seen=i;
 const phase=(i/130)%1;const result=contact.step({phase,worldZ:i*.003,totalPhase:i/130});
 assert(result.ankleTarget.every(Number.isFinite));
 if(result.planted){
  stance++;
  assert(Math.abs(result.anchor[1]-H(result.anchor[0],result.anchor[2],'rough',.7))<1e-12,'touchdown must land on real surface');
  if(anchorAtStance&&contact.pivot===anchorAtStance.pivot&&contact.transitions===anchorAtStance.transitions)
   {assert.deepEqual(result.anchor,anchorAtStance.anchor,'stance anchor slid while root walked');held++}
  anchorAtStance={anchor:result.anchor,pivot:contact.pivot,transitions:contact.transitions};
 }else{anchorAtStance=null;swing++;}
}
assert(stance>140&&swing>65&&held>60);
let y=0,prev=0;
for(let i=0;i<500;i++){
 const z=i*.004; y=terrainBodyLift(y,H(0,z,'rough',.7),1/120);
 assert(Math.abs(y-prev)<=.4/120+1e-11);prev=y;
}
assert.throws(()=>terrainBodyLift(0,1,NaN));
console.log('TERRAIN_MESH_EQUALS_PHYSICAL_HEIGHT_PASS modes='+TERRAIN_MODES.join(','));
console.log('TERRAIN_WORLD_TOUCHDOWN_LOCK_PASS stance='+stance+' swing='+swing+' held='+held);
console.log('TERRAIN_BODY_LIFT_CONTINUITY_PASS');
