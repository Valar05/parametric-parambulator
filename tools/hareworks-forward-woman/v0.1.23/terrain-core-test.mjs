import assert from 'node:assert/strict';
import {TERRAIN_MODES,isProfileTerrain,terrainHeight as H,terrainNormal,terrainGrid,terrainBodyLift,longitudinalProfile,validTerrain} from './terrain-core.mjs';
import {SourceFootContact} from './foot-gait.mjs';
assert.equal(TERRAIN_MODES.length,8);
for(const z of [-4,0,1,3,7,14])for(const x of [-1.35,0,1.35])assert.equal(H(x,z,'flat',2),0);
for(const mode of ['profile-ridges','profile-steps','profile-ramp']){
 assert(isProfileTerrain(mode));
 for(const strength of [.2,1.1,3])for(let z=-2;z<=20;z+=.15){
  const y=H(0,z,mode,strength);
  for(const x of [-1.35,-.8,-.1,.1,.8,1.35])assert.equal(H(x,z,mode,strength),y,'GROUND_HEIGHT_MUST_BE_SAME_ACROSS_WIDTH '+mode);
  const n=terrainNormal(.6,z,mode,strength);
  assert(Math.abs(n[0])<1e-10,'NO_LATERAL_GRADE_IN_PROFILE '+mode);
  assert(Math.abs(Math.hypot(...n)-1)<1e-8);
 }
 const mesh=terrainGrid(mode,1.4,7,12,400);
 assert.equal(mesh.positions.length,13*401*3);
 for(let i=0;i<mesh.positions.length;i+=3){const [x,y,z]=mesh.positions.slice(i,i+3);assert(Math.abs(y-H(x,z,mode,1.4))<1e-12);}
 const edge=longitudinalProfile(mode,1.4,7,400);
 assert.equal(edge.length,401);
 for(const {z,y} of edge)assert(Math.abs(y-H(-1.35,z,mode,1.4))<1e-12);
}
assert(Math.max(...Array.from({length:200},(_,i)=>Math.abs(H(0,i*.085,'profile-ridges',3))))>.30,'MAX_RIDGE_NOT_STRESSFUL');
assert(H(0,4,'profile-steps',3)>.50,'MAX_STEP_NOT_STRESSFUL');
assert(H(0,4,'profile-ramp',3)>1.8,'MAX_RAMP_NOT_STRESSFUL');
assert(Math.abs(H(0,8,'rough',.7)-H(.8,8,'rough',.7))>1e-4,'old surface remains independent selectable option');
assert.throws(()=>H(0,0,'bad',1));assert.throws(()=>H(0,0,'profile-steps',3.01));
assert.throws(()=>terrainGrid('profile-steps',1,0,5,401));
const samples=Array.from({length:60},(_,i)=>{const q=i/60,z=.18*Math.sin(2*Math.PI*q);return {ankle:[.08,.18,z],hip:[.08,.9,0],knee:[.08,.53,.1],heel:[.08,.03,z-.07],sole:[.08,0,z],toe:[.08,.03,z+.08]};});
let tick=0,held=0,previous=null;
const C=new SourceFootContact({samples,gait:{start:.1,duty:.58},sourceGround:0,readWitness:k=>[.08,k==='ankle'?.18:0,tick*.003],rootAt:q=>q,terrainAt:(x,z)=>H(x,z,'profile-steps',2.5)});
for(let i=0;i<450;i++){
 tick=i;const r=C.step({phase:(i/130)%1,worldZ:i*.003,totalPhase:i/130});
 if(!r.planted){previous=null;continue;}
 assert(Math.abs(r.anchor[1]-H(r.anchor[0],r.anchor[2],'profile-steps',2.5))<1e-12,'STRESS_GROUND_CONTACT_Y');
 if(previous&&previous.pivot===r.pivot&&previous.transitions===C.transitions){assert.deepEqual(r.anchor,previous.anchor,'PINNED_CONTACT_SLID');held++;}
 previous={pivot:r.pivot,transitions:C.transitions,anchor:r.anchor};
}
assert(held>80);
let y=0;for(let i=0;i<400;i++){let ny=terrainBodyLift(y,H(0,i*.015,'profile-ramp',3),1/120);assert(Math.abs(ny-y)<=1.5/120+1e-11);y=ny;}
console.log('WIDTH_INVARIANT_LONGITUDINAL_PROFILE_PASS modes=3, strengths=3, width=2.70 units');
console.log('TRUE_STRESS_GEOMETRY_PASS fullMax=300% profileRidges/profileSteps/profileRamp');
console.log('REAL_TOUCHDOWN_ANCHOR_HEIGHT_AND_LOCK_PASS held='+held);
