/* v0.1.8: upper-body source t=0 pose is the authority, not restored bind pose.
 * Track evaluations use phase-driven equations only, never clip playback.
 * Rotations and translations are fitted as deltas FROM source time zero.
 */
import {quatConjugate,quatMultiply,quatLog,quatExp,fitVectorSeries,evalVectorSeries} from '../v0.1.5/upper-kernel.mjs';
function isVec(v,n){return Array.isArray(v)&&v.length===n&&v.every(Number.isFinite)}
export function fitSourceAnchoredTrack(samples,maxHarmonics=12){
 if(!Array.isArray(samples)||samples.length<2*maxHarmonics+4||
    !samples.every(s=>s&&isVec(s.quaternion,4)&&isVec(s.position,3)))throw Error('UPPER_SOURCE_ANCHOR_SAMPLES');
 const q0=samples[0].quaternion.slice(),p0=samples[0].position.slice();
 const norm=Math.hypot(...q0);if(Math.abs(norm-1)>1e-4)throw Error('UPPER_SOURCE_QUATERNION_NOT_UNIT');
 const rotations=samples.map(s=>quatLog(quatMultiply(quatConjugate(q0),s.quaternion)));
 const positions=samples.map(s=>s.position.map((v,i)=>v-p0[i]));
 return {baselineQuaternion:q0,baselinePosition:p0,
  rotation:fitVectorSeries(rotations,maxHarmonics),translation:fitVectorSeries(positions,maxHarmonics),
  sampleCount:samples.length,maxHarmonics};
}
export function evalSourceAnchoredTrack(fit,phase,harmonics,strength){
 if(!fit||!isVec(fit.baselineQuaternion,4)||!isVec(fit.baselinePosition,3))throw Error('UPPER_ANCHOR_INVALID');
 if(!Number.isInteger(harmonics)||harmonics<1||harmonics>fit.maxHarmonics)throw Error('UPPER_ANCHOR_HARMONICS');
 if(!Number.isFinite(strength)||strength<0||strength>1.5)throw Error('UPPER_ANCHOR_STRENGTH');
 const rotation=evalVectorSeries(fit.rotation,phase,harmonics,strength),translation=evalVectorSeries(fit.translation,phase,harmonics,strength);
 return {quaternion:quatMultiply(fit.baselineQuaternion,quatExp(rotation)),
  position:fit.baselinePosition.map((v,i)=>v+translation[i])};
}
