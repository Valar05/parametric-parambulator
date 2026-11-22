import assert from 'node:assert/strict';
import fs from 'node:fs';
import {LATERAL_FACTOR,LATERAL_FIXED_POLES,lateralCadence,leftRootDelta,lateralSource,lateralPreviewTarget,lateralPole,lateralKnee,leftTravelPass} from './lateral-gait.mjs';
import {rootAt} from './root-motion.mjs';
import {speedGait} from './speed-gait.mjs';
import {sourceAt} from './foot-gait.mjs';
import {independentPose} from '../v0.1.2/pose-kernel.mjs';
import {kneeFromTarget} from './ik-core.mjs';
const D=1.224546,curve={stride:D},linear=(_c,q)=>D*q;
const motion=speedGait(.52,D);
assert(LATERAL_FACTOR>=.65&&LATERAL_FACTOR<=.9);
assert(lateralCadence(.52,motion)>motion.cadence);
let t=0,x=0;
for(let i=0;i<1800;i++){
 const dt=1/120,prev=t;t+=lateralCadence(.52,motion)*dt;
 const step=leftRootDelta(linear,curve,prev,t,motion);
 assert(step<=0&&step>-.012,'physical -X increments');x+=step;
}
assert(leftTravelPass(x,0,.52*15,.00001),'exact lateral travel speed');
assert(!leftTravelPass(x,.4,.52*15,.02),'reject fake diagonally-drifting X travel');
assert.throws(()=>lateralCadence(-1,motion));
const start={hip:[.11,.91,.13],knee:[.11,.55,.2],ankle:[.12,.21,.39],heel:[.12,.02,.30],sole:[.12,.01,.39],toe:[.12,.02,.51],q:[0,0,0,1]};
let left=lateralSource(start,'left'),right=lateralSource(start,'right');
assert(left.ankle[0]<start.ankle[0]-.1,'left swing must stride laterally');
assert(Math.abs(left.ankle[2]-start.hip[2])<Math.abs(start.ankle[2]-start.hip[2])*.20);
assert.equal(left.ankle[1],start.ankle[1]);
assert(Math.max(...left.toe.map((v,i)=>Math.abs((v-left.ankle[i])-(start.toe[i]-start.ankle[i]))))<1e-12,'shoe shape rigid');
assert(Math.abs((right.ankle[0]-left.ankle[0])+.05)<1e-12);
assert.deepEqual(lateralPreviewTarget(start.hip,start.ankle,'left'),left.ankle);
assert.throws(()=>lateralSource(start,'north'),/BAD_SOURCE/);
for(let side of ['left','right']){
 let pole=lateralPole(side,0);assert.deepEqual(pole,LATERAL_FIXED_POLES[side]);
 assert(pole[2]>.90,'static pole stays well ahead of body');
 const sg=side==='left'?1:-1;
 const H=[sg*.12,.92,.12],A=[sg*.13,.22,.18],K=lateralKnee({hip:H,contactAnkle:A,
  sourceHip:H,sourceKnee:[sg*.17,.59,.21],upperLength:.357,lowerLength:.38,side,pelvisYaw:0,centerX:0});
 assert(Math.hypot(...K.ankle.map((v,i)=>v-H[i]))<.737);
 assert(sg*K.knee[0]>=.012,'knee on anatomical side');
 assert(K.unfulfilledContactDelta<.005);
}
const archivePath=process.argv[2],profilePath=process.argv[3];
if(archivePath&&profilePath){
 const S=JSON.parse(fs.readFileSync(archivePath,'utf8')).samples;
 const p=JSON.parse(fs.readFileSync(profilePath,'utf8'));
 assert.equal(S.length,60);let crossings=0,maxReq=0;
 for(const src of S)for(const side of ['left','right']){
  const raw={...src.legs[side],heel:src.legs[side].ankle,sole:src.legs[side].ankle,toe:src.legs[side].ankle};
  const q=lateralSource(raw,side),g=src.legs[side],center=(src.legs.left.hip[0]+src.legs.right.hip[0])*.5;
  const k=lateralKnee({hip:g.hip,contactAnkle:q.ankle,sourceHip:g.hip,sourceKnee:g.knee,
  upperLength:p[side].upperLength,lowerLength:p[side].lowerLength,side,pelvisYaw:0,centerX:center});
  if(k.signedKneeClearance<.012)crossings++;
  maxReq=Math.max(maxReq,k.unfulfilledContactDelta);
 }
 assert.equal(crossings,0,'source archive knee must stay on its side');
 assert(maxReq<.009,'archived lateral step must be anatomically reachable');
 // Second gate: 360 source-interpolated midframes, with the ACTUAL fitted
 // pelvis yaw, not a convenient yaw=0 assumption. Keep the previously hard
 // centerline guard, with a stronger 0.015u protected margin.
 const motionPath=process.argv[4];
 assert(motionPath,'actual fitted pelvis motion profile is mandatory');
 const motionFit=JSON.parse(fs.readFileSync(motionPath,'utf8'));
 const bySide=Object.fromEntries(['left','right'].map(side=>[side,S.map((item,i)=>{
  const d=item.legs[side];
  return {phase:i/S.length,hip:d.hip,knee:d.knee,ankle:d.ankle,
   heel:d.ankle,sole:d.ankle,toe:d.toe,q:[0,0,0,1]};
 })]));
 let minMid=Infinity,maxKneeStep=0,maxInterpReach=0,oldPoleFails=0;
 for(const side of ['left','right']){
  const sg=side==='left'?1:-1;let priorKnee=null;
  for(let i=0;i<360;i++){
   const q=i/360,raw=sourceAt(bySide[side],q),other=sourceAt(bySide[side==='left'?'right':'left'],q);
   const transformed=lateralSource(raw,side);
   const yaw=independentPose(motionFit,q*motionFit.duration).pelvisYaw;
   const hipCenter=(raw.hip[0]+other.hip[0])*.5;
   const k=lateralKnee({hip:raw.hip,contactAnkle:transformed.ankle,
    sourceHip:raw.hip,sourceKnee:raw.knee,
    upperLength:p[side].upperLength,lowerLength:p[side].lowerLength,
    side,pelvisYaw:yaw,centerX:hipCenter});
   minMid=Math.min(minMid,k.signedKneeClearance);
   maxInterpReach=Math.max(maxInterpReach,k.unfulfilledContactDelta);
   if(priorKnee){const d=Math.hypot(...k.knee.map((v,j)=>v-priorKnee[j]));maxKneeStep=Math.max(maxKneeStep,d);}
   priorKnee=k.knee;
   if(side==='left'){
    const pole=[raw.hip[0]+.70,raw.hip[1]-.02,raw.hip[2]+.95];
    const legacy=kneeFromTarget(raw.hip,k.ankle,p[side].upperLength,p[side].lowerLength,pole);
    if(legacy[0]-hipCenter<.012)oldPoleFails++;
   }
  }
 }
 assert(minMid>=.015,'ARCHIVED_MIDFRAME_KNEE_CROSSES_CENTER_OR_CLEARANCE_TOO_SMALL '+minMid);
 assert(maxKneeStep<.020,'LATERAL_POLE_MIDFRAME_KNEE_DISCONTINUITY '+maxKneeStep);
 assert(maxInterpReach<.009,'ARCHIVED_MIDFRAME_LATERAL_ANKLE_UNREACHABLE '+maxInterpReach);
 assert(oldPoleFails>=8,'INJECTED_OLD_PLUS_070_POLE_NOT_REJECTED '+oldPoleFails);
 console.log('LEFT_LATERAL_ARCHIVED_KNEE_ENVELOPE_PASS 120 source poses; 720 yaw-aware midframe leg solves; minSide='+minMid.toFixed(5)+' maxKneeFrameStep='+maxKneeStep.toFixed(5)+' oldPoleRejectedFrames='+oldPoleFails+' maxReachClamp='+maxReq);
}
console.log('LEFT_WORLD_X_PROCEDURAL_ROOT_SOURCE_PRESERVATION_PASS displacement='+x.toFixed(5));
