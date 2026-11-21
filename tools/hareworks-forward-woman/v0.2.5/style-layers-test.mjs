import assert from 'node:assert/strict';
import {stylePose,sourceSignature,groupOf,qangleDeg,qslerp,zeroGains,PHASE_OFFSET} from './style-layers.mjs';
const N=360,ID=[0,0,0,1],base={bones:{}},normal={sampleCount:N,bones:{}},woman={sampleCount:N,bones:{}};
const names=['mixamorigHips','mixamorigLeftUpLeg','mixamorigLeftLeg','mixamorigLeftFoot','mixamorigLeftToeBase','mixamorigRightUpLeg','mixamorigRightLeg','mixamorigRightFoot','mixamorigRightToeBase','mixamorigSpine','mixamorigNeck','mixamorigHead','mixamorigLeftShoulder','mixamorigLeftArm','mixamorigLeftForeArm','mixamorigLeftHand','mixamorigRightShoulder','mixamorigRightArm','mixamorigRightForeArm','mixamorigRightHand'];
while(names.length<74)names.push('mixamorigLeftHandIndex'+names.length);
const rotate=a=>[0,0,Math.sin(a/2),Math.cos(a/2)];
for(const name of names){const gr=groupOf(name),staticAngle=gr==='arms'?.55:.18;
 base.bones[name]={quaternion:ID.slice(),position:name==='mixamorigHips'?[0,.92,.1065]:[0,0,0],scale:[1,1,1]};
 normal.bones[name]={quat:[],pos:[],scale:[]};woman.bones[name]={quat:[],pos:[],scale:[]};
 for(let k=0;k<N;k++){const t=2*Math.PI*k/N;normal.bones[name].quat.push(rotate(.15*Math.sin(t)));
  // Distinct initial orientation but SAME dynamic motion on unrelated fingers.
  woman.bones[name].quat.push(rotate(staticAngle+(gr==='arms'?.28:.20)*Math.sin(t)));
  normal.bones[name].pos.push(name==='mixamorigHips'?[.01*Math.sin(t),.92+.02*Math.cos(t),.1065-.8*k/N]:[0,0,0]);
  woman.bones[name].pos.push(name==='mixamorigHips'?[.01*Math.sin(t),.92+.013*Math.cos(t),.1065-.9*k/N]:[0,0,0]);
  for(const c of [normal,woman])c.bones[name].scale.push([1,1,1]);
 }
}
const z=stylePose(base,normal,woman,.4,zeroGains());assert.deepEqual(z.bones,base.bones,'zero gain EXACT base');
const l=stylePose(base,normal,woman,0,{pelvis:1,legs:1,torso:1,arms:1},0);assert.ok(Object.keys(l.bones).every(n=>qangleDeg(l.bones[n].quaternion,base.bones[n].quaternion)<.001),'first frame anchored');
const leg=stylePose(base,normal,woman,.23,{pelvis:0,legs:.8,torso:0,arms:0},0);
assert.ok(qangleDeg(leg.bones.mixamorigLeftLeg.quaternion,ID)>1,'leg motion present');
assert.equal(qangleDeg(leg.bones.mixamorigLeftArm.quaternion,ID),0,'arms untouched by leg layer');
const arm=stylePose(base,normal,woman,.27,{pelvis:0,legs:0,torso:0,arms:1},0);
assert.ok(qangleDeg(arm.bones.mixamorigLeftHand.quaternion,ID)>1,'arm dynamic transfer visible');
assert.equal(qangleDeg(arm.bones.mixamorigSpine.quaternion,ID),0,'torso independent');
const pelvis=stylePose(base,normal,woman,.3,{pelvis:1,legs:0,torso:0,arms:0},0);
assert.equal(pelvis.bones.mixamorigHips.position[2],.1065,'no root travel imported');
assert.ok(Math.abs(pelvis.bones.mixamorigHips.position[1]-.92)>1e-4,'bounce changed');
assert.deepEqual(base.bones.mixamorigHips.position,[0,.92,.1065],'approved base not mutated');
const seam0=stylePose(base,normal,woman,0,{pelvis:1,legs:1,torso:1,arms:1});
const seam1=stylePose(base,normal,woman,1-1e-8,{pelvis:1,legs:1,torso:1,arms:1});
assert.ok(qangleDeg(seam0.bones.mixamorigLeftArm.quaternion,seam1.bones.mixamorigLeftArm.quaternion)<.01,'periodic seam');
assert.throws(()=>stylePose(base,normal,woman,.2,{pelvis:2}),/GAIN_OUT_OF_RANGE/);
assert.throws(()=>stylePose({bones:{}},normal,woman,.2,{}),/SOURCE_TOPOLOGY_NOT_74/);
assert.ok(Math.abs(PHASE_OFFSET-.9777777777777777)<1e-9,'research phase constant pinned');
const d=sourceSignature(normal,woman,'mixamorigLeftArm',0,0);assert.ok(qangleDeg(d.dynamic,ID)<.001,'static pose not transferred');
console.log('STYLE_LAYER_TEST_PASS: phase-zero, source-static-offset subtraction, four layers, root protection, seam, negative cases');
