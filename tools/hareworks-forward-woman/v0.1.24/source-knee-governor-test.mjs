import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chooseSourceKnee,stableForwardPole,STABLE_LOCAL_POLES} from './source-knee-governor.mjs';
const source=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const profile=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
assert.equal(source.samples.length,60);
let maxBaseline=0,minSide=Infinity,maxAccepted=0,suppressed=0,baselineMismatch=0,cases=0;
const norm=a=>Math.hypot(...a);
for(const side of ['left','right']){
 const sign=side==='left'?1:-1,{upperLength,lowerLength}=profile[side];
 for(let i=0;i<60;i++){
  const entry=source.samples[i],s=entry.legs[side],cent=(entry.legs.left.hip[0]+entry.legs.right.hip[0])*.5;
  // Validate original archived knee-plane, as opposed to guessing an angle.
  // A static, forward (+Z) character-local bend pole. Not one retargeted
  // from an animated knee, and not an oscillating X/Y offset.
  assert(STABLE_LOCAL_POLES[side][2]>.88);
  const pole=stableForwardPole(side,entry.pelvisYaw);
  const base={hip:s.hip,sourceHip:s.hip,sourceKnee:s.knee,sourceAnkle:s.ankle,
    pole,upperLength,lowerLength,side,centerX:cent};
  const fit=chooseSourceKnee({...base,contactAnkle:s.ankle});
  assert.equal(fit.baselineMismatch,false);
  assert.equal(fit.acceptedFraction,1);
  maxBaseline=Math.max(maxBaseline,fit.kneeSourceError);minSide=Math.min(minSide,fit.signedKneeClearance);
  assert(fit.signedKneeClearance>.012);
  for(const x of [-.3,-.1,0,.08,.22])for(const z of [-.13,0,.13]){
   const contact=[s.ankle[0]-sign*x,s.ankle[1],s.ankle[2]+z];
   const k=chooseSourceKnee({...base,contactAnkle:contact});
   const repeat=chooseSourceKnee({...base,contactAnkle:contact});
   assert.deepEqual(k,repeat,'no hidden knee history / frame rate coupling');
   assert(k.signedKneeClearance>=.012-1e-8,'cannot cross pelvis center');
   assert(k.kneeSourceError<=.025+1e-8,'do not sacrifice knee silhouette for contact');
   assert(Math.abs(norm(k.ankle.map((v,j)=>v-s.hip[j]))-upperLength-lowerLength)<1.0);
   if(k.unfulfilledContactDelta>.025)suppressed++;
   maxAccepted=Math.max(maxAccepted,k.kneeSourceError);
   if(k.baselineMismatch)baselineMismatch++;
   cases++;
  }
 }
}
assert(maxBaseline<.020&&minSide>.018,'stable forward pole must resemble real archived knees');
assert(suppressed>30,'synthetic contact disturbance must challenge the knee guard');
for(const side of ['left','right'])for(const yaw of [-.4,0,.2,.6]){
 const p=stableForwardPole(side,yaw),q=stableForwardPole(side,yaw);
 assert.deepEqual(p,q);assert(Math.hypot(...p)>.85);
 const c=Math.cos(yaw),s=Math.sin(yaw),localX=p[0]*c-p[2]*s,localZ=p[0]*s+p[2]*c;
 assert(Math.abs(localX-STABLE_LOCAL_POLES[side][0])<1e-12,'lateral pole movement forbidden');
 assert(Math.abs(localZ-STABLE_LOCAL_POLES[side][2])<1e-12,'forward pole must stay out front');
}
assert.throws(()=>stableForwardPole('bad',0));
assert.equal(baselineMismatch,0);
assert.throws(()=>chooseSourceKnee({}));
console.log(`STATIC_FORWARD_KNEE_POLE_SOURCE_RESEMBLANCE_PASS samples=120 max=${maxBaseline} minSide=${minSide}`);
console.log(`STATELESS_KNEE_CONTACT_GOVERNOR_PASS cases=${cases} kneeMax=${maxAccepted} protectedConflicts=${suppressed}`);
