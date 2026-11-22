import assert from 'node:assert/strict';
import fs from 'node:fs';
import {speedGait,transformSourceFoot} from './speed-gait.mjs';
const reference=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const profile=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
assert.equal(reference.samples.length,60);
const norm=v=>Math.hypot(...v);
function kneeFlex(l1,l2,H,A){
 const d=norm(A.map((v,i)=>v-H[i]));
 return 180-Math.acos(Math.max(-1,Math.min(1,(l1*l1+l2*l2-d*d)/(2*l1*l2))))*180/Math.PI;
}
let sampled=0;
for(const speed of [.0,.15,.30,.52,.8])for(const side of ['left','right']){
 const motion=speedGait(speed,1.224546), l=profile[side],flexErrors=[];
 for(const s of reference.samples){
  const raw=s.legs[side];
  const input={...raw,heel:raw.ankle.slice(),sole:raw.ankle.slice(),toe:raw.toe.slice()};
  const adjusted=transformSourceFoot(input,side,motion);
  for(const k of ['hip','ankle','knee','heel','sole','toe'])
   assert.deepEqual(adjusted[k],input[k],'speed or foot heading must not move pre-IK joint/patch '+side+'/'+k);
  const f0=kneeFlex(l.upperLength,l.lowerLength,raw.hip,raw.ankle),
        f1=kneeFlex(l.upperLength,l.lowerLength,adjusted.hip,adjusted.ankle);
  flexErrors.push(Math.abs(f0-f1));sampled++;
 }
 assert(Math.max(...flexErrors)<1e-10,'original source knee flexion changed at speed '+speed);
 const originalNearFull=reference.samples.filter(s=>{
  const a=s.legs[side].ankle,h=s.legs[side].hip;
  return norm(a.map((v,i)=>v-h[i]))>l.upperLength+l.lowerLength-.005;
 });
 assert(originalNearFull.length>=10,'reference must exercise nearly straight source leg');
 for(const s of reference.samples){
  const a=s.legs[side].ankle,h=s.legs[side].hip;
  assert(norm(a.map((v,i)=>v-h[i]))<=l.upperLength+l.lowerLength-.00025,
   'reference source reach cannot fit new numerical IK safety limit');
 }
}
console.log('V018_PRE_IK_KNEE_AND_ANKLE_REFERENCE_EXACT_PASS samples='+sampled);
