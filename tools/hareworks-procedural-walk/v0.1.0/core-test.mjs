import assert from 'node:assert/strict';
import {clamp,wrap,shortest,smooth,rotateY,landing,swing,chooseFoot,targetHeading,headingStep,distXZ,DEFAULTS} from './gait-core.mjs';
const near=(a,b,eps=1e-8)=>assert.ok(Math.abs(a-b)<=eps,`${a} != ${b}`);
near(shortest(-Math.PI+0.1,Math.PI-0.1),.2);
near(wrap(Math.PI*3),Math.PI);
for(let t=0;t<=1;t+=.02){const s=swing([0,0,0],[1,0,0],t,.1);assert.ok(s.every(Number.isFinite));assert.ok(s[1]>=0);if(t===0||t>=.999)near(s[1],0,1e-6)}
let origin=[0,0,0],foot=[-.12,.16,.15];for(let i=0;i<200;i++){origin[2]+=0.01;near(distXZ(foot,[-.12,.16,.15]),0)}
const p=landing([2,0,3],[.2,.16,0],Math.PI/2,[1,0,0],.1,.16);near(p[0],2.1);near(p[2],2.8);
assert.equal(chooseFoot(.2,.2,'left'),'right');assert.equal(chooseFoot(.9,.1,'right'),'left');assert.equal(chooseFoot(0,0,'left',1),'left');assert.equal(chooseFoot(0,0,'right',-1),'right');
const t=targetHeading(0,Math.PI*.9,Math.PI/5);near(t.twist,Math.PI/5);assert.ok(t.excess>0);
let h=0;for(let i=0;i<120;i++)h=headingStep(h,Math.PI/2,.8,1/60);assert.ok(h>1&&h<=Math.PI/2);
for(const v of [[0,0,1],[1,0,0],[-1,0,0],[0,0,-1]])near(distXZ(rotateY(v,.9),[0,0,0]),1);
assert.ok(DEFAULTS.reach>DEFAULTS.footLift);console.log('CORE_TESTS=PASS angle-wrap, swing, world-lock, turn-budget, alternation, directional landing');
