import assert from 'node:assert/strict';
import {angleDeg,slerp,alignPhase,compareClips,groupBone,mod1} from './analysis-core.mjs';
const q=z=>[0,0,Math.sin(z/2),Math.cos(z/2)];
assert.ok(angleDeg(q(0),q(Math.PI/2))>89.999);
assert.ok(angleDeg(q(0),q(0))<1e-5);
assert.ok(angleDeg(q(0),q(2*Math.PI))<1e-5);
assert.ok(angleDeg(slerp(q(0),q(Math.PI),.5),q(Math.PI/2))<1e-4);
assert.equal(groupBone('mixamorigLeftForeArm'),'forearms');
assert.equal(groupBone('mixamorigRightHandIndex1'),'fingers');
const n=240, names=['mixamorigLeftFoot','mixamorigRightFoot','mixamorigHips','mixamorigHead',...Array.from({length:70},(_,i)=>`Extra_${i}`)];
function fixture(phaseShift=0,armBias=0){const bones={};for(const name of names){bones[name]=[];for(let i=0;i<n;i++){
 const p=mod1(i/n-phaseShift),sgn=name.includes('Left')?1:name.includes('Right')?-1:0;
 const gait=2*Math.PI*p,x=.11*sgn*Math.sin(gait),z=.23*Math.sin(gait+sgn*.5);
 bones[name].push({lq:q((name==='mixamorigHead'?armBias:0)+.12*Math.sin(gait+sgn)),lp:[0,0,0],wp:[x,.9,z],hq:[0,0,0,1],hp:[x,.2+.01*Math.cos(gait),z]});
 }}return {count:n,boneNames:names,bones}}
const a=fixture(),b=fixture(.21,.1),d=alignPhase(a,b);assert.ok(Math.abs(d.womanPhaseOffset-.21)<.02,`phase alignment: ${d.womanPhaseOffset}`);
const report=compareClips(a,b,d);assert.equal(report.perBone.length,74);assert.ok(report.sampledMatchedPhases>150);
const head=report.perBone.find(x=>x.bone==='mixamorigHead');assert.ok(head.staticPoseOffsetDeg>5&&head.staticPoseOffsetDeg<7);assert.ok(head.motionDeltaRmsDeg<.6,`false dynamic difference ${head.motionDeltaRmsDeg}`);
const changed=fixture(.21,.1);changed.bones.mixamorigHead.forEach((x,i)=>x.lq=q(.1+.23*Math.sin(2*Math.PI*mod1(i/n-.21))));
const styled=compareClips(a,changed,d).perBone.find(x=>x.bone==='mixamorigHead');assert.ok(styled.motionDeltaRmsDeg>2,'animated delta must be detected');
assert.throws(()=>compareClips(a,{...b,boneNames:['bad']},d),/SOURCE_RIG_RESEARCH_CONTRACT/);
console.log('HAREWORKS_STYLE_RESEARCH_CORE_PASS: phase alignment, baseline-pose isolation, dynamic shoulder/hand-style detection, full 74-bone metrics, negative fixture');
