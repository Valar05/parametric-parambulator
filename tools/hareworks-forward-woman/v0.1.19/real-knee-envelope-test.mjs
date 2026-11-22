import assert from 'node:assert/strict';
import fs from 'node:fs';
import {speedGait,transformSourceFoot} from './speed-gait.mjs';
const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const profile=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
assert(data.samples.length===60&&data.sourceSha256===profile.sourceSha256);
const norm=v=>Math.hypot(...v);
const angle=(L1,L2,dist)=>{
 const c=Math.max(-1,Math.min(1,(L1*L1+L2*L2-dist*dist)/(2*L1*L2)));
 return 180-Math.acos(c)*180/Math.PI;
};
for(const speed of [.15,.30,.52,.80]){
 const motion=speedGait(speed,1.224546);
 for(const side of ['left','right']){
  let maxExtra=0,maxDelta=0;
  for(const frame of data.samples){
   const leg=frame.legs[side],L1=profile[side].upperLength,L2=profile[side].lowerLength;
   const src={...leg,heel:leg.ankle,sole:leg.ankle,toe:leg.toe};
   const adapted=transformSourceFoot(src,side,motion);
   const d0=norm(leg.ankle.map((x,i)=>x-leg.hip[i]));
   const d1=norm(adapted.ankle.map((x,i)=>x-leg.hip[i]));
   const extra=angle(L1,L2,d1)-angle(L1,L2,d0);
   maxExtra=Math.max(maxExtra,extra);maxDelta=Math.max(maxDelta,Math.abs(extra));
  }
  assert(maxExtra<5.5&&maxDelta<6.0,'V017_KNEE_SOURCE_DEVIATION_EXCESS '+side+' speed='+speed+' max='+maxExtra);
  console.log('V017_ORIGINAL_RIG_KNEE_ENVELOPE_PASS side='+side+' speed='+speed+' peakExtra='+maxExtra.toFixed(3));
 }
}
