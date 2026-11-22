/* Hareworks v0.1.24: second cardinal locomotion slot, backward -Z.
 * The actor keeps forward +Z facing. The source data are startup calibration
 * samples, never an animation played on the visible rig. Backward contact
 * chronology is the reverse of the measured source chronology, with a reversed
 * root-velocity integral and reversed toe-to-heel rocker order.
 */
import {rootAt,phase01} from './root-motion.mjs';
export const DIRECTION_SLOTS=Object.freeze(['forward','backward']);
export function signForDirection(slot){
 if(!DIRECTION_SLOTS.includes(slot))throw Error('BACKWARD_UNKNOWN_DIRECTION_'+slot);
 return slot==='backward'?-1:1;
}
export function sourcePhase(slot,totalPhase){
 signForDirection(slot);
 return phase01(slot==='backward'?-totalPhase:totalPhase);
}
export function reversedSamples(bySide){
 if(!bySide||!['left','right'].every(s=>Array.isArray(bySide[s])&&bySide[s].length>=60))throw Error('BACKWARD_SOURCE_SAMPLES_MISSING');
 const out={};
 for(const side of ['left','right']){
  const a=bySide[side],n=a.length;
  out[side]=Array.from({length:n},(_,i)=>{
   const s=a[(n-i)%n];
   for(const key of ['ankle','hip','knee','heel','sole','toe'])
    if(!Array.isArray(s[key])||s[key].length!==3||!s[key].every(Number.isFinite))throw Error('BACKWARD_INVALID_SOURCE_'+key);
   if(!Array.isArray(s.q)||s.q.length!==4)throw Error('BACKWARD_INVALID_SOURCE_FOOT_QUATERNION');
   return {phase:i/n,ankle:s.ankle.slice(),hip:s.hip.slice(),knee:s.knee.slice(),
    heel:s.heel.slice(),sole:s.sole.slice(),toe:s.toe.slice(),q:s.q.slice()};
  });
 }
 return out;
}
export function reversedWindows(gaits){
 if(!gaits||!['left','right'].every(s=>gaits[s]&&Number.isFinite(gaits[s].start)&&Number.isFinite(gaits[s].duty)&&gaits[s].duty>.45&&gaits[s].duty<.73))
  throw Error('BACKWARD_SOURCE_STANCE_WINDOWS_INVALID');
 return Object.fromEntries(['left','right'].map(side=>{
  const g=gaits[side];return [side,{...g,start:phase01(-g.start-g.duty),
   method:'source-measured stance reversed in phase; foot rocker toe to heel'}];
 }));
}
export function backwardRootDelta(rootFn,curve,previous,next,motion){
 if(!curve||!motion||motion.referenceStride!==curve.stride||!Number.isFinite(previous)||!Number.isFinite(next)||next<previous)throw Error('BACKWARD_ROOT_CONTRACT_INVALID');
 const delta=(rootFn(curve,-next)-rootFn(curve,-previous))*motion.scale;
 if(!Number.isFinite(delta)||delta>Math.max(.005,(next-previous)*.25))throw Error('BACKWARD_ROOT_NONPHYSICAL_LOCAL_SPIKE');
 return delta;
}
export function signedTravelPass(slot,distance,expected,margin=.17){
 const sign=signForDirection(slot);
 if(!Number.isFinite(distance)||!Number.isFinite(expected)||expected<0)return false;
 return Math.abs(distance-sign*expected)<=margin;
}
