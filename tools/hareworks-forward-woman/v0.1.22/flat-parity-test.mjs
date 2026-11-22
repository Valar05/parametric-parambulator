import assert from 'node:assert/strict';
import {SourceFootContact as OriginalContact} from '../v0.1.20/foot-gait.mjs';
import {SourceFootContact as TerrainContact} from './foot-gait.mjs';
const samples=Array.from({length:360},(_,i)=>{
 const q=i/360,phi=2*Math.PI*q,z=.22*Math.cos(phi),x=.10;
 return {q,ankle:[x,.2+.03*Math.max(0,Math.sin(phi)),z],hip:[x,.9,0],knee:[x,.56,.1],
  heel:[x,.015,z-.09],sole:[x,.0,z],toe:[x,.015,z+.10]};
});
let current=0;
const readWitness=kind=>kind==='ankle'?[.10,.20,current*.003]:[.10,.007,current*.003];
const options={samples,gait:{start:.14,duty:.59},sourceGround:0,groundY:0,readWitness,rootAt:q=>q};
const old=new OriginalContact(options),next=new TerrainContact({...options,terrainAt:null});
let comparisons=0;
for(let i=0;i<1200;i++){
 current=i;const phase=(i/193.2)%1,worldZ=i*.003;
 const a=old.step({phase,worldZ,totalPhase:i/193.2}),b=next.step({phase,worldZ,totalPhase:i/193.2});
 assert.deepEqual(b,a,'flat-ground source gait must be byte-equivalent numerically at frame '+i);
 assert.equal(next.activeDuty,old.activeDuty);
 assert.equal(next.transitions,old.transitions);
 comparisons++;
}
const bad=new TerrainContact({...options,terrainAt:()=>NaN});
assert.throws(()=>bad.step({phase:.2,worldZ:0,totalPhase:.2}),/TERRAIN_CONTACT_ANCHOR_INVALID/);
console.log('FLAT_GROUND_V020_CONTACT_NUMERIC_PARITY_PASS frames='+comparisons);
console.log('TERRAIN_CONTACT_INVALID_SURFACE_FAIL_CLOSED_PASS');
