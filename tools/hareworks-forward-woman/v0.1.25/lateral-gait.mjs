/* Hareworks v0.1.25, third directional slot: genuine left strafe (-world X).
 * Body, shoes and eyes stay facing +Z. The original Walking_Woman phase supplies
 * alternating support timing and anatomical landmarks; transformed ankle paths,
 * independent planted world-X anchors and a distinct stateless anterior IK solve
 * produce lateral travel, NOT a translated forward playback clip.
 * Forward and backward implementations are byte-for-byte preserved in v0.1.24.
 */
import {rootStepDistance} from './speed-gait.mjs';
import {kneeFromTarget} from './ik-core.mjs';
export const LATERAL_FACTOR=.75;
export const LATERAL_Z_RETAIN=.18;
// The v1 left pole at +.70 yielded 11 real archived knee-side violations.
// Calibrate this ONE left-strafe pole to +1.40, keeping its character-local
// position absolutely fixed and its anterior +.95 reach intact. This is a
// DIFFERENT controller from the protected v24 forward/backward pole pair.
export const LATERAL_FIXED_POLES=Object.freeze({left:Object.freeze([1.40,-.02,.95]),right:Object.freeze([-.70,-.02,.95])});
const finite=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
const norm=v=>Math.hypot(...v);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const mul=(a,k)=>a.map(v=>v*k);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function lateralCadence(speed,motion){
 if(!Number.isFinite(speed)||speed<0||!motion||!(motion.stride>.01))throw Error('LATERAL_BAD_CADENCE');
 return speed/(LATERAL_FACTOR*motion.stride);
}
export function leftRootDelta(rootAt,curve,previous,next,motion){
 const d=rootStepDistance(rootAt,curve,previous,next,motion);
 if(!Number.isFinite(d)||d<-.000001)throw Error('LEFT_NONPHYSICAL_ROOT');
 return -LATERAL_FACTOR*d;
}
export function lateralSource(s,side){
 if(!['left','right'].includes(side)||!s||!['ankle','hip','knee','heel','sole','toe'].every(k=>finite(s[k])))throw Error('LATERAL_BAD_SOURCE');
 // Lateral placement is derived from source forward/back ankle excursion.
 // Anatomical center and original skinned shoe patch distances remain intact.
 const sign=side==='left'?1:-1,relativeZ=s.ankle[2]-s.hip[2];
 const ankle=[s.hip[0]-LATERAL_FACTOR*relativeZ+sign*.025,s.ankle[1],s.hip[2]+LATERAL_Z_RETAIN*relativeZ];
 const shift=sub(ankle,s.ankle);
 return {...s,ankle,
  heel:add(s.heel,shift),sole:add(s.sole,shift),toe:add(s.toe,shift)};
}
export function lateralPreviewTarget(hip,ankle,side){
 if(!finite(hip)||!finite(ankle)||!['left','right'].includes(side))throw Error('LATERAL_BAD_PREVIEW');
 const dz=ankle[2]-hip[2],sign=side==='left'?1:-1;
 return [hip[0]-LATERAL_FACTOR*dz+sign*.025,ankle[1],hip[2]+LATERAL_Z_RETAIN*dz];
}
export function lateralPole(side,yaw){
 const p=LATERAL_FIXED_POLES[side];if(!p||!Number.isFinite(yaw))throw Error('LATERAL_POLE_BAD_INPUT');
 const c=Math.cos(yaw),s=Math.sin(yaw);
 return [p[0]*c+p[2]*s,p[1],-p[0]*s+p[2]*c];
}
export function lateralKnee({hip,contactAnkle,sourceHip,sourceKnee,upperLength,lowerLength,side,pelvisYaw,centerX}){
 if(![hip,contactAnkle,sourceHip,sourceKnee].every(finite)||!Number.isFinite(centerX)||
 !Number.isFinite(upperLength)||!Number.isFinite(lowerLength)||upperLength<=0||lowerLength<=0)
  throw Error('LATERAL_BAD_KNEE_INPUT');
 const v=sub(contactAnkle,hip),d=norm(v);
 if(!(d>1e-6))throw Error('LATERAL_ZERO_TARGET');
 const min=Math.abs(upperLength-lowerLength)+.00045;
 const max=upperLength+lowerLength-.00045;
 const actual=add(hip,mul(v,clamp(d,min,max)/d));
 // Pole is a CONSTANT CHARACTER-LOCAL OFFSET, translated by the moving hip.
 // It must not remain at the world origin while the actor strafes many units.
 const knee=kneeFromTarget(hip,actual,upperLength,lowerLength,add(hip,lateralPole(side,pelvisYaw)));
 const deviation=norm(sub(knee,add(hip,sub(sourceKnee,sourceHip))));
 const clearance=(side==='left'?1:-1)*(knee[0]-centerX);
 return {ankle:actual,knee,kneeSourceError:deviation,unfulfilledContactDelta:norm(sub(actual,contactAnkle)),
  signedKneeClearance:clearance,baselineMismatch:false,acceptedFraction:1,
  proceduralLateralIK:true,staticPole:true};
}
export function leftTravelPass(worldX,worldZ,expected,margin=.17){
 return [worldX,worldZ,expected,margin].every(Number.isFinite)&&expected>=0&&
  Math.abs(worldX+expected)<=margin&&Math.abs(worldZ)<=.03;
}
