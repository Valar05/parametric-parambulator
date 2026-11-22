import assert from 'node:assert/strict';
import {pelvisReachCorrection,segmentTerrainPenetration} from './terrain-hip.mjs';
const h={left:[.10,.90,0],right:[-.10,.90,0]},f={left:[.12,.03,.15],right:[-.12,.05,-.15]},l={left:[.37,.38],right:[.37,.38]};
const noTerrain=()=>0;
let out=pelvisReachCorrection(h,f,l,0,noTerrain,0);assert.equal(out.feasible,true,'pelvis must solve the overextended baseline');assert(out.delta<0,'hips must lower at startup when targets are below reach');
for(const low of [-.18,-.06,0,.05,.16]){
 const H={left:[.10,.65+low,0],right:[-.10,.65+low,0]};
 const F={left:[.12,.06,.12],right:[-.12,.08,-.12]};
 const x=pelvisReachCorrection(H,F,l,low,(xx,z)=>.04-.1*Math.sin(z),1/120);
 assert.equal(x.feasible,true);assert(Math.abs(x.delta)<=1.5/120+1e-8);
 for(const side of ['left','right']){
  const newY=H[side][1]+x.delta,depth=Math.hypot(F[side][0]-H[side][0],F[side][1]-newY,F[side][2]-H[side][2]);
  assert(depth<.752);
 }
}
const H={left:[.1,1,0],right:[-.1,1,0]};
const F={left:[.1,.05,.05],right:[-.1,.05,.05]};
const down=pelvisReachCorrection(H,F,l,0,noTerrain,0);assert(down.feasible&&down.delta<0,'at start must lower pelvis to reach ground');
assert(segmentTerrainPenetration([0,.20,0],[0,.20,1],(_,z)=>z>.5?.3:0)>.13);
assert(segmentTerrainPenetration([0,.6,0],[0,.6,1],()=>0)===0);
assert.throws(()=>pelvisReachCorrection({},F,l,0,noTerrain,0));
console.log('TERRAIN_TWO_LEG_PELVIS_REACH_AND_SHIN_COLLISION_PASS');
