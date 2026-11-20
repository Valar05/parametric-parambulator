/* Intentionally tests actual source measurements not a manufactured constant. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {curve,phase,independentPose,validateProfile,angleDiff} from './pose-kernel.mjs';
const profile=JSON.parse(fs.readFileSync(new URL('./motion-profile.json',import.meta.url)));
const source=JSON.parse(fs.readFileSync(new URL('./reference-samples.json',import.meta.url)));
validateProfile(profile);
assert.equal(source.sourceSha256,profile.sourceSha256);
assert.equal(source.samples.length,60);
assert.ok(source.samples.at(-1).t<profile.duration);
const dev={};
for(let i=1;i<60;i+=2){const row=source.samples[i],p=independentPose(profile,row.t);
 const fields={pelvisX:[p.pelvis[0],row.pelvis[0]],pelvisY:[p.pelvis[1],row.pelvis[1]],pelvisZ:[p.pelvis[2],row.pelvis[2]],pelvisYaw:[p.pelvisYaw,row.pelvisYaw]};
 for(const side of ['left','right']){
  for(let j=0;j<3;j++)fields[side+'Toe'+j]=[p.feet[side].toeVector[j],row.feet[side].toeVector[j]];
  fields[side+'AnkleYaw']=[p.feet[side].ankleYaw,row.feet[side].ankleYaw];
 }
 for(const [k,[a,b]] of Object.entries(fields)){
  const err=k.includes('Yaw')?Math.abs(angleDiff(a,b)):Math.abs(a-b);
  (dev[k]??=[]).push(err);
 }
}
const stats=Object.fromEntries(Object.entries(dev).map(([k,v])=>[k,{rms:Math.sqrt(v.reduce((a,b)=>a+b*b,0)/v.length),max:Math.max(...v)}]));
for(const [k,v] of Object.entries(stats)){
 let lim=k.includes('Yaw')?.2:k.startsWith('pelvis')?.035:.04;
 assert.ok(v.max<lim,`${k}: held-out maximum ${v.max} > ${lim}`);
}
for(const side of ['left','right']){
 const start=independentPose(profile,0).feet[side];const e=independentPose(profile,profile.duration-1e-8).feet[side];
 assert.ok(start.toeVector.every((v,i)=>Math.abs(v-e.toeVector[i])<1e-5));
 assert.ok(Math.abs(angleDiff(start.ankleYaw,e.ankleYaw))<1e-5);
}
for(let frame=0;frame<30;frame++){
 const t=frame/30,p=independentPose(profile,t);
 assert.ok([...p.pelvis,p.pelvisYaw,...Object.values(p.feet).flatMap(f=>[...f.toeVector,f.ankleYaw])].every(Number.isFinite));
}
assert.ok(Math.abs(phase(profile.duration,profile.duration)-1)<1e-8);
console.log(JSON.stringify({result:'PASS',sampleCount:60,independentHeldOutSamples:30,generatedFramesAt30fps:30,maxErrors:stats,limitations:'fit and phase math only; actual GLB skin and visual acceptance require browser'},null,2));
