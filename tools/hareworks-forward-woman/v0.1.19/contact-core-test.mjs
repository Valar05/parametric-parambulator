import assert from 'node:assert/strict';
import {WorldContact,mod1,stanceAt,swingPoint,nextStartDelta,swingProgress,followCamera,cadenceFor,travelToNextContact} from './contact-core.mjs';
assert.equal(mod1(-.25),.75);
const cam0=followCamera([0,0,0],[-5,3,6]);const cam1=followCamera([0,0,4],[-5,3,6]);assert.deepEqual(cam1.position.map((v,i)=>v-cam0.position[i]),[0,0,4]);assert.deepEqual(cam1.position.map((v,i)=>v-cam1.target[i]),[-5,3,6]);
assert.equal(stanceAt(.95,.8,.55),true);
assert.equal(stanceAt(.4,.8,.55),false);
assert.equal(nextStartDelta(.3,.8),.5);
assert(Math.abs(swingPoint([0,0,0],[0,0,1],.5,.13)[1]-.13)<1e-10);
const c=new WorldContact({side:'left',start:0,duty:.55,sole:[0,0,0],groundY:0});
let max=0,range=0;
for(let cycle=0;cycle<3;cycle++)for(let i=0;i<240;i++){
 const p=i/240,body=cycle+p,result=c.step({phase:p,nominalLanding:[0,0,body+.45],footLift:.12});
 if(result.planted){const delta=Math.hypot(...result.target.map((v,j)=>v-result.anchor[j]));max=Math.max(max,delta)}
 range=Math.max(range,body);
}
assert.equal(max,0,'world stance target must not depend on traveling root');
assert(c.transitions>=5,'alternating stance/swing must actually occur');
assert(range>2,'root must travel even while anchor stays fixed');
const s=new WorldContact({side:'right',start:.4,duty:.55,sole:[.2,0,0],groundY:0});
assert.equal(s.isStance,false);
for(let i=0;i<=120;i++)s.step({phase:i/120,nominalLanding:[.2,0,i/120+.2]});
assert(s.transitions>=2);
for(const x of [-2,-1,0,.01,.5,.999,3.2])assert(swingProgress(x,.3,.55)>=0);
assert.throws(()=>new WorldContact({side:'bad',start:0,sole:[NaN,0,0]}));
assert.throws(()=>c.step({phase:.2,nominalLanding:[0,NaN,0]}));
console.log('WORLD_CONTACT_TEST_PASS transitions='+c.transitions+' maxPinnedTargetDrift='+max+' movingRoot='+range);

// Regression: speed input never changes world travel per gait cycle.
for(const s of [.36,.52,.76]){
 const stride=.66, cadence=cadenceFor(s,stride),worldInCycle=s/cadence;
 assert(Math.abs(worldInCycle-stride)<1e-12);
 for(const p of [.01,.2,.45,.98])assert(Math.abs(travelToNextContact(stride,p)-s*(p/cadence))<1e-12);
}
assert.equal(cadenceFor(0,.66),0);
assert.throws(()=>cadenceFor(0,0));
assert.throws(()=>travelToNextContact(.66,-.1));
assert.equal(travelToNextContact(.66,.45),.29700000000000004);
console.log('SPEED_CADENCE_LANDING_COHERENCE_PASS stride=.66 lift=.055');
